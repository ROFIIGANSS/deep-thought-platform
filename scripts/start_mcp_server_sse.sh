#!/bin/bash
# Start MCP Server with SSE transport for Cursor IDE integration
# This script runs the MCP server locally using HTTP/SSE

set -e

cd "$(dirname "$0")/.."

echo "Starting MCP Server (SSE transport) for Cursor IDE..."
echo "Connecting to gRPC Router at localhost:50051"
echo "SSE endpoint: http://localhost:3000/sse"

# Activate virtual environment
if [ ! -d "venv" ]; then
    echo "Error: Virtual environment not found. Run 'make setup' first."
    exit 1
fi

source venv/bin/activate

# Set environment variables
export GRPC_ROUTER_HOST=localhost
export GRPC_ROUTER_PORT=50051
export MCP_TRANSPORT=sse
export MCP_PORT=3000

# Check if services are running
if ! nc -z localhost 50051 2>/dev/null; then
    echo "Warning: gRPC Router not accessible at localhost:50051"
    echo "Make sure services are running: make up"
fi

# Install MCP dependencies if needed
if ! python -c "import mcp" 2>/dev/null; then
    echo "Installing MCP dependencies..."
    pip install -r requirements.txt
fi

# Run MCP server with SSE transport
echo "MCP Server starting with SSE transport..."
echo "Configure Cursor to use: http://localhost:3000/sse"
echo ""
python mcp-server/server.py

