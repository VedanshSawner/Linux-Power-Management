#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

echo "🚀 Starting automated build process..."

# Get the root directory of the project (where this script's folder is)
PROJECT_ROOT=$(dirname "$0")/..

# Navigate to the drivers directory
cd "$PROJECT_ROOT/drivers"

# --- Compile each driver ---

echo "Building: brightness tool..."
(cd brightness && make)

echo "Building: webcam tool..."
(cd webcam && make)

# Add a line here for the fan controller when you create it
# echo "Building: fan tool..."
# (cd fan && make)

echo "✅ All drivers compiled successfully!"
