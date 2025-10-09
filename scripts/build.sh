#!/bin/bash
set -e
echo "🚀 Starting automated build process..."
PROJECT_ROOT=$(dirname "$0")/..
cd "$PROJECT_ROOT/drivers"

echo "Cleaning: brightness tool..."
(cd brightness && make clean)

echo "Cleaning: usb_manager tool..."
(cd usb_manager && make clean)

echo "Cleaning: notifier tool..."
(cd notifier && make clean)

echo "Building: brightness tool..."
(cd brightness && make)

echo "Building: usb_manager tool..."
(cd usb_manager && make)

echo "Building: notifier tool..."
(cd notifier && make)

echo "✅ All drivers cleaned and compiled successfully!"