# Security and production-readiness review

Record at least 8 concrete risks or improvements relevant to your final solution.
This is a review requirement, not the number of hidden faults.

For each finding:
- Risk and evidence:
- Impact:
- Implemented fix / commit:
- Production follow-up:
- How to verify:

Cover secrets, ports, container user, image selection, networks, persistence/backup,
logging/monitoring and availability. Separate completed work from planned improvements.

## Finding 1
- Risk and evidence: Dockerfile originally copied `config/app.env` (containing the database password) directly into the image layer (troubleshooting.md Entry 2).
- Impact: Anyone with access to the built image (registry, `docker save`, or a leaked layer) could extract the database password without ever touching the running container.
- Implemented fix / commit: Removed the COPY line entirely; secrets now only enter the container via `env_file` at runtime. Commit 7df0629.
- Production follow-up: Use a real secrets manager (HashiCorp Vault, AWS Secrets Manager, etc.) instead of a plain `.env` file even at runtime.
- How to verify: `docker history barq-assessment-app-01` shows no `app.env` layer.

## Finding 2
- Risk and evidence: Container originally ran as root despite the Dockerfile creating a dedicated "app" user (Entry 3).
- Impact: A container-escape or code-execution vulnerability in the app would grant root privileges within the container's namespace, widening the blast radius of any compromise.
- Implemented fix / commit: Changed `USER root` to `USER app`. Commit 7df0629.
- Production follow-up: Add a read-only root filesystem and drop all Linux capabilities not explicitly required (`cap_drop: [ALL]`).
- How to verify: `docker compose exec app-01 whoami` returns `app`.

## Finding 3
- Risk and evidence: postgres and redis ports were published to the host (`127.0.0.1:15432`, `127.0.0.1:16379`), bypassing the intended network isolation (Entries 12 and 14 — an initial grep-based check produced a false negative, corrected after re-inspecting the raw file).
- Impact: Any process on the host machine could connect directly to the database or cache, bypassing the application layer and any authorization logic it enforces.
- Implemented fix / commit: Removed both `ports:` mappings entirely. Commit 7190abc.
- Production follow-up: Add firewall/security-group rules as defense in depth even when Compose-level ports aren't published, in case of host-level misconfiguration elsewhere.
- How to verify: `docker compose ps -a` shows no host-port binding prefix for postgres/redis (just `5432/tcp`, `6379/tcp`).

## Finding 4
- Risk and evidence: nginx was attached to the `backend` network in addition to `frontend`, giving it a direct network path to postgres/redis (Entry 13).
- Impact: A compromised nginx process (e.g., via a config-injection or worker exploit) could reach the database/cache directly, skipping all application-level authorization.
- Implemented fix / commit: Removed `backend` from nginx's `networks` list. Commit 79bd474.
- Production follow-up: Formal network-policy enforcement (see decisions.md) rather than relying on Compose network membership alone as the only isolation boundary.
- How to verify: `docker exec nginx ping postgres` fails with "bad address 'postgres'" (DNS resolution itself fails, not just a blocked connection).

## Finding 5
- Risk and evidence: No memory or CPU limits were set on app containers originally.
- Impact: A single runaway or compromised container could exhaust host resources (memory/CPU), causing a denial of service for sibling containers on the same host.
- Implemented fix / commit: Added `mem_limit: 256m`, `cpus: 0.5`. Commit f2991ba.
- Production follow-up: Tune limits based on real load testing/profiling rather than estimation; add horizontal pod/container autoscaling in a real orchestrator instead of a hard static ceiling.
- How to verify: `docker inspect app-01 --format '{{.HostConfig.Memory}}'` returns `268435456`.

## Finding 6
- Risk and evidence: The initial `backup.sh` used plain `pg_dump` with no `--clean`/`--if-exists` flags, causing restore to partially fail against a freshly-initialized database (Entry 15).
- Impact: An operator following the documented backup/restore procedure during a real incident could believe a restore succeeded (script printed "PASS") while data was actually silently incomplete — a dangerous false sense of safety.
- Implemented fix / commit: Added `--clean --if-exists` to the `pg_dump` command so the dump safely drops conflicting objects before recreating them. Commit 5b8ad5c.
- Production follow-up: Add an automated restore-verification step (e.g., checksum or row-count comparison) that fails loudly instead of a bare exit-code check, since `psql` can partially succeed with embedded errors while still exiting 0.
- How to verify: Full backup→wipe→restore cycle in troubleshooting.md Entry 15 shows all 3 records present after restore, with "COPY 3" visible in the restore output.

## Finding 7
- Risk and evidence: No automated image or dependency vulnerability scanning exists in the current CI pipeline.
- Impact: A known-vulnerable base image layer or a Python dependency with a published CVE could ship to "production" undetected.
- Implemented fix / commit: Not implemented in this lab (documented here as a known gap rather than silently omitted).
- Production follow-up: Add Trivy or Grype scanning as a required CI step, configured to fail the build on high/critical severity findings.
- How to verify: N/A — this is a planned improvement, not yet implemented; verify by checking `.github/workflows/ci.yml` for the absence of a scan step.

## Finding 8
- Risk and evidence: No centralized logging or alerting exists; each container's logs only go to its own stdout/stderr.
- Impact: A production incident (like the intermittent backend failures seen in the historical logs analyzed in log_analysis.md) could go unnoticed by operators until a user reports it, since nothing actively watches for error-rate spikes.
- Implemented fix / commit: Not implemented in this lab.
- Production follow-up: Ship logs to a centralized system (ELK, Loki, or a managed equivalent) with alerting rules on 5xx rate thresholds, informed directly by the patterns found in this assessment's log analysis (e.g., the 6-episode flapping pattern in Entry/Q7 would have triggered several alerts).
- How to verify: N/A — planned improvement; verify by confirming no log-shipping sidecar or agent exists in docker-compose.yml.

