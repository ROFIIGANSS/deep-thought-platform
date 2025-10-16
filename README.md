# Deep Thought Agent Execution Platform

[![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python&logoColor=white)](https://python.org)
[![gRPC](https://img.shields.io/badge/gRPC-1.60.0-green?logo=grpc&logoColor=white)](https://grpc.io)
[![React](https://img.shields.io/badge/React-19.1.1-blue?logo=react&logoColor=white)](https://reactjs.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-green?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Docker](https://img.shields.io/badge/Docker-3.9-blue?logo=docker&logoColor=white)](https://docker.com)
[![HAProxy](https://img.shields.io/badge/HAProxy-2.9-red?logo=haproxy&logoColor=white)](https://haproxy.org)
[![Consul](https://img.shields.io/badge/Consul-1.19-purple?logo=consul&logoColor=white)](https://consul.io)
[![Node.js](https://img.shields.io/badge/Node.js-20-green?logo=node.js&logoColor=white)](https://nodejs.org)
[![Vite](https://img.shields.io/badge/Vite-7.1.7-purple?logo=vite&logoColor=white)](https://vitejs.dev)
[![Nginx](https://img.shields.io/badge/Nginx-Alpine-green?logo=nginx&logoColor=white)](https://nginx.org)
[![Protocol Buffers](https://img.shields.io/badge/Protocol%20Buffers-4.25.1-orange?logo=protobuf&logoColor=white)](https://developers.google.com/protocol-buffers)
[![MCP](https://img.shields.io/badge/MCP-1.0.0+-yellow?logo=modelcontextprotocol&logoColor=white)](https://modelcontextprotocol.io)

A distributed **Proof of Concept (PoC)** agent platform built with Python and gRPC, featuring service discovery, dynamic routing, horizontal scaling with HAProxy load balancing, and extensible agent/tool architecture. This PoC demonstrates a more efficient model to deploy agents in a standardized way.

> **⚠️ Not Production Ready**: This is a PoC based on Docker Compose for development and testing. For production deployment, the next moves should be in the direction of deploying to a Kubernetes cluster using Terraform, Helm charts, and proper CI/CD pipelines.

![Deep Thought](docs/deep-thought.png)

> **🤖 Name Origins**: Inspired by "The Hitchhiker's Guide to the Galaxy" - where the Deep Thought computer calculated that the answer to the ultimate question of life, the universe, and everything is **42**. This platform represents our attempt to build the "agent infrastructure" that can help answer complex questions through distributed AI agents.

## 🏗️ Architecture

The platform consists of the following components:

### Core Components

1. **MCP Router** - Central routing service with service discovery
   - Routes requests to agents and tools
   - Manages service registry via Consul
   - Handles load balancing and failover
   - **Horizontally scalable with HAProxy load balancer**
   - Port: `50051` (public endpoint through HAProxy)

2. **HAProxy** - Load balancer for all HTTP/gRPC services
   - Round-robin load distribution
   - Health checks every 2 seconds
   - Real-time statistics dashboard
   - Routes: gRPC Router (50051), MCP Server (3000), Catalog API (8000), Catalog UI (8080)
   - Stats UI available at `http://localhost:8404`

3. **Consul** - Service discovery and health checking
   - Centralized service registry
   - Health monitoring with automatic failover
   - UI available at `http://localhost:8500`

4. **Catalog Services** - Web-based service catalog and documentation
   - **Catalog API** (Port: `8000` via HAProxy) - FastAPI backend
     - Lists all agents, tools, and workers
     - Shows parameters, schemas, and examples
     - Queries Consul and gRPC for live data
     - Scalable (1-3 instances)
   - **Catalog UI** (Port: `8080` via HAProxy) - React frontend
     - Modern web interface for browsing services
     - Real-time service status
     - Request/response examples
     - Scalable (1-3 instances)

![Architecture Overview](docs/architecture-overview.png)

### Agents

Agents are autonomous services that can execute tasks with specific capabilities.

- **Echo Agent** (Port: `50052`)
  - Simple demonstration agent
  - Echoes back input with processing
  - Shows streaming capabilities

### Tools

Tools provide specific functionality that agents can use.

- **Weather Tool** (Port: `50053`)
  - Provides weather information
  - Supports current weather and forecasts
  - Mock data for demonstration

### Task Workers

Specialized workers for complex, long-running tasks.

- **Itinerary Task Worker** (Port: `50054`)
  - Plans travel itineraries
  - AI-powered route optimization
  - Integrates with weather tool

## 🚀 Quick Start

### Prerequisites

- Python 3.11 or higher
- Docker and Docker Compose
- Git

### Installation

1. **Clone the repository**
```bash
cd agent-platform-server
```

2. **One-command setup** (recommended)
```bash
make quick-start
```

This will automatically:
- Create a virtual environment
- Install dependencies
- Compile Protocol Buffer definitions
- Build Docker images
- Start all services

**OR manual setup:**

```bash
# Run setup
make setup

# Build images
make build

# Start services
make up
```

3. **Verify services are running**
```bash
make status
```

All services should show as "healthy" or "running".

4. **Test the platform**
```bash
make test
```

Tests will connect through the MCP Router and verify all services.

5. **Browse the service catalog**
```bash
make ui-catalog
# Or visit: http://localhost:8080
```

The Catalog UI provides a web interface to:
- Browse all available agents, tools, and workers
- View parameters and schemas
- See example requests and responses
- Check real-time service status
- Monitor instance counts

## 📖 Service Catalog

The platform includes a **web-based service catalog** that dynamically discovers and documents all available services:

### Features

- **Live Service Discovery**: Automatically finds all agents, tools, and workers via Consul
- **Health-Aware Consolidation** ✨: Shows service health (healthy/degraded/unhealthy/down) with instance breakdown
- **Automatic Deduplication** ✨: Multiple instances display as single entry with instance count
- **Interactive Documentation**: Browse parameters, types, and descriptions
- **Example Requests**: See how to call each service
- **Example Responses**: View expected output format with session_id support
- **Real-time Status**: Check service health and instance counts
- **Scalable Architecture**: Both API and UI scale independently

### Access

- **Web UI**: http://localhost:8080 (or `make ui-catalog`)
- **REST API**: http://localhost:8000
  - `/api/catalog` - Complete catalog (agents, tools, workers)
  - `/api/agents` - List all agents
  - `/api/tools` - List all tools
  - `/api/workers` - List all workers
  - `/health` - Health check

### Architecture

```
Browser → HAProxy:8080 → catalog-ui (1-3 instances) → Consul
             ↓
          HAProxy:8000 → catalog-api (1-3 instances) → Consul + gRPC
```

Both services:
- Register with Consul for service discovery
- Route through HAProxy for load balancing
- Scale independently (1-3 instances each)
- Provide health checks
- **Deduplicate services** automatically (no duplicate entries)
- **Track health status** (healthy/unhealthy instance counts)

## ⚖️ Load Balancing & Scaling

The platform supports **horizontal scaling** of all services with HAProxy load balancing for the MCP Router and Consul-based service discovery!

### Scale MCP Router Instances

```bash
# Scale to 3 instances (recommended for production)
docker-compose up -d --scale mcp-router=3

# Scale to 5 instances (high availability)
docker-compose up -d --scale mcp-router=5

# Use the convenient management script
./scripts/manage_routers.sh scale 3

# Or use Makefile
make scale-router N=3
```

### Scale Other Services

```bash
# Scale agents, tools, and workers
make scale-echo N=3
make scale-weather N=2
make scale-itinerary N=3

# Scale catalog services
make scale-catalog N=3        # Both API and UI
make scale-catalog-api N=3    # API only
make scale-catalog-ui N=3     # UI only

# Or scale all services at once
make scale-all N=3
```

### Monitoring

- **Catalog UI**: http://localhost:8080 (or `make ui-catalog`) - Browse all services with examples
- **HAProxy Stats**: http://localhost:8404 (or `make ui-haproxy`) - Load balancer dashboard
- **Consul Service Registry**: http://localhost:8500 (or `make ui-consul`) - Service discovery
- **Service Health**: `make consul-check`
- **Service Status**: `make status`

### Management Commands

```bash
# Show status of all router instances
./scripts/manage_routers.sh status

# Check health of all services
./scripts/manage_routers.sh health

# View logs from all routers
./scripts/manage_routers.sh logs

# Open HAProxy dashboard
./scripts/manage_routers.sh haproxy

# Open Consul UI
./scripts/manage_routers.sh consul
```

**For detailed information**, see:
- [LOAD_BALANCING.md](docs/LOAD_BALANCING.md) - Complete load balancing guide
- [SCALING_GUIDE.md](docs/SCALING_GUIDE.md) - Comprehensive scaling documentation
- [QUICK_REFERENCE_LOAD_BALANCING.md](docs/QUICK_REFERENCE_LOAD_BALANCING.md) - Quick command reference

## 📖 Usage

> **Note**: All clients connect through the **MCP Router** (port 50051), which handles service discovery and routing to backend services.

### Session ID Support (NEW!)

All services now support **session IDs** for context recovery and maintaining conversational state across multiple requests:

```python
import uuid

# Generate a session ID (use same ID for related requests)
session_id = str(uuid.uuid4())

# Include session_id in your requests
request = agent_platform_pb2.TaskRequest(
    task_id=str(uuid.uuid4()),
    agent_id='echo-agent',
    input='Remember this context',
    parameters={'key': 'value'},
    session_id=session_id  # NEW: Session ID for context recovery
)

# Response includes the session_id for correlation
response = stub.ExecuteTask(request)
print(f"Session ID: {response.session_id}")

# Use same session_id in follow-up requests to maintain context
request2 = agent_platform_pb2.TaskRequest(
    task_id=str(uuid.uuid4()),
    agent_id='echo-agent',
    input='Do you remember?',
    session_id=session_id  # Same session ID
)
```

Session IDs enable:
- 🧠 **Context Memory** - Agents remember previous interactions
- 🔄 **Multi-Turn Conversations** - Build complex workflows
- 📊 **Session Tracking** - Monitor user sessions
- 💾 **State Recovery** - Resume from interruptions

**📘 Complete guide:** [SESSION_ID_GUIDE.md](docs/SESSION_ID_GUIDE.md)

### Using the Echo Agent

```python
import grpc
import agent_platform_pb2
import agent_platform_pb2_grpc
import uuid

# Connect through MCP Router (NOT directly to agent!)
channel = grpc.insecure_channel('localhost:50051')
stub = agent_platform_pb2_grpc.AgentServiceStub(channel)

# Execute a task
task_id = str(uuid.uuid4())
request = agent_platform_pb2.TaskRequest(
    task_id=task_id,
    agent_id='echo-agent',
    input='Hello, World!',
    parameters={'key': 'value'}
)

response = stub.ExecuteTask(request)
print(f"Success: {response.success}")
print(f"Output: {response.output}")

# Get agent status
status_request = agent_platform_pb2.StatusRequest(agent_id='echo-agent')
status = stub.GetStatus(status_request)
print(f"Status: {status.status}")
print(f"Active tasks: {status.active_tasks}")
```

### Using the Weather Tool

```python
import grpc
import agent_platform_pb2
import agent_platform_pb2_grpc

# Connect through MCP Router
channel = grpc.insecure_channel('localhost:50051')
stub = agent_platform_pb2_grpc.ToolServiceStub(channel)

# Get weather
request = agent_platform_pb2.ToolRequest(
    tool_id='weather-tool',
    operation='get_weather',
    parameters={'location': 'Paris'}
)

response = stub.ExecuteTool(request)
print(response.result)

# Get forecast
forecast_request = agent_platform_pb2.ToolRequest(
    tool_id='weather-tool',
    operation='get_forecast',
    parameters={'location': 'Tokyo', 'days': '5'}
)

forecast_response = stub.ExecuteTool(forecast_request)
print(forecast_response.result)
```

### Using the Itinerary Task Worker

```python
import grpc
import agent_platform_pb2
import agent_platform_pb2_grpc
import uuid

# Connect through MCP Router
channel = grpc.insecure_channel('localhost:50051')
stub = agent_platform_pb2_grpc.TaskWorkerStub(channel)

# Plan an itinerary
task_id = str(uuid.uuid4())
request = agent_platform_pb2.TaskRequest(
    task_id=task_id,
    agent_id='itinerary-worker',
    input='Plan a vacation',
    parameters={
        'destination': 'Paris',
        'days': '3',
        'interests': 'culture,food,history'
    }
)

response = stub.ProcessTask(request)
print(f"Success: {response.success}")
print(f"Itinerary:\n{response.output}")
```

## 🔧 Development

### Project Structure

```
agent-platform-server/
├── proto/                      # Protocol Buffer definitions
│   └── agent_platform.proto
├── mcp-router/                 # MCP Router service
│   ├── app.py
│   ├── Dockerfile
│   └── requirements.txt
├── mcp-server/                 # MCP Server (Cursor integration)
│   ├── server.py
│   ├── Dockerfile
│   └── requirements.txt
├── catalog-api/                # Catalog API backend
│   ├── app.py
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── README.md
│   └── SCALING.md
├── catalog-ui/                 # Catalog UI frontend
│   ├── src/
│   │   ├── App.jsx
│   │   └── App.css
│   ├── Dockerfile
│   ├── nginx.conf
│   ├── docker-entrypoint.sh
│   └── register_consul.py
├── agents/
│   └── echo/                   # Echo Agent
│       ├── server.py
│       ├── Dockerfile
│       └── requirements.txt
├── tools/
│   └── weather-tool/           # Weather Tool
│       ├── server.py
│       ├── Dockerfile
│       └── requirements.txt
├── tasks/
│   └── itinerary-task/         # Itinerary Worker
│       ├── worker.py
│       ├── Dockerfile
│       └── requirements.txt
├── haproxy/                    # Load balancer
│   ├── haproxy.cfg
│   └── Dockerfile
├── scripts/                    # Utility scripts
│   ├── setup.sh
│   ├── compile_proto.sh
│   └── test_client.py
├── docs/                       # Documentation
├── docker-compose.yml
├── requirements.txt
├── Makefile
└── README.md
```

### Adding a New Agent

1. **Create agent directory**
```bash
mkdir -p agents/my-agent
```

2. **Create server.py**
```python
# Implement AgentService interface from proto
class MyAgentService:
    def ExecuteTask(self, request, context):
        # Your agent logic here
        pass
```

3. **Create Dockerfile**
```dockerfile
FROM python:3.11-slim
# ... (follow pattern from echo agent)
```

4. **Add to docker-compose.yml**
```yaml
my-agent:
  build:
    context: .
    dockerfile: agents/my-agent/Dockerfile
  # ... (follow pattern from other services)
```

### Adding a New Tool

Follow the same pattern as agents, but implement the `ToolService` interface.

### Compiling Proto Files

After modifying `agent_platform.proto`:

```bash
bash scripts/compile_proto.sh
```

This generates:
- `agent_platform_pb2.py` - Message definitions
- `agent_platform_pb2_grpc.py` - Service stubs

## 🧪 Testing

### Run all tests
```bash
python scripts/test_client.py
```

### Test individual services
```bash
# Test Echo Agent
python scripts/test_client.py --service echo

# View logs
docker-compose logs echo-agent

# Check service health in Consul
open http://localhost:8500
```

## 🔍 Monitoring

### Consul UI
Access the Consul UI to monitor service health and registry:
```
http://localhost:8500
```

### HAProxy Statistics Dashboard
Monitor load balancer performance and backend health:
```
http://localhost:8404
```

### Service Logs
```bash
# All services
docker-compose logs -f

# Specific services
docker-compose logs -f mcp-router
docker-compose logs -f echo-agent
docker-compose logs -f weather-tool
docker-compose logs -f itinerary-worker
docker-compose logs -f haproxy

# Using Makefile
make logs              # All services
make router-logs       # MCP Router only
make haproxy-logs      # HAProxy only
make consul-logs       # Consul only
```

### Check Service Status
```bash
# List running services
docker-compose ps

# Check health via Consul
docker-compose exec consul consul members

# Check all services in Consul
make check-consul

# Check router instances
./scripts/manage_routers.sh status
```

## 📈 Scaling

The Agent Platform supports **horizontal scaling** of all services with automatic service discovery and load balancing. Scale up to handle increased load, improve availability, or distribute workload.

### Quick Scaling Commands

```bash
# Scale MCP Router (with HAProxy load balancing)
make scale-router N=3
./scripts/manage_routers.sh scale 3

# Scale individual services
make scale-echo N=3          # Echo Agent
make scale-weather N=5       # Weather Tool
make scale-itinerary N=2     # Itinerary Worker

# Scale all services to 3 instances
make scale-all N=3

# Scale down to 1 instance each
make scale-down

# Check all services registered in Consul
make check-consul
```

### How Scaling Works

- **Automatic Service Discovery**: Each instance registers with Consul using a unique ID
- **Load Balancing**: 
  - MCP Router: HAProxy distributes requests across router instances
  - Other Services: Consul-based service discovery for load distribution
- **Health Monitoring**: Unhealthy instances are automatically removed from rotation
- **Dynamic Ports**: Docker assigns unique host ports to avoid conflicts
- **Zero-Downtime**: Add or remove instances without service interruption

### Example: Scaling for Production

```bash
# Start services
docker-compose up -d

# Scale MCP Router for high availability
make scale-router N=3

# Scale agents and workers based on load
make scale-echo N=3
make scale-weather N=2
make scale-itinerary N=3

# Verify all instances are registered
make check-consul

# Monitor status
docker-compose ps
./scripts/manage_routers.sh status
```

### Architecture Benefits

✅ **High Availability** - Service continues if instances fail  
✅ **Load Distribution** - Requests spread across multiple instances  
✅ **Easy Scaling** - One command to scale up or down  
✅ **Auto-Discovery** - New instances join automatically  
✅ **Health Checks** - Failed instances removed automatically  

**📘 For detailed scaling information, see:**
- [SCALING_GUIDE.md](docs/SCALING_GUIDE.md) - Comprehensive scaling guide
- [LOAD_BALANCING.md](docs/LOAD_BALANCING.md) - MCP Router load balancing details
- [SCALING_DEMO.md](docs/SCALING_DEMO.md) - Live demo of scaling capabilities

## 🎯 Cursor IDE Integration

**NEW!** Use your platform's agents and tools directly in Cursor IDE via the Model Context Protocol (MCP):

```bash
# MCP Server runs automatically with the platform
make up

# Configure Cursor (Settings → MCP Servers)
{
  "mcpServers": {
    "agent-platform": {
      "url": "http://localhost:3000/sse",
      "transport": "sse"
    }
  }
}

# Then ask in Cursor: "What's the weather in Tokyo?"
```

Cursor can now:
- ✅ Call tools (weather-tool) directly from chat
- ✅ **Execute agents and workers as callable tools**
- ✅ Access agents and workers as resources
- ✅ Auto-discover all platform capabilities
- ✅ **See comprehensive metadata** (detailed descriptions, use cases, return formats)
- ✅ Use SSE transport (HTTP-based, easy to debug)
- ✅ Load balanced via HAProxy (scalable with `make scale-mcp N=3`)
- ✅ Monitored via Consul (visible at http://localhost:8500)

**Complete setup guide**: [CURSOR_INTEGRATION.md](docs/CURSOR_INTEGRATION.md)

## 🔍 Querying Available Services

Discover what agents, tools, and workers are available in your platform:

```bash
# Query all services
make mcp-query

# Query specific service types
make mcp-query-agents       # List all agents
make mcp-query-tools        # List all tools
make mcp-query-workers      # List all workers

# Get JSON output (useful for scripting)
make mcp-query-json

# Or use the script directly
python scripts/query_mcp.py all
python scripts/query_mcp.py agents --json
```

**Example output:**
```
======================================================================
AGENTS
======================================================================

📦 Echo Agent
   ID: echo-agent
   Description: Echo agent service
   Endpoint: container:50052
   Capabilities: agent, echo, text-processing

======================================================================
TOOLS
======================================================================

🛠️  Weather Tool
   ID: weather-tool
   Description: Provides weather information and forecasts
   Endpoint: container:50053
   Parameters:
      - location (string, required): City or location name
      - days (integer, optional): Number of days for forecast
```

## 🛠️ Common Commands

For a complete list of all available commands, see [MAKEFILE_REFERENCE.md](docs/MAKEFILE_REFERENCE.md).

### Essential Commands

```bash
# Service Management
make up                     # Start all services
make down                   # Stop all services
make restart                # Restart all services
make status                 # Show service status

# Service Discovery
make mcp-query              # Query all available services
make mcp-query-agents       # List agents
make mcp-query-tools        # List tools
make mcp-query-workers      # List workers

# Web Interfaces
make ui-catalog             # Open Catalog UI (service browser)
make ui-consul              # Open Consul UI
make ui-haproxy             # Open HAProxy stats

# Monitoring
make logs                   # Stream all logs
make logs-router            # View MCP Router logs
make logs-echo              # View Echo Agent logs
make logs-catalog-api       # View Catalog API logs
make logs-catalog-ui        # View Catalog UI logs

# Testing
make test                   # Run test suite

# Consul Operations
make consul-check           # Check registered services
make consul-cleanup         # Clean up stale registrations
make consul-purge           # Nuclear: delete all Consul data

# Scaling
make scale-router N=3       # Scale router to 3 instances
make scale-catalog N=3      # Scale catalog services to 3
make scale-catalog-api N=3  # Scale catalog API to 3
make scale-catalog-ui N=3   # Scale catalog UI to 3
make scale-all N=3          # Scale all services to 3
make scale-down             # Scale back to 1 instance

# Catalog Services
make catalog-build          # Build catalog services
make catalog-up             # Start catalog services
make catalog-restart        # Restart catalog services

# Development
make proto-compile          # Compile protocol buffers
make rebuild                # Full rebuild
make clean                  # Clean up everything
```

## 🧹 Consul Maintenance

Over time, Consul may accumulate stale service registrations (e.g., from container restarts during development).

### Check Service Registry

```bash
# View all registered services and their health
make consul-check
```

### Clean Up Stale Services

```bash
# Remove only unhealthy/stale registrations (safe)
make consul-cleanup

# Or use the cleanup script directly
./scripts/cleanup_consul.sh stale
```

### Complete Reset (if needed)

```bash
# WARNING: This removes ALL Consul data!
make consul-purge

# Services will automatically re-register when restarted
make restart
```

For more details, see the cleanup script: `scripts/cleanup_consul.sh`

## 🐛 Troubleshooting

### Proto compilation errors
```bash
make proto-compile
# Or manually:
pip install grpcio-tools==1.60.0
bash scripts/compile_proto.sh
```

### Service won't start
```bash
# Check logs
make logs-router            # or logs-echo, logs-weather, etc.

# Check status
make status

# Restart specific service
docker-compose restart mcp-router

# Rebuild and restart
docker-compose up -d --build [service-name]
```

### Consul connection issues
```bash
# Restart Consul
docker-compose restart consul

# Wait for Consul to be healthy
docker-compose ps consul
```

### Port conflicts
Edit `.env` file to change ports:
```bash
# Change ports if needed
MCP_ROUTER_PORT=50051
AGENT_PORT=50052
TOOL_PORT=50053
WORKER_PORT=50054
```

## 📚 API Reference

### gRPC Services

#### AgentService
- `ExecuteTask(TaskRequest) -> TaskResponse` - Execute a task
- `StreamTask(TaskRequest) -> stream TaskChunk` - Stream task execution
- `GetStatus(StatusRequest) -> StatusResponse` - Get agent status
- `RegisterAgent(AgentInfo) -> RegistrationResponse` - Register agent

#### ToolService
- `ExecuteTool(ToolRequest) -> ToolResponse` - Execute tool operation
- `ListTools(ListToolsRequest) -> ListToolsResponse` - List available tools
- `RegisterTool(ToolInfo) -> RegistrationResponse` - Register tool

#### TaskWorker
- `ProcessTask(TaskRequest) -> TaskResponse` - Process a task
- `GetTaskStatus(TaskStatusRequest) -> TaskStatusResponse` - Get task status

## 🚢 Deployment

### Docker Compose (Production)
```bash
# Start all services
docker-compose up -d

# Scale MCP Router for high availability (recommended: 3-5 instances)
docker-compose up -d --scale mcp-router=3

# Scale agents and workers based on load
docker-compose up -d --scale echo-agent=3 --scale weather-tool=2 --scale itinerary-worker=3

# Or use convenient Makefile commands
make scale-all N=3
```

### Production Deployment Recommendations

**Minimum High Availability Setup**:
```bash
make scale-router N=3      # 3 router instances
make scale-echo N=2        # 2 agent instances
make scale-weather N=2     # 2 tool instances
make scale-itinerary N=2   # 2 worker instances
```

**High-Load Setup**:
```bash
make scale-router N=5      # 5 router instances
make scale-echo N=5        # 5 agent instances
make scale-weather N=3     # 3 tool instances
make scale-itinerary N=5   # 5 worker instances
```

### Environment Variables
Create a `.env` file based on `.env.example` for configuration:
```bash
# Copy example
cp .env.example .env

# Edit as needed
vim .env
```

### Monitoring in Production
- Set up alerts on HAProxy metrics: http://localhost:8404
- Monitor Consul health checks: http://localhost:8500
- Aggregate logs with ELK stack or similar
- Use Prometheus + Grafana for metrics (see Future Enhancements)

## 🤝 Contributing

1. Create a new branch for your feature
2. Implement your changes
3. Add tests for new functionality
4. Update documentation
5. Submit a pull request

## 📝 License

This project is provided as-is for educational and development purposes.

## 🔗 Resources

### Documentation

**📚 [Complete Documentation Index](docs/)** - All documentation organized in the `docs/` folder

**Getting Started:**
- [START_HERE.md](docs/START_HERE.md) - New user welcome guide
- [QUICKSTART.md](docs/QUICKSTART.md) - 5-minute quick start

**Architecture:**
- [ARCHITECTURE.md](docs/ARCHITECTURE.md) - Overall system architecture
- [ARCHITECTURE_GRPC.md](docs/ARCHITECTURE_GRPC.md) - gRPC subsystem details
- [ARCHITECTURE_MCP.md](docs/ARCHITECTURE_MCP.md) - MCP subsystem details
- [ARCHITECTURE_OVERVIEW.md](docs/ARCHITECTURE_OVERVIEW.md) - Documentation navigation guide

**Integration:**
- [CURSOR_INTEGRATION.md](docs/CURSOR_INTEGRATION.md) - Complete Cursor IDE setup guide
- [MCP_CURSOR_SETUP.md](docs/MCP_CURSOR_SETUP.md) - Quick MCP reference

**Scaling & Operations:**
- [SCALING_GUIDE.md](docs/SCALING_GUIDE.md) - Comprehensive scaling guide
- [LOAD_BALANCING.md](docs/LOAD_BALANCING.md) - Load balancing configuration
- [SCALING_DEMO.md](docs/SCALING_DEMO.md) - Live demo of scaling

**Features & Guides:**
- [CATALOG.md](docs/CATALOG.md) - Web-based service catalog and documentation
- [HEALTH_RESILIENCE.md](docs/HEALTH_RESILIENCE.md) - **NEW:** Health-aware service consolidation
- [DEDUPLICATION_GUIDE.md](docs/DEDUPLICATION_GUIDE.md) - **NEW:** Automatic service deduplication
- [SESSION_ID_GUIDE.md](docs/SESSION_ID_GUIDE.md) - Session ID for context recovery
- [ECHO_AGENT_USAGE.md](docs/ECHO_AGENT_USAGE.md) - How to use the Echo Agent
- [MCP_SERVICE_DISCOVERY.md](docs/MCP_SERVICE_DISCOVERY.md) - Service discovery guide
- [MAKEFILE_REFERENCE.md](docs/MAKEFILE_REFERENCE.md) - All make commands
- [AGENTS_AS_TOOLS.md](docs/AGENTS_AS_TOOLS.md) - Using agents as MCP tools in Cursor

**Examples:**
- [examples/README.md](examples/README.md) - Code examples

### External Resources
- [gRPC Documentation](https://grpc.io/docs/)
- [Protocol Buffers](https://developers.google.com/protocol-buffers)
- [Consul Documentation](https://www.consul.io/docs)
- [HAProxy Documentation](http://www.haproxy.org/)
- [Docker Documentation](https://docs.docker.com/)

## 💡 Next Steps

### Extend the Platform

1. **Add Authentication** - Implement token-based auth for services
2. **Add Persistence** - Store task results in a database
3. **Add Monitoring** - Integrate Prometheus/Grafana
4. **Add Message Queue** - Use RabbitMQ or Kafka for async tasks
5. **Add API Gateway** - REST API wrapper for gRPC services
6. **Add Real AI** - Integrate OpenAI, Anthropic, or local LLMs
7. **Add More Tools** - Database tools, API clients, etc.
8. **Add Agent Orchestration** - Multi-agent collaboration

### Production Considerations

- Add TLS/SSL for secure communication
- Implement proper authentication and authorization
- Add rate limiting and request throttling
- Set up centralized logging (ELK, Loki)
- Implement distributed tracing (Jaeger, Zipkin)
- Add backup and disaster recovery
- Configure horizontal pod autoscaling
- Set up CI/CD pipelines

---

**Built with ❤️ using Python, gRPC, and Consul**