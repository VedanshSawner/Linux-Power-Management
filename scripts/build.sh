#!/bin/bash
# This script compiles all C driver tools for the project.

set -e
echo "🚀 Starting automated build process..."
PROJECT_ROOT=$(dirname "$0")/..
cd "$PROJECT_ROOT/drivers"

echo "Cleaning: brightness tool..."
(cd brightness && make clean)
echo "Cleaning: notifier tool..."
(cd notifier && make clean)
#echo "Cleaning: keyboard_backlight tool..."
#(cd keyboard_backlight && make clean)
echo "Cleaning: cpu_governor tool..."
(cd cpu_governor && make clean)
echo "Cleaning: power_status tool..."
(cd power_status && make clean)

# --- Check for uhubctl before cleaning/building usb_manager ---
echo "Checking for uhubctl support..."
UHUBCTL_SUPPORTED=0
if command -v uhubctl >/dev/null 2>&1; then
    if sudo uhubctl 2>/dev/null | grep -qiE 'port|ports|powered|power'; then
        UHUBCTL_SUPPORTED=1
        echo "Found compatible uhubctl hardware."
    else
        echo "⚠️  uhubctl found, but no switchable hubs were detected."
    fi
else
    echo "⚠️  uhubctl command not found."
fi

if [ "$UHUBCTL_SUPPORTED" -eq 1 ]; then
    echo "Cleaning: usb_manager tool..."
    (cd usb_manager && make clean)
fi

echo "--- Building all tools ---"

#echo "Building: brightness tool..."
#(cd brightness && make)
echo "Building: notifier tool..."
(cd notifier && make)
echo "Building: cpu_governor tool..."
(cd cpu_governor && make)
echo "Building: power_status tool..."
(cd power_status && make)

if [ "$UHUBCTL_SUPPORTED" -eq 1 ]; then
    echo "Building: usb_manager tool..."
    (cd usb_manager && make)
else
    echo "Skipping: usb_manager tool (hardware not supported or uhubctl not found)."
fi

echo "✅ Build process finished!"
