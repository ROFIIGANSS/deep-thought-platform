# MCP Subsystem Architecture

## Overview

The MCP (Model Context Protocol) subsystem provides a standardized protocol bridge that enables AI IDEs like Cursor to interact with the Agent Platform. It translates between the Model Context Protocol and the platform's internal gRPC APIs.

## MCP Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                      MCP CLIENT LAYER                            │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│   Cursor IDE         Claude Desktop        Other MCP Clients    │
│   (AI Assistant)     (Anthropic)           (VS Code, etc.)      │
│         │                  │                      │             │
│         │                  │                      │             │
│         └──────────────────┼──────────────────────┘             │
│                            │                                     │
│                            │ Model Context Protocol              │
│                            │ (JSON-RPC 2.0)                      │
│                            │                                     │
│                            │ Transport Options:                  │
│                            │ - stdio (stdin/stdout)              │
│                            │ - SSE (HTTP Server-Sent Events)     │
│                            │                                     │
│                            ▼                                     │
├──────────────────────────────────────────────────────────────────┤
│                   MCP PROTOCOL LAYER                            │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│                    ┌──────────────────┐                         │
│                    │   MCP Server     │                         │
│                    │   Port: 3000     │                         │
│                    │                  │                         │
│                    │  Components:     │                         │
│                    │  - mcp.Server    │                         │
│                    │  - GrpcBridge    │                         │
│                    │  - Starlette     │                         │
│                    │    (for SSE)     │                         │
│                    │                  │                         │
│                    │  Functions:      │                         │
│                    │  - list_tools    │                         │
│                    │  - call_tool     │                         │
│                    │  - list_resources│                         │
│                    │  - read_resource │                         │
│                    └────────┬─────────┘                         │
│                             │                                    │
│                             │ Protocol Translation               │
│                             │ MCP ↔ gRPC                        │
│                             │                                    │
│                             ▼                                    │
├──────────────────────────────────────────────────────────────────┤
│                    TRANSLATION LAYER                            │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│   MCP Format                          gRPC Format               │
│   ┌─────────────────────────┐        ┌──────────────────────┐  │
│   │ Tool: weather-tool      │   →    │ ToolRequest          │  │
│   │ Args: {                 │        │   tool_id: weather   │  │
│   │   location: "Paris",    │        │   parameters: {...}  │  │
│   │   days: 3               │        │                      │  │
│   │ }                       │        │                      │  │
│   └─────────────────────────┘        └──────────────────────┘  │
│                                                                  │
│   ┌─────────────────────────┐        ┌──────────────────────┐  │
│   │ Resource: agent://echo  │   →    │ TaskRequest          │  │
│   │ Method: execute         │        │   agent_id: echo     │  │
│   └─────────────────────────┘        └──────────────────────┘  │
│                                                                  │
│                             │                                    │
│                             │ gRPC calls                         │
│                             ▼                                    │
├──────────────────────────────────────────────────────────────────┤
│                   LOAD BALANCING LAYER                          │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│                    ┌──────────────────┐                         │
│                    │     HAProxy      │                         │
│                    │  Load Balancer   │                         │
│                    │                  │                         │
│                    │  Backends:       │                         │
│                    │  - Port 50051    │                         │
│                    │    (gRPC)        │                         │
│                    │  - Port 3000     │                         │
│                    │    (MCP/SSE)     │                         │
│                    └────────┬─────────┘                         │
│                             │                                    │
│          ┌──────────────────┼──────────────────┐                │
│          │                  │                  │                │
│          ▼                  ▼                  ▼                │
│    ┌──────────┐       ┌──────────┐      ┌──────────┐          │
│    │  gRPC    │       │  gRPC    │      │  gRPC    │          │
│    │ Router 1 │       │ Router 2 │      │ Router N │          │
│    └────┬─────┘       └────┬─────┘      └────┬─────┘          │
│         │                   │                  │                │
│         │                   │                  │                │
│         └───────────────────┴──────────────────┘                │
│                             │                                    │
│                             │ Service Discovery                  │
│                             ▼                                    │
├──────────────────────────────────────────────────────────────────┤
│                   BACKEND SERVICE LAYER                         │
├──────────────────────────────────────────────────────────────────┤
│         ┌──────────────────┬──────────────────┐                 │
│         ▼                  ▼                  ▼                 │
│   ┌───────────┐      ┌───────────┐     ┌───────────┐          │
│   │  Agents   │      │   Tools   │     │  Workers  │          │
│   │ (gRPC)    │      │  (gRPC)   │     │  (gRPC)   │          │
│   └───────────┘      └───────────┘     └───────────┘          │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

## Model Context Protocol

### What is MCP?

The **Model Context Protocol** is an open standard created by Anthropic for connecting AI assistants to external data sources and tools. It provides a standardized way for AI IDEs to discover and use external capabilities.

**Official Spec**: https://modelcontextprotocol.io/

### Key Concepts

#### 1. Tools
Executable functions that the AI can call:
```json
{
  "name": "weather-tool",
  "description": "Get weather information for a location",
  "inputSchema": {
    "type": "object",
    "properties": {
      "location": {"type": "string"},
      "days": {"type": "number"}
    }
  }
}
```

#### 2. Resources
Readable data sources that provide context:
```json
{
  "uri": "agent://echo-agent",
  "name": "Echo Agent",
  "mimeType": "text/plain",
  "description": "Autonomous echo agent"
}
```

#### 3. Prompts
Pre-defined interaction templates (not currently implemented)

### Transport Mechanisms

#### stdio (Standard Input/Output)
- **Use Case**: Local development, direct process spawning
- **Protocol**: JSON-RPC over stdin/stdout
- **Configuration**: Command + args in Cursor settings
- **Pros**: Simple, no network configuration
- **Cons**: One client per server instance

#### SSE (Server-Sent Events)
- **Use Case**: Production, multi-client scenarios
- **Protocol**: JSON-RPC over HTTP with Server-Sent Events
- **Configuration**: URL in Cursor settings
- **Pros**: Multiple clients, HTTP-based, easy debugging
- **Cons**: Requires server process

## MCP Server Implementation

### Location
- **Directory**: `mcp-server/`
- **Main File**: `mcp-server/server.py`
- **Port**: 3000 (HTTP/SSE) or stdio
- **Dependencies**: `mcp>=1.0.0`, `grpcio`, `protobuf`, `starlette`

### Core Classes

#### 1. Server (MCP Protocol Handler)

```python
from mcp.server import Server
import mcp.types as types

app = Server("agent-platform")

@app.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """Discover all available tools from gRPC backend"""
    # Query gRPC router for available tools
    # Transform to MCP Tool format
    return tools

@app.call_tool()
async def handle_call_tool(
    name: str, 
    arguments: dict
) -> list[types.TextContent]:
    """Execute a tool via gRPC backend"""
    # Translate MCP call to gRPC ToolRequest
    # Execute via gRPC router
    # Return result in MCP format
    return [types.TextContent(type="text", text=result)]

@app.list_resources()
async def handle_list_resources() -> list[types.Resource]:
    """List agents and workers as resources"""
    # Query gRPC router for agents and workers
    # Transform to MCP Resource format
    return resources

@app.read_resource()
async def handle_read_resource(uri: str) -> str:
    """Read agent/worker information"""
    # Parse resource URI
    # Get info from gRPC backend
    return resource_info
```

#### 2. GrpcBridge (Protocol Translation)

```python
class GrpcBridge:
    """Bridge between MCP and gRPC protocols"""
    
    def __init__(self, grpc_host: str, grpc_port: int):
        self.router_address = f"{grpc_host}:{grpc_port}"
    
    async def list_tools(self) -> list:
        """Query gRPC backend for available tools"""
        channel = grpc.insecure_channel(self.router_address)
        stub = agent_platform_pb2_grpc.ToolServiceStub(channel)
        
        request = agent_platform_pb2.ListToolsRequest()
        response = stub.ListTools(request)
        
        # Transform gRPC response to MCP format
        return self._transform_tools(response.tools)
    
    async def call_tool(self, tool_id: str, parameters: dict) -> dict:
        """Execute tool via gRPC"""
        channel = grpc.insecure_channel(self.router_address)
        stub = agent_platform_pb2_grpc.ToolServiceStub(channel)
        
        request = agent_platform_pb2.ToolRequest(
            tool_id=tool_id,
            parameters=parameters
        )
        response = stub.ExecuteTool(request)
        
        return {
            'success': response.success,
            'result': response.output,
            'error': response.error if not response.success else None
        }
```

### Transport Implementations

#### stdio Transport

```python
async def main_stdio():
    """Run MCP server with stdio transport"""
    from mcp.server.stdio import stdio_server
    
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )
```

**Cursor Configuration** (`.cursor/mcp.json`):
```json
{
  "mcpServers": {
    "agent-platform": {
      "command": "python",
      "args": ["/path/to/mcp-server/server.py"],
      "env": {
        "GRPC_ROUTER_HOST": "localhost",
        "GRPC_ROUTER_PORT": "50051",
        "MCP_TRANSPORT": "stdio"
      }
    }
  }
}
```

#### SSE Transport (Recommended)

```python
from starlette.applications import Starlette
from starlette.routing import Route
from mcp.server.sse import SseServerTransport

async def handle_sse(request):
    """SSE endpoint for MCP protocol"""
    async with sse_server(request) as streams:
        await app.run(
            streams[0], streams[1],
            app.create_initialization_options()
        )

async def main_sse():
    """Run MCP server with SSE transport"""
    starlette_app = Starlette(
        routes=[
            Route("/sse", endpoint=handle_sse),
        ]
    )
    
    # Register with Consul
    register_with_consul(port=3000)
    
    # Run server
    import uvicorn
    uvicorn.run(starlette_app, host="0.0.0.0", port=3000)
```

**Cursor Configuration**:
```json
{
  "mcpServers": {
    "agent-platform": {
      "url": "http://localhost:3000/sse",
      "transport": "sse"
    }
  }
}
```

### Consul Registration

MCP Server instances register with Consul for monitoring:

```python
import consul
import socket

def register_with_consul(port: int):
    """Register MCP server instance with Consul"""
    consul_host = os.getenv('CONSUL_HOST', 'consul')
    consul_port = int(os.getenv('CONSUL_PORT', '8500'))
    
    hostname = socket.gethostname()
    instance_id = f"mcp-server-{hostname}"
    
    consul_client = consul.Consul(host=consul_host, port=consul_port)
    
    consul_client.agent.service.register(
        name='mcp-server',
        service_id=instance_id,
        address=hostname,
        port=port,
        tags=['mcp', 'cursor', 'http', 'sse', f'instance:{hostname}'],
        check=consul.Check.http(
            f"http://{hostname}:{port}/sse",
            interval='10s',
            timeout='5s'
        )
    )
```

## Protocol Mapping

### Platform → MCP Mapping

| Platform Concept | MCP Type | Mapping Strategy |
|-----------------|----------|------------------|
| **Tools** (weather, etc.) | MCP Tools | Direct 1:1 mapping with parameter transformation |
| **Agents** (echo, etc.) | MCP Resources | Exposed as readable/executable resources |
| **Workers** (itinerary, etc.) | MCP Resources | Exposed as task processing resources |

### Tool Mapping Example

**gRPC Tool Definition**:
```protobuf
message ToolInfo {
  string tool_id = 1;        // "weather-tool"
  string name = 2;           // "Weather Tool"
  string description = 3;     // "Get weather information"
  repeated string tags = 4;   // ["weather", "data"]
}
```

**MCP Tool Format**:
```json
{
  "name": "weather-tool",
  "description": "Get weather information for a location",
  "inputSchema": {
    "type": "object",
    "properties": {
      "location": {
        "type": "string",
        "description": "City or location name"
      },
      "days": {
        "type": "number",
        "description": "Number of days for forecast (1-7)",
        "default": 3
      }
    },
    "required": ["location"]
  }
}
```

### Resource Mapping Example

**gRPC Agent Definition**:
```protobuf
message AgentInfo {
  string agent_id = 1;         // "echo-agent"
  string name = 2;             // "Echo Agent"
  string description = 3;       // "Echoes input"
  repeated string capabilities = 4;  // ["echo", "text"]
  string endpoint = 5;          // "echo-agent:50052"
}
```

**MCP Resource Format**:
```json
{
  "uri": "agent://echo-agent",
  "name": "Echo Agent",
  "description": "Autonomous echo agent that processes text",
  "mimeType": "application/json",
  "metadata": {
    "capabilities": ["echo", "text-processing"],
    "type": "agent"
  }
}
```

## Data Flow Examples

### Example 1: Cursor Asks for Weather

```
User in Cursor: "What's the weather in Paris?"

1. Cursor IDE
   ↓ MCP tool call
   {
     "method": "tools/call",
     "params": {
       "name": "weather-tool",
       "arguments": {"location": "Paris", "days": 3}
     }
   }

2. MCP Server (port 3000)
   ↓ Translate to gRPC
   ToolRequest {
     tool_id: "weather-tool",
     parameters: {"location": "Paris", "days": "3"}
   }

3. HAProxy (port 50051)
   ↓ Load balance

4. gRPC Router
   ↓ Discover tool via Consul
   
5. Weather Tool (port 50053)
   ↓ Process request
   ToolResponse {
     output: "Paris: Sunny, 22°C, ...",
     success: true
   }

6. MCP Server
   ↓ Translate to MCP
   {
     "content": [{
       "type": "text",
       "text": "Paris: Sunny, 22°C, ..."
     }]
   }

7. Cursor IDE displays result
```

### Example 2: Cursor Lists Available Tools

```
User opens Cursor → Cursor queries capabilities

1. Cursor IDE
   ↓ MCP request
   { "method": "tools/list" }

2. MCP Server
   ↓ Query gRPC backend
   ListToolsRequest {}

3. gRPC Router
   ↓ Query Consul for services tagged 'tool'

4. Consul
   ↓ Returns: tool-weather

5. MCP Server
   ↓ Transform to MCP format
   {
     "tools": [
       {
         "name": "weather-tool",
         "description": "Get weather information",
         ...
       }
     ]
   }

6. Cursor IDE shows available tools in UI
```

## Scaling MCP Servers

### Docker Compose Scaling

```bash
# Scale to 3 instances
docker-compose up -d --scale mcp-server=3

# Or using Makefile
make scale-mcp N=3
```

### HAProxy Configuration

**Configuration** (`haproxy/haproxy.cfg`):
```haproxy
# Frontend for MCP Server (HTTP/SSE)
frontend mcp_server_frontend
    bind *:3000
    mode http
    option httplog
    default_backend mcp_server_backend

# Backend for MCP Server
backend mcp_server_backend
    mode http
    balance roundrobin
    option httpchk GET /sse
    http-check expect status 200
    
    # Dynamic backends (supports up to 5 instances)
    server mcp1 agent-platform-server-mcp-server-1:3000 check
    server mcp2 agent-platform-server-mcp-server-2:3000 check
    server mcp3 agent-platform-server-mcp-server-3:3000 check
    server mcp4 agent-platform-server-mcp-server-4:3000 check
    server mcp5 agent-platform-server-mcp-server-5:3000 check
```

### Scaling Benefits

✅ **Multiple concurrent clients**: Each Cursor instance can connect  
✅ **High availability**: Failover if one instance crashes  
✅ **Load distribution**: HAProxy balances SSE connections  
✅ **Zero downtime**: Scale up/down without interruption  

## Cursor IDE Integration

### Setup Steps

1. **Ensure platform is running**:
   ```bash
   make up
   make status
   ```

2. **Configure Cursor** (Settings → MCP Servers):
   ```json
   {
     "mcpServers": {
       "agent-platform": {
         "url": "http://localhost:3000/sse",
         "transport": "sse"
       }
     }
   }
   ```

3. **Verify connection**:
   - Open Cursor Settings
   - Check MCP Servers section
   - Status should be green (connected)

### Usage in Cursor

Once connected, you can:

**Ask about weather**:
```
User: "What's the weather in Tokyo?"
→ Cursor automatically calls weather-tool
→ Returns weather information
```

**Discover capabilities**:
```
User: "What tools do you have access to?"
→ Cursor lists: weather-tool, echo-agent, itinerary-worker
```

**Use agents**:
```
User: "Echo this message: Hello!"
→ Cursor uses echo-agent resource
→ Returns echoed message
```

## Monitoring

### Check MCP Server Status

```bash
# View logs
make mcp-server-logs

# Check in Consul
make consul-check
# Look for: === MCP Servers (Cursor Integration) ===

# Test SSE endpoint
curl -N http://localhost:3000/sse
```

### Verify Consul Registration

```bash
# Check via Consul API
curl http://localhost:8500/v1/health/service/mcp-server

# Check via Consul UI
open http://localhost:8500/ui
# Navigate to Services → mcp-server
```

### HAProxy Statistics

```bash
# Open stats dashboard
open http://localhost:8404

# Check mcp_server_backend section
# - Green = healthy
# - Red = down
```

## Troubleshooting

### Issue 1: Cursor Shows Yellow Status

**Symptom**: Yellow indicator in Cursor MCP settings

**Meaning**: Connected but not used yet

**Solution**: This is normal! Status turns green after first tool use.

### Issue 2: Connection Failed

**Symptom**: Red indicator in Cursor, "Connection failed"

**Possible Causes**:
- MCP server not running
- Wrong URL in configuration
- Port 3000 not accessible

**Solution**:
```bash
# Check if MCP server is running
docker ps | grep mcp-server

# Check logs
make mcp-server-logs

# Restart if needed
docker-compose restart mcp-server

# Verify endpoint
curl -N http://localhost:3000/sse
```

### Issue 3: Tools Not Showing

**Symptom**: Cursor connected but no tools available

**Possible Causes**:
- Backend services not running
- gRPC router not accessible
- Consul registration issues

**Solution**:
```bash
# Check backend services
make consul-check

# Verify gRPC router
make logs-router

# Test tool discovery
make mcp-query-tools
```

### Issue 4: Tool Execution Fails

**Symptom**: Tool listed but execution returns error

**Possible Causes**:
- Backend service unhealthy
- gRPC communication failure
- Parameter mismatch

**Solution**:
```bash
# Check specific service health
make consul-check

# Test tool directly via gRPC
python scripts/test_client.py weather Paris

# Check MCP server logs for errors
make mcp-server-logs
```

## Performance Considerations

### Latency

| Component | Added Latency |
|-----------|--------------|
| MCP protocol parsing | ~1-2ms |
| JSON ↔ Protobuf translation | ~1-2ms |
| SSE overhead | ~1-2ms |
| **Total MCP overhead** | **~5-10ms** |

**Total MCP path**: ~15-30ms (vs ~10-20ms for direct gRPC)

### Throughput

| Configuration | Throughput |
|--------------|------------|
| Single MCP server | ~500 req/s |
| 3 MCP servers (HA) | ~1,200 req/s |
| 5 MCP servers | ~2,000 req/s |

### Optimization Tips

1. **Use SSE over stdio**: Better for production, supports multiple clients
2. **Scale MCP servers**: `make scale-mcp N=3` for high load
3. **Enable caching**: MCP server caches tool/resource lists
4. **Monitor HAProxy**: Watch for backend bottlenecks

## Security Considerations

### Current State (Development)

⚠️ **Development Mode**:
- HTTP (not HTTPS) for SSE
- No authentication on MCP endpoint
- Localhost-only access
- Plain-text communication

### Production Recommendations

1. **HTTPS for SSE**:
   ```python
   uvicorn.run(
       app,
       host="0.0.0.0",
       port=3000,
       ssl_keyfile="key.pem",
       ssl_certfile="cert.pem"
   )
   ```

2. **Authentication**:
   - API keys for MCP clients
   - JWT tokens in request headers
   - OAuth for IDE integrations

3. **Network Security**:
   - Firewall rules (allow only known clients)
   - VPN for remote access
   - Private network for backend communication

4. **Rate Limiting**:
   ```python
   from slowapi import Limiter
   limiter = Limiter(key_func=get_remote_address)
   
   @app.route("/sse")
   @limiter.limit("100/minute")
   async def handle_sse(request):
       ...
   ```

## Related Documentation

- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Overall system architecture
- **[ARCHITECTURE_GRPC.md](ARCHITECTURE_GRPC.md)** - gRPC subsystem details
- **[CURSOR_INTEGRATION.md](CURSOR_INTEGRATION.md)** - Complete Cursor setup guide
- **[MCP_CURSOR_SETUP.md](MCP_CURSOR_SETUP.md)** - Quick reference for MCP setup

## Summary

The MCP subsystem provides:

✅ **Standard Protocol**: Implements official Model Context Protocol spec  
✅ **IDE Integration**: Native support for Cursor, Claude Desktop, etc.  
✅ **Protocol Bridge**: Seamless MCP ↔ gRPC translation  
✅ **Scalable**: Multiple instances via HAProxy  
✅ **Monitored**: Registered in Consul like other services  
✅ **Flexible**: Supports stdio and SSE transports  

**Best for**: AI IDE integrations, interactive development, human-AI collaboration

---

**MCP: Bringing AI assistants to your Agent Platform**

