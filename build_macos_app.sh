#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
APP_NAME="GetbijiEx"
DIST_DIR="$ROOT/dist"
BUILD_DIR="$ROOT/build"

cd "$ROOT"
uv sync --dev
uv run pyinstaller --noconfirm "$ROOT/$APP_NAME.spec"

echo "\n构建完成：$DIST_DIR/$APP_NAME.app"
echo "可直接在 Finder 中双击打开。"
