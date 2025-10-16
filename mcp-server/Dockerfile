FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY mcp-server/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy proto files
COPY proto /app/proto

# Compile proto files
WORKDIR /app/proto
RUN python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. agent_platform.proto

# Copy MCP server
WORKDIR /app
COPY mcp-server/server.py .

# Add proto directory to Python path
ENV PYTHONPATH="/app/proto:${PYTHONPATH}"

# Set environment variables
ENV GRPC_ROUTER_HOST=mcp-router
ENV GRPC_ROUTER_PORT=50051

# Run the MCP server
CMD ["python", "server.py"]

