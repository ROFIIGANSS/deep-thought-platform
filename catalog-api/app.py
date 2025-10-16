#!/usr/bin/env python3
"""
Catalog API - Dynamic catalog of agents, tools, and workers
Queries Consul for service discovery and gRPC for details
"""

import os
import sys
import logging
import socket
import atexit
from typing import List, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import consul
import grpc

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add proto directory to path so we can import the pb2 files directly
proto_path = os.path.join(os.path.dirname(__file__), 'proto')
sys.path.insert(0, proto_path)

try:
    import agent_platform_pb2
    import agent_platform_pb2_grpc
except ImportError as e:
    logger.error(f"Error importing proto files: {e}")
    logger.error(f"Proto path: {proto_path}")
    logger.error(f"Proto path exists: {os.path.exists(proto_path)}")
    if os.path.exists(proto_path):
        logger.error(f"Proto contents: {os.listdir(proto_path)}")
    logger.error(f"Python path: {sys.path}")
    print("Error: Proto files not found. Make sure they're compiled.", file=sys.stderr)
    sys.exit(1)

app = FastAPI(title="Agent Platform Catalog API", version="1.0.0")

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
CONSUL_HOST = os.getenv('CONSUL_HOST', 'consul')
CONSUL_PORT = int(os.getenv('CONSUL_PORT', '8500'))
GRPC_ROUTER_HOST = os.getenv('GRPC_ROUTER_HOST', 'haproxy')
GRPC_ROUTER_PORT = int(os.getenv('GRPC_ROUTER_PORT', '50051'))
CATALOG_API_PORT = int(os.getenv('CATALOG_API_PORT', '8000'))
CATALOG_API_HOST = os.getenv('CATALOG_API_HOST', socket.gethostname())

# Consul service registration
consul_client = None
service_id = None


# Models
class ParameterSchema(BaseModel):
    name: str
    type: str
    required: bool
    description: str


class HealthInfo(BaseModel):
    healthy_instances: int
    unhealthy_instances: int
    total_instances: int
    status: str  # "healthy", "degraded", "unhealthy", "down"


class AgentInfo(BaseModel):
    id: str
    name: str
    description: str
    capabilities: List[str]
    endpoint: str
    instances: int
    status: str
    health: HealthInfo
    example_response: Dict[str, Any] = {}
    detailed_description: str = ""
    how_it_works: str = ""
    return_format: str = ""
    use_cases: List[str] = []
    version: str = "1.0.0"


class ToolInfo(BaseModel):
    id: str
    name: str
    description: str
    endpoint: str
    parameters: List[ParameterSchema]
    instances: int
    status: str
    health: HealthInfo
    example_response: Dict[str, Any] = {}
    detailed_description: str = ""
    how_it_works: str = ""
    return_format: str = ""
    use_cases: List[str] = []
    version: str = "1.0.0"


class WorkerInfo(BaseModel):
    id: str
    name: str
    description: str
    endpoint: str
    tags: List[str]
    instances: int
    status: str
    health: HealthInfo
    example_response: Dict[str, Any] = {}
    detailed_description: str = ""
    how_it_works: str = ""
    return_format: str = ""
    use_cases: List[str] = []
    version: str = "1.0.0"
    parameters: List[ParameterSchema] = []


class CatalogResponse(BaseModel):
    agents: List[AgentInfo]
    tools: List[ToolInfo]
    workers: List[WorkerInfo]
    total_services: int


def get_consul_client():
    """Get Consul client"""
    try:
        return consul.Consul(host=CONSUL_HOST, port=CONSUL_PORT)
    except Exception as e:
        logger.error(f"Failed to connect to Consul: {e}")
        return None


def get_grpc_stub():
    """Get gRPC stub for router"""
    try:
        channel = grpc.insecure_channel(f'{GRPC_ROUTER_HOST}:{GRPC_ROUTER_PORT}')
        return channel
    except Exception as e:
        logger.error(f"Failed to connect to gRPC router: {e}")
        return None


def get_service_health(consul_client, service_name: str) -> HealthInfo:
    """
    Get health information for a service from Consul.
    Returns consolidated health data for all instances.
    """
    try:
        # Query all instances (not just passing ones)
        _, all_services = consul_client.health.service(service_name)
        
        healthy = 0
        unhealthy = 0
        
        for service in all_services:
            # Check the aggregated health status
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
    except Exception as e:
        logger.error(f"Error getting health for service {service_name}: {e}")
        return HealthInfo(
            healthy_instances=0,
            unhealthy_instances=0,
            total_instances=0,
            status="unknown"
        )


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Agent Platform Catalog API",
        "version": "1.0.0",
        "endpoints": {
            "catalog": "/api/catalog",
            "agents": "/api/agents",
            "tools": "/api/tools",
            "workers": "/api/workers",
            "health": "/health"
        }
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    consul_client = get_consul_client()
    consul_healthy = consul_client is not None
    
    grpc_channel = get_grpc_stub()
    grpc_healthy = grpc_channel is not None
    if grpc_channel:
        grpc_channel.close()
    
    return {
        "status": "healthy" if (consul_healthy and grpc_healthy) else "degraded",
        "consul": "up" if consul_healthy else "down",
        "grpc_router": "up" if grpc_healthy else "down"
    }


@app.get("/api/agents", response_model=List[AgentInfo])
async def get_agents():
    """Get all registered agents with health information"""
    consul_client = get_consul_client()
    if not consul_client:
        raise HTTPException(status_code=503, detail="Consul unavailable")
    
    try:
        # Get health info for echo agent service
        health_info = get_service_health(consul_client, 'agent-echo')
        
        # Get agent details from gRPC (try healthy instances first)
        channel = get_grpc_stub()
        if not channel:
            raise HTTPException(status_code=503, detail="gRPC router unavailable")
        
        stub = agent_platform_pb2_grpc.AgentServiceStub(channel)
        request = agent_platform_pb2.ListAgentsRequest()
        response = stub.ListAgents(request)
        channel.close()
        
        # Use a dictionary to deduplicate agents by agent_id
        # (gRPC may return duplicate entries from multiple instances)
        agents_dict = {}
        
        for agent in response.agents:
            # Skip if we already have this agent
            if agent.agent_id in agents_dict:
                continue
                
            # Create example response based on agent type
            example_response = {
                "task_id": "task-abc123",
                "status": "completed",
                "result": "Echo: your input text",
                "metadata": {
                    "agent_id": agent.agent_id,
                    "processing_time_ms": 150,
                    "timestamp": "2025-10-15T12:00:00Z",
                    "session_id": "550e8400-e29b-41d4-a716-446655440000"
                },
                "session_id": "550e8400-e29b-41d4-a716-446655440000"
            }
            
            agents_dict[agent.agent_id] = AgentInfo(
                id=agent.agent_id,
                name=agent.name,
                description=agent.description,
                capabilities=list(agent.capabilities),
                endpoint=agent.endpoint,
                instances=health_info.total_instances,
                status=health_info.status,
                health=health_info,
                example_response=example_response,
                detailed_description=agent.detailed_description if hasattr(agent, 'detailed_description') else "",
                how_it_works=agent.how_it_works if hasattr(agent, 'how_it_works') else "",
                return_format=agent.return_format if hasattr(agent, 'return_format') else "",
                use_cases=list(agent.use_cases) if hasattr(agent, 'use_cases') else [],
                version=agent.version if hasattr(agent, 'version') else "1.0.0"
            )
        
        return list(agents_dict.values())
    
    except Exception as e:
        logger.error(f"Error fetching agents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/tools", response_model=List[ToolInfo])
async def get_tools():
    """Get all registered tools with health information"""
    consul_client = get_consul_client()
    if not consul_client:
        raise HTTPException(status_code=503, detail="Consul unavailable")
    
    try:
        # Get health info for weather tool service
        health_info = get_service_health(consul_client, 'tool-weather')
        
        # Get tool details from gRPC
        channel = get_grpc_stub()
        if not channel:
            raise HTTPException(status_code=503, detail="gRPC router unavailable")
        
        stub = agent_platform_pb2_grpc.ToolServiceStub(channel)
        request = agent_platform_pb2.ListToolsRequest()
        response = stub.ListTools(request)
        channel.close()
        
        # Use a dictionary to deduplicate tools by tool_id
        # (gRPC may return duplicate entries from multiple instances)
        tools_dict = {}
        
        for tool in response.tools:
            # Skip if we already have this tool
            if tool.tool_id in tools_dict:
                continue
                
            parameters = []
            for param in tool.parameters:
                parameters.append(ParameterSchema(
                    name=param.name,
                    type=param.type,
                    required=param.required,
                    description=param.description
                ))
            
            # Add session_id as a common parameter for all tools
            parameters.append(ParameterSchema(
                name="session_id",
                type="string",
                required=False,
                description="Optional session ID for context recovery from memory store"
            ))
            
            # Create example response based on tool type
            if tool.tool_id == 'weather-tool':
                example_response = {
                    "location": "San Francisco",
                    "current": {
                        "temperature": 18,
                        "condition": "Partly Cloudy",
                        "humidity": 65,
                        "wind_speed": 12
                    },
                    "forecast": [
                        {"day": "Today", "high": 20, "low": 15, "condition": "Sunny"},
                        {"day": "Tomorrow", "high": 19, "low": 14, "condition": "Cloudy"},
                        {"day": "Day 3", "high": 21, "low": 16, "condition": "Partly Cloudy"}
                    ],
                    "timestamp": "2025-10-15T12:00:00Z",
                    "session_id": "550e8400-e29b-41d4-a716-446655440000"
                }
            else:
                example_response = {
                    "result": "Tool execution result",
                    "status": "success",
                    "session_id": "550e8400-e29b-41d4-a716-446655440000"
                }
            
            tools_dict[tool.tool_id] = ToolInfo(
                id=tool.tool_id,
                name=tool.name,
                description=tool.description,
                endpoint=tool.endpoint,
                parameters=parameters,
                instances=health_info.total_instances,
                status=health_info.status,
                health=health_info,
                example_response=example_response,
                detailed_description=tool.detailed_description if hasattr(tool, 'detailed_description') else "",
                how_it_works=tool.how_it_works if hasattr(tool, 'how_it_works') else "",
                return_format=tool.return_format if hasattr(tool, 'return_format') else "",
                use_cases=list(tool.use_cases) if hasattr(tool, 'use_cases') else [],
                version=tool.version if hasattr(tool, 'version') else "1.0.0"
            )
        
        return list(tools_dict.values())
    
    except Exception as e:
        logger.error(f"Error fetching tools: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/workers", response_model=List[WorkerInfo])
async def get_workers():
    """Get all registered workers with health information"""
    consul_client = get_consul_client()
    if not consul_client:
        raise HTTPException(status_code=503, detail="Consul unavailable")
    
    try:
        # Get health info for itinerary worker service
        health_info = get_service_health(consul_client, 'worker-itinerary')
        
        # Get worker details from gRPC
        channel = get_grpc_stub()
        if not channel:
            raise HTTPException(status_code=503, detail="gRPC router unavailable")
        
        stub = agent_platform_pb2_grpc.TaskWorkerStub(channel)
        request = agent_platform_pb2.ListWorkersRequest()
        response = stub.ListWorkers(request)
        channel.close()
        
        # Use a dictionary to deduplicate workers by worker_id
        # (gRPC may return duplicate entries from multiple instances)
        workers_dict = {}
        
        for worker in response.workers:
            # Skip if we already have this worker
            if worker.worker_id in workers_dict:
                continue
                
            # Create example response based on worker type
            if worker.worker_id == 'itinerary-worker':
                example_response = {
                    "task_id": "itinerary-xyz789",
                    "status": "completed",
                    "itinerary": {
                        "destination": "Paris",
                        "duration_days": 5,
                        "activities": [
                            {"day": 1, "activity": "Visit Eiffel Tower", "time": "10:00 AM"},
                            {"day": 2, "activity": "Louvre Museum", "time": "09:00 AM"},
                            {"day": 3, "activity": "Notre-Dame Cathedral", "time": "11:00 AM"}
                        ],
                        "estimated_cost": "$2500"
                    },
                    "metadata": {
                        "worker_id": worker.worker_id,
                        "processing_time_ms": 350,
                        "timestamp": "2025-10-15T12:00:00Z"
                    },
                    "session_id": "550e8400-e29b-41d4-a716-446655440000"
                }
            else:
                example_response = {
                    "task_id": "task-xyz789",
                    "status": "completed",
                    "result": "Task completed successfully",
                    "timestamp": "2025-10-15T12:00:00Z",
                    "session_id": "550e8400-e29b-41d4-a716-446655440000"
                }
            
            # Extract parameters if available
            worker_parameters = []
            if hasattr(worker, 'parameters'):
                for param in worker.parameters:
                    worker_parameters.append(ParameterSchema(
                        name=param.name,
                        type=param.type,
                        required=param.required,
                        description=param.description
                    ))
            
            # Add session_id as a common parameter for all workers
            worker_parameters.append(ParameterSchema(
                name="session_id",
                type="string",
                required=False,
                description="Optional session ID for context recovery from memory store"
            ))
            
            workers_dict[worker.worker_id] = WorkerInfo(
                id=worker.worker_id,
                name=worker.name,
                description=worker.description,
                endpoint=worker.endpoint,
                tags=list(worker.tags),
                instances=health_info.total_instances,
                status=health_info.status,
                health=health_info,
                example_response=example_response,
                detailed_description=worker.detailed_description if hasattr(worker, 'detailed_description') else "",
                how_it_works=worker.how_it_works if hasattr(worker, 'how_it_works') else "",
                return_format=worker.return_format if hasattr(worker, 'return_format') else "",
                use_cases=list(worker.use_cases) if hasattr(worker, 'use_cases') else [],
                version=worker.version if hasattr(worker, 'version') else "1.0.0",
                parameters=worker_parameters
            )
        
        return list(workers_dict.values())
    
    except Exception as e:
        logger.error(f"Error fetching workers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/catalog", response_model=CatalogResponse)
async def get_catalog():
    """Get complete catalog of all agents, tools, and workers"""
    try:
        agents = await get_agents()
        tools = await get_tools()
        workers = await get_workers()
        
        return CatalogResponse(
            agents=agents,
            tools=tools,
            workers=workers,
            total_services=len(agents) + len(tools) + len(workers)
        )
    
    except Exception as e:
        logger.error(f"Error fetching catalog: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def register_with_consul():
    """Register service with Consul"""
    global consul_client, service_id
    
    try:
        consul_client = consul.Consul(host=CONSUL_HOST, port=CONSUL_PORT)
        service_id = f"catalog-api-{CATALOG_API_HOST}-{CATALOG_API_PORT}"
        
        # Register service
        consul_client.agent.service.register(
            name="catalog-api",
            service_id=service_id,
            address=CATALOG_API_HOST,
            port=CATALOG_API_PORT,
            tags=["catalog", "api", "http"],
            check=consul.Check.http(
                f"http://{CATALOG_API_HOST}:{CATALOG_API_PORT}/health",
                interval="10s",
                timeout="5s",
                deregister="30s"
            )
        )
        logger.info(f"Registered with Consul: {service_id} at {CATALOG_API_HOST}:{CATALOG_API_PORT}")
    except Exception as e:
        logger.error(f"Failed to register with Consul: {e}")


def deregister_from_consul():
    """Deregister service from Consul"""
    global consul_client, service_id
    
    if consul_client and service_id:
        try:
            consul_client.agent.service.deregister(service_id)
            logger.info(f"Deregistered from Consul: {service_id}")
        except Exception as e:
            logger.error(f"Failed to deregister from Consul: {e}")


@app.on_event("startup")
async def startup_event():
    """Register with Consul on startup"""
    register_with_consul()
    # Register cleanup on exit
    atexit.register(deregister_from_consul)


@app.on_event("shutdown")
async def shutdown_event():
    """Deregister from Consul on shutdown"""
    deregister_from_consul()


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv('CATALOG_API_PORT', '8000'))
    uvicorn.run(app, host="0.0.0.0", port=port)

