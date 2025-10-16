"""
Echo Agent - A simple agent that echoes back input with processing
Demonstrates basic agent implementation with gRPC
"""

import grpc
from concurrent import futures
import os
import logging
import time
import sys
import uuid

# Add proto to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'proto'))

try:
    import agent_platform_pb2
    import agent_platform_pb2_grpc
except ImportError:
    print("Warning: Proto files not yet compiled")
    agent_platform_pb2 = None
    agent_platform_pb2_grpc = None

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EchoAgentService:
    """Echo Agent Service Implementation"""
    
    def __init__(self):
        self.agent_id = "echo-agent"
        self.start_time = time.time()
        self.task_count = 0
        self.active_tasks = {}
        
    def ExecuteTask(self, request, context):
        """Execute a task - echo back the input with processing"""
        logger.info(f"Received task: {request.task_id} - Input: {request.input} - Session: {request.session_id}")
        
        self.task_count += 1
        self.active_tasks[request.task_id] = time.time()
        
        try:
            # Process the input
            output = f"Echo Agent Response: {request.input}"
            
            # Add metadata
            metadata = {
                'agent_id': self.agent_id,
                'processed_at': str(time.time()),
                'task_number': str(self.task_count)
            }
            
            # Add session_id to metadata if provided
            if request.session_id:
                metadata['session_id'] = request.session_id
            
            # Add parameters to output if provided
            if request.parameters:
                params_str = ", ".join([f"{k}={v}" for k, v in request.parameters.items()])
                output += f" | Parameters: {params_str}"
            
            logger.info(f"Task {request.task_id} completed successfully")
            
            # Clean up
            del self.active_tasks[request.task_id]
            
            return agent_platform_pb2.TaskResponse(
                task_id=request.task_id,
                output=output,
                success=True,
                error="",
                metadata=metadata,
                session_id=request.session_id
            )
            
        except Exception as e:
            logger.error(f"Task {request.task_id} failed: {e}")
            if request.task_id in self.active_tasks:
                del self.active_tasks[request.task_id]
            
            return agent_platform_pb2.TaskResponse(
                task_id=request.task_id,
                output="",
                success=False,
                error=str(e),
                metadata={'agent_id': self.agent_id},
                session_id=request.session_id
            )
    
    def StreamTask(self, request, context):
        """Stream task execution - yields chunks of response"""
        logger.info(f"Streaming task: {request.task_id} - Session: {request.session_id}")
        
        try:
            # Split input into words and stream each
            words = request.input.split()
            
            for i, word in enumerate(words):
                yield agent_platform_pb2.TaskChunk(
                    task_id=request.task_id,
                    content=word,
                    is_final=False,
                    session_id=request.session_id
                )
                time.sleep(0.1)  # Simulate processing
            
            # Send final chunk
            yield agent_platform_pb2.TaskChunk(
                task_id=request.task_id,
                content="[COMPLETE]",
                is_final=True,
                session_id=request.session_id
            )
            
        except Exception as e:
            logger.error(f"Streaming task {request.task_id} failed: {e}")
            yield agent_platform_pb2.TaskChunk(
                task_id=request.task_id,
                content=f"Error: {str(e)}",
                is_final=True,
                session_id=request.session_id
            )
    
    def GetStatus(self, request, context):
        """Get agent status"""
        uptime = int(time.time() - self.start_time)
        
        return agent_platform_pb2.StatusResponse(
            agent_id=self.agent_id,
            status="healthy",
            active_tasks=len(self.active_tasks),
            uptime_seconds=uptime
        )
    
    def RegisterAgent(self, request, context):
        """Register agent (placeholder for router registration)"""
        logger.info(f"Registration request for agent: {request.agent_id}")
        
        return agent_platform_pb2.RegistrationResponse(
            success=True,
            message="Agent registered successfully",
            service_id=request.agent_id
        )
    
    def ListAgents(self, request, context):
        """List available agents (returns self)"""
        logger.info("ListAgents called")
        
        agent_info = agent_platform_pb2.AgentInfo(
            agent_id=self.agent_id,
            name='Echo Agent',
            description='Demonstrates agent capabilities by echoing input with processing',
            capabilities=['agent', 'echo', 'text-processing'],
            endpoint='echo-agent:50052'
        )
        
        return agent_platform_pb2.ListAgentsResponse(agents=[agent_info])


def serve():
    """Start the Echo Agent gRPC server"""
    if not agent_platform_pb2_grpc:
        logger.error("Proto files not compiled. Please run proto compilation first.")
        return
    
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    
    # Add Echo Agent service
    echo_service = EchoAgentService()
    agent_platform_pb2_grpc.add_AgentServiceServicer_to_server(echo_service, server)
    
    port = os.getenv('AGENT_PORT', '50052')
    server.add_insecure_port(f'[::]:{port}')
    
    logger.info(f"Echo Agent starting on port {port}")
    server.start()
    
    # Register with Consul (if available)
    try:
        import consul
        import socket
        
        # Get container hostname for unique service ID
        hostname = socket.gethostname()
        service_id = f'echo-agent-{hostname}'
        
        consul_client = consul.Consul(
            host=os.getenv('CONSUL_HOST', 'localhost'),
            port=int(os.getenv('CONSUL_PORT', '8500'))
        )
        
        consul_client.agent.service.register(
            name='agent-echo',  # Service name (same for all instances)
            service_id=service_id,  # Unique ID per instance
            address=hostname,  # Use container hostname
            port=int(port),
            tags=['agent', 'echo', 'text-processing'],
            check=consul.Check.tcp(hostname, int(port), interval='10s')
        )
        logger.info(f"Echo Agent registered with Consul as {service_id}")
    except Exception as e:
        logger.warning(f"Could not register with Consul: {e}")
    
    logger.info("Echo Agent is ready")
    
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        logger.info("Shutting down Echo Agent")
        server.stop(0)


if __name__ == '__main__':
    logger.info('Echo Agent starting...')
    serve()