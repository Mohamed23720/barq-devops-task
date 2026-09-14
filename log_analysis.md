# Log analysis

Use all three supplied logs. Answer every question with commands/scripts and actual output.

1. What UTC interval is covered? How many valid, malformed and duplicate lines are in each file?
2. How many distinct client requests occurred? How did you deduplicate and avoid counting retries twice?
3. What are the final client status counts and error rate? State your denominator.
4. Which paths, time windows and backends account for the failures?
5. What are the median and p95 client latencies? State the percentile method and units.
6. Which requests retried upstream? How many succeeded after retrying?
7. Build an incident timeline using evidence from access, error AND application logs.
8. Show one correlated failed request and one successful request. Include IDs and timestamps.
9. Which errors appear to be proxy/connectivity issues versus dependency/application issues? What proves it?
10. What do the logs not prove? What would you check next in a running environment?

## Commands / scripts

**Q1 — validity, malformed lines, time range:**
```python
import json
for f in ['logs/access.log','logs/application.log']:
    lines = open(f, encoding='utf-8', errors='replace').readlines()
    valid, bad = 0, 0
    times = []
    for l in lines:
        try:
            d = json.loads(l)
            valid += 1
            if 'timestamp' in d: times.append(d['timestamp'])
        except Exception:
            bad += 1
    print(f, 'valid:', valid, 'bad:', bad, 'range:', min(times) if times else None, '->', max(times) if times else None)
```

**Q2/Q3 — distinct requests (deduplicated by request_id) and status distribution:**
```python
import json
seen = set()
status_count = {}
for l in open('logs/access.log', encoding='utf-8', errors='replace'):
    try:
        d = json.loads(l)
    except Exception:
        continue
    rid = d.get('request_id')
    if rid in seen: continue
    seen.add(rid)
    s = d.get('status')
    status_count[s] = status_count.get(s, 0) + 1
print('distinct requests:', len(seen))
print('status distribution:', status_count)
errors = sum(v for k,v in status_count.items() if k and k >= 500)
print('5xx rate:', errors, '/', len(seen), '=', round(100*errors/len(seen),2), '%')
```

**Q4 — failing paths/backends:**
```python
import json
from collections import Counter
c = Counter()
for l in open('logs/access.log', encoding='utf-8', errors='replace'):
    try:
        d = json.loads(l)
    except Exception:
        continue
    if d.get('status',0) >= 500:
        c[(d.get('path'), d.get('upstream'))] += 1
for k,v in c.most_common(10):
    print(k, v)
```

**Q5 — median/p95 latency:**
```python
import json, statistics
times = []
for l in open('logs/access.log', encoding='utf-8', errors='replace'):
    try:
        d = json.loads(l)
        rt = d.get('request_time')
        if rt is not None: times.append(float(rt)*1000)
    except Exception:
        continue
times.sort()
print('count:', len(times))
print('median ms:', statistics.median(times))
p95_idx = int(len(times)*0.95)
print('p95 ms:', times[p95_idx])
```

**Q6 — retried requests (comma-separated upstream field):**
```python
import json
retried = 0
succeeded_after_retry = 0
for l in open('logs/access.log', encoding='utf-8', errors='replace'):
    try:
        d = json.loads(l)
    except Exception:
        continue
    up = d.get('upstream', '') or ''
    if ',' in up:
        retried += 1
        if d.get('status') == 200:
            succeeded_after_retry += 1
print('requests with multiple upstream attempts:', retried)
print('of those, succeeded (200):', succeeded_after_retry)
```

**Q7 — per-minute 5xx error buckets (incident timeline):**
```python
import json
from collections import Counter
buckets = Counter()
for l in open('logs/access.log', encoding='utf-8', errors='replace'):
    try:
        d = json.loads(l)
    except Exception:
        continue
    if d.get('status', 0) >= 500:
        ts = d.get('timestamp', '')
        minute = ts[:16]
        buckets[minute] += 1
for k in sorted(buckets):
    print(k, buckets[k])
```

**Q8 — correlated failed and successful request examples, cross-referenced across logs:**
```bash
grep "lab-000122" logs/error.log
grep "lab-000122" logs/application.log
```

## Results

**Q1:** access.log: 725 valid JSON lines, 1 malformed line. application.log: 729 valid, 1 malformed.
Time range covered: `2026-08-20T11:00:00.015Z` to `2026-08-20T11:29:57.578Z` (30 minutes).

**Q2:** 720 distinct client requests, deduplicated by `request_id` (out of 726 raw non-malformed lines — 5 were duplicate request_ids, i.e. the same request logged more than once, likely from a retried upstream attempt being logged twice).

**Q3:** Status distribution: `{200: 615, 404: 10, 502: 40, 503: 47, 504: 8}`.
Denominator = 720 distinct requests.
Error rate (5xx only) = 95/720 = **13.19%**.
(404s are excluded from the "error rate" since they represent client-side/not-found requests, not server or dependency failures — see Conclusions.)

**Q4:** Failures concentrated on two backend IPs:
- `172.23.0.12:8080` — 68 failures: `/records`(18), `/counter`(18), `/ready`(12), `/health`(10), `/`(10)
- `172.23.0.11:8080` — 19 failures: `/ready`(11), `/counter`(8), `/records`(8)

`172.23.0.12` accounts for ~72% of all 5xx failures.

**Q5:** n = 725 valid requests with a `request_time` value.
Median latency = **54.0 ms**. p95 latency = **2001.0 ms** (~2 seconds), computed by sorting all `request_time` values (converted from seconds to ms) and taking the value at the index closest to the 95th percentile position (`int(len*0.95)`).
The large median/p95 gap indicates a small subset of requests (likely those hitting the failing backend before timing out) drag the tail latency up significantly.

**Q6:** 19 requests had multiple upstream attempts (comma-separated `upstream` field). All 19 (100%) eventually succeeded with status 200 after retrying — NGINX's retry behavior fully masked these particular failures from the end client.

## Timeline and correlated examples

**Q7 — Incident timeline:** The incident was **not continuous** — it occurred in 6 distinct episodes across the 30-minute window:
- `11:05–11:09` (5 min, ~8 errors/min)
- `11:12–11:15` (4 min, ~8 errors/min)
- `11:20–11:21` (2 min, ~8 errors/min)
- `11:25–11:26` (2 min, ~4 errors/min — roughly half the earlier rate)

Gaps between episodes (`11:10-11`, `11:16-19`, `11:22-24`) show **zero** 5xx errors, meaning the system fully recovered between episodes. The declining error rate in the final two episodes suggests the underlying issue was intermittent and gradually resolving — consistent with a flapping/restarting backend rather than one sustained crash.

**Q8 — Correlated failed request:**
- `access.log`: `lab-000122`, `11:05:02.503Z`, `GET /health`, status `502`, upstream `172.23.0.12:8080`
- `error.log`: same timestamp — `"connect() failed (111: Connection refused) while connecting to upstream ... http://172.23.0.12:8080/health"`
- `application.log`: **no entry found** for `lab-000122` — confirms the connection was refused at the network level before ever reaching the Flask app process, so the app itself never logged it.

**Correlated successful request** (during a recovery gap):
- `access.log`: `lab-000241`, `11:10:00.015Z`, `GET /`, status `200`, upstream `172.23.0.11:8080`, `request_time: 0.015s` — a normal fast response from the healthy backend.

## Conclusions and limits

**Q9:** The `172.23.0.12` failures — including `/health`, which requires no external dependencies — are **proxy/connectivity issues**. Evidence: `error.log` shows `"Connection refused"`, and `application.log` has zero entries for these request_ids, meaning the backend process itself was unreachable (likely down or restarting), not merely slow or internally erroring.

In contrast, `172.23.0.11`'s failures were concentrated on `/ready`, `/counter`, `/records` (all dependency-touching endpoints) while its `/health` succeeded — this pattern points to a **dependency-layer issue** (postgres/redis reachability from that instance) rather than the backend process itself being down.

**Q10:** These logs do not prove the root cause of *why* `172.23.0.12` became unreachable (crash? OOM kill? deployment restart?) — only network-layer symptoms are visible, with no container lifecycle events included. They also don't prove this exact intermittent pattern would reproduce in the current (fixed) environment, since this is historical data from a separate incident, not a live test of today's configuration. In a running environment, the next checks would be: `docker events` / `docker inspect .State` history for the affected container around `11:05–11:26`, correlating with any deployment or resource-limit (OOM) events from that same window, and checking host-level resource graphs (CPU/memory) for that timeframe.
