#!/bin/bash
# Script to compile Protocol Buffer definitions

set -e

echo "Compiling Protocol Buffer definitions..."

# Compile proto files
cd proto
python -m grpc_tools.protoc \
    -I. \
    --python_out=. \
    --grpc_python_out=. \
    agent_platform.proto

echo "✓ Proto files compiled successfully!"
echo ""
echo "Generated files:"
echo "  - agent_platform_pb2.py"
echo "  - agent_platform_pb2_grpc.py"

