#!/bin/bash
until pg_isready -h $DB_HOST -p $DB_PORT -U $DB_USER; do
  echo "Waiting for database..."
  sleep 2
done

alembic upgrade head
