# Echo Agent Usage Guide

## Overview

The **Echo Agent** is a demonstration agent that echoes back input with processing metadata. It's useful for:
- Testing the platform
- Understanding agent architecture
- Developing new agents

## Current Status

| Access Method | Status | How to Use |
|---------------|--------|------------|
| **Python/gRPC** | ✅ Fully functional | Direct task execution |
| **Cursor (MCP)** | ℹ️ Resource only | Read info, not executable |

## Method 1: Python/gRPC Client (Recommended)

### Quick Test

```bash
cd agent-platform-server
source venv/bin/activate
python scripts/test_client.py
```

This runs all tests including echo agent.

### Custom Script

```python
import grpc
import sys
import uuid
sys.path.insert(0, 'proto')
import agent_platform_pb2
import agent_platform_pb2_grpc

# Connect to MCP Router
channel = grpc.insecure_channel('localhost:50051')
stub = agent_platform_pb2_grpc.AgentServiceStub(channel)

# Execute task
request = agent_platform_pb2.TaskRequest(
    task_id=str(uuid.uuid4()),
    agent_id='echo-agent',
    input='Your message here',
    parameters={
        'custom_param': 'value',
        'test': 'true'
    }
)

response = stub.ExecuteTask(request)

print(f"Success: {response.success}")
print(f"Output: {response.output}")
print(f"Metadata: {dict(response.metadata)}")

channel.close()
```

### Expected Output

```
Success: True
Output: Echo Agent Response: Your message here | Parameters: custom_param=value, test=true
Metadata: {
  'agent_id': 'echo-agent',
  'processed_at': '1697318776.123',
  'task_number': '42'
}
```

## Method 2: Cursor (View Only)

### View Agent Information

In Cursor, ask:
```
"Tell me about agent://echo-agent"
"What is the echo-agent resource?"
"Show me available resources"
```

### Response

Cursor will show:
```markdown
# Echo Agent

**ID**: echo-agent
**Description**: Echo agent service
**Endpoint**: <container>:50052
**Capabilities**: agent, echo, text-processing

This agent can execute tasks through the Agent Platform.
```

### Limitation

Currently, echo-agent is exposed as an **MCP Resource** (readable), not an **MCP Tool** (callable).

- ✅ Can read information about it
- ❌ Cannot execute tasks from Cursor

## Method 3: Make Echo Agent Callable in Cursor

To enable execution from Cursor, you would need to modify `mcp-server/server.py`:

### Add to Tool List

```python
@app.list_tools()
async def handle_list_tools() -> list[Tool]:
    """List available tools"""
    tools = []
    
    # Existing weather-tool code...
    
    # Add echo-agent as a tool
    tools.append(Tool(
        name="echo-agent",
        description="Echo back your input with metadata",
        inputSchema={
            "type": "object",
            "properties": {
                "input": {
                    "type": "string",
                    "description": "Text to echo back"
                },
                "parameters": {
                    "type": "object",
                    "description": "Optional parameters",
                    "additionalProperties": {"type": "string"}
                }
            },
            "required": ["input"]
        }
    ))
    
    return tools
```

### Add Tool Execution Handler

```python
@app.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool execution"""
    
    if name == "echo-agent":
        try:
            channel = grpc.insecure_channel(GRPC_ADDRESS)
            stub = agent_platform_pb2_grpc.AgentServiceStub(channel)
            
            request = agent_platform_pb2.TaskRequest(
                task_id=str(uuid.uuid4()),
                agent_id='echo-agent',
                input=arguments.get("input", ""),
                parameters=arguments.get("parameters", {})
            )
            
            response = stub.ExecuteTask(request)
            channel.close()
            
            if response.success:
                return [TextContent(
                    type="text",
                    text=response.output
                )]
            else:
                return [TextContent(
                    type="text",
                    text=f"Error: {response.error}"
                )]
                
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"Error executing echo-agent: {str(e)}"
            )]
    
    # Other tools...
```

Then in Cursor:
```
"Use echo-agent to say 'Hello World'"
"Echo this message: 'Testing the platform'"
```

## Echo Agent Capabilities

### What It Does

1. **Echoes input**: Returns your message with a prefix
2. **Adds metadata**: Includes agent ID, timestamp, task number
3. **Processes parameters**: Displays any custom parameters
4. **Demonstrates streaming**: Can stream responses word-by-word

### Example Interactions

#### Simple Echo
```python
Input: "Hello, World!"
Output: "Echo Agent Response: Hello, World!"
```

#### With Parameters
```python
Input: "Test message"
Parameters: {"mode": "debug", "user": "admin"}
Output: "Echo Agent Response: Test message | Parameters: mode=debug, user=admin"
```

#### Status Check
```python
status_request = agent_platform_pb2.StatusRequest(agent_id='echo-agent')
status = stub.GetStatus(status_request)

# Returns:
# status: "healthy"
# active_tasks: 0
# uptime_seconds: 3600
```

## Use Cases

### 1. Platform Testing
Verify the entire stack is working:
```bash
python scripts/test_client.py
```

### 2. Load Testing
Test platform performance:
```python
for i in range(1000):
    response = stub.ExecuteTask(
        agent_platform_pb2.TaskRequest(
            task_id=str(uuid.uuid4()),
            agent_id='echo-agent',
            input=f'Test {i}'
        )
    )
```

### 3. Agent Development
Use as a template for new agents:
```bash
cp -r agents/echo agents/my-agent
# Modify my-agent/server.py with your logic
```

### 4. Debugging
Test routing and service discovery:
```bash
# Check agent is registered
make consul-check

# Query via router
make mcp-query-agents

# Test direct execution
python scripts/test_client.py
```

## Architecture

```
Your Code
    ↓
gRPC → localhost:50051 (HAProxy)
    ↓
MCP Router (gRPC Router)
    ↓
Consul Discovery
    ↓
Echo Agent Container (port 50052)
    ↓
EchoAgentService.ExecuteTask()
    ↓
Response
```

## Performance

- **Response Time**: ~50ms
- **Memory**: ~50MB
- **Throughput**: Handles concurrent requests
- **Uptime**: 5885s+ (running continuously)

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `AGENT_PORT` | 50052 | Port to listen on |
| `CONSUL_HOST` | localhost | Consul server |
| `CONSUL_PORT` | 8500 | Consul port |

### Service Registration

Registered in Consul as:
- **Service Name**: `agent-echo`
- **Tags**: `agent`, `echo`, `text-processing`
- **Health Check**: TCP check every 10s

## Source Code

**Location**: `agents/echo/server.py`

**Key Methods**:
- `ExecuteTask()` - Execute a task
- `StreamTask()` - Stream response chunks
- `GetStatus()` - Get agent status
- `RegisterAgent()` - Register with router

## Troubleshooting

### Agent Not Found

```bash
# Check if registered in Consul
make consul-check | grep echo

# Restart agent
docker-compose restart agent-platform-server-echo-agent-1
```

### Task Execution Fails

```bash
# Check logs
docker logs agent-platform-server-echo-agent-1

# Test direct connection
nc -zv localhost 50052
```

### Status Shows Unhealthy

```bash
# View detailed logs
make logs-echo

# Check resource usage
docker stats agent-platform-server-echo-agent-1
```

## Summary

| Feature | Status | Notes |
|---------|--------|-------|
| Task Execution | ✅ Working | Via Python/gRPC |
| Streaming | ✅ Working | Word-by-word streaming |
| Status Check | ✅ Working | Health and uptime |
| Consul Registration | ✅ Working | Auto-registers |
| Cursor Integration | ⚠️ View Only | Resource, not tool |
| Load Handling | ✅ Working | Concurrent requests |

**Best Way to Use**: Python/gRPC client for execution, Cursor for information viewing.

**To Make Cursor-Callable**: Modify `mcp-server/server.py` to expose as tool (code provided above).

