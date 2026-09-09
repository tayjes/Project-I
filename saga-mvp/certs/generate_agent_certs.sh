#!/usr/bin/env bash
# Generates a self-signed TLS cert shared by both agent containers
# (local/dev use only -- client-side verification is disabled for this
# MVP, so a single cert with both hostnames as SANs is fine).
set -e
cd "$(dirname "$0")"
openssl req -x509 -newkey rsa:4096 -nodes \
  -keyout agent.key -out agent.crt -days 365 \
  -subj "/CN=saga-agent" \
  -addext "subjectAltName=DNS:alice-agent,DNS:bob-agent,DNS:localhost,IP:127.0.0.1"
echo "Agent certs written to $(pwd)/agent.key and $(pwd)/agent.crt"
