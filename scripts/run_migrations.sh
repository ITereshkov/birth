#!/usr/bin/env bash
set -euo pipefail

if [[ -z "${DATABASE_URL:-}" ]]; then
  echo "ERROR: DATABASE_URL is not set"
  echo "Example: postgresql://avito:avito@localhost:5432/avito_copilot"
  exit 1
fi

for file in sql/migrations/*.sql; do
  echo "Applying $file"
  psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f "$file"
done

echo "Migrations applied successfully"
