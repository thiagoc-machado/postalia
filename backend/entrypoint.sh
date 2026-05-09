#!/bin/sh
set -e

python manage.py migrate --noinput
python manage.py bootstrap

exec gunicorn postalia.wsgi:application --bind 0.0.0.0:8000 --workers 3 --timeout "${GUNICORN_TIMEOUT:-900}"
