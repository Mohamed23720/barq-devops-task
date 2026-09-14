#!/usr/bin/env bash
set -euo pipefail
PROJECT="barq-assessment"

if [ $# -ne 1 ]; then
    echo "Usage: ./restore.sh <backup_file.sql>" >&2
    exit 2
fi

FILE="$1"
if [ ! -f "$FILE" ]; then
    echo "FAIL: backup file $FILE not found" >&2
    exit 1
fi

echo "Restoring from ${FILE}..."
cat "$FILE" | docker exec -i "$(docker compose -p "$PROJECT" ps -q postgres)" \
  psql -U barq_app -d barq_tasks

echo "PASS: restore command completed."