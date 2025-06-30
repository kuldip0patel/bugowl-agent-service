#!/bin/bash
#If any step fails. It will stop
echo "STARTING..."
echo "SET -E option"
set -e
pwd
MANAGE_PY="/app/bugowl/manage.py"
# Ensure log directory exists and has proper permissions
# mkdir -p /logs
# touch /logs/django.log
# chmod 777 /logs/django.log

ls -l /app/.venv

. /app/.venv/Scripts/activate

echo "Python executable path:"
which python

echo "Python version:"
python --version

echo "Pip executable path:"
which pip

echo "Installed packages:"
pip list


echo "RUNNING MAKE MIGRATIONS: manage.py makemigrations"
python $MANAGE_PY makemigrations --no-input

echo "RUNNING DJANGO MIGRATIONS: manage.py migrate"
python $MANAGE_PY migrate

echo "RUNNING COLLECT STATIC: collectstatic"
rm -rf /app/staticfiles/*
python $MANAGE_PY collectstatic --no-input --clear

echo "RUNNING manage.py create_admin_user"
python $MANAGE_PY create_admin_user

echo "STARTING SERVER WITH DAPHNE"
daphne -b 0.0.0.0 -p 8020 api.asgi:application
