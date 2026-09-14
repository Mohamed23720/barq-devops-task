# AI usage disclosure

Write None if no AI was used. Otherwise record each use:

- Tool/model:
- Purpose:
- Files or decisions affected:
- What you changed or rejected:
- How you independently verified it:
- Related commit:

You may use AI and external resources. You must understand and demonstrate the work.

- Tool/model: Claude (Anthropic), used via chat conversation throughout the assessment (Sept 2026).
- Purpose: Understanding the starter project structure and API contract (README.md, assessment/TASK.md, assessment/APPLICATION.md, app/server.py); guiding a systematic Observe → Hypothesis → Test → Root Cause → Fix → Retest → Commit investigation methodology for every issue found in Dockerfile, docker-compose.yml, nginx/nginx.conf, and config/app.env; explaining Docker/Compose/NGINX/PostgreSQL/Redis/Git concepts as they came up during the investigation; drafting initial versions of validate.py, failure_test.py, backup.sh, restore.sh, and .github/workflows/ci.yml; drafting documentation templates and initial content for decisions.md, security_review.md, log_analysis.md, and this file.
- Files or decisions affected: Dockerfile, docker-compose.yml, nginx/nginx.conf, config/app.env, troubleshooting.md, decisions.md, security_review.md, log_analysis.md, validate.py, failure_test.py, backup.sh, restore.sh, .github/workflows/ci.yml, README.md, docs/EVIDENCE_INDEX.md.

- What you changed or rejected:
I did not accept every suggestion as-is. Several times I caught mistakes or pushed back on the approach, tested things independently, and made my own calls:

1. **Rejected the initial documentation approach entirely.** Early in the investigation, Claude pre-wrote "Symptom/Root cause" conclusions for docker-compose.yml issues before I had actually run the environment and observed real failures myself. After a second opinion flagged this as inconsistent with the task's requirement for genuine investigation evidence, I rejected that approach and had Claude restructure the entire remaining process into a strict Observe → Hypothesis → Test → Root Cause → Fix → Retest → Commit workflow, where I ran every diagnostic command myself and reported real output before any fix was applied.

2. **Caught and corrected a false negative in my own investigation (Entry 12 → Entry 14).** Claude's suggested `grep -A2 "postgres:" docker-compose.yml | grep ports` returned empty, and I initially accepted "no host ports published" as the conclusion (Entry 12). Later, when reviewing the full raw file myself, I found the `ports:` lines were actually present — the grep pattern had silently failed to match. I rejected the earlier conclusion, documented the mistake transparently as a new entry (Entry 14) rather than editing history, and fixed the actual issue.

3. **Identified a script that failed in real testing and required a fix beyond what was first given (Entry 15).** The first version of `backup.sh` used a plain `pg_dump` with no flags. When I actually ran the full backup → wipe → restore cycle myself, `restore.sh` threw real `psql` errors (`relation already exists`, duplicate key violations) and the record did not come back. I reported the exact error output, and only after seeing that real failure did we add `--clean --if-exists` to the dump command. I re-ran the entire test cycle myself a second time to confirm the fix actually worked before committing it.

4. **Switched to the official `troubleshooting.md` template instead of Claude's invented format.** Claude initially proposed its own Symptom/Investigation/Root cause/Fix structure. I checked the actual template already present in the starter repo, found it used different required fields (Hypothesis, Command or test, Actual output, Failed attempt, Remaining uncertainty), and had every entry rewritten to match the real required template instead.

5. **Deprioritized a fix I had already identified, which then caused a real downstream bug I had to catch myself.** The APP_HOST binding issue (Entry 9) was flagged as a hypothesis very early (6.1), but I moved on to investigate the healthcheck issue first and the APP_HOST fix was never actually applied. This surfaced later as a chain of confusing 502 errors (Entries 7–8) that I had to trace back, ultimately re-discovering and applying the original fix myself.

- How you independently verified it: Every suggested fix was tested against the live running environment before being committed — never accepted on faith. Verification included: `docker compose ps/logs` for health status, direct `curl` checks against every endpoint, `docker exec` commands comparing environment variables and file contents inside running containers against the source files, manual failure injection with `docker kill`/`docker compose stop`, full down/up persistence cycles, and a full backup→wipe→restore cycle. Every fix's real command output (not assumed output) is recorded entry-by-entry in troubleshooting.md, including one case where an incorrect conclusion (Entry 12) was caught and corrected (Entry 14) after re-verifying with a more precise command.
- Related commit: See troubleshooting.md and decisions.md — each entry/decision lists its own specific commit hash under "Related commit" / "Evidence / commit".

