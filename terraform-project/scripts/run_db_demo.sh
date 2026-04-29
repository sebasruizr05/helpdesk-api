#!/usr/bin/env bash

set -euo pipefail

: "${DB_HOST:?DB_HOST no definido}"
: "${DB_NAME:?DB_NAME no definido}"
: "${DB_USER:?DB_USER no definido}"
: "${DB_PASSWORD:?DB_PASSWORD no definido}"

export PGPASSWORD="${DB_PASSWORD}"

echo "[1/3] Creating demo schema..."
psql "host=${DB_HOST} dbname=${DB_NAME} user=${DB_USER} sslmode=disable" -f /tmp/create_schema.sql
echo "[2/3] Seeding and querying demo data..."
psql "host=${DB_HOST} dbname=${DB_NAME} user=${DB_USER} sslmode=disable" -f /tmp/seed_and_query.sql
echo "[3/3] Dropping demo schema..."
psql "host=${DB_HOST} dbname=${DB_NAME} user=${DB_USER} sslmode=disable" -f /tmp/drop_schema.sql
echo "Database demo completed successfully."
