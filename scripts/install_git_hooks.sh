#!/usr/bin/env sh
set -e
ROOT="$(git rev-parse --show-toplevel)"
GIT_DIR="$(git rev-parse --git-dir)"
mkdir -p "$GIT_DIR/hooks"
cp "$ROOT/scripts/git-hooks/pre-commit" "$GIT_DIR/hooks/pre-commit"
chmod +x "$GIT_DIR/hooks/pre-commit"
echo "Installed: $GIT_DIR/hooks/pre-commit"
