#!/usr/bin/env python3
"""
MCP Server for Agent Platform
Bridges Model Context Protocol (for Cursor/Claude) with gRPC backend
"""

import asyncio
import os
import sys
import logging
import socket
import uuid
from typing import Any

# Add proto to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'proto'))

import grpc
import consul
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Resource,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
)

# Import proto after adding to path
try:
    import agent_platform_pb2
    import agent_platform_pb2_grpc
except ImportError:
    print("Error: Proto files not found. Make sure they're compiled.", file=sys.stderr)
    sys.exit(1)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
GRPC_HOST = os.getenv('GRPC_ROUTER_HOST', 'localhost')
GRPC_PORT = os.getenv('GRPC_ROUTER_PORT', '50051')
GRPC_ADDRESS = f'{GRPC_HOST}:{GRPC_PORT}'

# Create MCP server instance
app = Server("agent-platform")


class GrpcBridge:
    """Bridge to communicate with gRPC backend"""
    
    @staticmethod
    def get_tools():
        """Query available tools from gRPC backend"""
        try:
            channel = grpc.insecure_channel(GRPC_ADDRESS)
            stub = agent_platform_pb2_grpc.ToolServiceStub(channel)
            
            request = agent_platform_pb2.ListToolsRequest()
            response = stub.ListTools(request)
            
            channel.close()
            
            # Deduplicate tools by tool_id (gRPC may return duplicates from multiple instances)
            tools_dict = {}
            for tool in response.tools:
                if tool.tool_id not in tools_dict:
                    tools_dict[tool.tool_id] = tool
            
            return list(tools_dict.values())
        except Exception as e:
            logger.error(f"Error fetching tools from gRPC: {e}")
            return []
    
    @staticmethod
    def execute_tool(tool_id: str, operation: str, parameters: dict, session_id: str = ""):
        """Execute a tool via gRPC backend"""
        try:
            channel = grpc.insecure_channel(GRPC_ADDRESS)
            stub = agent_platform_pb2_grpc.ToolServiceStub(channel)
            
            request = agent_platform_pb2.ToolRequest(
                tool_id=tool_id,
                operation=operation,
                parameters=parameters,
                session_id=session_id
            )
            response = stub.ExecuteTool(request)
            
            channel.close()
            return response
        except Exception as e:
            logger.error(f"Error executing tool via gRPC: {e}")
            raise
    
    @staticmethod
    def get_agents():
        """Query available agents from gRPC backend"""
        try:
            channel = grpc.insecure_channel(GRPC_ADDRESS)
            stub = agent_platform_pb2_grpc.AgentServiceStub(channel)
            
            request = agent_platform_pb2.ListAgentsRequest()
            response = stub.ListAgents(request)
            
            channel.close()
            
            # Deduplicate agents by agent_id (gRPC may return duplicates from multiple instances)
            agents_dict = {}
            for agent in response.agents:
                if agent.agent_id not in agents_dict:
                    agents_dict[agent.agent_id] = agent
            
            return list(agents_dict.values())
        except Exception as e:
            logger.error(f"Error fetching agents from gRPC: {e}")
            return []
    
    @staticmethod
    def get_workers():
        """Query available workers from gRPC backend"""
        try:
            channel = grpc.insecure_channel(GRPC_ADDRESS)
            stub = agent_platform_pb2_grpc.TaskWorkerStub(channel)
            
            request = agent_platform_pb2.ListWorkersRequest()
            response = stub.ListWorkers(request)
            
            channel.close()
            
            # Deduplicate workers by worker_id (gRPC may return duplicates from multiple instances)
            workers_dict = {}
            for worker in response.workers:
                if worker.worker_id not in workers_dict:
                    workers_dict[worker.worker_id] = worker
            
            return list(workers_dict.values())
        except Exception as e:
            logger.error(f"Error fetching workers from gRPC: {e}")
            return []


@app.list_resources()
async def handle_list_resources() -> list[Resource]:
    """
    List available resources (agents and workers).
    Resources in MCP represent data sources that can be read.
    """
    resources = []
    
    # Add agents as resources
    agents = GrpcBridge.get_agents()
    for agent in agents:
        resources.append(Resource(
            uri=f"agent://{agent.agent_id}",
            name=agent.name,
            description=agent.description,
            mimeType="application/json"
        ))
    
    # Add workers as resources
    workers = GrpcBridge.get_workers()
    for worker in workers:
        resources.append(Resource(
            uri=f"worker://{worker.worker_id}",
            name=worker.name,
            description=worker.description,
            mimeType="application/json"
        ))
    
    logger.info(f"Listed {len(resources)} resources")
    return resources


@app.read_resource()
async def handle_read_resource(uri: str) -> str:
    """
    Read resource information.
    Returns details about the agent or worker.
    """
    logger.info(f"Reading resource: {uri}")
    
    if uri.startswith("agent://"):
        agent_id = uri.replace("agent://", "")
        agents = GrpcBridge.get_agents()
        for agent in agents:
            if agent.agent_id == agent_id:
                return f"""# {agent.name}

**ID**: {agent.agent_id}
**Description**: {agent.description}
**Endpoint**: {agent.endpoint}
**Capabilities**: {', '.join(agent.capabilities)}

This agent can execute tasks through the Agent Platform.
"""
    
    elif uri.startswith("worker://"):
        worker_id = uri.replace("worker://", "")
        workers = GrpcBridge.get_workers()
        for worker in workers:
            if worker.worker_id == worker_id:
                return f"""# {worker.name}

**ID**: {worker.worker_id}
**Description**: {worker.description}
**Endpoint**: {worker.endpoint}
**Tags**: {', '.join(worker.tags)}

This worker processes complex tasks.
"""
    
    return f"Resource not found: {uri}"


@app.list_tools()
async def handle_list_tools() -> list[Tool]:
    """
    List available tools from the gRPC backend.
    Tools in MCP are functions that the LLM can call.
    """
    logger.info("=== list_tools called ===")
    mcp_tools = []
    
    # Add agents as callable tools
    agents = GrpcBridge.get_agents()
    logger.info(f"Found {len(agents)} agents from gRPC")
    for agent in agents:
        # Build comprehensive description
        detailed_desc = f"{agent.description}"
        
        if hasattr(agent, 'detailed_description') and agent.detailed_description:
            detailed_desc = f"{agent.detailed_description}"
        
        if hasattr(agent, 'how_it_works') and agent.how_it_works:
            detailed_desc += f"\n\n**How it works:**\n{agent.how_it_works}"
        
        if hasattr(agent, 'return_format') and agent.return_format:
            detailed_desc += f"\n\n**Return format:**\n{agent.return_format}"
        
        if hasattr(agent, 'use_cases') and agent.use_cases:
            use_cases_text = "\n".join([f"- {uc}" for uc in agent.use_cases])
            detailed_desc += f"\n\n**Use cases:**\n{use_cases_text}"
        
        if hasattr(agent, 'version') and agent.version:
            detailed_desc += f"\n\n**Version:** {agent.version}"
        
        mcp_tool = Tool(
            name=agent.agent_id,
            description=detailed_desc,
            inputSchema={
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
                    },
                    "session_id": {
                        "type": "string",
                        "description": "Optional session ID for context recovery from memory store"
                    }
                },
                "required": ["input"]
            }
        )
        mcp_tools.append(mcp_tool)
    
    # Add workers as callable tools
    workers = GrpcBridge.get_workers()
    logger.info(f"Found {len(workers)} workers from gRPC")
    for worker in workers:
        # Build comprehensive description
        detailed_desc = f"{worker.description}"
        
        if hasattr(worker, 'detailed_description') and worker.detailed_description:
            detailed_desc = f"{worker.detailed_description}"
        
        if hasattr(worker, 'how_it_works') and worker.how_it_works:
            detailed_desc += f"\n\n**How it works:**\n{worker.how_it_works}"
        
        if hasattr(worker, 'return_format') and worker.return_format:
            detailed_desc += f"\n\n**Return format:**\n{worker.return_format}"
        
        if hasattr(worker, 'use_cases') and worker.use_cases:
            use_cases_text = "\n".join([f"- {uc}" for uc in worker.use_cases])
            detailed_desc += f"\n\n**Use cases:**\n{use_cases_text}"
        
        if hasattr(worker, 'version') and worker.version:
            detailed_desc += f"\n\n**Version:** {worker.version}"
        
        # Build input schema with worker parameters if available
        properties = {
            "input": {
                "type": "string",
                "description": "Input text or data for the worker to process"
            }
        }
        
        if hasattr(worker, 'parameters') and worker.parameters:
            params_dict = {}
            for param in worker.parameters:
                params_dict[param.name] = {
                    "type": param.type,
                    "description": param.description
                }
            properties["parameters"] = {
                "type": "object",
                "properties": params_dict,
                "description": "Task-specific parameters"
            }
        else:
            properties["parameters"] = {
                "type": "object",
                "description": "Optional parameters for the worker",
                "additionalProperties": {"type": "string"}
            }
        
        # Add session_id to all worker tools
        properties["session_id"] = {
            "type": "string",
            "description": "Optional session ID for context recovery from memory store"
        }
        
        mcp_tool = Tool(
            name=worker.worker_id,
            description=detailed_desc,
            inputSchema={
                "type": "object",
                "properties": properties,
                "required": ["input"]
            }
        )
        mcp_tools.append(mcp_tool)
    
    # Add backend tools (like weather-tool)
    grpc_tools = GrpcBridge.get_tools()
    logger.info(f"Found {len(grpc_tools)} backend tools from gRPC")
    for tool in grpc_tools:
        # Build comprehensive description
        detailed_desc = f"{tool.description}"
        
        if hasattr(tool, 'detailed_description') and tool.detailed_description:
            detailed_desc = f"{tool.detailed_description}"
        
        if hasattr(tool, 'how_it_works') and tool.how_it_works:
            detailed_desc += f"\n\n**How it works:**\n{tool.how_it_works}"
        
        if hasattr(tool, 'return_format') and tool.return_format:
            detailed_desc += f"\n\n**Return format:**\n{tool.return_format}"
        
        if hasattr(tool, 'use_cases') and tool.use_cases:
            use_cases_text = "\n".join([f"- {uc}" for uc in tool.use_cases])
            detailed_desc += f"\n\n**Use cases:**\n{use_cases_text}"
        
        if hasattr(tool, 'version') and tool.version:
            detailed_desc += f"\n\n**Version:** {tool.version}"
        
        # Convert gRPC tool parameters to MCP tool schema
        properties = {}
        required = []
        
        for param in tool.parameters:
            properties[param.name] = {
                "type": param.type,
                "description": param.description
            }
            if param.required:
                required.append(param.name)
        
        # Add session_id to all backend tools
        properties["session_id"] = {
            "type": "string",
            "description": "Optional session ID for context recovery from memory store"
        }
        
        # Create MCP tool
        mcp_tool = Tool(
            name=tool.tool_id,
            description=detailed_desc,
            inputSchema={
                "type": "object",
                "properties": properties,
                "required": required
            }
        )
        mcp_tools.append(mcp_tool)
    
    logger.info(f"=== Returning {len(mcp_tools)} total tools: {[t.name for t in mcp_tools]} ===")
    return mcp_tools


@app.call_tool()
async def handle_call_tool(name: str, arguments: dict | None) -> list[TextContent | ImageContent | EmbeddedResource]:
    """
    Execute a tool via the gRPC backend.
    Supports agents, workers, and backend tools.
    """
    logger.info(f"Calling tool: {name} with arguments: {arguments}")
    
    if arguments is None:
        arguments = {}
    
    # Check if this is an agent
    agents = GrpcBridge.get_agents()
    for agent in agents:
        if agent.agent_id == name:
            return await execute_agent(name, arguments)
    
    # Check if this is a worker
    workers = GrpcBridge.get_workers()
    for worker in workers:
        if worker.worker_id == name:
            return await execute_worker(name, arguments)
    
    # Otherwise, treat as a backend tool
    operation = 'get_weather' if name == 'weather-tool' else 'execute'
    
    try:
        # Extract session_id if provided
        session_id = arguments.get("session_id", "") if arguments else ""
        
        # Convert arguments to string dict (gRPC expects map<string, string>)
        str_params = {k: str(v) for k, v in arguments.items() if k != "session_id"}
        
        # Call gRPC backend
        response = GrpcBridge.execute_tool(name, operation, str_params, session_id)
        
        if response.success:
            result_text = response.result
            if response.session_id:
                result_text += f"\n\n**Session ID**: {response.session_id}"
            
            return [TextContent(
                type="text",
                text=result_text
            )]
        else:
            return [TextContent(
                type="text",
                text=f"Error: {response.error}"
            )]
    
    except Exception as e:
        logger.error(f"Error calling tool {name}: {e}")
        return [TextContent(
            type="text",
            text=f"Error executing tool: {str(e)}"
        )]


async def execute_agent(agent_id: str, arguments: dict) -> list[TextContent]:
    """Execute an agent task via gRPC"""
    try:
        channel = grpc.insecure_channel(GRPC_ADDRESS)
        stub = agent_platform_pb2_grpc.AgentServiceStub(channel)
        
        # Extract parameters
        input_text = arguments.get("input", "")
        parameters = arguments.get("parameters", {})
        session_id = arguments.get("session_id", "")
        
        # Convert parameters to string dict if needed
        if isinstance(parameters, dict):
            str_params = {k: str(v) for k, v in parameters.items()}
        else:
            str_params = {}
        
        # Create task request
        request = agent_platform_pb2.TaskRequest(
            task_id=str(uuid.uuid4()),
            agent_id=agent_id,
            input=input_text,
            parameters=str_params,
            session_id=session_id
        )
        
        # Execute task
        response = stub.ExecuteTask(request)
        channel.close()
        
        if response.success:
            # Format response with metadata (including session_id)
            output = response.output
            if response.metadata:
                metadata_str = ", ".join([f"{k}={v}" for k, v in response.metadata.items()])
                output += f"\n\n**Metadata**: {metadata_str}"
            if response.session_id:
                output += f"\n**Session ID**: {response.session_id}"
            
            return [TextContent(
                type="text",
                text=output
            )]
        else:
            return [TextContent(
                type="text",
                text=f"Agent execution failed: {response.error}"
            )]
    
    except Exception as e:
        logger.error(f"Error executing agent {agent_id}: {e}")
        return [TextContent(
            type="text",
            text=f"Error executing agent: {str(e)}"
        )]


async def execute_worker(worker_id: str, arguments: dict) -> list[TextContent]:
    """Execute a worker task via gRPC"""
    try:
        channel = grpc.insecure_channel(GRPC_ADDRESS)
        stub = agent_platform_pb2_grpc.TaskWorkerStub(channel)
        
        # Extract parameters
        input_text = arguments.get("input", "")
        parameters = arguments.get("parameters", {})
        session_id = arguments.get("session_id", "")
        
        # Convert parameters to string dict if needed
        if isinstance(parameters, dict):
            str_params = {k: str(v) for k, v in parameters.items()}
        else:
            str_params = {}
        
        # Create task request
        request = agent_platform_pb2.TaskRequest(
            task_id=str(uuid.uuid4()),
            agent_id=worker_id,  # Workers use same request format
            input=input_text,
            parameters=str_params,
            session_id=session_id
        )
        
        # Execute task
        response = stub.ProcessTask(request)
        channel.close()
        
        if response.success:
            # Format response with metadata (including session_id)
            output = response.output
            if response.metadata:
                metadata_str = ", ".join([f"{k}={v}" for k, v in response.metadata.items()])
                output += f"\n\n**Metadata**: {metadata_str}"
            if response.session_id:
                output += f"\n**Session ID**: {response.session_id}"
            
            return [TextContent(
                type="text",
                text=output
            )]
        else:
            return [TextContent(
                type="text",
                text=f"Worker execution failed: {response.error}"
            )]
    
    except Exception as e:
        logger.error(f"Error executing worker {worker_id}: {e}")
        return [TextContent(
            type="text",
            text=f"Error executing worker: {str(e)}"
        )]


async def main_stdio():
    """Run MCP server with stdio transport (for local Cursor)"""
    logger.info(f"Starting MCP Server (stdio)")
    logger.info(f"Connecting to gRPC backend at {GRPC_ADDRESS}")
    
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="agent-platform",
                server_version="1.0.0",
                capabilities=app.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


def register_with_consul(port: int):
    """Register MCP server instance with Consul"""
    try:
        # Get configuration
        consul_host = os.getenv('CONSUL_HOST', 'consul')
        consul_port = int(os.getenv('CONSUL_PORT', '8500'))
        
        # Get hostname for service registration
        hostname = socket.gethostname()
        instance_id = f"mcp-server-{hostname}"
        
        # Create Consul client
        consul_client = consul.Consul(host=consul_host, port=consul_port)
        
        # Register service
        consul_client.agent.service.register(
            name='mcp-server',
            service_id=instance_id,
            address=hostname,
            port=port,
            tags=['mcp', 'cursor', 'http', 'sse', f'instance:{hostname}'],
            check=consul.Check.http(f"http://{hostname}:{port}/sse", interval='10s', timeout='5s')
        )
        
        logger.info(f"MCP Server instance {instance_id} registered with Consul at {consul_host}:{consul_port}")
        logger.info(f"Service: mcp-server, Address: {hostname}:{port}")
        return True
    except Exception as e:
        logger.warning(f"Failed to register with Consul: {e}")
        logger.warning("MCP Server will continue without Consul registration")
        return False


async def main_sse():
    """Run MCP server with SSE transport (for remote Cursor)"""
    from mcp.server.sse import SseServerTransport
    from starlette.applications import Starlette
    from starlette.routing import Route
    from starlette.responses import Response
    import uvicorn
    
    logger.info(f"Starting MCP Server (SSE)")
    logger.info(f"Connecting to gRPC backend at {GRPC_ADDRESS}")
    
    port = int(os.getenv('MCP_PORT', '3000'))
    
    # Register with Consul
    register_with_consul(port)
    
    sse = SseServerTransport("/messages")
    
    # Monkey-patch SSE to handle session IDs without hyphens
    original_get_session = sse._sessions.get if hasattr(sse, '_sessions') else None
    
    def normalize_session_id(session_id: str) -> str:
        """Normalize session ID by adding hyphens if missing"""
        if session_id and len(session_id) == 32 and "-" not in session_id:
            return f"{session_id[:8]}-{session_id[8:12]}-{session_id[12:16]}-{session_id[16:20]}-{session_id[20:]}"
        return session_id
    
    # Wrap the sessions dict to normalize lookups
    if hasattr(sse, '_sessions'):
        class SessionDictWrapper(dict):
            def __getitem__(self, key):
                normalized_key = normalize_session_id(str(key))
                logger.info(f"Session lookup: {key} -> {normalized_key}")
                return super().__getitem__(normalized_key)
            
            def get(self, key, default=None):
                normalized_key = normalize_session_id(str(key))
                logger.info(f"Session get: {key} -> {normalized_key}")
                return super().get(normalized_key, default)
            
            def __contains__(self, key):
                normalized_key = normalize_session_id(str(key))
                return super().__contains__(normalized_key)
        
        # Replace sessions dict with wrapper
        original_sessions = sse._sessions
        wrapped_sessions = SessionDictWrapper(original_sessions)
        sse._sessions = wrapped_sessions
    
    async def handle_sse(request):
        logger.info(f"=== GET /sse called ===")
        async with sse.connect_sse(
            request.scope,
            request.receive,
            request._send,
        ) as streams:
            await app.run(
                streams[0],
                streams[1],
                InitializationOptions(
                    server_name="agent-platform",
                    server_version="1.0.0",
                    capabilities=app.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={},
                    ),
                ),
            )
        return Response()
    
    async def handle_messages(request):
        session_id = request.query_params.get("session_id", "")
        logger.info(f"=== POST /messages called with session_id: {session_id} ===")
        
        # Fix session ID format: add hyphens if missing (UUID format)
        if session_id and len(session_id) == 32 and "-" not in session_id:
            # Convert: 9efc45a23fb04ef0911c620fdc594971 -> 9efc45a2-3fb0-4ef0-911c-620fdc594971
            session_id_formatted = f"{session_id[:8]}-{session_id[8:12]}-{session_id[12:16]}-{session_id[16:20]}-{session_id[20:]}"
            logger.info(f"Reformatted session ID: {session_id} -> {session_id_formatted}")
            
            # Update query params with formatted session ID
            from starlette.datastructures import QueryParams
            new_query_params = QueryParams({**request.query_params, "session_id": session_id_formatted})
            request.scope["query_string"] = str(new_query_params).encode()
        
        try:
            await sse.handle_post_message(request.scope, request.receive, request._send)
            return Response()
        except Exception as e:
            logger.error(f"Error handling POST /messages: {e}")
            raise
    
    starlette_app = Starlette(
        routes=[
            Route("/sse", endpoint=handle_sse),
            Route("/messages", endpoint=handle_messages, methods=["POST"]),
        ],
    )
    
    logger.info(f"MCP Server listening on http://0.0.0.0:{port}")
    logger.info(f"SSE endpoint: http://localhost:{port}/sse")
    
    config = uvicorn.Config(starlette_app, host="0.0.0.0", port=port, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == "__main__":
    # Check if we should use SSE or stdio
    transport = os.getenv('MCP_TRANSPORT', 'stdio').lower()
    
    if transport == 'sse':
        asyncio.run(main_sse())
    else:
        asyncio.run(main_stdio())

