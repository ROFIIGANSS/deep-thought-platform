"""
Weather Tool - Provides weather information
Demonstrates tool implementation with MCP protocol support
"""

import grpc
from concurrent import futures
import os
import logging
import json
import sys
from datetime import datetime
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


class WeatherToolService:
    """Weather Tool Service Implementation"""
    
    def __init__(self):
        self.tool_id = "weather-tool"
        # Mock weather data for demonstration
        self.weather_data = {
            'new york': {'temp': 72, 'condition': 'Partly Cloudy', 'humidity': 65},
            'london': {'temp': 62, 'condition': 'Rainy', 'humidity': 80},
            'tokyo': {'temp': 75, 'condition': 'Sunny', 'humidity': 55},
            'paris': {'temp': 68, 'condition': 'Cloudy', 'humidity': 70},
            'sydney': {'temp': 82, 'condition': 'Sunny', 'humidity': 60},
        }
    
    def get_weather(self, location: str) -> dict:
        """Get weather for a location"""
        location_lower = location.lower()
        
        # Check if we have data for this location
        if location_lower in self.weather_data:
            data = self.weather_data[location_lower]
        else:
            # Generate random weather for unknown locations
            data = {
                'temp': random.randint(50, 90),
                'condition': random.choice(['Sunny', 'Cloudy', 'Rainy', 'Partly Cloudy']),
                'humidity': random.randint(40, 90)
            }
        
        return {
            'location': location,
            'temperature': data['temp'],
            'condition': data['condition'],
            'humidity': data['humidity'],
            'timestamp': datetime.now().isoformat()
        }
    
    def get_forecast(self, location: str, days: int = 3) -> list:
        """Get weather forecast for a location"""
        forecast = []
        base_weather = self.get_weather(location)
        
        for i in range(days):
            day_weather = {
                'day': i + 1,
                'location': location,
                'temperature': base_weather['temperature'] + random.randint(-5, 5),
                'condition': random.choice(['Sunny', 'Cloudy', 'Rainy', 'Partly Cloudy']),
                'humidity': base_weather['humidity'] + random.randint(-10, 10)
            }
            forecast.append(day_weather)
        
        return forecast
    
    def ExecuteTool(self, request, context):
        """Execute tool operation"""
        logger.info(f"Tool request - Operation: {request.operation} - Session: {request.session_id}")
        
        try:
            operation = request.operation
            params = dict(request.parameters)
            
            if operation == 'get_weather':
                location = params.get('location', '')
                if not location:
                    raise ValueError("Location parameter is required")
                
                weather = self.get_weather(location)
                result = json.dumps(weather, indent=2)
                
                logger.info(f"Weather retrieved for {location}")
                
                return agent_platform_pb2.ToolResponse(
                    success=True,
                    result=result,
                    error="",
                    session_id=request.session_id
                )
            
            elif operation == 'get_forecast':
                location = params.get('location', '')
                days = int(params.get('days', 3))
                
                if not location:
                    raise ValueError("Location parameter is required")
                
                forecast = self.get_forecast(location, days)
                result = json.dumps(forecast, indent=2)
                
                logger.info(f"Forecast retrieved for {location}")
                
                return agent_platform_pb2.ToolResponse(
                    success=True,
                    result=result,
                    error="",
                    session_id=request.session_id
                )
            
            else:
                raise ValueError(f"Unknown operation: {operation}")
        
        except Exception as e:
            logger.error(f"Tool execution failed: {e}")
            return agent_platform_pb2.ToolResponse(
                success=False,
                result="",
                error=str(e),
                session_id=request.session_id
            )
    
    def ListTools(self, request, context):
        """List available tools"""
        tool_info = agent_platform_pb2.ToolInfo(
            tool_id=self.tool_id,
            name="Weather Tool",
            description="Provides weather information and forecasts",
            endpoint="weather-tool:50053",
            parameters=[
                agent_platform_pb2.ToolParameter(
                    name="location",
                    type="string",
                    required=True,
                    description="City or location name"
                ),
                agent_platform_pb2.ToolParameter(
                    name="days",
                    type="integer",
                    required=False,
                    description="Number of days for forecast (default: 3)"
                )
            ],
            detailed_description=(
                "The Weather Tool provides comprehensive weather information for any location worldwide. "
                "It offers current weather conditions, multi-day forecasts, and detailed atmospheric data. "
                "This tool is designed for applications that need real-time weather data, travel planning, "
                "event scheduling, or any weather-dependent decision making."
            ),
            how_it_works=(
                "The tool accepts a location name (city, address, or coordinates) and optionally the number "
                "of forecast days. It processes the request by:\n"
                "1. Validating and normalizing the location input\n"
                "2. Fetching current weather data from weather APIs\n"
                "3. Retrieving forecast data for the specified period\n"
                "4. Aggregating and formatting the data into a structured response\n"
                "Note: Currently returns mock data for demonstration purposes. In production, "
                "this would integrate with real weather APIs like OpenWeatherMap, Weather.gov, or similar services."
            ),
            return_format=(
                "Returns a JSON object containing:\n"
                "- location: {name, coordinates, timezone}\n"
                "- current: {temperature, condition, humidity, wind_speed, pressure, feels_like}\n"
                "- forecast: Array of daily forecasts with {date, high, low, condition, precipitation_chance}\n"
                "- metadata: {timestamp, source, units}\n"
                "All temperatures in Celsius, wind speeds in km/h, pressure in hPa."
            ),
            use_cases=[
                "Travel planning - Check weather before trips",
                "Event scheduling - Plan outdoor events around weather",
                "Agriculture - Monitor conditions for farming decisions",
                "Logistics - Optimize delivery routes based on weather",
                "Smart home automation - Adjust settings based on conditions",
                "Personal planning - Decide daily activities and clothing"
            ],
            version="1.0.0"
        )
        
        return agent_platform_pb2.ListToolsResponse(tools=[tool_info])
    
    def RegisterTool(self, request, context):
        """Register tool"""
        logger.info(f"Registration request for tool: {request.tool_id}")
        
        return agent_platform_pb2.RegistrationResponse(
            success=True,
            message="Tool registered successfully",
            service_id=request.tool_id
        )


def serve():
    """Start the Weather Tool gRPC server"""
    if not agent_platform_pb2_grpc:
        logger.error("Proto files not compiled. Please run proto compilation first.")
        return
    
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    
    # Add Weather Tool service
    weather_service = WeatherToolService()
    agent_platform_pb2_grpc.add_ToolServiceServicer_to_server(weather_service, server)
    
    port = os.getenv('TOOL_PORT', '50053')
    server.add_insecure_port(f'[::]:{port}')
    
    logger.info(f"Weather Tool starting on port {port}")
    server.start()
    
    # Register with Consul (if available)
    try:
        import consul
        import socket
        
        # Get container hostname for unique service ID
        hostname = socket.gethostname()
        service_id = f'weather-tool-{hostname}'
        
        consul_client = consul.Consul(
            host=os.getenv('CONSUL_HOST', 'localhost'),
            port=int(os.getenv('CONSUL_PORT', '8500'))
        )
        
        consul_client.agent.service.register(
            name='tool-weather',  # Service name (same for all instances)
            service_id=service_id,  # Unique ID per instance
            address=hostname,  # Use container hostname
            port=int(port),
            tags=['tool', 'weather', 'data'],
            check=consul.Check.tcp(hostname, int(port), interval='10s')
        )
        logger.info(f"Weather Tool registered with Consul as {service_id}")
    except Exception as e:
        logger.warning(f"Could not register with Consul: {e}")
    
    logger.info("Weather Tool is ready")
    
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        logger.info("Shutting down Weather Tool")
        server.stop(0)


if __name__ == '__main__':
    logger.info('Weather Tool starting...')
    serve()