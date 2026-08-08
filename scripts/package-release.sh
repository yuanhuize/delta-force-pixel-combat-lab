#!/usr/bin/env bash

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD_DIR="$PROJECT_DIR/build/web-desktop"
RELEASE_DIR="$PROJECT_DIR/release"
PROJECT_NAME="$(node -p "require('$PROJECT_DIR/package.json').name")"
PROJECT_VERSION="$(node -p "require('$PROJECT_DIR/package.json').version")"
ARCHIVE_NAME="${PROJECT_NAME}-v${PROJECT_VERSION}-web.zip"
ARCHIVE_PATH="$RELEASE_DIR/$ARCHIVE_NAME"
CHECKSUM_PATH="$ARCHIVE_PATH.sha256"

if [[ ! "$PROJECT_VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+(-[0-9A-Za-z.-]+)?(\+[0-9A-Za-z.-]+)?$ ]]; then
  echo "Invalid semantic version in package.json: $PROJECT_VERSION" >&2
  exit 1
fi

if [[ ! -f "$BUILD_DIR/index.html" || ! -f "$BUILD_DIR/src/settings.json" ]]; then
  echo "Web build is incomplete. Build the project before packaging." >&2
  exit 1
fi

mkdir -p "$RELEASE_DIR"

if [[ -e "$ARCHIVE_PATH" || -e "$CHECKSUM_PATH" ]]; then
  echo "Release files already exist for v$PROJECT_VERSION; refusing to overwrite them." >&2
  exit 1
fi

if command -v ditto >/dev/null 2>&1; then
  ditto -c -k --norsrc --keepParent "$BUILD_DIR" "$ARCHIVE_PATH"
elif command -v zip >/dev/null 2>&1; then
  (
    cd "$(dirname "$BUILD_DIR")"
    zip -qr "$ARCHIVE_PATH" "$(basename "$BUILD_DIR")"
  )
else
  echo "Neither ditto nor zip is available." >&2
  exit 1
fi

if command -v shasum >/dev/null 2>&1; then
  (
    cd "$RELEASE_DIR"
    shasum -a 256 "$ARCHIVE_NAME" > "$ARCHIVE_NAME.sha256"
  )
elif command -v sha256sum >/dev/null 2>&1; then
  (
    cd "$RELEASE_DIR"
    sha256sum "$ARCHIVE_NAME" > "$ARCHIVE_NAME.sha256"
  )
else
  echo "No SHA-256 checksum tool is available." >&2
  exit 1
fi

echo "Created release/$ARCHIVE_NAME"
echo "Created release/$ARCHIVE_NAME.sha256"
