#!/bin/sh
set -e

if [ -f alembic.ini ]; then
  echo "Running database migrations..."
  alembic upgrade head
else
  echo "No alembic.ini found — skipping migrations."
fi

exec "$@"
