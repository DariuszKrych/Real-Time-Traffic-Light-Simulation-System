#!/usr/bin/env bash
# Build a distro-agnostic AppImage of the traffic simulation.
#
# Output: dist/TrafficSim-x86_64.AppImage
#
# Requirements on the build host:
#   - python 3.10+ with pip
#   - wget (used to grab appimagetool the first time)
#   - libfuse2 if you want to *run* the AppImage you just built
#     (Debian/Ubuntu: `sudo apt install libfuse2`)
#
# For maximum compatibility across distros, build on the oldest realistic
# Linux you support (Ubuntu 22.04 LTS is a good default — glibc 2.35).

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BUILD_DIR="$ROOT/build"
DIST_DIR="$ROOT/dist"
APPDIR="$BUILD_DIR/TrafficSim.AppDir"

cd "$ROOT"

echo ">> Installing Python build deps"
python3 -m pip install --upgrade pip
python3 -m pip install --upgrade pyinstaller PySDL3

echo ">> Cleaning previous build output"
rm -rf "$APPDIR" "$DIST_DIR/TrafficSim" "$BUILD_DIR/TrafficSim" \
       "$ROOT/TrafficSim.spec" "$DIST_DIR"/TrafficSim-*.AppImage

echo ">> Locating PySDL3 native libs"
SDL3_BIN="$(python3 -c 'import os, sdl3; print(os.path.join(os.path.dirname(sdl3.__file__), "bin"))')"
if [ ! -d "$SDL3_BIN" ]; then
    echo "ERROR: PySDL3 bin/ folder not found at $SDL3_BIN" >&2
    exit 1
fi

echo ">> Running PyInstaller (onedir)"
python3 -m PyInstaller --noconfirm --clean \
    --name TrafficSim \
    --onedir \
    --windowed \
    --add-data "src/package.json:." \
    --add-data "${SDL3_BIN}:sdl3/bin" \
    --collect-all sdl3 \
    --hidden-import src.main \
    --hidden-import src.gui \
    --hidden-import src.setup_gui \
    --hidden-import src.network \
    --hidden-import src.traffic_server \
    --hidden-import src.render \
    --hidden-import src.light_logic \
    --hidden-import src.cars \
    --hidden-import src.cars.north \
    --hidden-import src.cars.east \
    --hidden-import src.cars.south \
    --hidden-import src.cars.west \
    run.py

echo ">> Building AppDir"
mkdir -p "$APPDIR/usr/bin"
cp -r "$DIST_DIR/TrafficSim/." "$APPDIR/usr/bin/"
cp "$BUILD_DIR/icon.png" "$APPDIR/TrafficSim.png"

cat > "$APPDIR/AppRun" <<'EOF'
#!/bin/bash
HERE="$(dirname "$(readlink -f "$0")")"
# Make CWD-relative file loads (e.g. package.json) resolve.
cd "$HERE/usr/bin"
exec "$HERE/usr/bin/TrafficSim" "$@"
EOF
chmod +x "$APPDIR/AppRun"

cat > "$APPDIR/TrafficSim.desktop" <<'EOF'
[Desktop Entry]
Type=Application
Name=Traffic Sim
Comment=Real-Time Traffic Light Simulation System
Exec=TrafficSim
Icon=TrafficSim
Categories=Game;Simulation;
Terminal=false
EOF

echo ">> Fetching appimagetool if missing"
APPIMAGETOOL="$BUILD_DIR/appimagetool-x86_64.AppImage"
if [ ! -x "$APPIMAGETOOL" ]; then
    wget -q -O "$APPIMAGETOOL" \
        "https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage"
    chmod +x "$APPIMAGETOOL"
fi

echo ">> Packaging AppImage"
mkdir -p "$DIST_DIR"
# `--appimage-extract-and-run` lets this work in CI / containers that lack FUSE.
ARCH=x86_64 "$APPIMAGETOOL" --appimage-extract-and-run \
    "$APPDIR" "$DIST_DIR/TrafficSim-x86_64.AppImage"

echo
echo "Done: $DIST_DIR/TrafficSim-x86_64.AppImage"
