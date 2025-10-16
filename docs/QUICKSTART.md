# Quick Start Guide

Get the Agent Platform running in 5 minutes with full horizontal scaling capabilities!

## Step 1: One-Command Setup ⚡

```bash
# Navigate to the project directory
cd agent-platform-server

# Run the quick-start command
make quick-start
```

This will automatically:
- ✓ Create a Python virtual environment
- ✓ Install all dependencies
- ✓ Compile Protocol Buffer files
- ✓ Build Docker images
- ✓ Start all services

**OR manual setup:**

```bash
make setup          # Setup environment
make build          # Build images
make up             # Start services
```

## Step 2: Verify Services

```bash
# Check service status
make status

# Check Consul registry
make consul-check
```

You should see:
- ✓ consul (port 8500) - Service registry
- ✓ haproxy (ports 50051, 8404) - Load balancer
- ✓ mcp-router (internal) - Gateway router
- ✓ echo-agent (internal) - Demo agent
- ✓ weather-tool (internal) - Weather service
- ✓ itinerary-worker (internal) - Itinerary planner

## Step 3: Test the Platform

```bash
# Run tests (connects through MCP Router)
make test
```

Expected output:
```
============================================================
Agent Platform - Service Tests (via MCP Router)
============================================================

Connecting to MCP Router at localhost:50051

=== Testing Echo Agent through MCP Router ===
✓ Task completed: True
✓ Agent status: healthy

=== Testing Weather Tool through MCP Router ===
✓ Request completed: True
✓ Available tools: 1

=== Testing Itinerary Worker through MCP Router ===
✓ Task completed: True

✓ All tests passed!
```

## Architecture Overview

```
Client → HAProxy (50051) → MCP Router → Consul Discovery → Backend Services
```

All clients connect through the **MCP Router** on port **50051**, which handles:
- Service discovery via Consul
- Request routing to backend services
- Load balancing
- Health checking

## What's Running?

### Service Catalog (Port 8080) 📖 NEW!
Modern web interface for browsing all platform services.
- **Catalog UI**: http://localhost:8080 (or `make ui-catalog`)
- Browse agents, tools, and workers
- View parameters and examples
- See real-time service status
- Check instance counts

### HAProxy Load Balancer (Ports 50051, 3000, 8000, 8080, Stats: 8404)
Load balancer for all HTTP/gRPC services with real-time statistics.
- **Stats Dashboard**: http://localhost:8404 (or `make ui-haproxy`)
- Routes: gRPC Router (50051), MCP Server (3000), Catalog API (8000), Catalog UI (8080)
- Shows health checks and traffic distribution

### Consul UI (Port 8500)
Service registry and health monitoring.
- **UI**: http://localhost:8500 (or `make ui-consul`)
- View all registered services
- Monitor health status

### MCP Router (Port 50051)
Central routing gateway that discovers and routes to agents/tools.
- Load balanced by HAProxy
- Horizontally scalable
- **Public endpoint for all clients**

### Echo Agent
A simple agent that echoes back your input.

**Try it:**
```python
import grpc
import agent_platform_pb2
import agent_platform_pb2_grpc
import uuid

# Connect through MCP Router (NOT directly to agent!)
channel = grpc.insecure_channel('localhost:50051')
stub = agent_platform_pb2_grpc.AgentServiceStub(channel)

request = agent_platform_pb2.TaskRequest(
    task_id=str(uuid.uuid4()),
    agent_id='echo-agent',  # Router will discover and route
    input='Hello, World!'
)

response = stub.ExecuteTask(request)
print(response.output)
# Output: Echo Agent Response: Hello, World!
```

### Weather Tool
Provides weather information for cities.

**Try it:**
```python
import grpc
import agent_platform_pb2
import agent_platform_pb2_grpc

# Connect through MCP Router
channel = grpc.insecure_channel('localhost:50051')
stub = agent_platform_pb2_grpc.ToolServiceStub(channel)

request = agent_platform_pb2.ToolRequest(
    tool_id='weather-tool',
    operation='get_weather',
    parameters={'location': 'Paris'}
)

response = stub.ExecuteTool(request)
print(response.result)
# Output: Weather data in JSON format
```

### Itinerary Worker
Plans travel itineraries with AI.

**Try it:**
```python
import grpc
import agent_platform_pb2
import agent_platform_pb2_grpc
import uuid

# Connect through MCP Router
channel = grpc.insecure_channel('localhost:50051')
stub = agent_platform_pb2_grpc.TaskWorkerStub(channel)

request = agent_platform_pb2.TaskRequest(
    task_id=str(uuid.uuid4()),
    agent_id='itinerary-worker',
    input='Plan a vacation',
    parameters={
        'destination': 'Tokyo',
        'days': '3',
        'interests': 'culture,food'
    }
)

response = stub.ProcessTask(request)
print(response.output)
# Output: Complete 3-day itinerary for Tokyo
```

## Common Commands

See [MAKEFILE_REFERENCE.md](MAKEFILE_REFERENCE.md) for complete command reference.

### Service Discovery
```bash
make mcp-query              # Query all available services
make mcp-query-agents       # List agents
make mcp-query-tools        # List tools
make mcp-query-workers      # List workers
make mcp-query-json         # Output as JSON
```

### Service Management
```bash
make up                     # Start all services
make down                   # Stop all services
make restart                # Restart all services
make status                 # Show service status
```

### Monitoring
```bash
make logs                   # View all logs
make logs-router            # View MCP Router logs
make logs-echo              # View Echo Agent logs
make ui-consul              # Open Consul UI
make ui-haproxy             # Open HAProxy stats
```

### Consul Operations
```bash
make consul-check           # Check registered services
make consul-cleanup         # Clean up stale registrations
```

### Testing
```bash
make test                   # Run test suite
```

## Scaling Services

### Scale MCP Router (with HAProxy)
```bash
# Scale to 3 instances (recommended for production)
make scale-router N=3

# Check status
make consul-check

# View HAProxy stats
make ui-haproxy
```

### Scale Other Services
```bash
# Scale individual services
make scale-echo N=3
make scale-weather N=2
make scale-itinerary N=3

# Or scale all at once
make scale-all N=3

# Scale down
make scale-down

# Verify in Consul
make consul-check
```

### Monitor Scaled Services
- **HAProxy Stats**: http://localhost:8404 - See all router instances
- **Consul UI**: http://localhost:8500 - See all service instances

## Troubleshooting

### Services won't start?
```bash
# Check logs
make logs-router

# Check status
make status

# Restart services
make restart
```

### Stale Consul registrations?
```bash
# Clean up unhealthy services
make consul-cleanup

# Check registry
make consul-check
```

### Port already in use?
Check and stop conflicting services, or edit `docker-compose.yml` to change ports.

### Proto compilation errors?
```bash
make proto-compile
```

### Need to rebuild?
```bash
make rebuild
```

## Next Steps

1. **Try Scaling** - Scale services: `make scale-router N=3`
2. **Explore Monitoring** - View UIs: `make ui-consul` and `make ui-haproxy`
3. **Run Tests** - Test the platform: `make test`
4. **View Documentation** - See [MAKEFILE_REFERENCE.md](MAKEFILE_REFERENCE.md)
5. **Add Your Own Agent** - Follow the patterns in `agents/echo/`
6. **Create New Tools** - Follow the patterns in `tools/weather-tool/`
7. **Learn Scaling** - See [SCALING_GUIDE.md](SCALING_GUIDE.md)
8. **Understand Architecture** - See [ARCHITECTURE.md](ARCHITECTURE.md)

## Important Notes

⚠️ **All clients connect through the MCP Router** on port **50051**  
⚠️ **Do NOT connect directly to backend services** (they're on dynamic ports)  
✅ **Router handles service discovery** and routes to healthy instances  
✅ **Use `make` commands** for consistent operation

## Need Help?

```bash
make help                   # Show all available commands
make consul-check           # Check service health
make logs                   # View logs
make test                   # Run tests
```

**Additional Resources:**
- [README.md](../README.md) - Complete documentation
- [MAKEFILE_REFERENCE.md](MAKEFILE_REFERENCE.md) - Command reference
- [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture
- [SCALING_GUIDE.md](SCALING_GUIDE.md) - Scaling guide
- [LOAD_BALANCING.md](LOAD_BALANCING.md) - Load balancing details

---

**Ready to build scalable, distributed agent systems! 🚀**
