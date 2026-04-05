#!/bin/bash

# macOS DMG Creation Script for DownloaderPRO
# Usage: ./create_dmg.sh

APP_NAME="YouTubeDownloaderPro"
DMG_NAME="DownloaderPRO_v3.0.0.dmg"
APP_BUNDLE="dist/${APP_NAME}.app"
STAGING_DIR="dist/dmg_staging"

echo "🚀 Creating macOS DMG for ${APP_NAME}..."

if [ ! -d "$APP_BUNDLE" ]; then
    echo "❌ Error: ${APP_BUNDLE} not found. Run build_app.py first."
    exit 1
fi

# Create staging directory
mkdir -p "$STAGING_DIR"
cp -R "$APP_BUNDLE" "$STAGING_DIR/"

# Add symbolic link to Applications
ln -s /Applications "$STAGING_DIR/Applications"

# Create the DMG
echo "📦 Building ${DMG_NAME}..."
hdiutil create -volname "DownloaderPRO" -srcfolder "$STAGING_DIR" -ov -format UDZO "dist/${DMG_NAME}"

# Cleanup
rm -rf "$STAGING_DIR"

echo "✅ DMG created: dist/${DMG_NAME}"
echo "🛡️  Reminder: To notarize this DMG, run:"
echo "    xcrun notarytool submit dist/${DMG_NAME} --apple-id <EMAIL>"
