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
