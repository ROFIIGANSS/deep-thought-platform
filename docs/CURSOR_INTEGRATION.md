# Cursor IDE Integration Guide

## Overview

The Agent Platform now supports the **Model Context Protocol (MCP)**, allowing Cursor IDE to directly access and use your agents and tools!

## What You Can Do

Once configured, Cursor can:
- 🌤️ **Call weather-tool** - Get weather information for any location
- 📦 **Access agents** - Browse and interact with echo-agent
- ⚙️ **Use workers** - Execute complex tasks through itinerary-worker
- 🔍 **Discover services** - Automatically see all available platform capabilities

## Quick Setup

### Prerequisites

1. **Start the Agent Platform**:
   ```bash
   cd agent-platform-server
   make up
   ```

2. **Install MCP dependencies** (if not already installed):
   ```bash
   source venv/bin/activate
   pip install mcp==0.9.0
   ```

### Option A: Local MCP Server with SSE (Recommended)

Run the MCP server locally using HTTP/SSE transport:

#### 1. Start the MCP Server

```bash
make mcp-server-start
```

This runs the MCP server with SSE transport on port 3000, connecting to the gRPC router.

#### 2. Configure Cursor

Add the MCP server to your Cursor settings:

**Location**: Cursor Settings → MCP Servers

**Configuration** (use the template file):
```bash
# The template is already configured for SSE
cat examples/cursor-mcp-config.json
```

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

**SSE Benefits**:
- ✅ HTTP-based (easier to debug)
- ✅ Works across networks
- ✅ No path configuration needed
- ✅ Better for remote servers

#### 3. Restart Cursor

Restart Cursor IDE to load the new MCP server.

### Option B: Local MCP Server with stdio

Run the MCP server locally using stdio transport (for direct process communication):

#### 1. Start the MCP Server

```bash
make mcp-server-start-stdio
```

#### 2. Configure Cursor for stdio

```json
{
  "mcpServers": {
    "agent-platform": {
      "command": "python",
      "args": ["mcp-server/server.py"],
      "cwd": "/absolute/path/to/agent-platform-server",
      "env": {
        "GRPC_ROUTER_HOST": "localhost",
        "GRPC_ROUTER_PORT": "50051",
        "MCP_TRANSPORT": "stdio"
      }
    }
  }
}
```

**Important**: Replace `/absolute/path/to/agent-platform-server` with your actual path!

### Option C: Docker MCP Server

Run the MCP server in Docker (for more isolation):

#### 1. Build and Start

```bash
make mcp-server-build
make mcp-server-up
```

#### 2. Configure Cursor for Docker

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

The Docker server runs with SSE transport by default.

## Usage Examples

Once configured, you can interact with your platform through Cursor's chat:

### Example 1: Check Weather

```
You: "What's the weather in Tokyo?"

Cursor: 
→ Calls weather-tool via MCP
→ Returns: "Tokyo: 72°F, Partly Cloudy, Humidity 65%"
```

### Example 2: List Available Tools

```
You: "What tools are available?"

Cursor:
→ Lists all MCP tools from the platform
→ Shows: weather-tool with parameters (location, days)
```

### Example 3: Get Weather Forecast

```
You: "Get a 5-day forecast for Paris"

Cursor:
→ Calls weather-tool with location=Paris, days=5
→ Returns detailed forecast
```

## Verification

### Check MCP Server is Running

```bash
# Check Docker container
docker ps | grep mcp-server

# Check logs
make mcp-server-logs
```

### Check Consul Registration

The MCP server registers with Consul for monitoring:

```bash
# Check all services including MCP server
make consul-check

# Or directly view in Consul UI
open http://localhost:8500/ui
# Look for "mcp-server" service with green checkmark
```

Expected output:
```
=== MCP Servers (Cursor Integration) ===
  mcp-server-<hostname> - <container-id>:3000 - passing
```

### Test gRPC Connection

```bash
# Verify backend services are accessible
make mcp-query
```

### Test SSE Endpoint

```bash
# Test the SSE endpoint directly
curl -N http://localhost:3000/sse
# Should return: event: endpoint
```

### Check Cursor Connection

In Cursor:
1. Open Settings → MCP Servers
2. Look for "agent-platform" in the list
3. Status should show "Connected" (green indicator)

## Troubleshooting

### MCP Server Won't Start

**Problem**: `ModuleNotFoundError: No module named 'mcp'`

**Solution**:
```bash
source venv/bin/activate
pip install mcp==0.9.0
```

### Connection Refused

**Problem**: MCP server can't connect to gRPC router

**Solution**:
```bash
# Check services are running
make status

# Verify port 50051 is accessible
nc -zv localhost 50051

# Restart services if needed
make restart
```

### Cursor Can't Find Tools

**Problem**: Cursor connects but doesn't show any tools

**Solution**:
1. Check MCP server logs: `make mcp-server-logs`
2. Verify services are registered: `make consul-check`
3. Test gRPC queries: `make mcp-query`
4. Restart MCP server

### Proto Import Errors

**Problem**: `ImportError: agent_platform_pb2`

**Solution**:
```bash
# Recompile proto files
make proto-compile

# Restart MCP server
```

### Permission Denied

**Problem**: Can't execute `start_mcp_server.sh`

**Solution**:
```bash
chmod +x scripts/start_mcp_server.sh
```

## Architecture

```
┌─────────────────────────────────────────┐
│         Cursor IDE                      │
│  (Chat interface, MCP client)           │
└───────────────┬─────────────────────────┘
                │
                ▼ stdio (Model Context Protocol)
┌─────────────────────────────────────────┐
│      MCP Server (mcp-server/server.py)  │
│  • Implements MCP protocol              │
│  • Exposes tools and resources          │
│  • Handles tool execution               │
└───────────────┬─────────────────────────┘
                │
                ▼ gRPC
┌─────────────────────────────────────────┐
│    HAProxy → MCP Router                 │
│  (localhost:50051)                      │
└───────────────┬─────────────────────────┘
                │
                ▼ Consul Discovery
┌─────────────────────────────────────────┐
│      Backend Services                   │
│  • echo-agent                           │
│  • weather-tool                         │
│  • itinerary-worker                     │
└─────────────────────────────────────────┘
```

## MCP Protocol Mapping

| Platform Concept | MCP Type | Description |
|-----------------|----------|-------------|
| **Tools** (weather-tool) | MCP Tools | Callable functions with parameters |
| **Agents** (echo-agent) | MCP Resources | Readable data sources |
| **Workers** (itinerary-worker) | MCP Resources | Complex task processors |

## Available Tools in Cursor

### weather-tool

**Description**: Provides weather information and forecasts

**Parameters**:
- `location` (string, required): City or location name
- `days` (integer, optional): Number of days for forecast (default: 3)

**Example**:
```
"What's the weather in London?"
"Get a 7-day forecast for San Francisco"
```

## Available Resources

### echo-agent

**URI**: `agent://echo-agent`

**Description**: Simple demonstration agent that echoes back input

**Capabilities**: agent, echo, text-processing

### itinerary-worker

**URI**: `worker://itinerary-worker`

**Description**: Plans travel itineraries

**Tags**: worker, itinerary, planning, ai

## Advanced Configuration

### Custom gRPC Host/Port

If your gRPC router is on a different host:

```json
{
  "mcpServers": {
    "agent-platform": {
      "command": "python",
      "args": ["mcp-server/server.py"],
      "env": {
        "GRPC_ROUTER_HOST": "custom-host",
        "GRPC_ROUTER_PORT": "9090"
      }
    }
  }
}
```

### Multiple Environments

Configure different MCP servers for dev/prod:

```json
{
  "mcpServers": {
    "agent-platform-dev": {
      "command": "python",
      "args": ["mcp-server/server.py"],
      "env": {
        "GRPC_ROUTER_HOST": "localhost",
        "GRPC_ROUTER_PORT": "50051"
      }
    },
    "agent-platform-prod": {
      "command": "python",
      "args": ["mcp-server/server.py"],
      "env": {
        "GRPC_ROUTER_HOST": "prod.example.com",
        "GRPC_ROUTER_PORT": "50051"
      }
    }
  }
}
```

## Useful Commands

```bash
# Start MCP server locally
make mcp-server-start

# Build MCP server Docker image
make mcp-server-build

# Start MCP server in Docker
make mcp-server-up

# View MCP server logs
make mcp-server-logs

# Query available services
make mcp-query

# Check service health
make consul-check

# Restart all services
make restart
```

## Security Considerations

### Local Development

- MCP server connects to `localhost:50051` (safe)
- No external network access required
- Data stays on your machine

### Production

For production use:
1. Use TLS/SSL for gRPC connections
2. Implement authentication in MCP server
3. Run MCP server in isolated environment
4. Use firewall rules to restrict access

## Performance

- **Latency**: ~10-50ms per tool call (local network)
- **Concurrency**: Handles multiple Cursor requests simultaneously
- **Caching**: MCP server caches tool listings (30s TTL)

## Next Steps

1. **Try it out**: Ask Cursor to check the weather
2. **Add more tools**: Follow patterns in `tools/weather-tool/`
3. **Custom agents**: Create agents for your specific needs
4. **Scale up**: Add more instances with `make scale-all N=3`

## Resources

- **MCP Specification**: https://modelcontextprotocol.io/
- **Platform Docs**: [README.md](../README.md)
- **Service Discovery**: [MCP_SERVICE_DISCOVERY.md](MCP_SERVICE_DISCOVERY.md)
- **Architecture**: [ARCHITECTURE.md](ARCHITECTURE.md)

## Support

### Check Status

```bash
make status                 # Platform services
make consul-check          # Service registry
make mcp-query            # Available capabilities
```

### Get Help

- View logs: `make logs` or `make mcp-server-logs`
- Check connectivity: `make test`
- Clean state: `make consul-cleanup`

---

**Ready to use your Agent Platform in Cursor!** 🚀

**Quick Test**: In Cursor, type: *"What's the weather in New York?"*

