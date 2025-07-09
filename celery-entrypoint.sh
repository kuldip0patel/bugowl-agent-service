#!/bin/bash
# Celery worker entrypoint with Playwright browser verification

echo "STARTING CELERY WORKER ENTRYPOINT..."

# Don't exit on errors initially, we want to handle them gracefully
set +e

# Set environment variables
export PYTHONPATH=/app:/app/bugowl/api
export DJANGO_SETTINGS_MODULE=api.settings
export PATH="/app/.venv/bin:$PATH"

echo "Current user: $(whoami)"
echo "Current user ID: $(id -u)"
echo "Current group ID: $(id -g)"

# Check if virtual environment exists and set up Python path
echo "Checking for virtual environment..."
if [ -d "/app/.venv" ] && [ -f "/app/.venv/bin/python" ]; then
    echo "Virtual environment found at /app/.venv"
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

echo "Verifying Playwright browser installation..."

# Run browser verification script
if [ -f "/app/verify-browsers.sh" ]; then
    echo "Running browser verification script..."
    bash /app/verify-browsers.sh || {
        echo "WARNING: Browser verification failed, but continuing..."
        echo "Browser tasks may fail until browsers are properly installed"
    }
else
    echo "Browser verification script not found, performing basic check..."

    # Fallback verification
    echo "PLAYWRIGHT_BROWSERS_PATH: ${PLAYWRIGHT_BROWSERS_PATH:-not set}"

    if [ -d "${PLAYWRIGHT_BROWSERS_PATH:-/root/.cache/ms-playwright}" ]; then
        echo "✓ Browser directory exists"
    else
        echo "✗ Browser directory missing, attempting installation..."
        $PYTHON_BIN -m playwright install chromium --with-deps || {
            echo "WARNING: Browser installation failed"
        }
    fi

    # Test browser access
    $PYTHON_BIN -c "
try:
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser_path = p.chromium.executable_path
        print(f'✓ Browser accessible at: {browser_path}')
except Exception as e:
    print(f'WARNING: Browser test failed: {e}')
" || echo "Browser test failed"
fi

echo "Environment variables:"
echo "PYTHONPATH=$PYTHONPATH"
echo "DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS_MODULE"
echo "PATH=$PATH"
echo "PYTHON_BIN=$PYTHON_BIN"

echo "STARTING CELERY WORKER"
cd /app/bugowl
exec /app/.venv/bin/celery -A api.celery_app worker -l info
