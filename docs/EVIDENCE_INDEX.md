# Evidence and submission index

- Repository URL:
- Final commit:
- Matching CI run:
- Continuous 12-18 minute video URL:
- Challenge receipt ID:
- Starting video commit:
- Later documentation-only commits, if any:

For each requirement, link: file/output -> commit -> video timestamp.
Match the final README, diagram, GitHub code and video (three instances, public port 8090).

- Repository URL: https://github.com/Mohamed23720/barq-devops-task
- Final commit: [حط آخر hash قبل التسليم مباشرة]
- Matching CI run: https://github.com/Mohamed23720/barq-devops-task/actions (CI #1, commit 69b020f, passed in 26s)
- Continuous 12-18 minute video URL: [بعد التسجيل]
- Challenge receipt ID: [من .assessment/challenge.json بعد الفيديو]
- Starting video commit: [hash أول commit وانت بتسجل]
- Later documentation-only commits, if any: [لو فيه]

| Requirement | File/Output | Commit | Video timestamp |
|---|---|---|---|
| App bound correctly so NGINX can reach it | docker-compose.yml (APP_HOST) | fa6a689 | |
| Healthcheck targets real /health route | docker-compose.yml | ef9b48d | |
| Distinct instance identity per backend | docker-compose.yml | d822af7 | |
| NGINX port mapping matches internal listen port | docker-compose.yml | fa6a689 | |
| NGINX upstream port typo fixed | nginx/nginx.conf | fa6a689 | |
| No secrets baked into Docker image | Dockerfile | 7df0629 | |
| Container runs as non-root user | Dockerfile | 7df0629 | |
| Correct DB/Redis credentials and internal ports | config/app.env | 8d7b753 | |
| PostgreSQL data persists across container recreation | docker-compose.yml | c6290f4 | |
| postgres/redis isolated from host (no published ports) | docker-compose.yml | 7190abc | |
| NGINX isolated from backend network | docker-compose.yml | 79bd474 | |
| Restart policy for automatic recovery | docker-compose.yml | ef5af82 | |
| Resource limits (mem/cpu) on app containers | docker-compose.yml | f2991ba | |
| Log analysis — all 10 questions answered | log_analysis.md | 31d88f7 | |
| Validation script (8 checks, PASS/FAIL, exit codes) | validate.py | 93bbc0b | |
| Failure injection + recovery proof | failure_test.py | 027d609 | |
| Backup/restore proven end-to-end | backup.sh, restore.sh | 5b8ad5c | |
| CI pipeline (build → readiness → validate) | .github/workflows/ci.yml | 69b020f | |
| 5+ documented technical decisions | decisions.md | [بعد commit التوثيق النهائي] | |
| 8+ security findings | security_review.md | [بعد commit التوثيق النهائي] | |
| AI usage disclosure | AI_USAGE.md | [بعد commit التوثيق النهائي] | |
| Architecture diagram | architecture.png | [بعد commit التوثيق النهائي] | |
| Live challenge script handled during video | .assessment/challenge.json | | |
| Port changed 8080→8090 live | docker-compose.yml | | |
| Third app instance added live | docker-compose.yml | | |
