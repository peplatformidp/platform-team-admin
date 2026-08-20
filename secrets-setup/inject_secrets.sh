#!/bin/bash
# =============================================================================
# inject_secrets.sh — Load JSON secrets into Bitwarden Vault
# =============================================================================
# Loops through all *.json files in the secrets-setup/ directory and creates
# or updates matching items in your Bitwarden vault.
#
# Usage (from any directory):
#   ./inject_secrets.sh
#
# Prerequisites:
#   - Bitwarden CLI installed: npm install -g @bitwarden/cli
#   - jq installed
#   - .env file present one level up (../.env) with:
#       BW_CLIENTID=your_bitwarden_api_key_client_id
#       BW_CLIENTSECRET=your_bitwarden_api_key_client_secret
#       BW_PASSWORD=your_bitwarden_master_password
#
# The Bitwarden CLI defaults to the .com (US) server region.
# If your account is on the .eu region, you must explicitly configure the CLI
# to target the EU server before attempting to log in with your API keys:
#   bw config server https://vault.bitwarden.eu
#
# What it does:
#   1. Loads credentials from ../.env
#   2. Authenticates, unlocks, and syncs the Bitwarden vault
#   3. For each *.json file in this directory, matches by exact item name
#      (not Bitwarden's fuzzy search, which also matches notes/fields):
#      - If the item already exists: update name, notes, and fields
#      - If it does not exist: create it
#      - If several items share the same name: warn and update the first
#   4. Syncs the vault to the cloud and locks it
# =============================================================================

set -euo pipefail

# ── Colours ───────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
ENV_FILE="${SCRIPT_DIR}/../.env"

VAULT_UNLOCKED=0
cleanup() {
    if [ "$VAULT_UNLOCKED" -eq 1 ]; then
        bw lock >/dev/null 2>&1 || true
    fi
}
trap cleanup EXIT

# ── Dependencies ──────────────────────────────────────────────────────
for cmd in bw jq; do
    if ! command -v "$cmd" >/dev/null 2>&1; then
        echo -e "${RED}Error: '$cmd' is not installed or not on PATH.${NC}"
        exit 1
    fi
done

# ── Load environment variables ────────────────────────────────────────
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}Error: .env file not found at $ENV_FILE${NC}"
    echo "Copy .env_example to .env and fill in your Bitwarden credentials:"
    echo "  cp \"${SCRIPT_DIR}/../.env_example\" \"$ENV_FILE\""
    exit 1
fi

set -o allexport
# shellcheck source=/dev/null
source "$ENV_FILE"
set +o allexport

# ── Verify required variables ─────────────────────────────────────────
for var in BW_CLIENTID BW_CLIENTSECRET BW_PASSWORD; do
    if [ -z "${!var:-}" ]; then
        echo -e "${RED}Error: $var is not set in $ENV_FILE${NC}"
        exit 1
    fi
done

# ── Authenticate and unlock vault ─────────────────────────────────────
echo -e "${YELLOW}Authenticating with Bitwarden...${NC}"

# Login with API key if not already logged in
if ! bw login --check &>/dev/null; then
    bw login --apikey
fi

echo -e "${YELLOW}Unlocking vault...${NC}"
BW_SESSION=$(bw unlock --passwordenv BW_PASSWORD --raw)
export BW_SESSION

if [ -z "$BW_SESSION" ]; then
    echo -e "${RED}Error: Failed to unlock Bitwarden vault. Check your BW_PASSWORD.${NC}"
    exit 1
fi
VAULT_UNLOCKED=1

echo -e "${GREEN}Vault unlocked successfully.${NC}"
echo -e "${YELLOW}Syncing vault...${NC}"
bw sync --session "$BW_SESSION" >/dev/null
echo ""

# Exact name match. `bw get item` / `bw list items --search` are fuzzy and
# also match notes and custom fields, so "Pulumi Secrets" can hit
# "GitHub Secrets" when the latter's notes mention Pulumi.
find_items_by_exact_name() {
    local name="$1"
    bw list items --session "$BW_SESSION" \
        | jq -c --arg name "$name" '[.[] | select(.name == $name)]'
}

# ── Process each JSON file ────────────────────────────────────────────
shopt -s nullglob
JSON_FILES=(*.json)
if [ ${#JSON_FILES[@]} -eq 0 ]; then
    echo -e "${YELLOW}No JSON files found in $SCRIPT_DIR. Nothing to upload.${NC}"
    exit 0
fi

echo "Processing secret files..."
echo ""

had_error=0

for json_file in "${JSON_FILES[@]}"; do
    echo "  Processing: $json_file"

    if ! jq -e '.' "$json_file" >/dev/null 2>&1; then
        echo -e "  ${YELLOW}  ⚠ Skipping $json_file: invalid JSON${NC}"
        had_error=1
        continue
    fi

    item_name=$(jq -r '.name // empty' "$json_file")
    if [ -z "$item_name" ]; then
        echo -e "  ${YELLOW}  ⚠ Skipping $json_file: missing 'name' field${NC}"
        had_error=1
        continue
    fi

    if jq -e '.fields[]? | select((.value | type == "string") and test("your_.*_here"; "i"))' \
        "$json_file" >/dev/null 2>&1; then
        echo -e "  ${YELLOW}  ⚠ '$item_name' still contains placeholder values${NC}"
    fi

    matches=$(find_items_by_exact_name "$item_name")
    match_count=$(echo "$matches" | jq 'length')

    if [ "$match_count" -gt 0 ]; then
        if [ "$match_count" -gt 1 ]; then
            echo -e "  ${YELLOW}  ⚠ Found $match_count items named '$item_name'. Updating the first; delete the extras in Bitwarden:${NC}"
            echo "$matches" | jq -r '.[] | "       id: \(.id)"'
        fi

        echo -e "  ${YELLOW}  ⟳ '$item_name' exists — updating...${NC}"
        existing_item=$(echo "$matches" | jq -c '.[0]')
        item_id=$(echo "$existing_item" | jq -r '.id')
        # Preserve Bitwarden metadata (id, folder, login, etc.); replace
        # name, notes, fields, and type from the local JSON.
        payload=$(jq -n \
            --argjson existing "$existing_item" \
            --slurpfile incoming "$json_file" \
            '$existing * {
                name: $incoming[0].name,
                notes: $incoming[0].notes,
                fields: $incoming[0].fields,
                type: $incoming[0].type
            }')

        if output=$(echo "$payload" | bw encode | bw edit item "$item_id" --session "$BW_SESSION" 2>&1); then
            echo -e "  ${GREEN}  ✓ '$item_name' updated${NC}"
        else
            echo -e "  ${RED}  ✗ '$item_name' update failed${NC}"
            echo "       $output"
            had_error=1
        fi
    else
        echo -e "  ${YELLOW}  + '$item_name' not found — creating...${NC}"
        if output=$(jq '.' "$json_file" | bw encode | bw create item --session "$BW_SESSION" 2>&1); then
            echo -e "  ${GREEN}  ✓ '$item_name' created${NC}"
        else
            echo -e "  ${RED}  ✗ '$item_name' creation failed${NC}"
            echo "       $output"
            had_error=1
        fi
    fi
done

# ── Sync (lock happens in EXIT trap) ──────────────────────────────────
echo ""
echo -e "${YELLOW}Syncing vault to cloud...${NC}"
bw sync --session "$BW_SESSION" >/dev/null
echo -e "${YELLOW}Locking vault...${NC}"
bw lock
VAULT_UNLOCKED=0
echo ""

if [ "$had_error" -ne 0 ]; then
    echo -e "${YELLOW}Done with warnings or errors. Check the output above and verify in Bitwarden.${NC}"
    exit 1
fi

echo -e "${GREEN}Done. Log in to Bitwarden to verify your secrets are populated.${NC}"
