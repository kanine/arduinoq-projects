#!/usr/bin/env bash

set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  ./bash/sync_to_uno1.sh [options] [app_name ...]

Sync Arduino Uno Q App Lab projects from this repo to a remote board using rsync.

Options:
  --host NAME       SSH host alias or hostname. Default: uno1
  --remote-dir DIR  Remote ArduinoApps directory. Default: /home/arduino/ArduinoApps
  --dry-run         Show what would change without copying files
  --delete          Delete remote files that no longer exist locally for synced apps
  -h, --help        Show this help

Examples:
  ./bash/sync_to_uno1.sh
  ./bash/sync_to_uno1.sh predictivesensorcontroller
  ./bash/sync_to_uno1.sh --dry-run sonic-sensor timeofflightcheck
EOF
}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

HOST="uno1"
REMOTE_DIR="/home/arduino/ArduinoApps"
DRY_RUN=0
DELETE=0

declare -a REQUESTED_APPS=()

while (($# > 0)); do
  case "$1" in
    --host)
      HOST="${2:-}"
      shift 2
      ;;
    --remote-dir)
      REMOTE_DIR="${2:-}"
      shift 2
      ;;
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    --delete)
      DELETE=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    -*)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 1
      ;;
    *)
      REQUESTED_APPS+=("$1")
      shift
      ;;
  esac
done

if [[ -z "${HOST}" || -z "${REMOTE_DIR}" ]]; then
  echo "Host and remote directory must be non-empty." >&2
  exit 1
fi

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Missing required command: $1" >&2
    exit 1
  fi
}

require_cmd rsync
require_cmd ssh

discover_apps() {
  local dir
  for dir in "${REPO_ROOT}"/*; do
    [[ -d "${dir}" ]] || continue
    [[ -f "${dir}/app.yaml" ]] || continue
    basename "${dir}"
  done
}

declare -a ALL_APPS=()
while IFS= read -r app; do
  [[ -n "${app}" ]] && ALL_APPS+=("${app}")
done < <(discover_apps | sort)

if ((${#ALL_APPS[@]} == 0)); then
  echo "No App Lab projects with app.yaml were found under ${REPO_ROOT}." >&2
  exit 1
fi

declare -a APPS_TO_SYNC=()

if ((${#REQUESTED_APPS[@]} == 0)); then
  APPS_TO_SYNC=("${ALL_APPS[@]}")
else
  declare -A APP_INDEX=()
  for app in "${ALL_APPS[@]}"; do
    APP_INDEX["${app}"]=1
  done

  for app in "${REQUESTED_APPS[@]}"; do
    if [[ -z "${APP_INDEX[${app}]:-}" ]]; then
      echo "App not found locally: ${app}" >&2
      exit 1
    fi
    APPS_TO_SYNC+=("${app}")
  done
fi

declare -a RSYNC_ARGS=(
  --archive
  --compress
  --human-readable
  --itemize-changes
  --omit-dir-times
  --exclude=.git
  --exclude=.DS_Store
  --exclude=__pycache__/
  --exclude=*.pyc
)

if ((DRY_RUN)); then
  RSYNC_ARGS+=(--dry-run)
fi

if ((DELETE)); then
  RSYNC_ARGS+=(--delete)
fi

echo "Remote host: ${HOST}"
echo "Remote app dir: ${REMOTE_DIR}"
echo "Repo root: ${REPO_ROOT}"
echo "Apps to sync: ${APPS_TO_SYNC[*]}"
echo

ssh "${HOST}" "mkdir -p '${REMOTE_DIR}'"

if ! ssh "${HOST}" "command -v rsync >/dev/null 2>&1"; then
  cat >&2 <<EOF
Remote host '${HOST}' does not have rsync installed.
Install it on the board first, then rerun this script.

Suggested remote command:
  ssh ${HOST} 'sudo apt update && sudo apt install -y rsync'
EOF
  exit 1
fi

for app in "${APPS_TO_SYNC[@]}"; do
  local_path="${REPO_ROOT}/${app}/"
  remote_path="${HOST}:${REMOTE_DIR}/${app}/"

  echo "==> Syncing ${app}"
  rsync "${RSYNC_ARGS[@]}" "${local_path}" "${remote_path}"
  echo
done

echo "Sync complete."
