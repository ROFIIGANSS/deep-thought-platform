# Agent Platform Catalog

A web application that provides a dynamic catalog of all agents, tools, and workers in the Agent Platform, including their parameters, expected responses, and live status information.

## Architecture

The catalog consists of two main components:

### Backend (catalog-api)
- **Technology**: Python FastAPI
- **Port**: 8000
- **Functions**:
  - Queries Consul for service discovery and health information
  - Communicates with the gRPC router to fetch service metadata
  - Exposes REST API endpoints for the frontend
  - Provides real-time information about registered services

### Frontend (catalog-ui)
- **Technology**: React + Vite
- **Port**: 8080
- **Features**:
  - Modern, responsive UI with dark theme
  - Real-time service status indicators
  - Displays service parameters and schemas
  - Shows usage examples for each service
  - Tab-based navigation (All/Agents/Tools/Workers)
  - One-click refresh

## Endpoints

### Backend API Endpoints

- `GET /` - Root endpoint with API information
- `GET /health` - Health check endpoint
- `GET /api/catalog` - Complete catalog of all services
- `GET /api/agents` - List of all registered agents
- `GET /api/tools` - List of all registered tools
- `GET /api/workers` - List of all registered workers

### Frontend

- `http://localhost:8080` - Main catalog UI
- Displays agents, tools, and workers with:
  - Name and description
  - Live status (healthy/degraded/unknown)
  - Instance count
  - Endpoint information
  - Parameters and schemas
  - Example usage/requests

## Quick Start

### Using Make

```bash
# Build catalog services
make catalog-build

# Start catalog services
make catalog-up

# View logs
make logs-catalog-api
make logs-catalog-ui

# Restart services
make catalog-restart

# Open UI in browser
make ui-catalog
```

### Manual Docker Compose

```bash
# Build
docker-compose build catalog-api catalog-ui

# Start
docker-compose up -d catalog-api catalog-ui

# View
open http://localhost:8080
```

## Service Information Displayed

### For Agents
- Agent ID
- Name and description
- Capabilities
- Endpoint
- Number of instances
- Status (healthy/unknown)
- Example request format

### For Tools
- Tool ID
- Name and description
- Endpoint
- Parameters with:
  - Name
  - Type
  - Required/Optional
  - Description
- Number of instances
- Status (healthy/unknown)
- Example request with parameters

### For Workers
- Worker ID
- Name and description
- Endpoint
- Tags
- Number of instances
- Status (healthy/unknown)
- Example task format

## Development

### Backend Development

```bash
cd catalog-api

# Install dependencies
pip install -r requirements.txt

# Run locally (requires running Consul and HAProxy)
python app.py
```

### Frontend Development

```bash
cd catalog-ui

# Install dependencies
npm install

# Run dev server
npm run dev

# Build for production
npm run build
```

## Environment Variables

### Backend (catalog-api)
- `CONSUL_HOST`: Consul hostname (default: consul)
- `CONSUL_PORT`: Consul port (default: 8500)
- `GRPC_ROUTER_HOST`: gRPC router hostname (default: haproxy)
- `GRPC_ROUTER_PORT`: gRPC router port (default: 50051)
- `CATALOG_API_PORT`: API server port (default: 8000)

### Frontend (catalog-ui)
- `VITE_API_URL`: Backend API URL (default: http://localhost:8000)

## Dependencies

### Backend
- fastapi: Web framework
- uvicorn: ASGI server
- python-consul: Consul client
- grpcio: gRPC client
- protobuf: Protocol buffers
- pydantic: Data validation

### Frontend
- react: UI library
- vite: Build tool
- Modern browser with ES2015+ support

## Features

- **Real-time Data**: Fetches live information from Consul and gRPC
- **Dynamic Discovery**: Automatically discovers new services
- **Health Status**: Shows service health and instance counts
- **Parameter Schemas**: Displays input parameters and types
- **Usage Examples**: Provides example requests for each service
- **Responsive Design**: Works on desktop and mobile
- **Dark Theme**: Modern, eye-friendly interface
- **Fast Refresh**: Quick updates with one click

## Integration

The catalog integrates with:
- **Consul**: For service discovery and health checks
- **HAProxy**: For load-balanced gRPC access
- **Proto Definitions**: For service schemas and metadata
- **Agent Platform**: For live service information

## Troubleshooting

### Backend not connecting to Consul
- Verify Consul is running: `make status`
- Check network connectivity
- Verify environment variables

### Frontend not showing data
- Check API is accessible: `curl http://localhost:8000/health`
- Verify CORS is configured (already enabled for all origins in dev)
- Check browser console for errors

### Services not appearing
- Ensure services are registered in Consul: `make consul-check`
- Verify gRPC router is accessible
- Check service health status

## Notes

- The catalog automatically refreshes when you click the refresh button
- Service status colors:
  - Green: Healthy (1+ instances)
  - Yellow: Degraded
  - Gray: Unknown (no instances)
  - Red: Down
- The catalog requires Consul and HAProxy to be running
- All services must be registered in Consul to appear

