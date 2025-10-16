FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY tools/weather-tool/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy proto files and compile them
COPY proto /app/proto
WORKDIR /app/proto
RUN python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. agent_platform.proto

# Copy application code
WORKDIR /app
COPY tools/weather-tool/server.py .

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/proto:$PYTHONPATH
ENV CONSUL_HOST=consul
ENV CONSUL_PORT=8500
ENV TOOL_PORT=50053
ENV TOOL_HOST=weather-tool

# Expose port
EXPOSE 50053

# Run the application
CMD ["python", "server.py"]

