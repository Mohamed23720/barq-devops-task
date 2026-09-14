# BARQ DevOps Assessment — Final Submission

Fixed, tested, and documented environment for the BARQ DevOps internship take-home task.
Full investigation record: `troubleshooting.md`, `log_analysis.md`, `decisions.md`, `security_review.md`, `AI_USAGE.md`.

## Requirements
- Linux or WSL2, Python 3.12, Git, Docker with Compose (Linux containers).

## Setup
```bash
git clone https://github.com/Mohamed23720/barq-devops-task.git
cd barq-devops-task
cp .env.example .env
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m unittest discover -s tests -v
deactivate
```

## Build & Start
```bash
docker compose -p barq-assessment up --build -d
docker compose -p barq-assessment ps -a
```
All 5 services (app-01, app-02, nginx, postgres, redis) should report `healthy`.

## Test
```bash
curl http://127.0.0.1:8080/
curl http://127.0.0.1:8080/health
curl http://127.0.0.1:8080/ready
curl http://127.0.0.1:8080/instance
curl -X POST -H 'Content-Type: application/json' -d '{"title":"example"}' http://127.0.0.1:8080/records
curl http://127.0.0.1:8080/records
curl http://127.0.0.1:8080/counter

python3 validate.py
```

## Failure / Recovery Test
```bash
python3 failure_test.py
```
Stops app-01, proves app-02 keeps serving traffic, restarts app-01, verifies recovery.

## Backup / Restore
```bash
./backup.sh
# ... later, to restore:
./restore.sh backup_YYYYMMDD_HHMMSS.sql
```

## Stop
```bash
docker compose -p barq-assessment down
```
Never add `--volumes` here unless you intend to permanently wipe the database.

## Cleanup
```bash
docker compose -p barq-assessment down --volumes
docker system prune
```

## Architecture
See `architecture.png` for the full request-flow, network, and storage diagram.

## CI
GitHub Actions (`.github/workflows/ci.yml`) builds the stack, waits for readiness, and runs `validate.py` on every push/PR.
