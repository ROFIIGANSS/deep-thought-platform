# Examples

This directory contains example clients, configuration templates, and usage patterns for the Agent Platform.

## Files in This Directory

- **`simple_client.py`** - Comprehensive Python gRPC client example
- **`cursor-mcp-config.json`** - Cursor IDE MCP configuration template
- **`README.md`** - This file

## Important: Connect Through MCP Router

⚠️ **All clients should connect through the MCP Router** on port **50051**.  
✅ The router handles service discovery and routes requests to backend services.  
❌ Do NOT connect directly to backend service ports (they use dynamic ports).

## Cursor IDE Integration

### Using the MCP Configuration Template

The `cursor-mcp-config.json` file provides a ready-to-use configuration for connecting Cursor IDE to the Agent Platform via the Model Context Protocol (MCP).

**To use it:**

1. Make sure the platform is running:
   ```bash
   make up
   ```

2. Copy the configuration to your Cursor settings:
   ```bash
   # View the template
   cat examples/cursor-mcp-config.json
   
   # Add to Cursor Settings → MCP Servers
   ```

3. The configuration uses SSE transport and connects to the MCP server via HAProxy:
   ```json
   {
     "mcpServers": {
       "agent-platform": {
         "url": "http://localhost:3000/sse",
         "transport": "sse",
         "description": "Agent Platform via HAProxy load balancer"
       }
     }
   }
   ```

4. Once configured, ask Cursor: **"What's the weather in Tokyo?"**

**For complete setup instructions**, see:
- [CURSOR_INTEGRATION.md](../docs/CURSOR_INTEGRATION.md) - Complete integration guide
- [MCP_CURSOR_SETUP.md](../docs/MCP_CURSOR_SETUP.md) - Quick reference

## Running Examples

### Simple Client Example

A comprehensive example showing all platform capabilities:

```bash
# Make sure services are running
make up

# Activate virtual environment
source venv/bin/activate

# Run the example
python examples/simple_client.py
```

This example demonstrates:
1. **Echo Agent** - Basic task execution
2. **Weather Tool** - Using external tools
3. **Itinerary Worker** - Complex task processing
4. **Streaming** - Real-time response streaming

## Example Output

```
====================================================
Agent Platform - Example Client
====================================================

Example 1: Echo Agent
📤 Sending task to Echo Agent...
   Task ID: abc-123
   Input: Hello from the Agent Platform!

📥 Received response:
   Success: True
   Output: Echo Agent Response: Hello from the Agent Platform!
   ...

Example 2: Weather Tool
🌤️  Getting weather for New York...
   Location: New York
   Temperature: 72°F
   Condition: Partly Cloudy
   ...

Example 3: Itinerary Task Worker
✈️  Planning a 3-day trip to Paris...
   Destination: Paris
   Duration: 3 days
   📅 Daily Schedule:
   Day 1 (2025-10-14):
      🌅 Morning: Eiffel Tower
      ☀️  Afternoon: Louvre Museum
      🌙 Evening: Dinner at Le Jules Verne
   ...

✓ All examples completed successfully!
```

## Creating Your Own Examples

### Basic Pattern (Through MCP Router)

```python
import grpc
import agent_platform_pb2
import agent_platform_pb2_grpc
import uuid

# 1. Connect to MCP Router (NOT directly to services!)
channel = grpc.insecure_channel('localhost:50051')

# 2. Create appropriate stub based on what you're accessing
stub = agent_platform_pb2_grpc.AgentServiceStub(channel)
# OR
stub = agent_platform_pb2_grpc.ToolServiceStub(channel)
# OR
stub = agent_platform_pb2_grpc.TaskWorkerStub(channel)

# 3. Create request
request = agent_platform_pb2.TaskRequest(
    task_id=str(uuid.uuid4()),
    agent_id='echo-agent',  # Router will discover this
    input='Your input',
    parameters={'key': 'value'}
)

# 4. Call service (router handles discovery and routing)
response = stub.ExecuteTask(request)

# 5. Process response
print(f"Success: {response.success}")
print(f"Output: {response.output}")

# 6. Close connection
channel.close()
```

### Architecture Flow

```
Your Client
     ↓
MCP Router (localhost:50051)
     ↓
Consul Service Discovery
     ↓
Backend Service (echo-agent, weather-tool, etc.)
     ↓
Response back through Router
     ↓
Your Client
```

### Available Service Types

All accessed through **MCP Router on port 50051**:

| Service Type | Stub | Agent/Tool ID | Methods |
|-------------|------|---------------|---------|
| Echo Agent | `AgentServiceStub` | `echo-agent` | ExecuteTask, StreamTask, GetStatus |
| Weather Tool | `ToolServiceStub` | `weather-tool` | ExecuteTool, ListTools |
| Itinerary Worker | `TaskWorkerStub` | `itinerary-worker` | ProcessTask, GetTaskStatus |

### Example: Echo Agent

```python
import grpc
import agent_platform_pb2
import agent_platform_pb2_grpc
import uuid

# Connect through MCP Router
channel = grpc.insecure_channel('localhost:50051')
stub = agent_platform_pb2_grpc.AgentServiceStub(channel)

# Execute task
request = agent_platform_pb2.TaskRequest(
    task_id=str(uuid.uuid4()),
    agent_id='echo-agent',
    input='Hello!'
)
response = stub.ExecuteTask(request)
print(response.output)

channel.close()
```

### Example: Weather Tool

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
    parameters={'location': 'Tokyo'}
)
response = stub.ExecuteTool(request)
print(response.result)

channel.close()
```

### Example: Itinerary Worker

```python
import grpc
import agent_platform_pb2
import agent_platform_pb2_grpc
import uuid

# Connect through MCP Router
channel = grpc.insecure_channel('localhost:50051')
stub = agent_platform_pb2_grpc.TaskWorkerStub(channel)

# Plan itinerary
request = agent_platform_pb2.TaskRequest(
    task_id=str(uuid.uuid4()),
    agent_id='itinerary-worker',
    input='Plan a trip',
    parameters={
        'destination': 'Paris',
        'days': '3'
    }
)
response = stub.ProcessTask(request)
print(response.output)

channel.close()
```

## Testing Your Examples

```bash
# Run official test suite
make test

# View service health
make consul-check

# Check router logs
make logs-router
```

## Scaling and Load Balancing

The platform supports horizontal scaling! Try scaling services while running examples:

```bash
# Scale MCP Router (load balanced by HAProxy)
make scale-router N=3

# Scale backend services
make scale-echo N=3
make scale-weather N=2

# Monitor in HAProxy dashboard
make ui-haproxy

# Monitor in Consul
make ui-consul

# Check service registry
make consul-check
```

Your client code doesn't change! The router automatically discovers and routes to healthy instances.

## Benefits of the Router Architecture

1. **Service Discovery** - No need to know backend addresses
2. **Load Balancing** - Automatic distribution across instances
3. **Health Checking** - Only routes to healthy services
4. **Scalability** - Add/remove instances without client changes
5. **Failover** - Automatic routing around failed instances

## More Examples

Check the test client for additional examples:
```bash
# Comprehensive test suite
python scripts/test_client.py

# View test source code
cat scripts/test_client.py
```

## Need Help?

- **Quick Start**: [QUICKSTART.md](../docs/QUICKSTART.md)
- **Architecture**: [ARCHITECTURE.md](../docs/ARCHITECTURE.md)
- **Complete Docs**: [README.md](../README.md)
- **Makefile Commands**: [MAKEFILE_REFERENCE.md](../docs/MAKEFILE_REFERENCE.md)
- **Scaling Guide**: [SCALING_GUIDE.md](../docs/SCALING_GUIDE.md)
- **Load Balancing**: [LOAD_BALANCING.md](../docs/LOAD_BALANCING.md)

## Common Issues

### Connection Refused
- Make sure services are running: `make status`
- Verify router is healthy: `make consul-check`
- Check router logs: `make logs-router`

### Service Not Found
- Check Consul registry: `make consul-check`
- Clean up stale registrations: `make consul-cleanup`
- Restart services: `make restart`

### All Commands

```bash
make help                   # Show all available commands
```

---

**Remember**: Always connect to **localhost:50051** (MCP Router), not directly to backend services!
