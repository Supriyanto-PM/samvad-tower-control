#!/bin/bash
# ==============================================================================
# Samvad Tower Control - 1-Click Application Launcher for macOS
# Starts Streamlit backend server, Cloudflare tunnel, and opens browser.
# ==============================================================================
cd "$(dirname "$0")"

echo "=========================================================="
echo " SAMVAD PMO COMMAND CENTER // 1-CLICK LAUNCHER"
echo "=========================================================="

# Check if Streamlit is already running on port 8502
if lsof -Pi :8502 -sTCP:LISTEN -t >/dev/null ; then
    echo "Streamlit server is already running on port 8502."
else
    echo "Starting Streamlit server on port 8502..."
    nohup .venv/bin/streamlit run app.py --server.port 8502 --server.headless true --server.address 0.0.0.0 --server.enableCORS false --server.enableXsrfProtection false > /dev/null 2>&1 &
    sleep 3
fi

# Check if cloudflared is already running
if pgrep -f "cloudflared tunnel" >/dev/null ; then
    echo "Cloudflare Tunnel is already running."
else
    echo "Starting Cloudflare Tunnel..."
    nohup .venv/bin/cloudflared tunnel --url http://127.0.0.1:8502 > /tmp/samvad_tunnel.log 2>&1 &
    sleep 4
    TUNNEL_URL=$(grep -o 'https://[-a-z0-9]*\.trycloudflare\.com' /tmp/samvad_tunnel.log | head -n 1)
    if [ -n "$TUNNEL_URL" ]; then
        echo "$TUNNEL_URL" > tunnel_url.txt
        echo "Public URL: $TUNNEL_URL"
    fi
fi

echo "Opening Samvad PMO Command Center in browser..."
open "http://localhost:8502"
echo "Application is running successfully in the background."
