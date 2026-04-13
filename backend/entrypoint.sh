#!/bin/bash

echo "Running migrations..."
alembic upgrade head

echo "Starting application..."
exec "$@"
