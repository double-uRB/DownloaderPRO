#!/bin/bash

# Linux Debian Package Creation Script for DownloaderPRO
# Usage: ./create_deb.sh

APP_NAME="downloaderpro"
VERSION="3.0.0"
DEB_DIR="dist/deb_staging"
BINARY_SOURCE="dist/YouTubeDownloaderPro"

echo "🚀 Creating Linux Debian (.deb) package for ${APP_NAME}..."

if [ ! -f "$BINARY_SOURCE" ]; then
    echo "❌ Error: $BINARY_SOURCE binary not found. Run build_app.py first."
    exit 1
fi

# Create directory structure
mkdir -p "$DEB_DIR/usr/bin"
mkdir -p "$DEB_DIR/usr/share/applications"
mkdir -p "$DEB_DIR/usr/share/pixmaps"
mkdir -p "$DEB_DIR/DEBIAN"

# Copy binary
cp "$BINARY_SOURCE" "$DEB_DIR/usr/bin/$APP_NAME"
chmod 755 "$DEB_DIR/usr/bin/$APP_NAME"

# Copy assets
cp "assets/logo.png" "$DEB_DIR/usr/share/pixmaps/$APP_NAME.png"
cp "assets/DownloaderPRO.desktop" "$DEB_DIR/usr/share/applications/$APP_NAME.desktop"

# Create control file
cat > "$DEB_DIR/DEBIAN/control" <<EOF
Package: $APP_NAME
Version: $VERSION
Section: utils
Priority: optional
Architecture: amd64
Maintainer: Rajesh Barai <https://github.com/double-uRB>
Description: Advanced YouTube Video and Audio Downloader Suite
  A professional desktop application built with Python and PySide6 for high-fidelity media downloads.
EOF

# Build package
echo "📦 Building ${APP_NAME}_${VERSION}_amd64.deb..."
dpkg-deb --build "$DEB_DIR" "dist/${APP_NAME}_${VERSION}_amd64.deb"

# Cleanup
rm -rf "$DEB_DIR"

echo "✅ Debian package created: dist/${APP_NAME}_${VERSION}_amd64.deb"
