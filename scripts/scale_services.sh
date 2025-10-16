#!/bin/bash
# Scale services script

SERVICE=$1
REPLICAS=$2

if [ -z "$SERVICE" ] || [ -z "$REPLICAS" ]; then
    echo "Usage: $0 <service-name> <number-of-replicas>"
    echo ""
    echo "Available services:"
    echo "  echo-agent"
    echo "  weather-tool"
    echo "  itinerary-worker"
    echo ""
    echo "Example: $0 echo-agent 3"
    exit 1
fi

echo "Scaling $SERVICE to $REPLICAS instances..."
docker-compose up -d --scale $SERVICE=$REPLICAS --no-recreate

echo ""
echo "Waiting for services to stabilize..."
sleep 3

echo ""
echo "Current status:"
docker-compose ps $SERVICE

echo ""
echo "Services registered in Consul:"
curl -s http://localhost:8500/v1/catalog/service/${SERVICE%-*}-${SERVICE#*-} | python3 -m json.tool 2>/dev/null || echo "Install jq for better output: brew install jq"

