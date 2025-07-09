#!/bin/bash
# Script to verify and install Playwright browsers if needed

echo "=== Playwright Browser Verification ==="

# Set default paths
PLAYWRIGHT_BROWSERS_PATH=${PLAYWRIGHT_BROWSERS_PATH:-/root/.cache/ms-playwright}
PYTHON_BIN=${PYTHON_BIN:-/app/.venv/bin/python}

echo "Browser path: $PLAYWRIGHT_BROWSERS_PATH"
echo "Python binary: $PYTHON_BIN"

# Function to install browsers
install_browsers() {
    echo "Installing Playwright browsers..."
    
    # Try multiple installation methods
    if command -v playwright &> /dev/null; then
        echo "Using playwright CLI..."
        playwright install chromium --with-deps
    elif [ -f "/app/.venv/bin/playwright" ]; then
        echo "Using venv playwright CLI..."
        /app/.venv/bin/playwright install chromium --with-deps
    elif [ -f "$PYTHON_BIN" ]; then
        echo "Using Python module..."
        $PYTHON_BIN -m playwright install chromium --with-deps
    else
        echo "ERROR: No playwright installation method available"
        return 1
    fi
    
    # Verify installation
    if [ -d "$PLAYWRIGHT_BROWSERS_PATH" ]; then
        echo "✓ Browsers installed successfully"
        chmod -R 755 "$PLAYWRIGHT_BROWSERS_PATH" 2>/dev/null || echo "Warning: Could not set permissions"
        return 0
    else
        echo "✗ Browser installation failed"
        return 1
    fi
}

# Check if browsers exist
if [ -d "$PLAYWRIGHT_BROWSERS_PATH" ]; then
    echo "✓ Browser directory exists: $PLAYWRIGHT_BROWSERS_PATH"
    
    # Check if chromium exists
    if find "$PLAYWRIGHT_BROWSERS_PATH" -name "chrome" -type f 2>/dev/null | grep -q .; then
        echo "✓ Chromium browser found"
        
        # Test if Python can access the browser
        if $PYTHON_BIN -c "
from playwright.sync_api import sync_playwright
try:
    with sync_playwright() as p:
        browser_path = p.chromium.executable_path
        print(f'✓ Python can access browser at: {browser_path}')
        exit(0)
except Exception as e:
    print(f'✗ Python cannot access browser: {e}')
    exit(1)
" 2>/dev/null; then
            echo "✓ Browser verification successful"
            exit 0
        else
            echo "✗ Python cannot access browser, reinstalling..."
            install_browsers
        fi
    else
        echo "✗ Chromium browser not found, installing..."
        install_browsers
    fi
else
    echo "✗ Browser directory not found, installing..."
    install_browsers
fi

# Final verification
echo "=== Final Verification ==="
if $PYTHON_BIN -c "
from playwright.sync_api import sync_playwright
try:
    with sync_playwright() as p:
        browser_path = p.chromium.executable_path
        print(f'✓ Final check: Browser available at {browser_path}')
        exit(0)
except Exception as e:
    print(f'✗ Final check failed: {e}')
    exit(1)
"; then
    echo "✓ Browser verification completed successfully"
    exit 0
else
    echo "✗ Browser verification failed"
    exit 1
fi
