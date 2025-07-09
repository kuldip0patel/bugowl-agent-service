#!/bin/bash
# Simple entrypoint without virtual environment dependency
echo "STARTING SIMPLE ENTRYPOINT..."

# Don't exit on errors initially, we want to handle them gracefully
set +e

# Set environment variables
export PYTHONPATH=/app:/app/bugowl/api
export DJANGO_SETTINGS_MODULE=api.settings
export PATH="/app/.venv/bin:$PATH"

# Define paths
MANAGE_PY="/app/bugowl/manage.py"

echo "Current user: $(whoami)"
echo "Current user ID: $(id -u)"
echo "Current group ID: $(id -g)"

# Ensure directories exist with proper permissions
echo "Setting up directories..."
mkdir -p /logs 2>/dev/null || echo "Warning: Could not create /logs directory"
mkdir -p /app/logs 2>/dev/null || echo "Warning: Could not create /app/logs directory"
mkdir -p /app/bugowl/logs 2>/dev/null || echo "Warning: Could not create /app/bugowl/logs directory"
mkdir -p /app/staticfiles 2>/dev/null || echo "Warning: Could not create /app/staticfiles directory"

# Try to set permissions on directories
chmod 777 /logs 2>/dev/null || echo "Warning: Could not set permissions on /logs"
chmod 777 /app/logs 2>/dev/null || echo "Warning: Could not set permissions on /app/logs"
chmod 777 /app/bugowl/logs 2>/dev/null || echo "Warning: Could not set permissions on /app/bugowl/logs"
chmod 777 /app/staticfiles 2>/dev/null || echo "Warning: Could not set permissions on /app/staticfiles"

# Try to create log files
if touch /logs/django.log 2>/dev/null; then
    echo "Created log file at /logs/django.log"
    chmod 666 /logs/django.log 2>/dev/null || echo "Warning: Could not set permissions on /logs/django.log"
else
    echo "Could not create /logs/django.log, trying /app/logs/django.log"
    touch /app/logs/django.log 2>/dev/null || echo "Warning: Could not create /app/logs/django.log"
fi

# Create Django-specific log file
if touch /app/bugowl/logs/django.log 2>/dev/null; then
    echo "Created Django log file at /app/bugowl/logs/django.log"
    chmod 666 /app/bugowl/logs/django.log 2>/dev/null || echo "Warning: Could not set permissions on /app/bugowl/logs/django.log"
else
    echo "Warning: Could not create /app/bugowl/logs/django.log"
fi

# Check if virtual environment exists and set up Python path
echo "Checking for virtual environment..."
echo "Directory /app/.venv exists: $([ -d "/app/.venv" ] && echo "YES" || echo "NO")"
echo "File /app/.venv/bin/python exists: $([ -f "/app/.venv/bin/python" ] && echo "YES" || echo "NO")"

if [ -d "/app/.venv" ] && [ -f "/app/.venv/bin/python" ]; then
    echo "Virtual environment found at /app/.venv"
    # Use the virtual environment's Python directly
    export PYTHON_BIN="/app/.venv/bin/python"
    export PATH="/app/.venv/bin:$PATH"
    echo "Using virtual environment Python: $PYTHON_BIN"
    echo "Python version: $($PYTHON_BIN --version)"
else
    echo "Virtual environment not found, using system Python"
    export PYTHON_BIN="python"
fi

# Now set strict error handling for the rest of the script
set -e

echo "Current working directory:"
pwd

echo "Python executable path:"
which $PYTHON_BIN || echo "Python not found in PATH"

echo "Python version:"
$PYTHON_BIN --version || echo "Failed to get Python version"

echo "Environment variables:"
echo "PYTHONPATH=$PYTHONPATH"
echo "DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS_MODULE"
echo "PATH=$PATH"
echo "PYTHON_BIN=$PYTHON_BIN"

echo "Checking if Django is available:"
$PYTHON_BIN -c "import django; print(f'Django version: {django.get_version()}')" || echo "Django not available"

echo "Checking Playwright browser installation:"
echo "PLAYWRIGHT_BROWSERS_PATH: ${PLAYWRIGHT_BROWSERS_PATH:-not set}"
if [ -d "${PLAYWRIGHT_BROWSERS_PATH:-/root/.cache/ms-playwright}" ]; then
    echo "Playwright browsers directory exists"
    ls -la "${PLAYWRIGHT_BROWSERS_PATH:-/root/.cache/ms-playwright}" || echo "Cannot list browser directory"
else
    echo "WARNING: Playwright browsers directory not found at ${PLAYWRIGHT_BROWSERS_PATH:-/root/.cache/ms-playwright}"
fi

# Test if playwright can find browsers
echo "Testing Playwright browser detection:"
$PYTHON_BIN -c "
try:
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser_path = p.chromium.executable_path
        print(f'Chromium browser found at: {browser_path}')
except Exception as e:
    print(f'WARNING: Playwright browser test failed: {e}')
    print('You may need to run: playwright install chromium')
" || echo "Playwright browser test failed"

echo "Contents of /app:"
ls -la /app/

# Check if manage.py exists
if [ -f "$MANAGE_PY" ]; then
    echo "Found Django manage.py at $MANAGE_PY"
else
    echo "ERROR: Django manage.py not found at $MANAGE_PY"
    echo "Contents of /app/bugowl:"
    ls -la /app/bugowl/ || echo "Directory /app/bugowl does not exist"
    exit 1
fi

echo "RUNNING MAKE MIGRATIONS: manage.py makemigrations"
$PYTHON_BIN $MANAGE_PY makemigrations --no-input

echo "RUNNING DJANGO MIGRATIONS: manage.py migrate"
$PYTHON_BIN $MANAGE_PY migrate

echo "RUNNING COLLECT STATIC: collectstatic"
rm -rf /app/staticfiles/*
$PYTHON_BIN $MANAGE_PY collectstatic --no-input --clear

echo "RUNNING manage.py create_admin_user (if command exists)"
$PYTHON_BIN $MANAGE_PY create_admin_user

echo "STARTING SERVER WITH DAPHNE AND AUTO-RELOAD"
cd /app/bugowl

# Check if auto-reload is disabled via environment variable
if [ "${DISABLE_AUTO_RELOAD:-false}" = "true" ]; then
    echo "Auto-reload disabled via DISABLE_AUTO_RELOAD environment variable"
    echo "Starting Daphne without auto-reload..."
    exec /app/.venv/bin/daphne -b 0.0.0.0 -p 8020 api.asgi:application
fi

# Check if watchmedo is available
if ! command -v watchmedo &> /dev/null; then
    echo "ERROR: watchmedo not found. Installing watchdog..."
    /app/.venv/bin/pip install watchdog

    # Verify installation
    if ! command -v watchmedo &> /dev/null; then
        echo "ERROR: Failed to install watchdog. Falling back to manual Daphne start."
        echo "Auto-reload will not be available."
        exec /app/.venv/bin/daphne -b 0.0.0.0 -p 8020 api.asgi:application
    fi
fi

echo "✓ watchmedo found: $(which watchmedo)"

# Verify the watch directory exists and show its contents
echo "Verifying watch directory..."
if [ -d "/app/bugowl" ]; then
    echo "✓ Watch directory /app/bugowl exists"
    echo "Contents of /app/bugowl:"
    ls -la /app/bugowl/ | head -10
else
    echo "✗ ERROR: Watch directory /app/bugowl does not exist!"
    exit 1
fi

echo "Starting Daphne with watchmedo auto-restart..."
echo "Watching directory: /app/bugowl"
echo "Patterns: *.py"
echo "Ignoring: __pycache__, *.pyc, *.pyo, .git, migrations"
echo "Debounce interval: 1 second"

# Use watchmedo to auto-restart daphne when Python files change
exec watchmedo auto-restart \
    --directory=/app/bugowl \
    --patterns="*.py" \
    --ignore-patterns="*/__pycache__/*;*.pyc;*.pyo;*/.git/*;*/migrations/*;*/.pytest_cache/*" \
    --recursive \
    --debounce-interval=1 \
    -- /app/.venv/bin/daphne -b 0.0.0.0 -p 8020 api.asgi:application
