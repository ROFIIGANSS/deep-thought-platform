FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY agents/echo/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy proto files and compile them
COPY proto /app/proto
WORKDIR /app/proto
RUN python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. agent_platform.proto

# Copy application code
WORKDIR /app
COPY agents/echo/server.py .

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/proto:$PYTHONPATH
ENV CONSUL_HOST=consul
ENV CONSUL_PORT=8500
ENV AGENT_PORT=50052
ENV AGENT_HOST=echo-agent

# Expose port
EXPOSE 50052

# Run the application
CMD ["python", "server.py"]

