#!/usr/bin/env bash
# Store Cloudflare R2 upload keys for rclone, as a remote named "r2".
# Run it yourself in a terminal: it asks for the keys without showing them,
# and writes them only to rclone's config file on this computer.
#
#   bash pipeline/setup_r2.sh
#
# You need, from the Cloudflare dashboard (R2 > API tokens):
#   the Access Key ID, the Secret Access Key, and the S3 endpoint
#   (https://<account id>.r2.cloudflarestorage.com).
set -euo pipefail
RCLONE="${RCLONE:-$(command -v rclone || echo "$HOME/.local/bin/rclone")}"

read -r  -p 'S3 endpoint (https://....r2.cloudflarestorage.com): ' endpoint
read -r  -p 'Access Key ID: ' key_id
read -rs -p 'Secret Access Key (hidden as you type): ' secret; echo

"$RCLONE" config create r2 s3 provider=Cloudflare env_auth=false \
  access_key_id="$key_id" secret_access_key="$secret" endpoint="$endpoint" \
  acl=private no_check_bucket=true --non-interactive >/dev/null
chmod 600 "$("$RCLONE" config file | tail -1)"
echo "Saved. Checking the connection..."
if "$RCLONE" lsd r2:apollo-media >/dev/null 2>&1 || "$RCLONE" ls r2:apollo-media --max-depth 1 >/dev/null 2>&1; then
  echo "Connected to the apollo-media bucket."
else
  echo "Could not reach r2:apollo-media. Check the endpoint and keys, then run this again."
  exit 1
fi
