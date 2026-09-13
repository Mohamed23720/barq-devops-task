# Troubleshooting journal

Keep chronological entries. Copy this block for each meaningful investigation.

## Entry / date / time
- Symptom:
- Hypothesis:
- Command or test:
- Actual output:
- Failed attempt and what changed your thinking:
- Root cause:
- Fix:
- Retest evidence:
- Related commit:
- Remaining uncertainty:

Do not fabricate a failed attempt just to fill the template. Record actual attempts.

## Entry 1 / 2026-09-12 / ~15:24 UTC
- Symptom: N/A — this is a pre-check before touching Docker, not a failure investigation.
- Hypothesis: The Flask app's own logic (routing, validation, response shape) should be correct independent of the broken Docker/networking environment.
- Command or test: `python -m unittest discover -s tests -v` (run inside a venv, fake dependencies, no real Postgres/Redis/Docker).
- Actual output: `Ran 8 tests in 0.166s — OK` (all 8 passed).
- Failed attempt and what changed your thinking: None — first attempt succeeded.
- Root cause: N/A.
- Fix: N/A.
- Retest evidence: 8/8 tests passing confirms app logic is sound; any issues found later must be in Docker/networking/config, not app code.
- Related commit: cd34351
- Remaining uncertainty: These tests use fake dependencies — they don't prove the real Postgres/Redis/Docker setup works.

## Entry 2 / 2026-09-12 / ~15:46 UTC
- Symptom: Dockerfile contained `COPY config/app.env /srv/app.env`, copying the file that holds the database password directly into the image layer.
- Hypothesis: This is unnecessary and a security leak — env vars are already injected at runtime via `env_file` in docker-compose.yml.
- Command or test: Reviewed Dockerfile line by line; ran `docker history barq-app` to confirm the app.env layer existed.
- Actual output: `docker history` showed a layer corresponding to the COPY of app.env.
- Failed attempt and what changed your thinking: None — confirmed directly from static review, no failed attempt needed.
- Root cause: Unnecessary COPY instruction baking secrets into the image itself.
- Fix: Removed the COPY line entirely. Secrets now only enter the container via env_file at runtime, never baked into the image.
- Retest evidence: `docker build -t barq-app .` still succeeds; `docker history barq-app` no longer shows the app.env layer.
- Related commit: 7df0629
- Remaining uncertainty: None.

## Entry 3 / 2026-09-12 / ~15:48 UTC
- Symptom: Dockerfile created a dedicated "app" user with `useradd`, but the final `USER root` instruction overrode it, so the container actually ran as root.
- Hypothesis: Leftover `USER root` line placed after the non-root user setup cancels its effect.
- Command or test: Traced the USER instructions top to bottom; ran `docker compose -p barq-assessment exec app-01 whoami`.
- Actual output: Returned `root` before the fix.
- Failed attempt and what changed your thinking: None.
- Root cause: Leftover `USER root` instruction placed after the non-root user setup.
- Fix: Changed `USER root` to `USER app`.
- Retest evidence: `docker compose -p barq-assessment exec app-01 whoami` now returns `app`, not `root`.
- Related commit: 7df0629
- Remaining uncertainty: None.

## Entry 4 / 2026-09-12 / ~18:42 UTC
- Symptom: N/A — this happened while applying the Entry 2/3 fixes, not a new investigation.
- Hypothesis: N/A
- Command or test: `docker compose -p barq-assessment up --build -d`
- Actual output: Build failed with `RUN pip install --no-cache-dir -r requirements.txt did not complete successfully: exit code: 1` because requirements.txt was not found in the image.
- Failed attempt and what changed your thinking: While removing the `COPY config/app.env` line, accidentally commented out `COPY requirements.txt` instead. The build error message pointed directly at the missing file, which made the mistake obvious immediately.
- Root cause: Wrong line was commented out during manual editing.
- Fix: Restored the `COPY requirements.txt ./requirements.txt` line, and correctly commented out `COPY config/app.env /srv/app.env` instead.
- Retest evidence: `docker compose -p barq-assessment up --build -d` now completes successfully (15/15 steps finished).
- Related commit: cd34351
- Remaining uncertainty: None.

## Entry 5 / 2026-09-13 / ~03:50 UTC
- Symptom: docker compose ps -a showed both app-01 and app-02 as "unhealthy" despite the app process running.
- Hypothesis: The Docker healthcheck might be targeting a path that doesn't exist on the app.
- Command or test: docker logs app-01/app-02 --tail 50; docker inspect app-01 --format '{{json .Config.Healthcheck}}'; manual test with docker exec app-01/app-02 python -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:8080/health').status)"
- Actual output: Logs showed repeated "GET /healthz" returning 404 every ~5 seconds (matching the healthcheck interval), timestamped 2026-09-12T20:50–20:52 UTC. docker inspect confirmed the healthcheck Test field targets /healthz. Manual request to /health returned 200 on both app-01 and app-02.
- Failed attempt and what changed your thinking: None — evidence was conclusive on first pass.
- Root cause: The Docker healthcheck was configured to call /healthz, a path that doesn't exist on the app (the real route is /health), causing Docker to mark both containers unhealthy even though the app itself was working correctly.
- Fix: Changed the healthcheck path in docker-compose.yml from /healthz to /health.
- Retest evidence: After `docker compose -p barq-assessment up --build -d`, `docker compose -p barq-assessment ps -a` shows app-01 and app-02 both as "Up ... (healthy)".
- Related commit: ef9b48d
- Remaining uncertainty: None.

## Entry 6 / 2026-09-13 / ~04:06 UTC
- Symptom: app-02's own logs showed "instance_id": "app-01" instead of "app-02" (confirmed also via `docker exec app-02 env | grep INSTANCE_ID` returning app-01).
- Hypothesis: app-02's INSTANCE_ID environment variable might be misconfigured with app-01's value in docker-compose.yml.
- Command or test: docker exec app-01 env | grep INSTANCE_ID; docker exec app-02 env | grep INSTANCE_ID
- Actual output: Both containers returned INSTANCE_ID=app-01 before the fix.
- Failed attempt and what changed your thinking: None — evidence was conclusive on first pass.
- Root cause: app-02's INSTANCE_ID was mistakenly set to "app-01" in docker-compose.yml (copy-paste error), giving both containers the same identity.
- Fix: Changed app-02's INSTANCE_ID value in docker-compose.yml from "app-01" to "app-02".
- Retest evidence: After rebuilding, `docker exec app-01 env | grep INSTANCE_ID` returns app-01, and `docker exec app-02 env | grep INSTANCE_ID` returns app-02 — each container now has its own distinct identity.
- Related commit: d822af7
- Remaining uncertainty: None.

## Entry 7 / 2026-09-13 / ~04:10 UTC
- Symptom: curl to http://127.0.0.1:8080/records (and any endpoint) failed with "Recv failure: Connection reset by peer".
- Hypothesis: The published host port might not match the port nginx actually listens on inside its container.
- Command or test: grep -A5 "nginx:" docker-compose.yml | grep ports; grep "listen" nginx/nginx.conf
- Actual output: docker-compose.yml mapped host port 8080 to container port 81, but nginx.conf showed nginx listens on port 80 inside the container — a mismatch.
- Failed attempt and what changed your thinking: None — evidence was conclusive on first pass.
- Root cause: docker-compose.yml published the host port to container port 81, but nginx only listens on port 80 inside its container, so no process was listening on the mapped port.
- Fix: Changed the container-side port in the ports mapping from 81 to 80.
- Retest evidence: After all three related fixes (Entry 7 port mapping, Entry 8 upstream typo, Entry 9 APP_HOST binding), curl to http://127.0.0.1:8080/ now returns a proper 200 response with the welcome message.
- Related commit: fa6a689
- Remaining uncertainty: None regarding the port-mapping fix itself.

## Entry 8 / 2026-09-13 / ~04:21 UTC
- Symptom: curl to http://127.0.0.1:8080/ returned "502 Bad Gateway" after fixing the port-mapping issue in Entry 7.
- Hypothesis: One of the two app services might be listed with a wrong port in nginx's upstream block.
- Command or test: docker logs nginx --tail 30; grep -A5 "upstream" nginx/nginx.conf
- Actual output: nginx logs showed "connect() failed (111: Connection refused) while connecting to upstream... http://172.18.0.3:8081/". The upstream block in nginx.conf listed "server app-01:8081" while app-02 correctly used port 8080.
- Failed attempt and what changed your thinking: None yet — evidence pointed clearly at the port typo, so applied the fix directly.
- Root cause: Typo in nginx.conf: app-01's upstream port (8081) didn't match the port the app actually listens on (8080).
- Fix: Corrected app-01's upstream port from 8081 to 8080 in nginx.conf. Confirmed the corrected line is present both on disk and inside the running container (`docker exec nginx grep "app-01" /etc/nginx/nginx.conf`).
- Retest evidence: After also fixing APP_HOST in Entry 9, curl to http://127.0.0.1:8080/ and /instance now succeed with 200 responses from both app-01 and app-02.
- Related commit: fa6a689
- Remaining uncertainty: The 502 persists despite the corrected upstream port being confirmed live in the container. Root cause of this remaining 502 is not yet fully confirmed — still investigating (possible causes: nginx DNS caching of container IPs, or a separate issue with app-01/app-02 themselves).

## Entry 9 / 2026-09-13 / ~04:26 UTC
- Symptom: nginx logs showed "connect() failed (111: Connection refused)" when trying to reach both app-01 (172.18.0.3:8080) and app-02 (172.18.0.2:8080), even after correcting the upstream port typo in Entry 8.
- Hypothesis: The apps might still be bound only to localhost inside their own containers, actively refusing connections from other containers like nginx.
- Command or test: docker exec app-01 env | grep APP_HOST; docker exec app-02 env | grep APP_HOST
- Actual output: Both containers returned APP_HOST=127.0.0.1.
- Failed attempt and what changed your thinking: This APP_HOST issue was originally identified as a hypothesis back in the very first investigation step (6.1), but was never actually applied — investigation moved to the healthcheck issue instead and this fix was overlooked. The persistent 502s after fixing the nginx port typo (Entry 8) led back to re-checking this original hypothesis.
- Root cause: APP_HOST was still set to "127.0.0.1" in docker-compose.yml, making both Flask apps bind only to loopback inside their own containers — actively refusing connections from nginx or any other container.
- Fix: Changed APP_HOST to "0.0.0.0" in docker-compose.yml for both app services.
- Retest evidence: After `docker compose -p barq-assessment up -d`, curl http://127.0.0.1:8080/ returns 200 with the welcome message. Looping curl on /instance 10 times shows both app-01 and app-02 alternating perfectly (5/5 split observed), confirming nginx load balancing now works correctly.
- Related commit: fa6a689
- Remaining uncertainty: None.

## Entry 10 / 2026-09-13 / ~05:32 UTC
- Symptom: POST/GET to /records returned {"error":"postgres_unavailable"} even though the postgres container itself was running and healthy.
- Hypothesis: config/app.env's DATABASE_URL/REDIS_URL might not match the real credentials/ports used by postgres and redis.
- Command or test: docker compose -p barq-assessment ps -a; docker logs app-01 --tail 20; cat config/app.env; grep -A5 "postgres:" docker-compose.yml | grep -E "POSTGRES_|ports"; grep -A3 "redis:" docker-compose.yml | grep -E "command|ports"
- Actual output: postgres and redis containers were both "Up ... (healthy)". config/app.env had DATABASE_URL password ending in "d" and port 5433, while docker-compose.yml's real POSTGRES_PASSWORD ends in "c" and postgres's actual internal port is 5432. Similarly, REDIS_URL used port 6380 while redis's real internal port is 6379.
- Failed attempt and what changed your thinking: Right after `--force-recreate`, GET /ready briefly reported postgres as "unavailable" even though the credentials were already corrected. Re-running the same check a few seconds later returned "ready" for both — this was a transient startup timing issue (postgres/app warm-up), not a second configuration problem. Confirmed this by checking /ready twice a few seconds apart.
- Root cause: Three separate typos in config/app.env: wrong last character in the database password, wrong postgres port (5433 instead of 5432), and wrong redis port (6380 instead of 6379).
- Fix: Corrected the password and both ports in config/app.env to match the real values.
- Retest evidence: After `docker compose -p barq-assessment up -d --force-recreate app-01 app-02`: POST /records successfully created a new record (id: 3), and GET /records returned it along with the pre-seeded records. GET /ready returned {"postgres":"ready","redis":"ready","status":"ready"} on a follow-up check a few seconds after recreation.
- Related commit: (after commit)
- Remaining uncertainty: None.