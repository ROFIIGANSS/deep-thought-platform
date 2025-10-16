# Service Deduplication Guide

## Overview

The Agent Platform automatically **deduplicates** services when multiple instances of the same agent, tool, or worker are running. This ensures clean catalog displays and prevents duplicate tool listings in Cursor/Claude.

## Problem Statement

When scaling services horizontally (e.g., running 2 echo-agent containers), the gRPC `ListAgents`, `ListTools`, and `ListWorkers` RPC calls return **multiple entries** - one from each instance. Without deduplication, this causes:

- ❌ **Duplicate cards** in the Catalog UI
- ❌ **Duplicate tool buttons** in Cursor IDE
- ❌ **Confused users** seeing "echo-agent" appear multiple times

## Solution

The platform implements **automatic deduplication** at two critical points:

### 1. Catalog API (`catalog-api/app.py`)

The Catalog API deduplicates services before returning them via REST endpoints:

```python
# Example: Deduplicating agents
agents_dict = {}
for agent in response.agents:
    # Skip if we already have this agent
    if agent.agent_id in agents_dict:
        continue
    agents_dict[agent.agent_id] = agent

return list(agents_dict.values())
```

**Endpoints affected:**
- `/api/agents` - Returns unique agents only
- `/api/tools` - Returns unique tools only
- `/api/workers` - Returns unique workers only

### 2. MCP Server (`mcp-server/server.py`)

The MCP Server deduplicates services before exposing them to Cursor/Claude:

```python
# Example: Deduplicating in get_agents()
@staticmethod
def get_agents():
    """Query available agents from gRPC backend"""
    channel = grpc.insecure_channel(GRPC_ADDRESS)
    stub = agent_platform_pb2_grpc.AgentServiceStub(channel)
    
    request = agent_platform_pb2.ListAgentsRequest()
    response = stub.ListAgents(request)
    channel.close()
    
    # Deduplicate agents by agent_id
    agents_dict = {}
    for agent in response.agents:
        if agent.agent_id not in agents_dict:
            agents_dict[agent.agent_id] = agent
    
    return list(agents_dict.values())
```

**Methods affected:**
- `get_agents()` - Returns unique agents
- `get_tools()` - Returns unique tools
- `get_workers()` - Returns unique workers

## How It Works

### Deduplication Strategy

1. **Query all instances** via gRPC (returns duplicates)
2. **Create a dictionary** keyed by unique ID (`agent_id`, `tool_id`, `worker_id`)
3. **First-wins strategy** - Keep the first entry encountered for each ID
4. **Return unique list** - Convert dictionary values back to list

### Health Information Preserved

Even though services are deduplicated, **health information** is preserved:

```json
{
  "id": "echo-agent",
  "name": "Echo Agent",
  "instances": 2,
  "status": "degraded",
  "health": {
    "healthy_instances": 1,
    "unhealthy_instances": 1,
    "total_instances": 2,
    "status": "degraded"
  }
}
```

The catalog still shows:
- ✅ **Total instance count** (2 instances)
- ✅ **Health breakdown** (1 healthy, 1 unhealthy)
- ✅ **Overall status** (degraded)

But displays as:
- ✅ **Single card/button** (not duplicated)

## Benefits

### For Catalog UI Users

**Before deduplication:**
```
Agents:
┌──────────────┐  ┌──────────────┐
│ Echo Agent   │  │ Echo Agent   │  ← Duplicates!
│ Status: OK   │  │ Status: OK   │
└──────────────┘  └──────────────┘
```

**After deduplication:**
```
Agents:
┌──────────────────────────────┐
│ Echo Agent                   │  ← Single entry
│ Status: degraded             │
│ Health: ✅ 1 healthy         │
│         ⚠️ 1 unhealthy       │
│ Total: 2 instances           │
└──────────────────────────────┘
```

### For Cursor/Claude Users

**Before deduplication:**
```
Available Tools:
- echo-agent    ← First instance
- echo-agent    ← Second instance (duplicate!)
- weather-tool
- itinerary-worker
```

**After deduplication:**
```
Available Tools:
- echo-agent    ← Single entry (works with all instances)
- weather-tool
- itinerary-worker
```

## Implementation Details

### Deduplication Keys

| Service Type | Deduplication Key | Example |
|--------------|-------------------|---------|
| Agents | `agent_id` | `echo-agent` |
| Tools | `tool_id` | `weather-tool` |
| Workers | `worker_id` | `itinerary-worker` |

### Scaling Behavior

When you scale services:

```bash
# Scale echo agent to 3 instances
docker-compose up -d --scale echo-agent=3

# Verify in Consul (shows 3 instances)
curl http://localhost:8500/v1/health/service/agent-echo

# Query catalog (shows 1 deduplicated entry)
curl http://localhost:8000/api/agents
```

**Result:**
- Consul shows: 3 instances registered
- Catalog API returns: 1 agent entry with `instances: 3`
- Cursor shows: 1 tool button (routes to all 3 instances)

### Load Balancing Integration

Deduplication works **seamlessly** with load balancing:

1. **User calls tool** in Cursor: `echo-agent`
2. **MCP Server** routes to HAProxy
3. **HAProxy** distributes to one of N instances
4. **Result returned** to user
5. **Next call** might hit different instance (load balanced)

From the user's perspective:
- ✅ Single tool/agent/worker name
- ✅ Works with any number of instances
- ✅ Automatically load balanced
- ✅ Transparent scaling

## Edge Cases

### All Instances Unhealthy

If all instances are unhealthy:

```json
{
  "id": "echo-agent",
  "status": "unhealthy",
  "health": {
    "healthy_instances": 0,
    "unhealthy_instances": 2,
    "total_instances": 2,
    "status": "unhealthy"
  }
}
```

- Still shows as **single entry**
- Status clearly indicates **all unhealthy**
- User warned before attempting to use

### No Instances Running

If no instances are registered:

```json
{
  "id": "echo-agent",
  "status": "down",
  "health": {
    "healthy_instances": 0,
    "unhealthy_instances": 0,
    "total_instances": 0,
    "status": "down"
  }
}
```

- May not appear in catalog at all
- Or shows with **down** status
- Prevents users from calling non-existent service

### Mixed Health States (Degraded)

With 3 instances (2 healthy, 1 unhealthy):

```json
{
  "id": "echo-agent",
  "status": "degraded",
  "health": {
    "healthy_instances": 2,
    "unhealthy_instances": 1,
    "total_instances": 3,
    "status": "degraded"
  }
}
```

- Shows as **single entry**
- Status: **degraded** (yellow badge)
- User informed of partial availability
- Service still functional via healthy instances

## Testing

### Verify Deduplication

```bash
# Scale echo agent to multiple instances
cd agent-platform-server
docker-compose up -d --scale echo-agent=3

# Wait for registration
sleep 5

# Check Consul (should show 3)
curl -s http://localhost:8500/v1/health/service/agent-echo | \
  python3 -c "import json, sys; print(f'Consul instances: {len(json.load(sys.stdin))}')"

# Check Catalog API (should show 1)
curl -s http://localhost:8000/api/agents | \
  python3 -c "import json, sys; data=json.load(sys.stdin); print(f'Catalog entries: {len(data)}'); print(f'Instance count: {data[0][\"instances\"]}')"
```

**Expected output:**
```
Consul instances: 3
Catalog entries: 1
Instance count: 3
```

### Visual Verification

1. **Catalog UI**: http://localhost:8080
   - Should show **ONE** Echo Agent card
   - With "3 instances" displayed
   - Health shows breakdown

2. **Cursor IDE**:
   - Reload MCP connection
   - Check available tools
   - Should see **ONE** `echo-agent` tool

## Troubleshooting

### Still Seeing Duplicates in Cursor?

**Solution:** Restart the MCP connection:
```bash
# Option 1: Restart Cursor completely
# Option 2: Reload window (Cmd+R / Ctrl+R)
# Option 3: Settings → Features → Reload MCP Servers
```

### Catalog Shows Duplicates?

**Solution:** Rebuild and restart catalog API:
```bash
cd agent-platform-server
docker-compose up -d --build catalog-api
```

### Services Not Consolidating?

**Check deduplication logic:**
```bash
# View catalog API logs
docker-compose logs catalog-api | grep -i duplicate

# Verify unique IDs match
curl -s http://localhost:8000/api/agents | \
  python3 -c "import json, sys; [print(f'{a[\"id\"]} - {a[\"instances\"]} instances') for a in json.load(sys.stdin)]"
```

## Related Documentation

- [HEALTH_RESILIENCE.md](HEALTH_RESILIENCE.md) - Health tracking and consolidation
- [SCALING_GUIDE.md](SCALING_GUIDE.md) - Horizontal scaling guide
- [LOAD_BALANCING.md](LOAD_BALANCING.md) - Load balancing configuration
- [CATALOG.md](CATALOG.md) - Catalog UI and API documentation

## Summary

✅ **Automatic deduplication** in Catalog API and MCP Server  
✅ **Single entry per service** regardless of instance count  
✅ **Health information preserved** and displayed  
✅ **Load balancing transparent** to end users  
✅ **Cursor integration clean** with no duplicate tools  
✅ **Scales seamlessly** with any number of instances  

Deduplication ensures a clean, professional user experience while maintaining full transparency about service health and availability.

---

**Version:** 1.0.0  
**Last Updated:** 2025-10-15

