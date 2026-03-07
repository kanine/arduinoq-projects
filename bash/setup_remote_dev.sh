#!/bin/bash

# --- Configuration ---
UNO_IP="<your-uno-q-ip>"
UNO_USER="arduino"
LOCAL_MOUNT_DIR="$HOME/ArduinoProjects"
REMOTE_DIR="/home/arduino/ArduinoApps"

echo "🚀 Starting Uno Q Remote Dev Setup..."

# 1. Install Dependencies
echo "📦 Installing sshfs..."
sudo apt update && sudo apt install -y sshfs

# 2. Create Mount Point
if [ ! -d "$LOCAL_MOUNT_DIR" ]; then
    echo "📁 Creating local mount directory at $LOCAL_MOUNT_DIR"
    mkdir -p "$LOCAL_MOUNT_DIR"
fi

# 3. Setup /etc/hosts Alias
if ! grep -q "uno1" /etc/hosts; then
    echo "📝 Adding 'uno1' to /etc/hosts (requires sudo)"
    echo "$UNO_IP uno1" | sudo tee -a /etc/hosts
else
    echo "✅ 'uno1' already exists in /etc/hosts"
fi

# 4. Enable user_allow_other in FUSE
echo "🔐 Enabling user_allow_other in /etc/fuse.conf"
sudo sed -i 's/#user_allow_other/user_allow_other/' /etc/fuse.conf

# 5. SSH Key Setup
if [ ! -f ~/.ssh/id_ed25519.pub ]; then
    echo "🔑 No SSH key found. Generating one..."
    ssh-keygen -t ed25519 -N "" -f ~/.ssh/id_ed25519
fi

echo "📤 Copying SSH key to Uno Q (Enter password for '$UNO_USER' if prompted)..."
ssh-copy-id -i ~/.ssh/id_ed25519.pub "$UNO_USER@uno1"

# 6. Create Helpful Aliases
echo "bash
# Uno Q Dev Aliases
alias mount-uno='sshfs $UNO_USER@uno1:$REMOTE_DIR $LOCAL_MOUNT_DIR -o allow_other,reconnect,ServerAliveInterval=15'
alias unmount-uno='fusermount -u $LOCAL_MOUNT_DIR'
alias uno-shell='ssh $UNO_USER@uno1'
" >> ~/.bashrc

echo "✨ Setup Complete!"
echo "🔄 Run 'source ~/.bashrc' to activate aliases."
echo "⌨️  Then type 'mount-uno' to link your files."