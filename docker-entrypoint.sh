#!/bin/bash

echo "Compiling scss into static files"
python manage.py sass static/scss static/styles -t compressed

# Collect static files
echo "Collect static files"
python manage.py collectstatic --noinput

echo "Downloading/Creating Database"
python -c "import RvaPiecesWebsite.db_sync; RvaPiecesWebsite.db_sync.download_db()"

# Apply database migrations
echo "Apply database migrations"
python manage.py migrate

# Start server
echo "Starting server"
gunicorn --bind 0.0.0.0:8080 --workers 3 RvaPiecesWebsite.wsgi:application
