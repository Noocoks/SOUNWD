#!/usr/bin/env bash
set -eu
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DESKTOP_DIR="${XDG_DESKTOP_DIR:-$HOME/Desktop}"
mkdir -p "$DESKTOP_DIR"
cp "$ROOT/Linux/Sonora.desktop" "$DESKTOP_DIR/Sonora.desktop"
chmod +x "$DESKTOP_DIR/Sonora.desktop"
if command -v gio >/dev/null 2>&1; then
  gio set "$DESKTOP_DIR/Sonora.desktop" metadata::trusted true 2>/dev/null || true
fi
printf 'Acceso directo de Sonora creado en: %s\n' "$DESKTOP_DIR"
