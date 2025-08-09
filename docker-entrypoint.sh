#!/bin/bash

# Wait for the database server to be ready
echo "Waiting for database server..."
dockerize -wait tcp://db:5432 -timeout 60s

# Collect static files
echo "Collect static files"
python manage.py collectstatic --noinput

# Apply database migrations
echo "Apply database migrations"
python manage.py migrate

# Start server
echo "Starting server"
gunicorn --bind 0.0.0.0:8000 --workers 3 RvaPiecesWebsite.wsgi:application
