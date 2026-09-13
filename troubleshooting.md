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