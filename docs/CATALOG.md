# Service Catalog Documentation

The Agent Platform includes a **web-based service catalog** that provides live documentation and browsing of all available agents, tools, and workers.

## 🎯 Overview

The catalog is a dual-service application:
- **Catalog API** (FastAPI backend) - Queries Consul and gRPC for service data
- **Catalog UI** (React frontend) - Modern web interface for browsing services

Both services are:
- Registered in Consul for service discovery
- Routed through HAProxy for load balancing
- Horizontally scalable (1-3 instances each)
- Health monitored with automatic failover

## 🚀 Quick Start

### Access the Catalog

```bash
# Open web interface
make ui-catalog

# Or visit directly
open http://localhost:8080
```

### API Endpoints

```bash
# Get complete catalog
curl http://localhost:8000/api/catalog | jq

# Get agents only
curl http://localhost:8000/api/agents | jq

# Get tools only
curl http://localhost:8000/api/tools | jq

# Get workers only
curl http://localhost:8000/api/workers | jq

# Health check
curl http://localhost:8000/health
```

## 📊 Features

### Live Service Discovery

The catalog automatically discovers all services registered in Consul:
- **Agents**: Task execution services with specific capabilities
- **Tools**: Utility services that provide specific functionality
- **Workers**: Specialized services for complex, long-running tasks

### Interactive Documentation

For each service, the catalog displays:
- **Basic Information**
  - Service ID
  - Name and description
  - Endpoint address
  - Instance count
  - Health status

- **Parameters** (for tools)
  - Parameter name
  - Data type (string, integer, boolean, etc.)
  - Required vs optional
  - Description

- **Capabilities** (for agents)
  - List of agent capabilities
  - Service tags

- **Example Requests**
  - Complete JSON request format
  - All parameters with example values

- **Example Responses**
  - Expected response structure
  - Sample data
  - Metadata fields

### Real-time Status

- **Health Status**: Live health check results (healthy/degraded/unknown)
- **Instance Counts**: Number of running instances for each service
- **Color-coded Badges**: Visual status indicators

### Responsive Design

- Modern dark theme
- Mobile-friendly layout
- Tab-based navigation (All/Agents/Tools/Workers)
- One-click refresh

## 🏗️ Architecture

### System Diagram

```
┌─────────────────────────────────────────────────────────┐
│                     Browser                             │
└────────────────────┬────────────────────────────────────┘
                     │
          ┌──────────▼──────────┐
          │  HAProxy (Port 8080)│
          │  Load Balancer      │
          └──────────┬──────────┘
                     │
        ┌────────────▼────────────┐
        │  Catalog UI (1-3 inst)  │
        │  React + Vite + Nginx   │
        └────────────┬────────────┘
                     │
          ┌──────────▼──────────┐
          │  HAProxy (Port 8000)│
          │  Load Balancer      │
          └──────────┬──────────┘
                     │
        ┌────────────▼────────────┐
        │ Catalog API (1-3 inst)  │
        │  FastAPI Backend        │
        └──┬─────────────────┬────┘
           │                 │
    ┌──────▼────┐     ┌─────▼───────┐
    │  Consul   │     │  HAProxy    │
    │ (Registry)│     │ (gRPC:50051)│
    └───────────┘     └──────┬──────┘
                             │
                      ┌──────▼──────┐
                      │ Agents/Tools│
                      │   Workers   │
                      └─────────────┘
```

### Component Details

#### Catalog API (Backend)

**Technology**: Python + FastAPI

**Responsibilities**:
- Query Consul for service list and health status
- Query gRPC services for metadata (names, descriptions, parameters)
- Aggregate data into unified response format
- Provide REST API endpoints
- Register itself with Consul
- Respond to health checks

**Endpoints**:
- `GET /` - API information
- `GET /health` - Health check (Consul monitors this)
- `GET /api/catalog` - Complete catalog
- `GET /api/agents` - List agents
- `GET /api/tools` - List tools
- `GET /api/workers` - List workers

**Port**: 8000 (via HAProxy)

**Scaling**: 1-3 instances

#### Catalog UI (Frontend)

**Technology**: React + Vite + Nginx

**Responsibilities**:
- Provide web interface for browsing services
- Display service information in organized format
- Show example requests and responses
- Real-time status indicators
- Register itself with Consul (via Python sidecar)
- Serve static files (nginx)

**Port**: 80 internally, 8080 via HAProxy

**Scaling**: 1-3 instances

### Consul Integration

Both services register with Consul:

**Catalog API Registration**:
```python
{
  "name": "catalog-api",
  "id": "catalog-api-{hostname}-8000",
  "address": "{container-hostname}",
  "port": 8000,
  "tags": ["catalog", "api", "http"],
  "check": {
    "http": "http://{hostname}:8000/health",
    "interval": "10s",
    "timeout": "5s"
  }
}
```

**Catalog UI Registration**:
```python
{
  "name": "catalog-ui",
  "id": "catalog-ui-{hostname}-80",
  "address": "{container-hostname}",
  "port": 80,
  "tags": ["catalog", "ui", "http", "nginx"],
  "check": {
    "http": "http://{hostname}:80/health",
    "interval": "10s",
    "timeout": "5s"
  }
}
```

### HAProxy Configuration

**Frontend for API** (port 8000):
```
frontend catalog_api_frontend
    bind *:8000
    mode http
    default_backend catalog_api_backend
```

**Backend for API**:
```
backend catalog_api_backend
    mode http
    balance roundrobin
    option httpchk GET /health
    
    server catalog-api1 agent-platform-server-catalog-api-1:8000 check
    server catalog-api2 agent-platform-server-catalog-api-2:8000 check
    server catalog-api3 agent-platform-server-catalog-api-3:8000 check
```

**Frontend for UI** (port 8080):
```
frontend catalog_ui_frontend
    bind *:8080
    mode http
    default_backend catalog_ui_backend
```

**Backend for UI**:
```
backend catalog_ui_backend
    mode http
    balance roundrobin
    option httpchk GET /health
    
    server catalog-ui1 agent-platform-server-catalog-ui-1:80 check
    server catalog-ui2 agent-platform-server-catalog-ui-2:80 check
    server catalog-ui3 agent-platform-server-catalog-ui-3:80 check
```

## 📦 Scaling

The catalog services are designed for horizontal scaling.

### Scaling Commands

```bash
# Scale both API and UI to 3 instances
make scale-catalog N=3

# Scale API only
make scale-catalog-api N=3

# Scale UI only
make scale-catalog-ui N=3

# Scale back to 1 instance
make scale-catalog N=1
```

### Verification

```bash
# Check instances in Consul
curl http://localhost:8500/v1/health/service/catalog-api | jq
curl http://localhost:8500/v1/health/service/catalog-ui | jq

# Or use Makefile
make consul-check

# View HAProxy stats
make ui-haproxy
```

### Load Distribution

HAProxy uses **round-robin** load balancing:
- Each request goes to the next available instance
- Health checks ensure only healthy instances receive traffic
- Failed instances are automatically removed from rotation
- New instances are automatically added when healthy

### Benefits

- **High Availability**: Service continues if instances fail
- **Load Distribution**: Multiple instances handle concurrent requests
- **Zero Downtime**: Scale up/down without interruption
- **Auto-Discovery**: New instances register automatically
- **Health Monitoring**: Failed instances removed automatically

## 🔧 Development

### Running Locally

#### Backend (API)

```bash
cd catalog-api

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export CONSUL_HOST=localhost
export CONSUL_PORT=8500
export GRPC_ROUTER_HOST=localhost
export GRPC_ROUTER_PORT=50051

# Run
python app.py
```

#### Frontend (UI)

```bash
cd catalog-ui

# Install dependencies
npm install

# Set API URL
export VITE_API_URL=http://localhost:8000

# Run dev server
npm run dev

# Build for production
npm run build
```

### Building Docker Images

```bash
# Build both services
make catalog-build

# Or individually
docker-compose build catalog-api
docker-compose build catalog-ui
```

### Starting Services

```bash
# Start both services
make catalog-up

# Or manually
docker-compose up -d catalog-api catalog-ui
```

### Viewing Logs

```bash
# API logs
make logs-catalog-api
# or
docker logs -f agent-platform-server-catalog-api-1

# UI logs
make logs-catalog-ui
# or
docker logs -f agent-platform-server-catalog-ui-1
```

### Restarting Services

```bash
# Restart both
make catalog-restart

# Or manually
docker-compose restart catalog-api catalog-ui
```

## 📚 API Response Format

### Catalog Response

```json
{
  "agents": [
    {
      "id": "echo-agent",
      "name": "Echo Agent",
      "description": "Echo agent service",
      "capabilities": ["agent", "echo", "text-processing"],
      "endpoint": "container:50052",
      "instances": 1,
      "status": "healthy",
      "example_response": {
        "task_id": "task-abc123",
        "status": "completed",
        "result": "Echo: your input text",
        "metadata": {
          "agent_id": "echo-agent",
          "processing_time_ms": 150,
          "timestamp": "2025-10-15T12:00:00Z"
        }
      }
    }
  ],
  "tools": [
    {
      "id": "weather-tool",
      "name": "Weather Tool",
      "description": "Provides weather information",
      "endpoint": "weather-tool:50053",
      "parameters": [
        {
          "name": "location",
          "type": "string",
          "required": true,
          "description": "City or location name"
        },
        {
          "name": "days",
          "type": "integer",
          "required": false,
          "description": "Number of days for forecast"
        }
      ],
      "instances": 1,
      "status": "healthy",
      "example_response": {
        "location": "San Francisco",
        "current": {
          "temperature": 18,
          "condition": "Partly Cloudy"
        },
        "forecast": [...]
      }
    }
  ],
  "workers": [...],
  "total_services": 3
}
```

## 🎨 UI Components

### Service Cards

Each service is displayed in a card containing:
- **Header**: Service name, status badge
- **Description**: What the service does
- **Details**: ID, endpoint, instance count
- **Capabilities/Tags**: Service-specific tags
- **Parameters Table** (tools only): Name, type, required, description
- **Example Request**: JSON format with all parameters
- **Example Response**: Sample output with realistic data

### Navigation

- **Tabs**: Filter by All, Agents, Tools, or Workers
- **Stats Bar**: Shows count of each service type
- **Refresh Button**: Reload latest data from API

### Status Indicators

- **Green (Healthy)**: Service has 1+ healthy instances
- **Yellow (Degraded)**: Service is partially available
- **Gray (Unknown)**: Service has no registered instances
- **Red (Down)**: Service is unavailable

## 🔍 Troubleshooting

### API Not Responding

```bash
# Check if API is running
docker ps | grep catalog-api

# Check logs
make logs-catalog-api

# Check health
curl http://localhost:8000/health

# Restart
docker-compose restart catalog-api
```

### UI Not Loading

```bash
# Check if UI is running
docker ps | grep catalog-ui

# Check logs
make logs-catalog-ui

# Check nginx status
docker exec agent-platform-server-catalog-ui-1 nginx -t

# Restart
docker-compose restart catalog-ui
```

### Services Not Appearing

```bash
# Verify services are in Consul
make consul-check

# Check gRPC connectivity
docker exec agent-platform-server-catalog-api-1 curl haproxy:50051

# Restart HAProxy
docker-compose restart haproxy
```

### HAProxy Not Routing

```bash
# Check HAProxy config
docker exec haproxy-lb cat /usr/local/etc/haproxy/haproxy.cfg

# View HAProxy logs
docker logs haproxy-lb

# Check HAProxy stats
make ui-haproxy
```

### Consul Registration Issues

```bash
# Check Consul connectivity
docker exec agent-platform-server-catalog-api-1 curl consul:8500/v1/status/leader

# View registered services
curl http://localhost:8500/v1/catalog/services

# Clean up stale registrations
make consul-cleanup
```

## 🎯 Best Practices

### Scaling Strategy

1. **Start with 1 instance** of each service (default)
2. **Scale to 2-3 instances** for production
3. **Monitor HAProxy stats** to verify load distribution
4. **Check Consul** to ensure all instances are healthy

### Performance

- **API**: Can handle ~1000 requests/second per instance
- **UI**: Nginx can serve ~10,000 requests/second per instance
- **Recommended**: 2-3 instances for production workloads

### Maintenance

- **Regular health checks**: Monitor HAProxy dashboard
- **Consul cleanup**: Run `make consul-cleanup` periodically
- **Log rotation**: Monitor log sizes, rotate as needed
- **Updates**: Use `make catalog-build` and rolling restart

## 🚀 Future Enhancements

Potential improvements to the catalog:

1. **Search & Filter**: Full-text search across services
2. **API Playground**: Test services directly from UI
3. **Metrics Dashboard**: Request rates, latency, errors
4. **Documentation Editor**: Add custom notes to services
5. **Version History**: Track service changes over time
6. **Export Options**: Download catalog as JSON/Markdown
7. **Authentication**: Secure access with user accounts
8. **Real-time Updates**: WebSocket for live status changes

## 📖 Related Documentation

- [README.md](../README.md) - Main documentation
- [SCALING.md](../catalog-api/SCALING.md) - Catalog scaling details
- [ARCHITECTURE.md](ARCHITECTURE.md) - Overall platform architecture
- [LOAD_BALANCING.md](LOAD_BALANCING.md) - HAProxy configuration
- [MCP_SERVICE_DISCOVERY.md](MCP_SERVICE_DISCOVERY.md) - Service discovery

---

**Built with ❤️ using React, FastAPI, and modern web technologies**

