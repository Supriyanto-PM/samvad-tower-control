#!/bin/bash
# ==============================================================================
# Samvad Tower Control - Clean Shutdown Script for macOS
# Safely stops Streamlit server and Cloudflare tunnel processes.
# ==============================================================================
cd "$(dirname "$0")"

echo "=========================================================="
echo " SAMVAD PMO COMMAND CENTER // SHUTDOWN"
echo "=========================================================="

echo "Stopping Streamlit server..."
pkill -f "streamlit run app.py" 2>/dev/null || true

echo "Stopping Cloudflare Tunnel..."
pkill -f "cloudflared tunnel" 2>/dev/null || true

echo "All Samvad background services have been stopped safely."
echo "Your database and all telemetry history remain permanently saved on disk."
