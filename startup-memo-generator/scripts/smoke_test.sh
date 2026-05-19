#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORKSPACE="$(cd "$ROOT/../.." && pwd)"
TMP_DIR="$(mktemp -d)"
DATA_ROOT="$TMP_DIR/data"
SOURCE="$TMP_DIR/source.md"

cat > "$SOURCE" <<'EOF'
# Seed Memo

This is exact source wording that must not be rewritten.

Contact us at https://example.com.
EOF

python3 "$ROOT/scripts/memo.py" --workspace "$WORKSPACE" --data-root "$DATA_ROOT" setup --org "Smoke Test Co" --gmail-sender "founder@example.com"
CREATE_OUTPUT="$(python3 "$ROOT/scripts/memo.py" --workspace "$WORKSPACE" --data-root "$DATA_ROOT" create-memo --title "Seed Memo" --category investor-memos --source "$SOURCE")"
MEMO_ID="$(python3 -c 'import json,sys; print(json.load(sys.stdin)["memo_id"])' <<< "$CREATE_OUTPUT")"
python3 "$ROOT/scripts/memo.py" --workspace "$WORKSPACE" --data-root "$DATA_ROOT" add-stakeholder --memo-id "$MEMO_ID" --email investor@example.com --name "Investor" --pin 1234 >/dev/null
python3 "$ROOT/scripts/memo.py" --workspace "$WORKSPACE" --data-root "$DATA_ROOT" email-pin --memo-id "$MEMO_ID" --email investor@example.com --pin 1234 >/dev/null
python3 "$ROOT/scripts/memo.py" --workspace "$WORKSPACE" --data-root "$DATA_ROOT" gate --memo-id "$MEMO_ID" >/dev/null
python3 "$ROOT/scripts/memo.py" --workspace "$WORKSPACE" --data-root "$DATA_ROOT" generate-route-bundle --memo-id "$MEMO_ID" >/dev/null
python3 "$ROOT/scripts/memo.py" --workspace "$WORKSPACE" --data-root "$DATA_ROOT" analytics-report --memo-id "$MEMO_ID" >/dev/null

test -f "$DATA_ROOT/memos/$MEMO_ID/memo.json"
test -f "$DATA_ROOT/exports/$MEMO_ID/zo-space/manifest.json"
test -f "$DATA_ROOT/outbox.jsonl"
grep -q '/analytics/${MEMO_ID}/event' "$DATA_ROOT/exports/$MEMO_ID/zo-space/"page__investor-memos__*.tsx
grep -q "\"path\": \"/api/startup-memo-generator/analytics/$MEMO_ID/:action\"" "$DATA_ROOT/exports/$MEMO_ID/zo-space/manifest.json"
grep -q "session_revoked_at" "$DATA_ROOT/exports/$MEMO_ID/zo-space/"api__startup-memo-generator__auth__*.ts
echo "smoke ok: $MEMO_ID"
