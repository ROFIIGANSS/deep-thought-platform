#!/bin/bash
# Setup script for Agent Platform

set -e

echo "=========================================="
echo "Agent Platform - Setup Script"
echo "=========================================="
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "✗ Python 3 is not installed. Please install Python 3.11 or higher."
    exit 1
fi

echo "✓ Python found: $(python3 --version)"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo ""
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
fi

# Activate virtual environment
echo ""
echo "Activating virtual environment..."
source venv/bin/activate
echo "✓ Virtual environment activated"

# Install base requirements
echo ""
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
echo "✓ Dependencies installed"

# Compile proto files
echo ""
echo "Compiling Protocol Buffer definitions..."
bash scripts/compile_proto.sh

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo ""
    echo "Creating .env file..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "✓ .env file created from template"
    else
        # Create a basic .env file with defaults
        cat > .env << 'EOF'
# Agent Platform Environment Configuration
# Customize as needed

# Consul Configuration
CONSUL_HOST=consul
CONSUL_PORT=8500

# MCP Router Configuration
MCP_ROUTER_PORT=50051
MCP_ROUTER_HOST=mcp-router

# General Settings
LOG_LEVEL=INFO
EOF
        echo "✓ .env file created with defaults"
    fi
else
    echo ""
    echo "✓ .env file already exists"
fi

echo ""
echo "=========================================="
echo "✓ Setup complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. Review and customize .env file if needed"
echo "  2. Start services with: docker-compose up -d"
echo "  3. Test services with: python scripts/test_client.py"
echo "  4. View Consul UI at: http://localhost:8500"
echo ""

