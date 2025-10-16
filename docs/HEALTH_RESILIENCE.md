# Health-Aware Service Resilience

## Overview

The catalog system is now **resilient** and handles service health intelligently. It consolidates duplicate instances, tracks health status, and displays clear health information.

## Features

### 1. **Automatic Instance Consolidation**
- Multiple instances of the same service are automatically consolidated
- No duplicate service cards in the UI
- Shows total instance count regardless of health status

### 2. **Health Status Tracking**
The system tracks four health states:

| Status | Description | Color | When It Happens |
|--------|-------------|-------|-----------------|
| **healthy** | All instances passing | 🟢 Green (#4ade80) | All health checks passing |
| **degraded** | Some instances unhealthy | 🟡 Yellow (#fbbf24) | Mix of healthy and unhealthy |
| **unhealthy** | All instances critical | 🔴 Red (#ef4444) | All health checks failing |
| **down** | No instances found | ⚫ Gray (#94a3b8) | No registered instances |

### 3. **Detailed Health Information**
Each service card now shows:
```
Health: ✅ 2 healthy  ⚠️ 1 unhealthy
```

This allows you to:
- **See total capacity** (healthy + unhealthy instances)
- **Identify problems** (unhealthy instance count)
- **Make informed decisions** about service reliability

## API Response Format

### Before (Old Format)
```json
{
  "id": "echo-agent",
  "instances": 1,
  "status": "healthy"
}
```

### After (New Format with Health)
```json
{
  "id": "echo-agent",
  "instances": 1,
  "status": "healthy",
  "health": {
    "healthy_instances": 1,
    "unhealthy_instances": 0,
    "total_instances": 1,
    "status": "healthy"
  }
}
```

## How It Works

### 1. Health Check Query
The catalog API queries **all instances** from Consul (not just passing ones):
```python
# Old way - only healthy instances
_, services = consul_client.health.service('agent-echo', passing=True)

# New way - all instances with health status
health_info = get_service_health(consul_client, 'agent-echo')
```

### 2. Health Status Calculation
```python
def get_service_health(consul_client, service_name: str) -> HealthInfo:
    _, all_services = consul_client.health.service(service_name)
    
    healthy = 0
    unhealthy = 0
    
    for service in all_services:
        checks = service.get('Checks', [])
        is_healthy = all(check.get('Status') == 'passing' for check in checks)
        
        if is_healthy:
            healthy += 1
        else:
            unhealthy += 1
    
    total = healthy + unhealthy
    
    # Determine overall status
    if total == 0:
        status = "down"
    elif unhealthy == 0:
        status = "healthy"
    elif healthy > 0:
        status = "degraded"
    else:
        status = "unhealthy"
    
    return HealthInfo(
        healthy_instances=healthy,
        unhealthy_instances=unhealthy,
        total_instances=total,
        status=status
    )
```

### 3. UI Display
The UI automatically displays health information for all services:

```jsx
{agent.health && (
  <div className="detail-item">
    <span className="label">Health:</span>
    <span className="value">
      ✅ {agent.health.healthy_instances} healthy
      {agent.health.unhealthy_instances > 0 && (
        <span style={{color: '#f44336', marginLeft: '10px'}}>
          ⚠️ {agent.health.unhealthy_instances} unhealthy
        </span>
      )}
    </span>
  </div>
)}
```

## Benefits

### 1. **No More Duplicates**
Services with multiple instances appear as a single card with instance count, not as duplicate entries.

### 2. **Visibility into Problems**
When a service has unhealthy instances, you can:
- See the exact count of healthy vs unhealthy
- Identify degraded services at a glance
- Make informed decisions about service capacity

### 3. **Resilient to Stale Registrations**
The system handles:
- Old containers that didn't deregister cleanly
- Services in the process of restarting
- Partial deployments with mixed health

### 4. **Backward Compatible**
The UI gracefully handles services that don't provide health info (optional health field).

## Examples

### Example 1: All Healthy
```json
{
  "id": "echo-agent",
  "status": "healthy",
  "health": {
    "healthy_instances": 3,
    "unhealthy_instances": 0,
    "total_instances": 3,
    "status": "healthy"
  }
}
```
**UI Shows:** `✅ 3 healthy` | Badge: 🟢 **healthy**

### Example 2: Degraded Service
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
**UI Shows:** `✅ 2 healthy ⚠️ 1 unhealthy` | Badge: 🟡 **degraded**

### Example 3: All Unhealthy
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
**UI Shows:** `✅ 0 healthy ⚠️ 2 unhealthy` | Badge: 🔴 **unhealthy**

### Example 4: Service Down
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
**UI Shows:** (no health section) | Badge: ⚫ **down**

## Cleanup Script

You can still manually clean up stale services:

```bash
# Remove only unhealthy/critical instances
bash scripts/cleanup_consul.sh stale

# List all services
bash scripts/cleanup_consul.sh list

# Remove specific service
bash scripts/cleanup_consul.sh remove echo-agent

# Nuclear option - remove everything
bash scripts/cleanup_consul.sh purge
```

## Testing Health Resilience

### Simulate an Unhealthy Instance
```bash
# Stop one instance but don't deregister it from Consul
docker stop agent-platform-server-echo-agent-1

# Check the catalog - it will show:
# Status: degraded
# Health: ✅ 0 healthy ⚠️ 1 unhealthy
```

### Simulate Multiple Instances
```bash
# Scale up echo agent
docker-compose up -d --scale echo-agent=3

# The catalog will show:
# Status: healthy
# Health: ✅ 3 healthy
# (consolidated into one card, not three separate cards)
```

## Migration Notes

### Breaking Changes
- **None** - The system is backward compatible
- Old services without health info will still work
- The `health` field is optional in the UI

### API Changes
- All three endpoints (`/api/agents`, `/api/tools`, `/api/workers`) now include `health` object
- The `status` field now reflects overall health, not just instance presence
- The `instances` field shows total count (healthy + unhealthy)

## Architecture Changes

### Catalog API (`catalog-api/app.py`)
- Added `HealthInfo` model
- Added `get_service_health()` helper function
- Updated all three endpoints to use health-aware queries
- Changed from `passing=True` to querying all instances

### Catalog UI (`catalog-ui/src/App.jsx`)
- Added health info display to all service cards
- Updated status badge colors to match health states
- Added conditional rendering for unhealthy instance warnings

## Future Enhancements

Potential improvements:
1. **Health History** - Track health over time
2. **Alerts** - Notify when services become unhealthy
3. **Auto-Cleanup** - Automatically deregister critical instances after N minutes
4. **Health Dashboard** - Aggregate view of platform health
5. **Instance Details** - Click to see individual instance health

---

**Last Updated:** 2025-10-15
**Version:** 1.1.0 (Health-Aware Release)

