#!/bin/bash

# Linux AppImage Creation Script for DownloaderPRO
# Usage: ./create_appimage.sh

APP_NAME="YouTubeDownloaderPro"
VERSION="3.0.0"
APPDIR="dist/DownloaderPRO.AppDir"
OUT_DIR="dist"

echo "🚀 Creating Linux AppImage for ${APP_NAME}..."

if [ ! -f "dist/${APP_NAME}" ]; then
    echo "❌ Error: dist/${APP_NAME} binary not found. Run build_app.py first."
    exit 1
fi

# Download appimagetool if not present
if [ ! -f "appimagetool" ]; then
    echo "📥 Downloading appimagetool..."
    wget -q https://github.com/AppImage/AppImageKit/releases/download/13/appimagetool-x86_64.AppImage -O appimagetool
    chmod +x appimagetool
fi

# Create AppDir structure
mkdir -p "$APPDIR/usr/bin"
cp "dist/${APP_NAME}" "$APPDIR/usr/bin/"
cp "assets/logo.png" "$APPDIR/DownloaderPRO.png"
cp "assets/DownloaderPRO.desktop" "$APPDIR/"

# Create AppRun script
cat > "$APPDIR/AppRun" <<EOF
#!/bin/bash
HERE="\$(dirname "\$(readlink -f "\${0}")")"
export PATH="\${HERE}/usr/bin:\${PATH}"
exec "\${HERE}/usr/bin/${APP_NAME}" "\$@"
EOF
chmod +x "$APPDIR/AppRun"

# Package AppImage
echo "📦 Building DownloaderPRO-${VERSION}.AppImage..."
./appimagetool "$APPDIR" "$OUT_DIR/DownloaderPRO-${VERSION}-x86_64.AppImage"

echo "✅ AppImage created: $OUT_DIR/DownloaderPRO-${VERSION}-x86_64.AppImage"
