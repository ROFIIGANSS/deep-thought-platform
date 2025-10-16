"""
Itinerary Task Worker - Plans travel itineraries
Demonstrates advanced task worker with AI agent capabilities
"""

import grpc
from concurrent import futures
import os
import logging
import json
import sys
from datetime import datetime, timedelta
import random

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


class ItineraryPlanner:
    """AI-powered itinerary planning logic"""
    
    def __init__(self):
        # Sample data for demonstration
        self.destinations = {
            'paris': {
                'activities': ['Eiffel Tower', 'Louvre Museum', 'Notre-Dame', 'Champs-Élysées', 'Montmartre'],
                'restaurants': ['Le Jules Verne', 'L\'Ami Jean', 'Septime', 'Le Comptoir du Relais'],
                'hotels': ['Hotel Plaza Athénée', 'Le Meurice', 'Hotel de Crillon']
            },
            'tokyo': {
                'activities': ['Senso-ji Temple', 'Tokyo Tower', 'Shibuya Crossing', 'Imperial Palace', 'Tsukiji Market'],
                'restaurants': ['Sukiyabashi Jiro', 'Narisawa', 'Sushi Saito', 'Den'],
                'hotels': ['The Peninsula Tokyo', 'Aman Tokyo', 'Park Hyatt Tokyo']
            },
            'new york': {
                'activities': ['Statue of Liberty', 'Central Park', 'Times Square', 'Brooklyn Bridge', 'Metropolitan Museum'],
                'restaurants': ['Eleven Madison Park', 'Le Bernardin', 'Per Se', 'Gramercy Tavern'],
                'hotels': ['The Plaza', 'The St. Regis', 'Four Seasons']
            },
            'london': {
                'activities': ['Big Ben', 'Tower of London', 'British Museum', 'London Eye', 'Buckingham Palace'],
                'restaurants': ['The Ledbury', 'Restaurant Gordon Ramsay', 'Sketch', 'Dishoom'],
                'hotels': ['The Savoy', 'Claridge\'s', 'The Ritz London']
            }
        }
    
    def plan_itinerary(self, destination: str, days: int, interests: list = None) -> dict:
        """Plan an itinerary for a destination"""
        destination_lower = destination.lower()
        
        if destination_lower not in self.destinations:
            return {
                'error': f'Destination {destination} not found in our database'
            }
        
        dest_data = self.destinations[destination_lower]
        interests = interests or ['sightseeing', 'food', 'culture']
        
        # Build daily itinerary
        itinerary = {
            'destination': destination,
            'total_days': days,
            'interests': interests,
            'daily_schedule': []
        }
        
        activities = dest_data['activities'].copy()
        restaurants = dest_data['restaurants'].copy()
        
        for day in range(1, days + 1):
            daily_plan = {
                'day': day,
                'date': (datetime.now() + timedelta(days=day-1)).strftime('%Y-%m-%d'),
                'morning': None,
                'afternoon': None,
                'evening': None
            }
            
            # Morning activity
            if activities:
                daily_plan['morning'] = {
                    'activity': activities.pop(0),
                    'time': '09:00 - 12:00',
                    'type': 'sightseeing'
                }
            
            # Afternoon activity
            if activities:
                daily_plan['afternoon'] = {
                    'activity': activities.pop(0),
                    'time': '14:00 - 17:00',
                    'type': 'culture'
                }
            
            # Evening dining
            if restaurants:
                daily_plan['evening'] = {
                    'activity': f'Dinner at {restaurants.pop(0)}',
                    'time': '19:00 - 21:00',
                    'type': 'dining'
                }
            
            itinerary['daily_schedule'].append(daily_plan)
        
        # Add hotel recommendation
        itinerary['accommodation'] = {
            'hotel': random.choice(dest_data['hotels']),
            'check_in': datetime.now().strftime('%Y-%m-%d'),
            'check_out': (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d')
        }
        
        return itinerary
    
    def optimize_route(self, itinerary: dict) -> dict:
        """Optimize the route for an itinerary"""
        # Simplified optimization - in reality, this would use more sophisticated algorithms
        itinerary['optimized'] = True
        itinerary['optimization_notes'] = [
            'Activities grouped by proximity',
            'Travel time minimized',
            'Peak hours avoided for popular attractions'
        ]
        return itinerary
    
    def get_weather_context(self, destination: str) -> dict:
        """Get weather context for planning (mock implementation)"""
        # In a real implementation, this would call the weather tool
        return {
            'destination': destination,
            'forecast': 'Partly cloudy with temperatures around 72°F',
            'recommendations': ['Bring an umbrella', 'Light jacket recommended']
        }


class ItineraryTaskWorker:
    """Task Worker Service Implementation"""
    
    def __init__(self):
        self.worker_id = "itinerary-worker"
        self.planner = ItineraryPlanner()
        self.task_status = {}
    
    def ProcessTask(self, request, context):
        """Process an itinerary planning task"""
        logger.info(f"Processing task: {request.task_id} - Session: {request.session_id}")
        
        self.task_status[request.task_id] = 'processing'
        
        try:
            # Parse input
            params = dict(request.parameters)
            destination = params.get('destination', '')
            days = int(params.get('days', 3))
            interests = params.get('interests', '').split(',') if params.get('interests') else None
            
            if not destination:
                raise ValueError("Destination parameter is required")
            
            # Plan itinerary
            logger.info(f"Planning itinerary for {destination} ({days} days)")
            itinerary = self.planner.plan_itinerary(destination, days, interests)
            
            # Check for errors
            if 'error' in itinerary:
                raise ValueError(itinerary['error'])
            
            # Optimize route
            itinerary = self.planner.optimize_route(itinerary)
            
            # Get weather context
            weather = self.planner.get_weather_context(destination)
            itinerary['weather_info'] = weather
            
            # Format output
            output = json.dumps(itinerary, indent=2)
            
            self.task_status[request.task_id] = 'completed'
            logger.info(f"Task {request.task_id} completed successfully")
            
            # Build metadata
            metadata = {
                'worker_id': self.worker_id,
                'destination': destination,
                'days': str(days)
            }
            
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
            self.task_status[request.task_id] = 'failed'
            
            return agent_platform_pb2.TaskResponse(
                task_id=request.task_id,
                output="",
                success=False,
                error=str(e),
                metadata={'worker_id': self.worker_id},
                session_id=request.session_id
            )
    
    def GetTaskStatus(self, request, context):
        """Get task status"""
        task_id = request.task_id
        status = self.task_status.get(task_id, 'unknown')
        
        return agent_platform_pb2.TaskStatusResponse(
            task_id=task_id,
            status=status,
            progress='100%' if status == 'completed' else '50%' if status == 'processing' else '0%',
            result='Task completed' if status == 'completed' else ''
        )
    
    def ListWorkers(self, request, context):
        """List available workers (returns self)"""
        logger.info("ListWorkers called")
        
        worker_info = agent_platform_pb2.WorkerInfo(
            worker_id=self.worker_id,
            name='Itinerary Worker',
            description='Plans detailed travel itineraries with attractions and activities',
            endpoint='itinerary-worker:50054',
            tags=['worker', 'itinerary', 'planning', 'ai']
        )
        
        return agent_platform_pb2.ListWorkersResponse(workers=[worker_info])


def serve():
    """Start the Itinerary Task Worker gRPC server"""
    if not agent_platform_pb2_grpc:
        logger.error("Proto files not compiled. Please run proto compilation first.")
        return
    
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    
    # Add Task Worker service
    worker_service = ItineraryTaskWorker()
    agent_platform_pb2_grpc.add_TaskWorkerServicer_to_server(worker_service, server)
    
    port = os.getenv('WORKER_PORT', '50054')
    server.add_insecure_port(f'[::]:{port}')
    
    logger.info(f"Itinerary Task Worker starting on port {port}")
    server.start()
    
    # Register with Consul (if available)
    try:
        import consul
        import socket
        
        # Get container hostname for unique service ID
        hostname = socket.gethostname()
        service_id = f'itinerary-worker-{hostname}'
        
        consul_client = consul.Consul(
            host=os.getenv('CONSUL_HOST', 'localhost'),
            port=int(os.getenv('CONSUL_PORT', '8500'))
        )
        
        consul_client.agent.service.register(
            name='worker-itinerary',  # Service name (same for all instances)
            service_id=service_id,  # Unique ID per instance
            address=hostname,  # Use container hostname
            port=int(port),
            tags=['worker', 'itinerary', 'planning', 'ai'],
            check=consul.Check.tcp(hostname, int(port), interval='10s')
        )
        logger.info(f"Itinerary Task Worker registered with Consul as {service_id}")
    except Exception as e:
        logger.warning(f"Could not register with Consul: {e}")
    
    logger.info("Itinerary Task Worker is ready")
    
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        logger.info("Shutting down Itinerary Task Worker")
        server.stop(0)


if __name__ == '__main__':
    logger.info('Itinerary Task Worker starting...')
    serve()