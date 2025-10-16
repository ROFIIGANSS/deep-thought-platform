# Agents and Workers as MCP Tools

## Overview

Agents and workers are now exposed as **callable MCP tools** in Cursor, not just read-only resources. This allows you to execute agent tasks directly from Cursor conversations.

## Changes Made

### Modified File: `mcp-server/server.py`

**What Changed:**

1. **`handle_list_tools()`** - Now exposes agents and workers as callable tools
   - Agents appear with their `agent_id` as the tool name
   - Workers appear with their `worker_id` as the tool name
   - Backend tools (like weather-tool) are still included
   - **Tools now include comprehensive metadata** from the service definitions:
     - Detailed description
     - How it works
     - Return format
     - Use cases
     - Version information

2. **`handle_call_tool()`** - Routes tool calls to the appropriate handler
   - Checks if tool name matches an agent → calls `execute_agent()`
   - Checks if tool name matches a worker → calls `execute_worker()`
   - Otherwise treats as backend tool

3. **New Functions:**
   - `execute_agent(agent_id, arguments)` - Executes agent tasks via gRPC
   - `execute_worker(worker_id, arguments)` - Executes worker tasks via gRPC

## How to Use in Cursor

### 1. Restart MCP Server

After making these changes, restart the MCP server:

```bash
cd agent-platform-server
docker-compose restart mcp-server
```

Or if using local mode:
```bash
# Stop existing server (Ctrl+C)
source venv/bin/activate
python mcp-server/server.py
```

### 2. Restart Cursor

Restart Cursor to pick up the new tool definitions.

### 3. Test Agent Execution

In Cursor, you can now use natural language to call agents:

```
"Use echo-agent to say Hello World"
"Call echo-agent with the input: Testing the platform"
"Execute echo-agent with message 'test' and parameters mode=debug"
```

### 4. Tool Schema

Each agent/worker is exposed as a tool with this schema, including comprehensive metadata:

```json
{
  "name": "echo-agent",
  "description": "The Echo Agent is a demonstration agent that showcases the agent platform's capabilities...\n\n**How it works:**\nThe Echo Agent processes tasks through these steps:\n1. Receives a task request...\n\n**Return format:**\nReturns a TaskResponse containing:\n- task_id: Unique identifier for the task...\n\n**Use cases:**\n- Testing platform connectivity and functionality\n- Learning how to interact with agents\n- Debugging agent communication issues\n- Benchmarking agent response times\n- Demonstrating streaming vs batch responses\n- Building example integrations and tutorials\n\n**Version:** 1.0.0",
  "inputSchema": {
    "type": "object",
    "properties": {
      "input": {
        "type": "string",
        "description": "Input text or message for the agent to process"
      },
      "parameters": {
        "type": "object",
        "description": "Optional parameters for the agent",
        "additionalProperties": {"type": "string"}
      }
    },
    "required": ["input"]
  }
}
```

**Note:** The description now includes rich metadata that helps Cursor's AI understand exactly what each tool does, how it works, what it returns, and when to use it. This provides better context for automatic tool selection and usage.

## Example Usage

### Simple Echo Agent Call

**Cursor Prompt:**
```
Use echo-agent to echo: "Hello from Cursor!"
```

**What Happens:**
1. Cursor calls the `echo-agent` tool with `{"input": "Hello from Cursor!"}`
2. MCP server routes to `execute_agent()`
3. Creates gRPC `TaskRequest` with unique task ID
4. Sends to router → routes to echo-agent container
5. Returns response: `"Echo Agent Response: Hello from Cursor!"`

### With Custom Parameters

**Cursor Prompt:**
```
Call echo-agent with input "test message" and parameters user=admin, mode=debug
```

**Tool Call:**
```json
{
  "input": "test message",
  "parameters": {
    "user": "admin",
    "mode": "debug"
  }
}
```

**Response:**
```
Echo Agent Response: test message | Parameters: user=admin, mode=debug

**Metadata**: agent_id=echo-agent, processed_at=1697318776.123, task_number=42
```

### Itinerary Worker Call

**Cursor Prompt:**
```
Use itinerary-worker to plan a trip to Paris
```

**What Happens:**
1. Calls `itinerary-worker` tool with `{"input": "plan a trip to Paris"}`
2. Routes to `execute_worker()`
3. Worker processes the request
4. Returns itinerary results

## Available Tools

After restart, Cursor will see these tools:

| Tool Name | Type | Description |
|-----------|------|-------------|
| `echo-agent` | Agent | Echo agent service |
| `itinerary-worker` | Worker | Itinerary task worker |
| `weather-tool` | Backend Tool | Weather information |

## Technical Details

### Agent Execution Flow

```
Cursor/Claude
    ↓ (MCP call_tool)
MCP Server → handle_call_tool()
    ↓ (check if agent)
execute_agent(agent_id, arguments)
    ↓ (create TaskRequest)
gRPC → localhost:50051 (HAProxy)
    ↓
MCP Router
    ↓ (Consul discovery)
Agent Container
    ↓
TaskResponse
    ↓
MCP TextContent → Cursor
```

### Request Format

```python
TaskRequest(
    task_id=uuid.uuid4(),      # Auto-generated
    agent_id="echo-agent",     # From tool name
    input=arguments["input"],  # Required
    parameters=arguments.get("parameters", {})  # Optional
)
```

### Response Format

```python
TaskResponse(
    task_id="...",
    output="Echo Agent Response: ...",
    success=True,
    error="",
    metadata={
        "agent_id": "echo-agent",
        "processed_at": "1697318776.123",
        "task_number": "42"
    }
)
```

## Backwards Compatibility

**Resources are still available:**
- Agents and workers remain exposed as resources
- You can still query `agent://echo-agent` for information
- Tools are added functionality, not a replacement

**No changes required for:**
- Python/gRPC clients
- Direct agent connections
- Existing tools

## Testing

### 1. Check Tools List

In Cursor, ask:
```
"What tools are available?"
"List all tools"
```

You should see:
- echo-agent
- itinerary-worker
- weather-tool
- (any other registered agents/workers)

### 2. Test Echo Agent

```
"Use echo-agent to test the connection"
```

Expected response:
```
Echo Agent Response: test the connection

**Metadata**: agent_id=echo-agent, processed_at=..., task_number=...
```

### 3. Verify with Python

```bash
cd agent-platform-server
source venv/bin/activate
python scripts/test_client.py
```

Should work as before - no changes to gRPC interface.

## Troubleshooting

### Tool Not Found

**Error:** "Tool 'echo-agent' not found"

**Fix:**
1. Check agent is running: `docker ps | grep echo`
2. Check Consul registration: `make consul-check`
3. Restart MCP server: `docker-compose restart mcp-server`
4. Restart Cursor

### Agent Execution Fails

**Error:** "Error executing agent: ..."

**Debug:**
```bash
# Check logs
docker logs agent-platform-server-mcp-server-1

# Check agent logs
docker logs agent-platform-server-echo-agent-1

# Test direct connection
python scripts/test_client.py
```

### Connection Refused

**Error:** "Error executing agent: failed to connect to all addresses"

**Fix:**
1. Verify services are running: `docker-compose ps`
2. Check HAProxy: `docker logs agent-platform-server-haproxy-1`
3. Verify port mappings: `docker-compose ps`

### Parameters Not Working

**Issue:** Parameters not showing in response

**Check:**
- Parameters should be passed as object: `{"user": "admin"}`
- Parameters are converted to strings
- Agent must support parameters (echo-agent does)

## Benefits

### Before (Resources Only)
- ✅ View agent information
- ❌ Cannot execute from Cursor
- ❌ Need Python script
- ❌ Limited context for AI

### After (Tools + Resources)
- ✅ View agent information
- ✅ **Execute from Cursor directly**
- ✅ Natural language interface
- ✅ Still supports Python scripts
- ✅ **Rich metadata for better AI understanding**
- ✅ **Context-aware tool selection**
- ✅ **Comprehensive documentation in tool descriptions**

### Detailed Descriptions Advantage

The new comprehensive metadata in tool descriptions provides:

1. **Better Context**: Cursor's AI understands what each tool does in depth
2. **Appropriate Usage**: Use cases help the AI decide when to use each tool
3. **Expected Results**: Return format information sets proper expectations
4. **Transparency**: Users can see exactly how tools work
5. **Self-Documentation**: Tools carry their own documentation

## Summary

| Feature | Status | Notes |
|---------|--------|-------|
| Agents as Tools | ✅ Implemented | Callable from Cursor |
| Workers as Tools | ✅ Implemented | Callable from Cursor |
| Backend Tools | ✅ Maintained | weather-tool still works |
| Resources | ✅ Maintained | Backwards compatible |
| Python/gRPC | ✅ Unchanged | Existing clients work |
| Metadata | ✅ Included | Returned in response |
| Error Handling | ✅ Implemented | Proper error messages |
| **Rich Descriptions** | ✅ **Implemented** | **Comprehensive tool metadata** |
| **Context Awareness** | ✅ **Enhanced** | **AI understands tool usage better** |

**Next Steps:**
1. Restart MCP server
2. Restart Cursor
3. Try: `"Use echo-agent to say hello"`
4. Enjoy direct agent execution! 🎉


