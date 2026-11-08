#!/usr/bin/env bash
set -eu
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DESKTOP_DIR="${XDG_DESKTOP_DIR:-$HOME/Desktop}"
mkdir -p "$DESKTOP_DIR"
SHORTCUT="$DESKTOP_DIR/SOUNWD.desktop"
ICON_DIR="$HOME/.local/share/icons/hicolor/512x512/apps"
mkdir -p "$ICON_DIR"
python3 "$ROOT/assets/generate_icon.py"
install -m 644 "$ROOT/assets/sounwd.png" "$ICON_DIR/sounwd.png"
cat > "$SHORTCUT" <<EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=SOUNWD
Comment=Tu música, a tu manera
Exec=python3 "$ROOT/bootstrap.py"
Icon=sounwd
Terminal=false
Categories=AudioVideo;Audio;
StartupNotify=true
EOF
chmod +x "$SHORTCUT"
if command -v gio >/dev/null 2>&1; then
  gio set "$SHORTCUT" metadata::trusted true 2>/dev/null || true
fi
printf 'Acceso directo creado en: %s\n' "$SHORTCUT"
