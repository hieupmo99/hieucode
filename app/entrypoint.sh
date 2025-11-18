#!/bin/bash
set -e

# Ensure ChromeDriver exists at expected path (/opt/homebrew/bin/chromedriver)
# This runs every time the container starts, before Python executes
mkdir -p /opt/homebrew/bin

# Remove any broken symlinks or old files
rm -f /opt/homebrew/bin/chromedriver

# Copy ChromeDriver from its installed location
if [ -f /usr/bin/chromedriver ]; then
    cp /usr/bin/chromedriver /opt/homebrew/bin/chromedriver
    echo "ChromeDriver copied from /usr/bin/chromedriver"
elif [ -f /usr/local/bin/chromedriver ]; then
    cp /usr/local/bin/chromedriver /opt/homebrew/bin/chromedriver
    echo "ChromeDriver copied from /usr/local/bin/chromedriver"
else
    echo "ERROR: ChromeDriver not found in /usr/bin or /usr/local/bin"
    exit 1
fi

# Make it executable
chmod +x /opt/homebrew/bin/chromedriver

# Verify ChromeDriver is accessible
if [ ! -f /opt/homebrew/bin/chromedriver ]; then
    echo "ERROR: ChromeDriver not found at /opt/homebrew/bin/chromedriver after copy"
    exit 1
fi

echo "ChromeDriver setup complete: $(/opt/homebrew/bin/chromedriver --version 2>&1 | head -1)"

# Run the Python script with all arguments
exec python "$@"
