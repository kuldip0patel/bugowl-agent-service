#!/bin/bash
#If any step fails. It will stop
echo "STARTING..."
echo "SET -E option"
set -e
pwd

# Ensure log directory exists and has proper permissions
mkdir -p /logs
touch /logs/django.log
chmod 777 /logs/django.log

echo "RUNNING MAKE MIGRATIONS: manage.py makemigrations"
python manage.py makemigrations --no-input

echo "RUNNING DJANGO MIGRATIONS: manage.py migrate"
python manage.py migrate

echo "RUNNING COLLECT STATIC: collectstatic"
rm -rf /app/staticfiles/*
python manage.py collectstatic --no-input --clear

echo "RUNNING manage.py create_admin_user"
python manage.py create_admin_user

echo "RUNNING manage.py runserver"
python manage.py runserver 0.0.0.0:8010
