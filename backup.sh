#!/usr/bin/env bash
set -euo pipefail
PROJECT="barq-assessment"
TIMESTAMP=$(date -u +%Y%m%d_%H%M%S)
FILE="backup_${TIMESTAMP}.sql"

echo "Backing up postgres to ${FILE}..."
docker exec "$(docker compose -p "$PROJECT" ps -q postgres)" \
  pg_dump -U barq_app -d barq_tasks --clean --if-exists > "$FILE"

if [ -s "$FILE" ]; then
    echo "PASS: backup written to $FILE ($(wc -l < "$FILE") lines)"
else
    echo "FAIL: backup file is empty"
    exit 1
fi