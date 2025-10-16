# gRPC Subsystem Architecture

## Overview

The gRPC subsystem provides high-performance, strongly-typed communication between all internal platform components. It serves as the primary protocol for the Agent Platform's microservices architecture.

## gRPC Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                      gRPC CLIENT LAYER                           │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Python Clients          Go Clients          Other gRPC Clients │
│  (test_client.py)        (custom SDKs)       (Java, Node, etc.) │
│         │                      │                      │          │
│         │                      │                      │          │
│         └──────────────────────┼──────────────────────┘          │
│                                │                                 │
│                                │ gRPC/HTTP2                      │
│                                │ Protocol Buffers                │
│                                ▼                                 │
├──────────────────────────────────────────────────────────────────┤
│                    LOAD BALANCING LAYER                         │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│                    ┌──────────────────┐                         │
│                    │     HAProxy      │                         │
│                    │  Load Balancer   │                         │
│                    │                  │                         │
│                    │  Port: 50051     │                         │
│                    │  Mode: TCP       │                         │
│                    │  Stats: 8404     │                         │
│                    └────────┬─────────┘                         │
│                             │                                    │
│                             │ Round-robin                        │
│                             │ Health checks every 2s             │
│                             │                                    │
│          ┌──────────────────┼──────────────────┐                │
│          │                  │                  │                │
├──────────┼──────────────────┼──────────────────┼────────────────┤
│                     gRPC ROUTER LAYER                           │
├──────────┼──────────────────┼──────────────────┼────────────────┤
│          ▼                  ▼                  ▼                │
│    ┌──────────┐       ┌──────────┐      ┌──────────┐          │
│    │  gRPC    │       │  gRPC    │      │  gRPC    │          │
│    │ Router 1 │       │ Router 2 │      │ Router N │          │
│    │          │       │          │      │          │          │
│    │ Port:    │       │ Port:    │      │ Port:    │          │
│    │ 50051    │       │ 50051    │      │ 50051    │          │
│    └────┬─────┘       └────┬─────┘      └────┬─────┘          │
│         │                   │                  │                │
│         │                   │                  │                │
│         │ ServiceRegistry   │ ServiceRegistry  │                │
│         │ (Consul client)   │ (Consul client)  │                │
│         │                   │                  │                │
│         └───────────────────┴──────────────────┘                │
│                             │                                    │
│                             │ Service Discovery                  │
│                             │ Consul DNS/API                     │
│                             ▼                                    │
│                   ┌──────────────────┐                          │
│                   │     Consul       │                          │
│                   │  Service Mesh    │                          │
│                   │  Port: 8500      │                          │
│                   └────────┬─────────┘                          │
│                            │                                     │
│                            │ Registered services                 │
│                            │ with health checks                  │
│                            │                                     │
├────────────────────────────┼─────────────────────────────────────┤
│                   BACKEND SERVICE LAYER                         │
├────────────────────────────┼─────────────────────────────────────┤
│         ┌──────────────────┼──────────────────┐                 │
│         │                  │                  │                 │
│         ▼                  ▼                  ▼                 │
│   ┌───────────┐      ┌───────────┐     ┌───────────┐          │
│   │  Agents   │      │   Tools   │     │  Workers  │          │
│   │           │      │           │     │           │          │
│   │ echo      │      │ weather   │     │ itinerary │          │
│   │ (50052)   │      │ (50053)   │     │ (50054)   │          │
│   │           │      │           │     │           │          │
│   │ gRPC      │      │ gRPC      │     │ gRPC      │          │
│   │ Server    │      │ Server    │     │ Server    │          │
│   └───────────┘      └───────────┘     └───────────┘          │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

## Protocol Buffer Definition

### Location
- **File**: `proto/agent_platform.proto`
- **Compilation**: `make proto-compile`
- **Generated Files**:
  - `proto/agent_platform_pb2.py` (messages)
  - `proto/agent_platform_pb2_grpc.py` (services)

### Core Services

#### 1. AgentService

```protobuf
service AgentService {
  rpc ExecuteTask(TaskRequest) returns (TaskResponse);
  rpc StreamTask(TaskRequest) returns (stream TaskResponse);
  rpc GetStatus(StatusRequest) returns (StatusResponse);
  rpc ListAgents(ListAgentsRequest) returns (ListAgentsResponse);
}
```

**Purpose**: Execute tasks via autonomous agents

**Methods**:
- `ExecuteTask`: Synchronous task execution
- `StreamTask`: Streaming task execution with progress updates
- `GetStatus`: Health and capability information
- `ListAgents`: Discover all available agents

#### 2. ToolService

```protobuf
service ToolService {
  rpc ExecuteTool(ToolRequest) returns (ToolResponse);
  rpc ListTools(ListToolsRequest) returns (ListToolsResponse);
}
```

**Purpose**: Execute specialized tools

**Methods**:
- `ExecuteTool`: Execute a tool operation
- `ListTools`: Discover all available tools

#### 3. TaskWorker

```protobuf
service TaskWorker {
  rpc ProcessTask(TaskRequest) returns (TaskResponse);
  rpc GetTaskStatus(TaskStatusRequest) returns (TaskStatusResponse);
  rpc ListWorkers(ListWorkersRequest) returns (ListWorkersResponse);
}
```

**Purpose**: Process complex, long-running tasks

**Methods**:
- `ProcessTask`: Execute complex task
- `GetTaskStatus`: Check task progress
- `ListWorkers`: Discover all available workers

### Key Messages

#### TaskRequest
```protobuf
message TaskRequest {
  string task_id = 1;
  string agent_id = 2;
  string input = 3;
  map<string, string> parameters = 4;
  repeated string tool_ids = 5;
}
```

#### TaskResponse
```protobuf
message TaskResponse {
  string task_id = 1;
  string output = 2;
  bool success = 3;
  string error = 4;
  map<string, string> metadata = 5;
}
```

#### AgentInfo
```protobuf
message AgentInfo {
  string agent_id = 1;
  string name = 2;
  string description = 3;
  repeated string capabilities = 4;
  string endpoint = 5;
}
```

## gRPC Router Implementation

### Location
- **Directory**: `mcp-router/` (⚠️ naming to be updated to `grpc-router/`)
- **Main File**: `mcp-router/app.py`
- **Port**: 50051 (internal, load balanced)

### Key Classes

#### ServiceRegistry

**Purpose**: Manages Consul interactions and service discovery

**Features**:
```python
class ServiceRegistry:
    def __init__(self, consul_host, consul_port):
        self.consul = consul.Consul(host=consul_host, port=consul_port)
        self.cache = {}  # Service endpoint cache
        self.cache_ttl = 60  # seconds
    
    def list_services(self, tag=None):
        """List all services, optionally filtered by tag"""
        
    def discover_service(self, service_name):
        """Discover healthy instance of a service"""
        
    def get_endpoint(self, service_name):
        """Get service endpoint with caching"""
```

**Caching Strategy**:
- Cache service endpoints for 60 seconds
- Reduces Consul queries
- Automatic cache invalidation on errors

#### Service Implementations

##### AgentServiceImpl
```python
class AgentServiceImpl(agent_platform_pb2_grpc.AgentServiceServicer):
    def ExecuteTask(self, request, context):
        # 1. Extract agent_id from request
        # 2. Transform to Consul service name (echo-agent → agent-echo)
        # 3. Discover service endpoint via Consul
        # 4. Create gRPC channel to agent
        # 5. Forward request and return response
        
    def ListAgents(self, request, context):
        # 1. Query Consul for services tagged 'agent'
        # 2. Transform to AgentInfo messages
        # 3. Return list of available agents
```

##### ToolServiceImpl
```python
class ToolServiceImpl(agent_platform_pb2_grpc.ToolServiceServicer):
    def ExecuteTool(self, request, context):
        # Similar pattern to AgentServiceImpl
        
    def ListTools(self, request, context):
        # Query Consul for services tagged 'tool'
```

##### TaskWorkerImpl
```python
class TaskWorkerImpl(agent_platform_pb2_grpc.TaskWorkerServicer):
    def ProcessTask(self, request, context):
        # Similar pattern to AgentServiceImpl
        
    def ListWorkers(self, request, context):
        # Query Consul for services tagged 'worker'
```

### Service Name Transformation

**Client-facing IDs** → **Consul Service Names**:

| Client ID | Consul Service Name |
|-----------|-------------------|
| `echo-agent` | `agent-echo` |
| `weather-tool` | `tool-weather` |
| `itinerary-worker` | `worker-itinerary` |

**Implementation**:
```python
def transform_client_id_to_service(client_id, service_type):
    """
    Transform client-facing ID to Consul service name
    Examples:
      echo-agent → agent-echo
      weather-tool → tool-weather
    """
    name = client_id.replace(f'-{service_type}', '')
    return f'{service_type}-{name}'
```

### Consul Registration

Each gRPC router instance registers with Consul:

```python
def register_with_consul():
    instance_id = f"mcp-router-{socket.gethostname()}"
    
    consul_client.agent.service.register(
        name='mcp-router',
        service_id=instance_id,
        address=socket.gethostname(),
        port=50051,
        tags=['router', 'mcp', f'instance:{socket.gethostname()}'],
        check=consul.Check.tcp(socket.gethostname(), 50051, interval='10s')
    )
```

## HAProxy Load Balancing

### Configuration
- **File**: `haproxy/haproxy.cfg`
- **Frontend**: `grpc_frontend` on port 50051
- **Backend**: `grpc_backend` with router instances

### Frontend Configuration

```haproxy
frontend grpc_frontend
    bind *:50051
    mode tcp
    option tcplog
    default_backend grpc_backend
```

### Backend Configuration

```haproxy
backend grpc_backend
    mode tcp
    balance roundrobin
    option tcp-check
    
    # Dynamic backend servers
    server router1 agent-platform-server-mcp-router-1:50051 check inter 2000 rise 2 fall 3
    server router2 agent-platform-server-mcp-router-2:50051 check inter 2000 rise 2 fall 3
    server router3 agent-platform-server-mcp-router-3:50051 check inter 2000 rise 2 fall 3
    # ... up to 10 instances
```

### Load Balancing Features

✅ **Round-robin distribution**: Equal load across instances  
✅ **Health checks**: TCP checks every 2 seconds  
✅ **Automatic failover**: Failed instances removed from pool  
✅ **Dynamic scaling**: Support up to 10 router instances  
✅ **Statistics**: Real-time dashboard on port 8404  

## Backend Services

### Agent Implementation Pattern

```python
import grpc
from concurrent import futures
import agent_platform_pb2
import agent_platform_pb2_grpc

class EchoAgentServicer(agent_platform_pb2_grpc.AgentServiceServicer):
    def ExecuteTask(self, request, context):
        # Process the task
        result = f"Echo: {request.input}"
        
        return agent_platform_pb2.TaskResponse(
            task_id=request.task_id,
            output=result,
            success=True
        )
    
    def GetStatus(self, request, context):
        return agent_platform_pb2.StatusResponse(
            status="healthy",
            capabilities=["echo", "text-processing"]
        )

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    agent_platform_pb2_grpc.add_AgentServiceServicer_to_server(
        EchoAgentServicer(), server
    )
    server.add_insecure_port('[::]:50052')
    
    # Register with Consul
    register_with_consul('agent-echo', 50052, ['agent', 'echo'])
    
    server.start()
    server.wait_for_termination()
```

### Consul Registration Pattern

```python
import consul
import socket

def register_with_consul(service_name, port, tags):
    consul_client = consul.Consul(host='consul', port=8500)
    
    instance_id = f"{service_name}-{socket.gethostname()}"
    
    consul_client.agent.service.register(
        name=service_name,
        service_id=instance_id,
        address=socket.gethostname(),
        port=port,
        tags=tags,
        check=consul.Check.tcp(socket.gethostname(), port, interval='10s')
    )
```

## Service Discovery Flow

### Request Routing Sequence

```
1. Client sends gRPC request to localhost:50051
   │
   ▼
2. HAProxy receives request on port 50051
   │ (Round-robin selection)
   ▼
3. HAProxy forwards to gRPC Router instance (e.g., router-1)
   │
   ▼
4. gRPC Router parses request (e.g., ExecuteTask with agent_id="echo-agent")
   │
   ▼
5. Router transforms ID: "echo-agent" → "agent-echo"
   │
   ▼
6. Router queries Consul: GET /v1/health/service/agent-echo?passing=true
   │
   ▼
7. Consul returns healthy instance: {address: "abc123", port: 50052}
   │
   ▼
8. Router creates gRPC channel to agent: grpc.insecure_channel("abc123:50052")
   │
   ▼
9. Router forwards request to agent
   │
   ▼
10. Agent processes task and returns response
    │
    ▼
11. Router returns response to client
```

### Service Discovery Caching

**Problem**: Querying Consul for every request adds latency

**Solution**: TTL-based caching

```python
class ServiceRegistry:
    def get_endpoint(self, service_name):
        # Check cache first
        if service_name in self.cache:
            cached_entry = self.cache[service_name]
            if time.time() - cached_entry['timestamp'] < self.cache_ttl:
                return cached_entry['endpoint']
        
        # Cache miss or expired - query Consul
        endpoint = self.discover_service(service_name)
        
        # Update cache
        self.cache[service_name] = {
            'endpoint': endpoint,
            'timestamp': time.time()
        }
        
        return endpoint
```

**Benefits**:
- Reduces Consul queries by ~95%
- Decreases latency by ~5-10ms per request
- Still detects failures (cache invalidated on errors)

## Client Implementation

### Python Client Example

```python
import grpc
import agent_platform_pb2
import agent_platform_pb2_grpc

# Connect to HAProxy endpoint
channel = grpc.insecure_channel('localhost:50051')

# Create stub for the service you want
agent_stub = agent_platform_pb2_grpc.AgentServiceStub(channel)

# Make request
request = agent_platform_pb2.TaskRequest(
    task_id='task-123',
    agent_id='echo-agent',
    input='Hello, World!'
)

response = agent_stub.ExecuteTask(request)
print(f"Result: {response.output}")
```

### Discovery API Example

```python
# List all available agents
request = agent_platform_pb2.ListAgentsRequest()
response = agent_stub.ListAgents(request)

for agent in response.agents:
    print(f"Agent: {agent.agent_id}")
    print(f"  Name: {agent.name}")
    print(f"  Capabilities: {', '.join(agent.capabilities)}")
```

## Scaling Strategies

### Horizontal Scaling

#### Scale gRPC Routers

```bash
# Using Docker Compose
docker-compose up -d --scale mcp-router=3

# Using Makefile
make scale-router N=3

# Using management script
./scripts/manage_routers.sh scale 3
```

**Result**: HAProxy distributes load across 3 router instances

#### Scale Backend Services

```bash
# Scale echo agents
make scale-echo N=3

# Scale weather tools
make scale-weather N=3

# Scale all services
make scale-all N=3
```

**Result**: Consul registers multiple instances, gRPC Router distributes requests

### Load Distribution

**Router Layer** (via HAProxy):
- Algorithm: Round-robin
- Session affinity: None (stateless)
- Health checks: TCP every 2s

**Service Layer** (via Consul):
- Algorithm: Client-side selection (first healthy instance)
- Session affinity: None (stateless)
- Health checks: TCP every 10s

## Performance Tuning

### Optimization Techniques

1. **Connection Pooling**
   - Reuse gRPC channels
   - Keep-alive for long-lived connections

2. **Service Discovery Caching**
   - 60-second TTL reduces Consul queries
   - Invalidate on errors

3. **HAProxy Tuning**
   - TCP mode (no protocol parsing)
   - Aggressive health checks (2s interval)
   - High connection limits

4. **gRPC Options**
   ```python
   channel = grpc.insecure_channel(
       target,
       options=[
           ('grpc.keepalive_time_ms', 10000),
           ('grpc.keepalive_timeout_ms', 5000),
           ('grpc.http2.max_pings_without_data', 0),
       ]
   )
   ```

### Performance Metrics

| Metric | Single Router | 3 Routers (HA) | 5 Routers |
|--------|--------------|----------------|-----------|
| Throughput | ~1,000 req/s | ~2,500 req/s | ~4,000 req/s |
| P50 Latency | ~10ms | ~12ms | ~15ms |
| P99 Latency | ~50ms | ~60ms | ~70ms |
| CPU Usage | ~10% | ~30% | ~50% |
| RAM Usage | ~50MB/router | ~150MB total | ~250MB total |

## Monitoring

### HAProxy Statistics

```bash
# Open stats dashboard
open http://localhost:8404

# Or via Makefile
make ui-haproxy
```

**Available Metrics**:
- Backend server status
- Request rate
- Response times
- Error rates
- Health check status

### Consul Service Health

```bash
# Check all services
make consul-check

# View specific service health
curl http://localhost:8500/v1/health/service/agent-echo?passing=true

# Consul UI
open http://localhost:8500
```

### Logs

```bash
# Router logs
make logs-router

# Backend service logs
make logs-echo
make logs-weather
make logs-itinerary

# All logs
make logs
```

## Troubleshooting

### Common Issues

#### 1. Service Not Found

**Symptom**: `grpc.StatusCode.UNAVAILABLE: Service not found`

**Cause**: Service not registered in Consul or unhealthy

**Solution**:
```bash
# Check Consul registry
make consul-check

# Check service logs
make logs-echo

# Restart service
docker-compose restart echo-agent
```

#### 2. Connection Refused

**Symptom**: `grpc.StatusCode.UNAVAILABLE: failed to connect`

**Cause**: HAProxy or router not running

**Solution**:
```bash
# Check HAProxy status
docker-compose ps haproxy

# Check router status
docker-compose ps mcp-router

# Restart if needed
docker-compose restart haproxy
```

#### 3. Slow Response Times

**Symptom**: High latency (>100ms)

**Possible Causes**:
- Service discovery cache disabled
- Network issues
- Backend service overloaded

**Solution**:
```bash
# Check HAProxy stats for bottlenecks
open http://localhost:8404

# Scale routers
make scale-router N=3

# Scale backend services
make scale-echo N=3
```

## Security Considerations

### Current State (Development)

⚠️ **Insecure Channels**:
```python
channel = grpc.insecure_channel(target)
```

### Production Recommendations

#### 1. Enable TLS

```python
# Server-side
credentials = grpc.ssl_server_credentials(
    [(server_key, server_cert)]
)
server.add_secure_port('[::]:50051', credentials)

# Client-side
credentials = grpc.ssl_channel_credentials(root_cert)
channel = grpc.secure_channel(target, credentials)
```

#### 2. Mutual TLS (mTLS)

```python
# Server validates client certificates
credentials = grpc.ssl_server_credentials(
    [(server_key, server_cert)],
    root_certificates=client_ca_cert,
    require_client_auth=True
)
```

#### 3. Token-Based Authentication

```python
# Add interceptor for JWT validation
class AuthInterceptor(grpc.ServerInterceptor):
    def intercept_service(self, continuation, handler_call_details):
        # Validate JWT token from metadata
        token = handler_call_details.invocation_metadata.get('authorization')
        if not validate_token(token):
            return grpc.unary_unary_rpc_method_handler(
                lambda request, context: context.abort(
                    grpc.StatusCode.UNAUTHENTICATED,
                    'Invalid token'
                )
            )
        return continuation(handler_call_details)
```

## Related Documentation

- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Overall system architecture
- **[ARCHITECTURE_MCP.md](ARCHITECTURE_MCP.md)** - MCP subsystem details
- **[LOAD_BALANCING.md](LOAD_BALANCING.md)** - HAProxy configuration guide
- **[SCALING_GUIDE.md](SCALING_GUIDE.md)** - Scaling strategies

## Summary

The gRPC subsystem provides:

✅ **High Performance**: Binary protocol, HTTP/2 multiplexing  
✅ **Strong Typing**: Protocol Buffers ensure type safety  
✅ **Service Discovery**: Consul-based dynamic discovery  
✅ **Load Balancing**: HAProxy for routers, Consul for services  
✅ **Horizontal Scaling**: Scale any component independently  
✅ **Monitoring**: HAProxy stats, Consul UI, service logs  

**Best for**: Internal services, high-throughput APIs, microservices communication

---

**gRPC: The high-performance backbone of the Agent Platform**

