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

## Entry 1 / 2026-09-12 / ~3:24 pm UTC
- Symptom: N/A — this is a pre-check before touching Docker, not a failure investigation.
- Hypothesis: The Flask app's own logic (routing, validation, response shape) should be correct independent of the broken Docker/networking environment.
- Command or test: `python -m unittest discover -s tests -v` (run inside a venv, fake dependencies, no real Postgres/Redis/Docker).
- Actual output: `Ran 8 tests in 0.166s — OK` (all 8 passed).
- Failed attempt and what changed your thinking: None — first attempt succeeded.
- Root cause: N/A.
- Fix: N/A.
- Retest evidence: 8/8 tests passing confirms app logic is sound; any issues found later must be in Docker/networking/config, not app code.
- Related commit: (commit hash after your `git commit -m "docs: record pre-check unit test results (8/8 passed)"`)
- Remaining uncertainty: These tests use fake dependencies — they don't prove the real Postgres/Redis/Docker setup works.

## Entry 2 / 2026-09-12 / ~3:46 pm UTC
- Symptom: Dockerfile contained `COPY config/app.env /srv/app.env`, copying the file that holds the database password directly into the image layer.
- Hypothesis: This is unnecessary and a security leak — env vars are already injected at runtime via `env_file` in docker-compose.yml.
- Command or test: Reviewed Dockerfile line by line; ran `docker history barq-app` to confirm the app.env layer existed.
- Actual output: `docker history` showed a layer corresponding to the COPY of app.env.
- Failed attempt and what changed your thinking: None — confirmed directly from static review, no failed attempt needed.
- Root cause: Unnecessary COPY instruction baking secrets into the image itself.
- Fix: Removed the COPY line entirely. Secrets now only enter the container via env_file at runtime, never baked into the image.
- Retest evidence: `docker build -t barq-app .` still succeeds; `docker history barq-app` no longer shows the app.env layer.
- Related commit: (fill after committing)
- Remaining uncertainty: None.

## Entry 3 / 2026-09-12 / ~3:48 pm UTC
- Symptom: Dockerfile created a dedicated "app" user with `useradd`, but the final `USER root` instruction overrode it, so the container actually ran as root.
- Hypothesis: Leftover `USER root` line placed after the non-root user setup cancels its effect.
- Command or test: Traced the USER instructions top to bottom; ran `docker compose -p barq-assessment exec app-01 whoami`.
- Actual output: Returned `root` before the fix.
- Failed attempt and what changed your thinking: None.
- Root cause: Leftover `USER root` instruction placed after the non-root user setup.
- Fix: Changed `USER root` to `USER app`.
- Retest evidence: `docker compose -p barq-assessment exec app-01 whoami` now returns `app`, not `root`.
- Related commit: (fill after committing)
- Remaining uncertainty: None.

## Entry 4 / 2026-09-12 / ~6:42 pm UTC
- Symptom: N/A — this happened while applying the Entry 2/3 fixes, not a new investigation.
- Hypothesis: N/A
- Command or test: `docker compose -p barq-assessment up --build -d`
- Actual output: Build failed with `RUN pip install --no-cache-dir -r requirements.txt did not complete successfully: exit code: 1` because requirements.txt was not found in the image.
- Failed attempt and what changed your thinking: While removing the `COPY config/app.env` line, accidentally commented out `COPY requirements.txt` instead. The build error message pointed directly at the missing file, which made the mistake obvious immediately.
- Root cause: Wrong line was commented out during manual editing.
- Fix: Restored the `COPY requirements.txt ./requirements.txt` line, and correctly commented out `COPY config/app.env /srv/app.env` instead.
- Retest evidence: `docker compose -p barq-assessment up --build -d` now completes successfully (15/15 steps finished).
- Related commit: (fill after committing)
- Remaining uncertainty: None.