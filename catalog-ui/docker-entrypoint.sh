#!/bin/sh
set -e

# Start Consul registration in background
python3 /usr/local/bin/register_consul.py &
CONSUL_PID=$!

# Function to cleanup on exit
cleanup() {
    echo "Shutting down..."
    kill $CONSUL_PID 2>/dev/null || true
    nginx -s quit 2>/dev/null || true
    wait $CONSUL_PID
}

# Setup trap
trap cleanup TERM INT

# Start nginx in foreground
nginx -g "daemon off;" &
NGINX_PID=$!

# Wait for processes
wait $NGINX_PID

# Cleanup
cleanup

