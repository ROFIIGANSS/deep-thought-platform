FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY tasks/itinerary-task/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy proto files and compile them
COPY proto /app/proto
WORKDIR /app/proto
RUN python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. agent_platform.proto

# Copy application code
WORKDIR /app
COPY tasks/itinerary-task/worker.py .

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/proto:$PYTHONPATH
ENV CONSUL_HOST=consul
ENV CONSUL_PORT=8500
ENV WORKER_PORT=50054
ENV WORKER_HOST=itinerary-worker

# Expose port
EXPOSE 50054

# Run the application
CMD ["python", "worker.py"]

