#!/usr/bin/env bash
# Generates a self-signed TLS cert for the Provider (local/dev use only).
# Run this from the project root: bash certs/generate_certs.sh
set -e
cd "$(dirname "$0")"
openssl req -x509 -newkey rsa:4096 -nodes \
  -keyout provider.key -out provider.crt -days 365 \
  -subj "/CN=provider" \
  -addext "subjectAltName=DNS:provider,DNS:localhost,IP:127.0.0.1"
echo "Certs written to $(pwd)/provider.key and $(pwd)/provider.crt"
