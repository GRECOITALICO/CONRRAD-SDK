#!/usr/bin/env bash
# prepare-commit-msg: remove Cursor AI co-author trailer (institutional policy).
set -euo pipefail
MSG_FILE="${1:?commit message file required}"
sed -i '/^Co-authored-by: Cursor <cursoragent@cursor.com>$/d' "$MSG_FILE"
