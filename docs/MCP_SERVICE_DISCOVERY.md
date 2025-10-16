# MCP Service Discovery

## Overview

The Agent Platform now includes comprehensive service discovery capabilities that allow you to query available agents, tools, and workers through the MCP Router.

## Features

- **Query All Services**: Get a complete list of agents, tools, and workers
- **Filtered Queries**: Query specific service types
- **Multiple Output Formats**: Human-readable or JSON output
- **Real-time Discovery**: Queries Consul registry for current service status
- **CLI Tool**: Easy-to-use command-line interface

## Quick Start

### Query All Services

```bash
make mcp-query
```

Output:
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

======================================================================
WORKERS
======================================================================

⚙️  Itinerary Worker
   ID: itinerary-worker
   Description: Itinerary task worker
   Endpoint: container:50054
   Tags: worker, itinerary, planning, ai
```

### Query Specific Service Types

```bash
# Query only agents
make mcp-query-agents

# Query only tools
make mcp-query-tools

# Query only workers
make mcp-query-workers
```

### JSON Output

Perfect for scripting and automation:

```bash
make mcp-query-json
```

Output:
```json
{
  "agents": [
    {
      "agent_id": "echo-agent",
      "name": "Echo Agent",
      "description": "Echo agent service",
      "capabilities": ["agent", "echo", "text-processing"],
      "endpoint": "container:50052"
    }
  ],
  "tools": [
    {
      "tool_id": "weather-tool",
      "name": "Weather Tool",
      "description": "Provides weather information and forecasts",
      "endpoint": "container:50053",
      "parameters": [...]
    }
  ],
  "workers": [...]
}
```

## CLI Tool

The `scripts/query_mcp.py` tool provides flexible querying options:

### Basic Usage

```bash
python scripts/query_mcp.py all        # Query everything
python scripts/query_mcp.py agents     # Query agents only
python scripts/query_mcp.py tools      # Query tools only
python scripts/query_mcp.py workers    # Query workers only
```

### Advanced Options

```bash
# Custom host and port
python scripts/query_mcp.py all --host localhost --port 50051

# JSON output
python scripts/query_mcp.py all --json

# Help
python scripts/query_mcp.py --help
```

## API Reference

### ListAgents

Query available agents through the MCP Router.

**Endpoint**: AgentService.ListAgents  
**Request**: `ListAgentsRequest { filter?: string }`  
**Response**: `ListAgentsResponse { agents: AgentInfo[] }`

**Example (Python)**:
```python
import grpc
import agent_platform_pb2
import agent_platform_pb2_grpc

channel = grpc.insecure_channel('localhost:50051')
stub = agent_platform_pb2_grpc.AgentServiceStub(channel)

request = agent_platform_pb2.ListAgentsRequest()
response = stub.ListAgents(request)

for agent in response.agents:
    print(f"Agent: {agent.name}")
    print(f"  ID: {agent.agent_id}")
    print(f"  Capabilities: {agent.capabilities}")
    print(f"  Endpoint: {agent.endpoint}")
```

### ListTools

Query available tools through the MCP Router.

**Endpoint**: ToolService.ListTools  
**Request**: `ListToolsRequest { filter?: string }`  
**Response**: `ListToolsResponse { tools: ToolInfo[] }`

**Example (Python)**:
```python
import grpc
import agent_platform_pb2
import agent_platform_pb2_grpc

channel = grpc.insecure_channel('localhost:50051')
stub = agent_platform_pb2_grpc.ToolServiceStub(channel)

request = agent_platform_pb2.ListToolsRequest()
response = stub.ListTools(request)

for tool in response.tools:
    print(f"Tool: {tool.name}")
    print(f"  ID: {tool.tool_id}")
    print(f"  Description: {tool.description}")
    for param in tool.parameters:
        print(f"  - {param.name}: {param.type} ({param.description})")
```

### ListWorkers

Query available task workers through the MCP Router.

**Endpoint**: TaskWorker.ListWorkers  
**Request**: `ListWorkersRequest { filter?: string }`  
**Response**: `ListWorkersResponse { workers: WorkerInfo[] }`

**Example (Python)**:
```python
import grpc
import agent_platform_pb2
import agent_platform_pb2_grpc

channel = grpc.insecure_channel('localhost:50051')
stub = agent_platform_pb2_grpc.TaskWorkerStub(channel)

request = agent_platform_pb2.ListWorkersRequest()
response = stub.ListWorkers(request)

for worker in response.workers:
    print(f"Worker: {worker.name}")
    print(f"  ID: {worker.worker_id}")
    print(f"  Tags: {worker.tags}")
    print(f"  Endpoint: {worker.endpoint}")
```

## Use Cases

### 1. Dynamic Service Discovery

Build clients that automatically discover available services:

```python
def get_available_agents():
    channel = grpc.insecure_channel('localhost:50051')
    stub = agent_platform_pb2_grpc.AgentServiceStub(channel)
    
    request = agent_platform_pb2.ListAgentsRequest()
    response = stub.ListAgents(request)
    
    return [agent.agent_id for agent in response.agents]

# Use in your application
available_agents = get_available_agents()
print(f"Found {len(available_agents)} agents: {available_agents}")
```

### 2. Service Health Monitoring

Check what services are currently available:

```bash
# Run periodically to monitor service availability
make mcp-query-json | jq '.agents | length'
```

### 3. Documentation Generation

Generate documentation from live service discovery:

```bash
python scripts/query_mcp.py all --json > services.json
# Process services.json to generate docs
```

### 4. Integration Testing

Verify services are registered before running tests:

```python
def wait_for_services():
    """Wait until all expected services are registered"""
    expected = {'echo-agent', 'weather-tool', 'itinerary-worker'}
    
    for i in range(30):  # Wait up to 30 seconds
        agents = get_available_agents()
        # ... check tools and workers too
        if all services found:
            return True
        time.sleep(1)
    
    raise TimeoutError("Services not available")
```

## Architecture

```
┌──────────────────────────┐
│   Query Tool / Client    │
│   (scripts/query_mcp.py) │
└────────────┬─────────────┘
             │
             ▼ (Port 50051)
┌──────────────────────────┐
│      MCP Router          │
│  - ListAgents()          │
│  - ListTools()           │
│  - ListWorkers()         │
└────────────┬─────────────┘
             │
             ▼
┌──────────────────────────┐
│   Consul Service         │
│   Registry               │
│  - agent-echo            │
│  - tool-weather          │
│  - worker-itinerary      │
└──────────────────────────┘
```

## Implementation Details

### Protocol Buffers

New messages added to `agent_platform.proto`:

```protobuf
message ListAgentsRequest {
  string filter = 1;  // Optional filter by tag/capability
}

message ListAgentsResponse {
  repeated AgentInfo agents = 1;
}

message ListWorkersRequest {
  string filter = 1;  // Optional filter by tag
}

message ListWorkersResponse {
  repeated WorkerInfo workers = 1;
}

message WorkerInfo {
  string worker_id = 1;
  string name = 2;
  string description = 3;
  string endpoint = 4;
  repeated string tags = 5;
}
```

### Service Name Transformation

The router automatically transforms between client IDs and Consul service names:

| Client Request | Consul Service |
|----------------|----------------|
| `echo-agent` | `agent-echo` |
| `weather-tool` | `tool-weather` |
| `itinerary-worker` | `worker-itinerary` |

## Troubleshooting

### No Services Found

**Problem**: Query returns empty results

**Solutions**:
1. Check services are running: `make status`
2. Check Consul registry: `make consul-check`
3. Clean stale registrations: `make consul-cleanup`
4. Restart services: `make restart`

### Connection Refused

**Problem**: Cannot connect to MCP Router

**Solutions**:
1. Verify router is running: `make logs-router`
2. Check port 50051 is accessible: `lsof -i :50051`
3. Restart router: `docker-compose restart mcp-router`

### Incomplete Results

**Problem**: Not all services appear in query results

**Solutions**:
1. Check Consul for service health: `make consul-check`
2. View service logs for registration errors
3. Ensure services have proper tags ('agent', 'tool', 'worker')

## Makefile Commands

```bash
make mcp-query              # Query all services
make mcp-query-agents       # Query agents only
make mcp-query-tools        # Query tools only
make mcp-query-workers      # Query workers only
make mcp-query-json         # JSON output
```

## Related Documentation

- [README.md](../README.md) - Main documentation
- [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture
- [MAKEFILE_REFERENCE.md](MAKEFILE_REFERENCE.md) - Complete command reference
- [proto/agent_platform.proto](proto/agent_platform.proto) - Protocol definitions

---

**Version**: 1.0  
**Date**: October 14, 2025  
**Status**: ✅ Production Ready

