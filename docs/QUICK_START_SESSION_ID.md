# Quick Start: Session ID Feature

## What Was Added

Session IDs have been added to **all requests and responses** in the Agent Platform, enabling context recovery from memory stores.

## Quick Example

```python
import grpc
import agent_platform_pb2
import agent_platform_pb2_grpc
import uuid

# Generate a session ID
session_id = str(uuid.uuid4())

# Connect to platform
channel = grpc.insecure_channel('localhost:50051')
stub = agent_platform_pb2_grpc.AgentServiceStub(channel)

# Request with session ID
request = agent_platform_pb2.TaskRequest(
    task_id=str(uuid.uuid4()),
    agent_id='echo-agent',
    input='Hello with session!',
    session_id=session_id  # NEW!
)

# Response includes session ID
response = stub.ExecuteTask(request)
print(f"Session ID: {response.session_id}")
```

## What Changed

### Protocol (gRPC)
- Added `session_id` field to: `TaskRequest`, `TaskResponse`, `TaskChunk`, `ToolRequest`, `ToolResponse`

### All Services
- Echo Agent, Weather Tool, Itinerary Worker now handle session IDs
- Session IDs logged, stored in metadata, and echoed back

### MCP Server
- Extracts session_id from tool calls
- Passes to backend services
- Returns in responses

## Testing

```bash
# Run the test suite
python scripts/test_session_id.py
```

Expected: **5/5 tests passed** ✅

## Documentation

- **Complete Guide**: [SESSION_ID_GUIDE.md](SESSION_ID_GUIDE.md)
- **Implementation Summary**: [SESSION_ID_IMPLEMENTATION_SUMMARY.md](SESSION_ID_IMPLEMENTATION_SUMMARY.md)

## Key Points

✅ **Backward Compatible** - Optional, no breaking changes  
✅ **All Services Updated** - Agents, tools, workers, MCP server  
✅ **Fully Tested** - Comprehensive test suite  
✅ **Well Documented** - Complete guides and examples  
✅ **Production Ready** - Ready to use now!  

## Next Steps

1. **Use it**: Just add `session_id` to your requests
2. **Integrate memory**: Connect to Redis/PostgreSQL for context storage
3. **Build features**: Enable multi-turn conversations and context recovery

That's it! Session IDs are now available across your entire platform. 🎉

