"""
MCP Router - Central routing service for the agent platform
Handles service discovery, request routing, and load balancing
"""

import grpc
from concurrent import futures
import consul
import os
import logging
import json
import time
import socket
import uuid
from typing import Dict, List, Optional
import sys

# Add proto to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'proto'))

try:
    import agent_platform_pb2
    import agent_platform_pb2_grpc
except ImportError:
    print("Warning: Proto files not yet compiled. Run: python -m grpc_tools.protoc -I../proto --python_out=../proto --grpc_python_out=../proto ../proto/agent_platform.proto")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ServiceRegistry:
    """Manages service discovery using Consul"""
    
    def __init__(self, consul_host='localhost', consul_port=8500):
        self.consul_client = consul.Consul(host=consul_host, port=consul_port)
        self.cache = {}
        self.cache_ttl = 30  # seconds
        
    def register_service(self, service_id: str, service_name: str, address: str, port: int, tags: List[str] = None):
        """Register a service with Consul"""
        try:
            self.consul_client.agent.service.register(
                name=service_name,
                service_id=service_id,
                address=address,
                port=port,
                tags=tags or [],
                check=consul.Check.tcp(address, port, interval='10s', timeout='5s')
            )
            logger.info(f"Registered service: {service_id} at {address}:{port}")
            return True
        except Exception as e:
            logger.error(f"Failed to register service {service_id}: {e}")
            return False
    
    def discover_service(self, service_name: str) -> Optional[Dict]:
        """Discover a service by name"""
        cache_key = f"service:{service_name}"
        
        # Check cache
        if cache_key in self.cache:
            cached_time, cached_data = self.cache[cache_key]
            if time.time() - cached_time < self.cache_ttl:
                return cached_data
        
        try:
            index, services = self.consul_client.health.service(service_name, passing=True)
            if services:
                service = services[0]
                service_info = {
                    'address': service['Service']['Address'],
                    'port': service['Service']['Port'],
                    'id': service['Service']['ID'],
                    'tags': service['Service']['Tags']
                }
                self.cache[cache_key] = (time.time(), service_info)
                return service_info
        except Exception as e:
            logger.error(f"Failed to discover service {service_name}: {e}")
        
        return None
    
    def list_services(self, tag: Optional[str] = None) -> List[Dict]:
        """List all services, optionally filtered by tag"""
        try:
            services = self.consul_client.agent.services()
            result = []
            
            for service_id, service_info in services.items():
                if tag and tag not in service_info.get('Tags', []):
                    continue
                    
                result.append({
                    'id': service_id,
                    'name': service_info['Service'],
                    'address': service_info['Address'],
                    'port': service_info['Port'],
                    'tags': service_info.get('Tags', [])
                })
            
            return result
        except Exception as e:
            logger.error(f"Failed to list services: {e}")
            return []


class AgentServiceImpl(agent_platform_pb2_grpc.AgentServiceServicer):
    """Implementation of AgentService that routes to backend agents"""
    
    def __init__(self, registry: ServiceRegistry):
        self.registry = registry
        self.request_count = 0
    
    def ExecuteTask(self, request, context):
        """Route task execution to appropriate agent"""
        self.request_count += 1
        logger.info(f"Routing ExecuteTask for agent: {request.agent_id}")
        
        # Transform agent_id to Consul service name
        # e.g., "echo-agent" -> "agent-echo"
        agent_name = request.agent_id.replace('-agent', '')
        service_name = f"agent-{agent_name}"
        service = self.registry.discover_service(service_name)
        
        if not service:
            logger.error(f"Agent {request.agent_id} not found in registry")
            return agent_platform_pb2.TaskResponse(
                task_id=request.task_id,
                output="",
                success=False,
                error=f"Agent {request.agent_id} not found"
            )
        
        try:
            # Connect to the backend agent
            channel = grpc.insecure_channel(f"{service['address']}:{service['port']}")
            stub = agent_platform_pb2_grpc.AgentServiceStub(channel)
            response = stub.ExecuteTask(request)
            channel.close()
            logger.info(f"Successfully routed task {request.task_id} to {request.agent_id}")
            return response
        except Exception as e:
            logger.error(f"Failed to route to agent {request.agent_id}: {e}")
            return agent_platform_pb2.TaskResponse(
                task_id=request.task_id,
                output="",
                success=False,
                error=f"Failed to connect to agent: {str(e)}"
            )
    
    def StreamTask(self, request, context):
        """Route streaming task to appropriate agent"""
        logger.info(f"Routing StreamTask for agent: {request.agent_id}")
        
        # Transform agent_id to Consul service name
        # e.g., "echo-agent" -> "agent-echo"
        agent_name = request.agent_id.replace('-agent', '')
        service_name = f"agent-{agent_name}"
        service = self.registry.discover_service(service_name)
        
        if not service:
            logger.error(f"Agent {request.agent_id} not found")
            yield agent_platform_pb2.TaskChunk(
                task_id=request.task_id,
                content=f"Agent {request.agent_id} not found",
                is_final=True
            )
            return
        
        try:
            channel = grpc.insecure_channel(f"{service['address']}:{service['port']}")
            stub = agent_platform_pb2_grpc.AgentServiceStub(channel)
            
            for chunk in stub.StreamTask(request):
                yield chunk
            
            channel.close()
        except Exception as e:
            logger.error(f"Failed to stream from agent {request.agent_id}: {e}")
            yield agent_platform_pb2.TaskChunk(
                task_id=request.task_id,
                content=f"Error: {str(e)}",
                is_final=True
            )
    
    def GetStatus(self, request, context):
        """Get status from specific agent"""
        logger.info(f"Getting status for agent: {request.agent_id}")
        
        # Transform agent_id to Consul service name
        # e.g., "echo-agent" -> "agent-echo"
        agent_name = request.agent_id.replace('-agent', '')
        service_name = f"agent-{agent_name}"
        service = self.registry.discover_service(service_name)
        
        if not service:
            return agent_platform_pb2.StatusResponse(
                agent_id=request.agent_id,
                status="not_found",
                active_tasks=0,
                uptime_seconds=0
            )
        
        try:
            channel = grpc.insecure_channel(f"{service['address']}:{service['port']}")
            stub = agent_platform_pb2_grpc.AgentServiceStub(channel)
            response = stub.GetStatus(request)
            channel.close()
            return response
        except Exception as e:
            logger.error(f"Failed to get status from agent {request.agent_id}: {e}")
            return agent_platform_pb2.StatusResponse(
                agent_id=request.agent_id,
                status="error",
                active_tasks=0,
                uptime_seconds=0
            )
    
    def RegisterAgent(self, request, context):
        """Handle agent registration"""
        logger.info(f"Agent registration request: {request.agent_id}")
        return agent_platform_pb2.RegistrationResponse(
            success=True,
            message="Registration handled by Consul",
            service_id=request.agent_id
        )
    
    def ListAgents(self, request, context):
        """List all registered agents from Consul"""
        logger.info("Listing all registered agents")
        
        # Get all services with 'agent' tag
        services = self.registry.list_services(tag='agent')
        
        # Detailed metadata for known agents
        agent_metadata = {
            'echo-agent': {
                'name': 'Echo Agent',
                'description': 'Demonstrates agent capabilities by echoing input with processing',
                'detailed_description': (
                    "The Echo Agent is a demonstration agent that showcases the agent platform's capabilities. "
                    "It processes text input and returns an echoed version with added metadata. The agent supports "
                    "both synchronous and streaming execution modes, making it ideal for testing and learning "
                    "how agents work in the platform. It's a simple but powerful example of task execution, "
                    "state management, and result reporting."
                ),
                'how_it_works': (
                    "The Echo Agent processes tasks through these steps:\n"
                    "1. Receives a task request with input text and optional parameters\n"
                    "2. Validates the input and creates a task tracking record\n"
                    "3. Processes the input by adding a 'Echo: ' prefix and timestamp\n"
                    "4. Can stream the response word-by-word or return complete result\n"
                    "5. Returns success status with metadata including processing time\n"
                    "The agent maintains active task state and provides health status on demand."
                ),
                'return_format': (
                    "Returns a TaskResponse containing:\n"
                    "- task_id: Unique identifier for the task\n"
                    "- output: The echoed text with 'Echo: ' prefix\n"
                    "- success: Boolean indicating if task completed successfully\n"
                    "- error: Error message if task failed (empty on success)\n"
                    "- metadata: {agent_id, timestamp, processing_time_ms}\n"
                    "For streaming mode, returns TaskChunk objects with incremental content."
                ),
                'use_cases': [
                    "Testing platform connectivity and functionality",
                    "Learning how to interact with agents",
                    "Debugging agent communication issues",
                    "Benchmarking agent response times",
                    "Demonstrating streaming vs batch responses",
                    "Building example integrations and tutorials"
                ],
                'version': '1.0.0'
            }
        }
        
        agents = []
        for service in services:
            # Extract agent name from service name (e.g., "agent-echo" -> "echo")
            agent_name = service['name'].replace('agent-', '')
            agent_id = f"{agent_name}-agent"
            
            # Get metadata if available, otherwise use defaults
            metadata = agent_metadata.get(agent_id, {
                'name': agent_name.capitalize() + " Agent",
                'description': f"{agent_name.capitalize()} agent service",
                'detailed_description': f"A service agent for {agent_name} operations",
                'how_it_works': "No detailed information available",
                'return_format': "Standard TaskResponse format",
                'use_cases': ["General agent tasks"],
                'version': '1.0.0'
            })
            
            agent_info = agent_platform_pb2.AgentInfo(
                agent_id=agent_id,
                name=metadata['name'],
                description=metadata['description'],
                capabilities=service.get('tags', []),
                endpoint=f"{service['address']}:{service['port']}",
                detailed_description=metadata['detailed_description'],
                how_it_works=metadata['how_it_works'],
                return_format=metadata['return_format'],
                use_cases=metadata['use_cases'],
                version=metadata['version']
            )
            agents.append(agent_info)
        
        logger.info(f"Found {len(agents)} registered agents")
        return agent_platform_pb2.ListAgentsResponse(agents=agents)


class ToolServiceImpl(agent_platform_pb2_grpc.ToolServiceServicer):
    """Implementation of ToolService that routes to backend tools"""
    
    def __init__(self, registry: ServiceRegistry):
        self.registry = registry
    
    def ExecuteTool(self, request, context):
        """Route tool execution to appropriate tool"""
        logger.info(f"Routing ExecuteTool for tool: {request.tool_id}")
        
        # Transform tool_id to Consul service name
        # e.g., "weather-tool" -> "tool-weather"
        tool_name = request.tool_id.replace('-tool', '')
        service_name = f"tool-{tool_name}"
        service = self.registry.discover_service(service_name)
        
        if not service:
            logger.error(f"Tool {request.tool_id} not found")
            return agent_platform_pb2.ToolResponse(
                success=False,
                result="",
                error=f"Tool {request.tool_id} not found"
            )
        
        try:
            channel = grpc.insecure_channel(f"{service['address']}:{service['port']}")
            stub = agent_platform_pb2_grpc.ToolServiceStub(channel)
            response = stub.ExecuteTool(request)
            channel.close()
            logger.info(f"Successfully routed tool request to {request.tool_id}")
            return response
        except Exception as e:
            logger.error(f"Failed to route to tool {request.tool_id}: {e}")
            return agent_platform_pb2.ToolResponse(
                success=False,
                result="",
                error=f"Failed to connect to tool: {str(e)}"
            )
    
    def ListTools(self, request, context):
        """List available tools from all registered tool services"""
        logger.info("Listing all available tools")
        
        all_tools = []
        
        # Get all services with 'tool' tag
        services = self.registry.list_services(tag='tool')
        
        for service in services:
            try:
                channel = grpc.insecure_channel(f"{service['address']}:{service['port']}")
                stub = agent_platform_pb2_grpc.ToolServiceStub(channel)
                response = stub.ListTools(request)
                all_tools.extend(response.tools)
                channel.close()
            except Exception as e:
                logger.error(f"Failed to list tools from {service['id']}: {e}")
        
        return agent_platform_pb2.ListToolsResponse(tools=all_tools)
    
    def RegisterTool(self, request, context):
        """Handle tool registration"""
        logger.info(f"Tool registration request: {request.tool_id}")
        return agent_platform_pb2.RegistrationResponse(
            success=True,
            message="Registration handled by Consul",
            service_id=request.tool_id
        )


class TaskWorkerImpl(agent_platform_pb2_grpc.TaskWorkerServicer):
    """Implementation of TaskWorker that routes to backend workers"""
    
    def __init__(self, registry: ServiceRegistry):
        self.registry = registry
    
    def ProcessTask(self, request, context):
        """Route task processing to appropriate worker"""
        logger.info(f"Routing ProcessTask for worker: {request.agent_id}")
        
        # Transform worker agent_id to Consul service name
        # e.g., "itinerary-worker" -> "worker-itinerary"
        worker_name = request.agent_id.replace('-worker', '')
        service_name = f"worker-{worker_name}"
        service = self.registry.discover_service(service_name)
        
        if not service:
            logger.error(f"Worker {request.agent_id} not found")
            return agent_platform_pb2.TaskResponse(
                task_id=request.task_id,
                output="",
                success=False,
                error=f"Worker {request.agent_id} not found"
            )
        
        try:
            channel = grpc.insecure_channel(f"{service['address']}:{service['port']}")
            stub = agent_platform_pb2_grpc.TaskWorkerStub(channel)
            response = stub.ProcessTask(request)
            channel.close()
            logger.info(f"Successfully routed task to worker {request.agent_id}")
            return response
        except Exception as e:
            logger.error(f"Failed to route to worker {request.agent_id}: {e}")
            return agent_platform_pb2.TaskResponse(
                task_id=request.task_id,
                output="",
                success=False,
                error=f"Failed to connect to worker: {str(e)}"
            )
    
    def GetTaskStatus(self, request, context):
        """Get task status from worker"""
        logger.info(f"Getting task status for: {request.task_id}")
        
        # For now, return a generic response
        # In production, you'd track which worker has which task
        return agent_platform_pb2.TaskStatusResponse(
            task_id=request.task_id,
            status="unknown",
            progress="Task tracking not implemented",
            result=""
        )
    
    def ListWorkers(self, request, context):
        """List all registered workers from Consul"""
        logger.info("Listing all registered workers")
        
        # Get all services with 'worker' tag
        services = self.registry.list_services(tag='worker')
        
        # Detailed metadata for known workers
        worker_metadata = {
            'itinerary-worker': {
                'name': 'Itinerary Worker',
                'description': 'Plans detailed travel itineraries with attractions and activities',
                'detailed_description': (
                    "The Itinerary Worker is a specialized task worker that creates comprehensive travel plans "
                    "based on destination, duration, and user interests. It considers various factors like popular "
                    "attractions, local culture, seasonal events, and practical logistics to build day-by-day "
                    "itineraries. The worker can integrate with other tools (like the weather tool) to provide "
                    "context-aware recommendations and optimize the schedule based on conditions."
                ),
                'how_it_works': (
                    "The worker processes itinerary requests through these steps:\n"
                    "1. Receives task with destination, number of days, and interests\n"
                    "2. Analyzes the destination to identify key attractions and activities\n"
                    "3. Filters and prioritizes based on user interests (culture, food, history, adventure, etc.)\n"
                    "4. Optionally checks weather forecasts to optimize outdoor vs indoor activities\n"
                    "5. Organizes activities into a day-by-day schedule with timing suggestions\n"
                    "6. Includes practical information like transportation and dining recommendations\n"
                    "7. Returns a structured itinerary with descriptions and tips for each activity"
                ),
                'return_format': (
                    "Returns a TaskResponse containing:\n"
                    "- task_id: Unique identifier for the planning task\n"
                    "- output: Formatted itinerary text with daily breakdown\n"
                    "- success: Boolean indicating if planning completed successfully\n"
                    "- error: Error message if planning failed (empty on success)\n"
                    "- metadata: {worker_id, destination, days, interests, processing_time_ms}\n"
                    "The output includes day-by-day activities with timing, descriptions, and practical tips."
                ),
                'use_cases': [
                    "Vacation planning - Create complete trip itineraries",
                    "Business travel - Optimize time for meetings and activities",
                    "Event planning - Schedule multi-day conferences or retreats",
                    "Tourism apps - Provide automated travel recommendations",
                    "Travel agencies - Generate initial itinerary drafts",
                    "Personal scheduling - Plan weekend getaways and day trips"
                ],
                'version': '1.0.0',
                'parameters': [
                    agent_platform_pb2.ToolParameter(
                        name="destination",
                        type="string",
                        required=True,
                        description="City or region to visit"
                    ),
                    agent_platform_pb2.ToolParameter(
                        name="days",
                        type="integer",
                        required=True,
                        description="Number of days for the trip"
                    ),
                    agent_platform_pb2.ToolParameter(
                        name="interests",
                        type="string",
                        required=False,
                        description="Comma-separated interests (culture, food, history, adventure, nature)"
                    )
                ]
            }
        }
        
        workers = []
        for service in services:
            # Extract worker name from service name (e.g., "worker-itinerary" -> "itinerary")
            worker_name = service['name'].replace('worker-', '')
            worker_id = f"{worker_name}-worker"
            
            # Get metadata if available, otherwise use defaults
            metadata = worker_metadata.get(worker_id, {
                'name': worker_name.capitalize() + " Worker",
                'description': f"{worker_name.capitalize()} task worker",
                'detailed_description': f"A specialized worker for {worker_name} tasks",
                'how_it_works': "No detailed information available",
                'return_format': "Standard TaskResponse format",
                'use_cases': ["General worker tasks"],
                'version': '1.0.0',
                'parameters': []
            })
            
            worker_info = agent_platform_pb2.WorkerInfo(
                worker_id=worker_id,
                name=metadata['name'],
                description=metadata['description'],
                endpoint=f"{service['address']}:{service['port']}",
                tags=service.get('tags', []),
                detailed_description=metadata['detailed_description'],
                how_it_works=metadata['how_it_works'],
                return_format=metadata['return_format'],
                use_cases=metadata['use_cases'],
                version=metadata['version'],
                parameters=metadata['parameters']
            )
            workers.append(worker_info)
        
        logger.info(f"Found {len(workers)} registered workers")
        return agent_platform_pb2.ListWorkersResponse(workers=workers)


def get_container_hostname():
    """Get the container's hostname for service registration"""
    try:
        return socket.gethostname()
    except Exception as e:
        logger.error(f"Failed to get hostname: {e}")
        return f"mcp-router-{uuid.uuid4().hex[:8]}"


def get_container_ip():
    """Get the container's IP address"""
    try:
        # Get IP address by connecting to an external host (doesn't actually send data)
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception as e:
        logger.error(f"Failed to get IP address: {e}")
        return socket.gethostbyname(socket.gethostname())


def serve():
    """Start the MCP Router gRPC server"""
    # Initialize service registry
    registry = ServiceRegistry(
        consul_host=os.getenv('CONSUL_HOST', 'localhost'),
        consul_port=int(os.getenv('CONSUL_PORT', '8500'))
    )
    
    # Create gRPC server
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    
    # Add service implementations
    agent_platform_pb2_grpc.add_AgentServiceServicer_to_server(
        AgentServiceImpl(registry), server
    )
    agent_platform_pb2_grpc.add_ToolServiceServicer_to_server(
        ToolServiceImpl(registry), server
    )
    agent_platform_pb2_grpc.add_TaskWorkerServicer_to_server(
        TaskWorkerImpl(registry), server
    )
    
    port = os.getenv('MCP_ROUTER_PORT', '50051')
    server.add_insecure_port(f'[::]:{port}')
    
    # Get unique instance information
    hostname = get_container_hostname()
    container_ip = get_container_ip()
    instance_id = f"mcp-router-{hostname}"
    
    logger.info(f"MCP Router starting on {container_ip}:{port} (hostname: {hostname}, id: {instance_id})")
    server.start()
    
    # Register router instance with Consul using unique ID
    registration_success = registry.register_service(
        service_id=instance_id,
        service_name='mcp-router',
        address=hostname,  # Use hostname for Docker network resolution
        port=int(port),
        tags=['router', 'mcp', f'instance:{hostname}']
    )
    
    if registration_success:
        logger.info(f"MCP Router instance {instance_id} registered successfully with Consul")
        logger.info(f"Consul monitoring enabled at http://consul:8500/ui/dc1/services/mcp-router")
    else:
        logger.warning(f"Failed to register MCP Router instance {instance_id} with Consul")
    
    logger.info(f"MCP Router is ready - Instance: {instance_id}")
    logger.info("Services exposed: AgentService, ToolService, TaskWorker")
    logger.info("Load balancer stats available at http://localhost:8404")
    
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        logger.info("Shutting down MCP Router...")
        # Deregister from Consul on shutdown
        try:
            registry.consul_client.agent.service.deregister(instance_id)
            logger.info(f"Deregistered instance {instance_id} from Consul")
        except Exception as e:
            logger.error(f"Failed to deregister from Consul: {e}")


if __name__ == '__main__':
    logger.info('MCP Router starting...')
    serve()
