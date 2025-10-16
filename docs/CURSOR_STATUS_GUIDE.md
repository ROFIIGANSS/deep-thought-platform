# Cursor MCP Connection Status Guide

## Status Indicators

### 🟢 Green - Fully Operational
- MCP server connected
- Tools successfully called
- Everything working perfectly

**Action**: Keep using! You're all set.

### 🟡 Yellow - Connected (Awaiting First Use)
- MCP server connected via SSE
- Cursor can see the server
- No tool calls made yet OR minor warning

**Action**: Make your first tool call to turn it green!

**Try this in Cursor**:
```
"What's the weather in Tokyo?"
```

### 🔴 Red - Error or Disconnected
- MCP server not running
- Connection failed
- Configuration issue

**Action**: Check troubleshooting below.

## Quick Diagnostics

### Check if MCP Server is Running

```bash
# Check process
ps aux | grep "mcp-server/server.py"

# Check port
lsof -i :3000

# Test SSE endpoint
curl -N http://localhost:3000/sse
```

### Check Backend Services

```bash
# Check all services
docker ps

# Test gRPC connection
cd agent-platform-server
make mcp-query
```

### Restart MCP Server

```bash
# Find and kill existing process
pkill -f "mcp-server/server.py"

# Start fresh
cd agent-platform-server
make mcp-server-start
```

## Common Issues

### Yellow Status Won't Turn Green

**Symptoms**: Cursor connected (yellow) but doesn't turn green after tool calls

**Solutions**:
1. Check MCP server logs for errors
2. Verify tools are listed: `make mcp-query`
3. Ensure backend services running: `docker ps`
4. Try restarting Cursor IDE
5. Restart MCP server: `make mcp-server-start`

### Can't Connect (Red Status)

**Symptoms**: Cursor shows red or "disconnected"

**Solutions**:
1. **Start MCP server** if not running:
   ```bash
   cd agent-platform-server
   make mcp-server-start
   ```

2. **Check configuration** in Cursor Settings → MCP Servers:
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

3. **Verify port 3000 is accessible**:
   ```bash
   curl -N http://localhost:3000/sse
   ```

4. **Check firewall** isn't blocking localhost:3000

5. **Restart Cursor** after configuration changes

### Tools Not Showing

**Symptoms**: Connected but no tools available in Cursor

**Solutions**:
1. Check tools exist:
   ```bash
   make mcp-query-tools
   ```

2. Verify backend services:
   ```bash
   docker ps | grep weather-tool
   ```

3. Test gRPC connection:
   ```bash
   nc -zv localhost 50051
   ```

4. Restart all services:
   ```bash
   make restart
   ```

## Testing Your Setup

### Test 1: MCP Server Accessibility

```bash
cd agent-platform-server
python test_mcp_sse.py
```

Expected output:
```
✅ SSE endpoint responding
✅ MCP server is running and accessible
```

### Test 2: Backend Services

```bash
make mcp-query
```

Expected output:
```
🛠️  Weather Tool
   ID: weather-tool
   ...
```

### Test 3: End-to-End in Cursor

In Cursor chat, try:
```
"What's the weather in San Francisco?"
```

Expected: Weather information returned, status turns green

## Architecture Diagram

```
Cursor IDE (Status Indicator)
    ↓ SSE (http://localhost:3000/sse)
MCP Server
    ↓ gRPC (localhost:50051)
HAProxy → MCP Router
    ↓ Consul Discovery
Backend Services (weather-tool, etc.)
```

## Status Change Timeline

1. **No Server**: 🔴 Red (disconnected)
2. **Start MCP Server**: 🟡 Yellow (connected, waiting)
3. **First Tool Call**: 🟢 Green (fully operational)
4. **Error Occurs**: 🟡 Yellow (warning) or 🔴 Red (failed)

## Verification Commands

```bash
# Full system check
cd agent-platform-server

# 1. Backend services
docker ps

# 2. MCP server
ps aux | grep mcp-server

# 3. Port accessibility
lsof -i :3000

# 4. SSE endpoint
curl -N http://localhost:3000/sse

# 5. Tool discovery
make mcp-query

# 6. Quick test
python test_mcp_sse.py
```

## Next Steps Based on Status

### If Yellow (Current State)
✅ Everything is working!  
➡️ Try a tool call in Cursor to turn it green

### If Red
❌ Something is wrong  
➡️ Run diagnostics above

### If Green
🎉 Perfect!  
➡️ Keep using your tools

## Getting Help

If issues persist:

1. **Check logs**:
   ```bash
   make logs
   ```

2. **Restart everything**:
   ```bash
   make restart
   pkill -f mcp-server
   make mcp-server-start
   ```

3. **Check documentation**:
   - [CURSOR_INTEGRATION.md](CURSOR_INTEGRATION.md)
   - [MCP_CURSOR_SETUP.md](MCP_CURSOR_SETUP.md)
   - [SSE_IMPLEMENTATION.md](SSE_IMPLEMENTATION.md)

---

**TL;DR**: 🟡 Yellow = Connected and ready. Just make your first tool call in Cursor!

