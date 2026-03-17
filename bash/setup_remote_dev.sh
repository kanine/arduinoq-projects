#!/bin/bash

set -euo pipefail

# --- Configuration ---
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
UNO_IP="<your-uno-q-ip>"
UNO_USER="arduino"
UNO_ALIAS="uno1"
LOCAL_MOUNT_DIR="$(dirname "$SCRIPT_DIR")"
REMOTE_DIR="/home/arduino/ArduinoApps"
SSH_CONFIG="$HOME/.ssh/config"

# --- Argument Parsing ---
while [[ $# -gt 0 ]]; do
    case "$1" in
        --unoip)
            if [[ -n "${2:-}" ]]; then
                UNO_IP="$2"
                shift 2
            else
                echo "Error: --unoip requires a value."
                exit 1
            fi
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# --- Validate UNO_IP ---
if [ "$UNO_IP" = "<your-uno-q-ip>" ]; then
    echo "❌ --unoip is required. Usage: $0 --unoip <ip-address>"
    exit 1
fi
if ! [[ "$UNO_IP" =~ ^([0-9]{1,3}\.){3}[0-9]{1,3}$ ]]; then
    echo "❌ Invalid IP address: '$UNO_IP'"
    exit 1
fi

echo "🚀 Starting Uno Q Remote Dev Setup..."

pause_for_stage() {
    local stage_num="$1"
    local stage_desc="$2"
    echo -e "\n📍 [STAGE $stage_num] $stage_desc"
    read -rp "   Press [Enter] to begin this stage or [Ctrl+C] to abort..."
}

require_cmd() {
    if ! command -v "$1" >/dev/null 2>&1; then
        echo "❌ Required command not found: $1"
        exit 1
    fi
}

print_alias_status() {
    local alias="$1"
    if grep -qE "^Host[[:space:]]+${alias}([[:space:]]|$)" "$SSH_CONFIG" 2>/dev/null; then
        echo "✅ SSH alias '${alias}' found in $SSH_CONFIG"
    else
        echo "⚠️  SSH alias '${alias}' not found in $SSH_CONFIG"
    fi
}

pick_reusable_key() {
    for key in "$HOME/.ssh/"*.pub; do
        [ -f "$key" ] || continue
        echo "$key"
        return 0
    done
    return 1
}

require_cmd ssh
require_cmd ssh-copy-id
require_cmd ssh-keygen
require_cmd awk
require_cmd grep

# --- Stage 1: Local System Preparation ---
pause_for_stage "1/4" "Environment: Install sshfs, create mount point, and configure FUSE."

# 1. Install Dependencies
if command -v sshfs >/dev/null 2>&1; then
    echo "✅ sshfs already installed"
else
    echo "📦 Installing sshfs..."
    sudo apt update && sudo apt install -y sshfs
fi

# 2. Create Mount Point
if [ ! -d "$LOCAL_MOUNT_DIR" ]; then
    echo "📁 Creating local mount directory at $LOCAL_MOUNT_DIR"
    mkdir -p "$LOCAL_MOUNT_DIR"
fi

# 5. Enable user_allow_other in FUSE only if needed (Moved up for logical grouping)
if grep -q '^user_allow_other' /etc/fuse.conf; then
    echo "✅ user_allow_other already enabled in /etc/fuse.conf"
else
    echo "🔐 Enabling user_allow_other in /etc/fuse.conf"
    sudo sed -i 's/^#user_allow_other/user_allow_other/' /etc/fuse.conf
fi

# --- Stage 2: Network Configuration ---
pause_for_stage "2/4" "Network: Map '${UNO_ALIAS}' to ${UNO_IP} in /etc/hosts."

# 3. Setup /etc/hosts Alias with exact match
if grep -qE "(^|[[:space:]])${UNO_ALIAS}([[:space:]]|$)" /etc/hosts; then
    echo "✅ '${UNO_ALIAS}' already exists in /etc/hosts"
else
        echo "📝 Adding '${UNO_ALIAS}' to /etc/hosts (requires sudo)"
        echo "$UNO_IP $UNO_ALIAS" | sudo tee -a /etc/hosts >/dev/null
fi

# 4. Add SSH config entry so 'ssh uno1' uses the arduino user automatically
if grep -qE "^Host[[:space:]]+${UNO_ALIAS}([[:space:]]|$)" "$SSH_CONFIG" 2>/dev/null; then
    echo "✅ SSH config entry for '${UNO_ALIAS}' already exists"
else
    mkdir -p "$(dirname "$SSH_CONFIG")"
    cat >> "$SSH_CONFIG" <<EOF

Host ${UNO_ALIAS}
    HostName ${UNO_IP}
    User ${UNO_USER}
EOF
    echo "✅ Added SSH config entry for '${UNO_ALIAS}' (user: ${UNO_USER}, host: ${UNO_IP})"
fi
print_alias_status "$UNO_ALIAS"

# --- Stage 3: SSH Security Setup ---
pause_for_stage "3/4" "Security: Generate or select an SSH key and copy it to the Uno Q."

# 6. SSH Key Setup (reuse-first)
SSH_PUB_KEY="$(pick_reusable_key || true)"
if [ -z "$SSH_PUB_KEY" ]; then
    NEW_KEY="$HOME/.ssh/id_ed25519_uno1"
    if [ -f "$NEW_KEY" ] || [ -f "${NEW_KEY}.pub" ]; then
        echo "❌ Found partial key material at ${NEW_KEY}; resolve manually to avoid overwrite."
        exit 1
    fi
    echo "🔑 No reusable key found. Generating dedicated key at ${NEW_KEY}"
    ssh-keygen -t ed25519 -N "" -f "$NEW_KEY"
    SSH_PUB_KEY="${NEW_KEY}.pub"
else
    echo "🔑 Reusing existing key: $SSH_PUB_KEY"
fi

echo "📤 Copying SSH key to Uno Q (enter password for '${UNO_USER}' if prompted)..."
ssh-copy-id -i "$SSH_PUB_KEY" "${UNO_USER}@${UNO_ALIAS}"

# --- Stage 4: Developer Experience ---
pause_for_stage "4/4" "Aliases: Add mount-uno, unmount-uno, and uno-shell to your ~/.bashrc."

# 7. Create Helpful Aliases (idempotent block)
if grep -q "# >>> Uno Q Dev Aliases >>>" "$HOME/.bashrc" 2>/dev/null; then
    echo "✅ Uno Q alias block already present in ~/.bashrc"
else
    cat >> "$HOME/.bashrc" <<EOF
# >>> Uno Q Dev Aliases >>>
alias mount-uno='sshfs $UNO_USER@$UNO_ALIAS:$REMOTE_DIR $LOCAL_MOUNT_DIR -o allow_other,reconnect,ServerAliveInterval=15'
alias unmount-uno='fusermount -u $LOCAL_MOUNT_DIR'
alias uno-shell='ssh $UNO_USER@$UNO_ALIAS'
# <<< Uno Q Dev Aliases <<<
EOF
    echo "✅ Added Uno Q alias block to ~/.bashrc"
fi

echo "✨ Setup Complete!"
echo "🔄 Run 'source ~/.bashrc' to activate aliases."
echo "⌨️  Then type 'mount-uno' to link your files."