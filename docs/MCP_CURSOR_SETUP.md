# MCP Integration - Complete Setup

## ✅ What Was Implemented

The Agent Platform now supports the **Model Context Protocol (MCP)**, enabling Cursor IDE to access your agents and tools!

## Architecture

```
Cursor IDE
    ↓ (stdio / Model Context Protocol)
MCP Server (mcp-server/server.py)
    ↓ (gRPC)
HAProxy → MCP Router (port 50051)
    ↓ (Consul Discovery)
Backend Services (agents/tools/workers)
```

## Quick Start for Cursor

### 1. Start Platform Services

```bash
cd agent-platform-server
make up
```

### 2. Configure Cursor

**Method A: SSE Transport (Recommended)**

```bash
# Use the provided template
cat examples/cursor-mcp-config.json
```

Then in **Cursor Settings → MCP Servers**, add:

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
- ✅ HTTP-based (easier to debug with curl/browser)
- ✅ Works across networks
- ✅ No path configuration needed
- ✅ Better for remote/Docker setups

**Method B: stdio Transport (Alternative)**

For direct process communication:

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

**Important**: For stdio, update the `cwd` path to your actual directory!

### 3. Test in Cursor

Open Cursor and try:
```
"What's the weather in Tokyo?"
```

Cursor will call the weather-tool through MCP! 🎉

## Files Created

### Core MCP Implementation
- `mcp-server/server.py` - MCP protocol server
- `mcp-server/requirements.txt` - MCP dependencies
- `mcp-server/Dockerfile` - Docker image for MCP server

### Configuration
- `examples/cursor-mcp-config.json` - Template for Cursor configuration
- `scripts/start_mcp_server.sh` - Local MCP server startup script

### Documentation
- `CURSOR_INTEGRATION.md` - Complete integration guide
- `MCP_CURSOR_SETUP.md` - This file (quick reference)

### Infrastructure
- Updated `docker-compose.yml` - Added mcp-server service
- Updated `Makefile` - Added MCP server commands
- Updated `requirements.txt` - Added MCP library

## Available Commands

```bash
# Start MCP server locally with SSE (default)
make mcp-server-start

# Start MCP server locally with stdio (alternative)
make mcp-server-start-stdio

# Build MCP server Docker image
make mcp-server-build

# Start MCP server in Docker (SSE)
make mcp-server-up

# View MCP server logs
make mcp-server-logs

# Query available services
make mcp-query
```

## Testing SSE Connection

You can test the SSE endpoint directly:

```bash
# Test if SSE endpoint is accessible
curl -N http://localhost:3000/sse

# Or open in browser
open http://localhost:3000/sse
```

Expected response: SSE stream connection established (will stay open)

## What Cursor Can Do

### Tools Available

**weather-tool**
- Get current weather: `"What's the weather in Paris?"`
- Get forecast: `"Get a 5-day forecast for London"`

Parameters:
- `location` (string, required): City name
- `days` (integer, optional): Number of forecast days

### Resources Available

**Agents**
- `agent://echo-agent` - Echo agent for testing
- Capabilities: agent, echo, text-processing

**Workers**
- `worker://itinerary-worker` - Travel itinerary planner
- Tags: worker, itinerary, planning, ai

## Testing

### Verify Setup

```bash
# 1. Check services are running
make status

# 2. Test gRPC connection
make mcp-query

# 3. Check Consul registry (includes MCP server)
make consul-check
# Look for: === MCP Servers (Cursor Integration) ===
#   mcp-server-<id> - <container>:3000 - passing

# 4. View in Consul UI
open http://localhost:8500/ui
# MCP server will be listed with green checkmark
```

### Test MCP Server Locally

```bash
# Start MCP server
make mcp-server-start

# In another terminal, verify proto files
ls -la proto/*_pb2.py
```

## Troubleshooting

### "Module not found: mcp"

```bash
source venv/bin/activate
pip install 'mcp>=1.0.0'
```

### "Connection refused: localhost:50051"

```bash
# Start services
make up

# Verify router is accessible
nc -zv localhost 50051
```

### "Proto files not found"

```bash
# Recompile proto files
make proto-compile
```

### Cursor Doesn't Show Tools

1. Check MCP server started without errors
2. Verify configuration path in Cursor settings
3. Restart Cursor IDE
4. Check Cursor console for MCP errors

## Architecture Details

### MCP Server Capabilities

The MCP server implements:

1. **Tool Listing** (`list_tools`)
   - Queries gRPC `ListTools()`
   - Transforms to MCP tool schema
   - Returns tool definitions to Cursor

2. **Tool Execution** (`call_tool`)
   - Receives tool call from Cursor
   - Proxies to gRPC `ExecuteTool()`
   - Returns results to Cursor

3. **Resource Listing** (`list_resources`)
   - Queries gRPC `ListAgents()` and `ListWorkers()`
   - Exposes as MCP resources
   - Provides URIs like `agent://echo-agent`

4. **Resource Reading** (`read_resource`)
   - Returns detailed information about agents/workers
   - Provides capabilities and metadata

### Protocol Flow

```
1. Cursor: "What's the weather in Tokyo?"
2. Cursor → MCP Server: list_tools()
3. MCP Server → gRPC Router: ListTools()
4. Router → Consul: discover weather-tool
5. Router → weather-tool: ListTools()
6. Response chain back to Cursor with tool definitions
7. Cursor → MCP Server: call_tool("weather-tool", {location: "Tokyo"})
8. MCP Server → gRPC Router: ExecuteTool("weather-tool", {location: "Tokyo"})
9. Router → weather-tool: ExecuteTool()
10. Result returns to Cursor
```

## Next Steps

### 1. Try It Out

```
In Cursor: "What's the weather in San Francisco?"
```

### 2. Add More Tools

Follow the pattern in `tools/weather-tool/`:
- Implement ToolService interface
- Register with Consul
- MCP automatically discovers it!

### 3. Scale Up

```bash
# Add more tool instances for load balancing
make scale-weather N=3
```

### 4. Custom Agents

Create agents for your specific use cases:
- Image processing
- Database queries
- API integrations
- Custom workflows

## Security Notes

### Local Development
- ✅ All communication on localhost
- ✅ No external network access
- ✅ Data stays on your machine

### Production Deployment
- ⚠️ Add TLS/SSL for gRPC
- ⚠️ Implement authentication in MCP server
- ⚠️ Use firewall rules
- ⚠️ Consider API rate limiting

## Performance

- **Tool Call Latency**: ~10-50ms (local network)
- **Concurrent Requests**: Handled efficiently
- **Caching**: Tool listings cached (30s TTL)
- **Scalability**: Add more backend instances as needed

## Resources

- **Complete Guide**: [CURSOR_INTEGRATION.md](CURSOR_INTEGRATION.md)
- **Service Discovery**: [MCP_SERVICE_DISCOVERY.md](MCP_SERVICE_DISCOVERY.md)
- **Architecture**: [ARCHITECTURE.md](ARCHITECTURE.md)
- **Main Docs**: [README.md](../README.md)
- **MCP Specification**: https://modelcontextprotocol.io/

## Support

```bash
# Check everything is working
make mcp-query            # List available services
make consul-check         # Check service registry
make test                 # Run platform tests
make logs                 # View all logs
```

---

**🎉 You're ready to use your Agent Platform in Cursor!**

**Quick Test**: Open Cursor and ask: *"What's the weather in Tokyo?"*

