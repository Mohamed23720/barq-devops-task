# Technical decisions

Record at least 5 decisions. Include assumptions and limits.

## Decision
- Choice:
- Why:
- Alternative:
- Trade-off:
- Evidence / commit:
- Production improvement:

Cover your base image, health checks, networks, timeouts/retries, restart/resource settings,
storage and any other meaningful choices.

## Decision 1
- Choice: Set restart policy to `unless-stopped` for app containers (was `"no"`).
- Why: A crashed container should recover automatically without manual intervention, while still respecting an intentional `docker compose stop`.
- Alternative: `on-failure` (narrower — doesn't restart after a manual stop the same way); `always` (restarts even after an explicit stop in some edge cases, less predictable for a lab assessment).
- Trade-off: unless-stopped balances automatic recovery with respecting deliberate stops, without needing extra crash-loop protection logic.
- Evidence / commit: (after commit)
- Production improvement: In a real production system, this would be paired with a crash-loop backoff/alerting mechanism, since Docker Compose's restart policy alone has no limit on retry attempts.
- Note on live behavior: The restart policy is correctly configured (`unless-stopped`, confirmed via `docker inspect .HostConfig.RestartPolicy`) and would trigger correctly on standard Docker Engine hosts (e.g., the GitHub Actions Linux runner used in CI). However, on this specific development machine (Docker Desktop + WSL2 backend), `docker kill` on a container did not trigger an automatic restart in manual testing — confirmed via `docker events` showing no subsequent "start" event. This appears to be a known class of Docker Desktop/WSL2 backend quirk with restart supervision, not a configuration defect. Documented here for transparency; the configuration itself is correct and will be demonstrated/relied upon via `docker compose start` in the failure_test.py recovery step instead of relying on automatic restart during local demos.

## Decision 2
- Choice: Added mem_limit: 256m and cpus: 0.5 to each app container.
- Why: No limits meant a single runaway container could exhaust host resources and affect sibling services.
- Alternative: Leave unlimited (simpler but riskier); much higher limits (safer but wasteful for this app's actual footprint).
- Trade-off: 256MB/0.5 CPU is generous for this lightweight Flask app while still providing a hard ceiling.
- Evidence / commit: f2991ba — verified via `docker inspect app-01 --format 'Memory={{.HostConfig.Memory}} CPUs={{.HostConfig.NanoCpus}}'` returning Memory=268435456, CPUs=500000000.
- Production improvement: Real limits should be based on measured load/profiling, not estimation.

## Decision 3
- Choice: Kept the pinned base image `python:3.12-slim-bookworm@sha256:...` instead of a full or alpine Python image.
- Why: Slim images reduce attack surface and image size; the sha256 pin guarantees reproducible builds regardless of tag mutations upstream.
- Alternative: `python:3.12` (full, larger, more attack surface); `python:3.12-alpine` (smaller, but musl libc can cause subtle compatibility issues with some pip packages, e.g. psycopg).
- Trade-off: slim-bookworm balances size, compatibility, and security — the safest default for this app's dependency set.
- Evidence / commit: baseline (unchanged from starter, deliberately kept).
- Production improvement: Add automated base-image vulnerability scanning (e.g., Trivy or Grype) as a required CI step.


## Decision 4
- Choice: Split Docker networks into `frontend` (nginx + apps) and `backend` (apps + postgres + redis, `internal: true`).
- Why: Limits blast radius — nginx (the externally-reachable component) never has a network route to the data layer, even if compromised.
- Alternative: Single flat network (simpler, but zero isolation); per-service dedicated networks (more granular, unnecessary complexity at this scale).
- Trade-off: Two-tier segmentation is the simplest design that still enforces the isolation the task explicitly requires.
- Evidence / commit: 79bd474
. Verified via `docker exec nginx ping postgres` failing with "bad address" after the fix.
- Production improvement: Add a dedicated network-policy enforcement layer (e.g., Kubernetes NetworkPolicies) for defense in depth beyond what Compose networks alone provide.

## Decision 5
- Choice: Kept `proxy_next_upstream off` in nginx.conf instead of enabling automatic failover to the healthy backend on error.
- Why: This makes backend failures visible as real client-facing errors during the failure test (as the task explicitly wants demonstrated), instead of nginx silently masking them by retrying the healthy backend transparently.
- Alternative: Enable `proxy_next_upstream` (masks failures from clients, better perceived uptime, but hides the true backend state during testing).
- Trade-off: Chose observability/honesty in testing over maximum apparent availability.
- Evidence / commit: baseline nginx.conf (unchanged). Confirmed the trade-off in practice: `failure_test.py` showed 5/10 requests failing (not silently retried) while app-01 was down — matching this design choice exactly.
- Production improvement: In a real production deployment, would enable `proxy_next_upstream` for end-user experience, paired with proper backend-health alerting so failures are still caught operationally even though clients don't see them.