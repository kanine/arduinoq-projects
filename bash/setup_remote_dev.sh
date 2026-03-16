#!/bin/bash

set -euo pipefail

# --- Configuration ---
UNO_IP="<your-uno-q-ip>"
UNO_USER="arduino"
UNO_ALIAS="uno1"
LOCAL_MOUNT_DIR="$HOME/ArduinoProjects"
REMOTE_DIR="/home/arduino/ArduinoApps"
SSH_CONFIG="$HOME/.ssh/config"

echo "🚀 Starting Uno Q Remote Dev Setup..."

require_cmd() {
    if ! command -v "$1" >/dev/null 2>&1; then
        echo "❌ Required command not found: $1"
        exit 1
    fi
}

find_identity_from_host() {
    local host="$1"
    local cfg="$2"

    if [ ! -f "$cfg" ]; then
        return 1
    fi

    awk -v host="$host" '
        BEGIN { in_host = 0 }
        /^[[:space:]]*[Hh]ost[[:space:]]+/ {
            in_host = 0
            for (i = 2; i <= NF; i++) {
                if ($i == host) {
                    in_host = 1
                }
            }
            next
        }
        in_host && /^[[:space:]]*[Ii]dentity[Ff]ile[[:space:]]+/ {
            sub(/^[[:space:]]*[Ii]dentity[Ff]ile[[:space:]]+/, "")
            gsub(/^"|"$/, "")
            print
            exit
        }
    ' "$cfg"
}

ensure_pub_from_private() {
    local private_key="$1"
    local public_key="${private_key}.pub"

    if [ ! -f "$private_key" ]; then
        return 1
    fi

    if [ ! -f "$public_key" ]; then
        echo "ℹ️ Public key missing for $private_key, regenerating ${public_key}"
        ssh-keygen -y -f "$private_key" > "$public_key"
        chmod 644 "$public_key"
    fi

    echo "$public_key"
}

pick_reusable_key() {
    local configured_identity
    local candidate
    local pub
    local -a common_private_keys=(
        "$HOME/.ssh/id_ed25519"
        "$HOME/.ssh/id_rsa"
        "$HOME/.ssh/id_ecdsa"
        "$HOME/.ssh/id_dsa"
    )

    configured_identity="$(find_identity_from_host "$UNO_ALIAS" "$SSH_CONFIG" || true)"
    if [ -n "$configured_identity" ]; then
        configured_identity="${configured_identity/#\~/$HOME}"
        configured_identity="${configured_identity/#\%d/$HOME}"
        configured_identity="${configured_identity//%u/$USER}"
        if [[ "$configured_identity" == *%* ]]; then
            echo "⚠️  IdentityFile path contains unexpanded SSH token(s): $configured_identity — skipping"
            configured_identity=""
        fi
        pub="$(ensure_pub_from_private "$configured_identity" || true)"
        if [ -n "$pub" ]; then
            echo "$pub"
            return 0
        fi
    fi

    for candidate in "${common_private_keys[@]}"; do
        pub="$(ensure_pub_from_private "$candidate" || true)"
        if [ -n "$pub" ]; then
            echo "⚠️  About to reuse $pub for uno1. This key may already be in use elsewhere." >&2
            read -rp "   Use this key? [y/N] " confirm </dev/tty
            [[ "$confirm" =~ ^[Yy]$ ]] || continue
            echo "$pub"
            return 0
        fi
    done

    return 1
}

print_alias_status() {
    local alias_name="$1"
    if [ -f "$SSH_CONFIG" ] && grep -qiE "^[[:space:]]*Host[[:space:]]+.*\b${alias_name}\b" "$SSH_CONFIG"; then
        echo "✅ SSH alias '${alias_name}' found in ${SSH_CONFIG}"
    else
        echo "⚠️ SSH alias '${alias_name}' not found in ${SSH_CONFIG}"
    fi
}

require_cmd ssh
require_cmd ssh-copy-id
require_cmd ssh-keygen
require_cmd awk
require_cmd grep

# 1. Install Dependencies
echo "📦 Installing sshfs..."
sudo apt update && sudo apt install -y sshfs

# 2. Create Mount Point
if [ ! -d "$LOCAL_MOUNT_DIR" ]; then
    echo "📁 Creating local mount directory at $LOCAL_MOUNT_DIR"
    mkdir -p "$LOCAL_MOUNT_DIR"
fi

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

# 5. Enable user_allow_other in FUSE only if needed
if grep -q '^user_allow_other' /etc/fuse.conf; then
    echo "✅ user_allow_other already enabled in /etc/fuse.conf"
else
    echo "🔐 Enabling user_allow_other in /etc/fuse.conf"
    sudo sed -i 's/^#user_allow_other/user_allow_other/' /etc/fuse.conf
fi

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
    echo "❌ UNO_IP is still a placeholder. Set it at the top of this script before running."
    exit 1
fi

echo "📤 Copying SSH key to Uno Q (enter password for '${UNO_USER}' if prompted)..."
ssh-copy-id -i "$SSH_PUB_KEY" "${UNO_USER}@${UNO_ALIAS}"

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