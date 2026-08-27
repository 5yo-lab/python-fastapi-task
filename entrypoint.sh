#!/bin/sh
set -e

if [ -f alembic.ini ]; then
  echo "Running database migrations..."
  alembic upgrade head
else
  echo "No alembic.ini found — skipping migrations."
fi

if [ "${SEED_ON_START:-true}" = "true" ]; then
  echo "Seeding database..."
  python -m app.seed
fi

exec "$@"
