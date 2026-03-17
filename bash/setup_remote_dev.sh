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

# ... (middle functions remain unchanged)

require_cmd ssh
require_cmd ssh-copy-id
require_cmd ssh-keygen
require_cmd awk
require_cmd grep

# --- Stage 1: Local System Preparation ---
pause_for_stage "1/4" "Environment: Install sshfs, create mount point, and configure FUSE."

# 1. Install Dependencies
echo "📦 Installing sshfs..."
sudo apt update && sudo apt install -y sshfs

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
    if [ "$UNO_IP" = "<your-uno-q-ip>" ]; then
        echo "⚠️ UNO_IP is still set to placeholder; skipping /etc/hosts update"
    else
        echo "📝 Adding '${UNO_ALIAS}' to /etc/hosts (requires sudo)"
        echo "$UNO_IP $UNO_ALIAS" | sudo tee -a /etc/hosts >/dev/null
    fi
fi

# 4. Show SSH Alias Status
print_alias_status "$UNO_ALIAS"
print_alias_status "nuci7"

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

if [ "$UNO_IP" = "<your-uno-q-ip>" ]; then
    echo "❌ UNO_IP is still a placeholder. Set it via --unoip or edit the script."
    exit 1
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