# Session ID Guide

## Overview

The Agent Platform now supports **session IDs** across all requests and responses, enabling context recovery from memory stores. This allows agents, workers, and tools to maintain conversational context across multiple interactions.

## What is a Session ID?

A session ID is a unique identifier (typically a UUID) that groups related requests together. By passing the same session ID across multiple requests, you can:

- **Maintain conversation context** - Agents can remember previous interactions
- **Recover state** - Access conversation history from a memory store
- **Track user sessions** - Associate requests with specific users or sessions
- **Enable multi-turn interactions** - Build complex workflows with memory

## Architecture Changes

### Protocol Buffers (gRPC)

The following messages now include a `session_id` field:

```protobuf
message TaskRequest {
  string task_id = 1;
  string agent_id = 2;
  string input = 3;
  map<string, string> parameters = 4;
  repeated string tool_ids = 5;
  string session_id = 6;  // NEW: Session ID for context recovery
}

message TaskResponse {
  string task_id = 1;
  string output = 2;
  bool success = 3;
  string error = 4;
  map<string, string> metadata = 5;
  string session_id = 6;  // NEW: Echoed back for correlation
}

message TaskChunk {
  string task_id = 1;
  string content = 2;
  bool is_final = 3;
  string session_id = 4;  // NEW: For streaming responses
}

message ToolRequest {
  string tool_id = 1;
  string operation = 2;
  map<string, string> parameters = 3;
  string session_id = 4;  // NEW: Session ID for tools
}

message ToolResponse {
  bool success = 1;
  string result = 2;
  string error = 3;
  string session_id = 4;  // NEW: Echoed back
}
```

### Service Updates

All services have been updated to handle `session_id`:

1. **MCP Server** - Extracts session_id from tool calls and passes it to gRPC services
2. **MCP Router** - Routes requests with session_id preservation
3. **Echo Agent** - Logs and returns session_id in responses
4. **Weather Tool** - Accepts and echoes back session_id
5. **Itinerary Worker** - Stores session_id in metadata and response

## Usage Examples

### 1. Using Session ID with Agents (via MCP/Cursor)

When calling an agent through the MCP interface, include the `session_id` parameter:

```json
{
  "input": "Hello, remember my preferences",
  "parameters": {
    "preference": "italian food"
  },
  "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

The response will include the session_id:

```
Echo Agent Response: Hello, remember my preferences | Parameters: preference=italian food

**Metadata**: agent_id=echo-agent, processed_at=1697400000.0, task_number=1, session_id=550e8400-e29b-41d4-a716-446655440000
**Session ID**: 550e8400-e29b-41d4-a716-446655440000
```

### 2. Using Session ID with Workers

When calling the itinerary worker:

```json
{
  "input": "Plan my trip",
  "parameters": {
    "destination": "Paris",
    "days": "3",
    "interests": "culture,food"
  },
  "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

The session_id is stored in metadata and returned in the response.

### 3. Using Session ID with Tools

When calling the weather tool:

```json
{
  "location": "New York",
  "days": "5",
  "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

The tool response includes:

```json
{
  "location": "New York",
  "temperature": 72,
  "condition": "Partly Cloudy",
  ...
}

**Session ID**: 550e8400-e29b-41d4-a716-446655440000
```

### 4. Direct gRPC Usage

When calling services directly via gRPC:

```python
import grpc
import agent_platform_pb2
import agent_platform_pb2_grpc
import uuid

# Create channel
channel = grpc.insecure_channel('localhost:50051')
stub = agent_platform_pb2_grpc.AgentServiceStub(channel)

# Create request with session_id
session_id = str(uuid.uuid4())
request = agent_platform_pb2.TaskRequest(
    task_id=str(uuid.uuid4()),
    agent_id='echo-agent',
    input='Hello with session',
    parameters={},
    session_id=session_id  # Include session ID
)

# Execute and check response
response = stub.ExecuteTask(request)
print(f"Session ID returned: {response.session_id}")
```

## Implementation Details

### Session ID Flow

1. **Client → MCP Server**: Client includes `session_id` in tool call arguments
2. **MCP Server → MCP Router**: Session ID passed in `TaskRequest.session_id`
3. **MCP Router → Service**: Session ID forwarded to backend service
4. **Service Processing**: Service uses session_id to:
   - Look up conversation history
   - Store new context
   - Track session state
5. **Service → Client**: Session ID echoed back in `TaskResponse.session_id`

### Logging

All services now log the session_id when present:

```
INFO - Received task: abc-123 - Input: Hello - Session: 550e8400-e29b-41d4-a716-446655440000
```

### Metadata Storage

Session IDs are also stored in the response metadata for easy access:

```python
metadata = {
    'agent_id': 'echo-agent',
    'processed_at': '1697400000.0',
    'session_id': '550e8400-e29b-41d4-a716-446655440000'
}
```

## Best Practices

### 1. Generate Session IDs

Use UUIDs for session IDs:

```python
import uuid
session_id = str(uuid.uuid4())
```

### 2. Persist Session IDs

Store session IDs on the client side to maintain continuity:

```python
# First request
session_id = str(uuid.uuid4())
response1 = call_agent(input="Hello", session_id=session_id)

# Follow-up request (same session)
response2 = call_agent(input="Remember me?", session_id=session_id)
```

### 3. Session Expiration

Implement session expiration in your memory store:

```python
# Example: Redis with TTL
redis.setex(f"session:{session_id}", 3600, context_data)  # 1 hour TTL
```

### 4. Optional Session ID

Session IDs are optional. If not provided:
- Services will work normally without context
- `session_id` field in responses will be empty
- No errors will occur

## Integration with Memory Stores

### Redis Example

```python
import redis
import json

redis_client = redis.Redis(host='localhost', port=6379)

def store_session_context(session_id: str, context: dict):
    """Store session context in Redis"""
    key = f"session:{session_id}"
    redis_client.setex(key, 3600, json.dumps(context))

def get_session_context(session_id: str) -> dict:
    """Retrieve session context from Redis"""
    key = f"session:{session_id}"
    data = redis_client.get(key)
    return json.loads(data) if data else {}

# In your agent/worker
def ExecuteTask(request, context):
    if request.session_id:
        # Load previous context
        previous_context = get_session_context(request.session_id)
        
        # Process with context
        result = process_with_context(request.input, previous_context)
        
        # Update context
        new_context = {**previous_context, 'last_input': request.input}
        store_session_context(request.session_id, new_context)
```

### PostgreSQL Example

```python
import psycopg2
import json
from datetime import datetime

def store_session_context(session_id: str, context: dict):
    """Store session context in PostgreSQL"""
    conn = psycopg2.connect("dbname=agent_platform")
    cur = conn.cursor()
    
    cur.execute("""
        INSERT INTO sessions (session_id, context, updated_at)
        VALUES (%s, %s, %s)
        ON CONFLICT (session_id) 
        DO UPDATE SET context = %s, updated_at = %s
    """, (session_id, json.dumps(context), datetime.now(),
          json.dumps(context), datetime.now()))
    
    conn.commit()
    cur.close()
    conn.close()

def get_session_context(session_id: str) -> dict:
    """Retrieve session context from PostgreSQL"""
    conn = psycopg2.connect("dbname=agent_platform")
    cur = conn.cursor()
    
    cur.execute(
        "SELECT context FROM sessions WHERE session_id = %s",
        (session_id,)
    )
    result = cur.fetchone()
    
    cur.close()
    conn.close()
    
    return json.loads(result[0]) if result else {}
```

## Testing Session IDs

### Test Script

```python
#!/usr/bin/env python3
"""Test session ID functionality"""

import grpc
import sys
import uuid
sys.path.insert(0, './proto')

import agent_platform_pb2
import agent_platform_pb2_grpc

def test_session_id():
    """Test session ID with echo agent"""
    channel = grpc.insecure_channel('localhost:50051')
    stub = agent_platform_pb2_grpc.AgentServiceStub(channel)
    
    # Generate session ID
    session_id = str(uuid.uuid4())
    print(f"Testing with session ID: {session_id}\n")
    
    # First request
    print("Request 1:")
    request1 = agent_platform_pb2.TaskRequest(
        task_id=str(uuid.uuid4()),
        agent_id='echo-agent',
        input='First message in session',
        session_id=session_id
    )
    response1 = stub.ExecuteTask(request1)
    print(f"  Output: {response1.output}")
    print(f"  Session ID returned: {response1.session_id}")
    print(f"  Metadata: {dict(response1.metadata)}\n")
    
    # Second request (same session)
    print("Request 2 (same session):")
    request2 = agent_platform_pb2.TaskRequest(
        task_id=str(uuid.uuid4()),
        agent_id='echo-agent',
        input='Second message in same session',
        session_id=session_id
    )
    response2 = stub.ExecuteTask(request2)
    print(f"  Output: {response2.output}")
    print(f"  Session ID returned: {response2.session_id}")
    print(f"  Metadata: {dict(response2.metadata)}\n")
    
    # Verify session IDs match
    assert response1.session_id == session_id
    assert response2.session_id == session_id
    print("✓ Session IDs match across requests!")
    
    channel.close()

if __name__ == '__main__':
    test_session_id()
```

Run the test:

```bash
cd agent-platform-server
python test_session_id.py
```

## Migration Guide

### Updating Existing Services

If you have custom agents/workers/tools, update them to handle `session_id`:

```python
def ExecuteTask(self, request, context):
    # Log session ID
    logger.info(f"Task: {request.task_id} - Session: {request.session_id}")
    
    # Your processing logic here
    result = process(request.input)
    
    # Return with session_id
    return agent_platform_pb2.TaskResponse(
        task_id=request.task_id,
        output=result,
        success=True,
        error="",
        metadata={'agent_id': 'my-agent'},
        session_id=request.session_id  # Echo back session ID
    )
```

### Backward Compatibility

All session_id fields are optional and backward compatible:

- Old clients without session_id will work normally
- New clients can opt-in to session management
- Services handle empty session_id gracefully

## Troubleshooting

### Session ID Not Returned

**Issue**: Response doesn't include session_id

**Solution**: 
1. Verify you're using the updated proto files
2. Recompile protos: `bash scripts/compile_proto.sh`
3. Restart all services

### Session Context Not Preserved

**Issue**: Agent doesn't remember previous context

**Solution**:
1. Verify same session_id is used across requests
2. Check memory store connection
3. Verify session hasn't expired
4. Check service logs for session_id

### Session ID Format Issues

**Issue**: Session IDs not working correctly

**Solution**:
1. Use UUID format: `550e8400-e29b-41d4-a716-446655440000`
2. Ensure consistent format across requests
3. Avoid special characters or spaces

## Next Steps

1. **Implement Memory Store**: Connect your agents to Redis, PostgreSQL, or other stores
2. **Add Context Logic**: Update agents to use session_id for context retrieval
3. **Session Management UI**: Build tools to view and manage active sessions
4. **Session Analytics**: Track session metrics and user interactions
5. **Multi-Agent Sessions**: Enable session sharing across different agents

## Related Documentation

- [Architecture Overview](ARCHITECTURE_OVERVIEW.md)
- [MCP Integration](ARCHITECTURE_MCP.md)
- [Echo Agent Usage](ECHO_AGENT_USAGE.md)
- [Scaling Guide](SCALING_GUIDE.md)

## Support

For questions or issues with session IDs:
1. Check service logs for session_id values
2. Test with the provided test script
3. Review this documentation
4. Check proto file for correct field definitions

