#!/bin/sh
set -eu

# If an SSH key is mounted read-only, its permissions may not be strict enough for OpenSSH.
# Copy it to a writable location with 0600 perms and point SSH_KEY_PATH to that copy.
if [ -n "${SSH_KEY_PATH:-}" ] && [ -f "${SSH_KEY_PATH}" ]; then
  mkdir -p /tmp/sbsync-ssh
  cp "${SSH_KEY_PATH}" /tmp/sbsync-ssh/id_key
  chmod 600 /tmp/sbsync-ssh/id_key
  export SSH_KEY_PATH=/tmp/sbsync-ssh/id_key
fi

exec python src/main.py
