#!/bin/bash
# ==============================================================================
# Samvad PMO CC - Public Tunnel Launcher (Cloudflare Tunnel)
# Exposes local Streamlit (port 8502) to a public HTTPS URL accessible from smartphones
# ==============================================================================
cd "$(dirname "$0")"

if [ ! -f ".venv/bin/cloudflared" ]; then
    echo "Downloading cloudflared..."
    curl -L -o /tmp/cloudflared.tgz https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-darwin-arm64.tgz
    tar -xzf /tmp/cloudflared.tgz -C .venv/bin/
    chmod +x .venv/bin/cloudflared
    rm /tmp/cloudflared.tgz
fi

echo "Starting Cloudflare Public Tunnel on port 8502..."
.venv/bin/cloudflared tunnel --url http://127.0.0.1:8502
