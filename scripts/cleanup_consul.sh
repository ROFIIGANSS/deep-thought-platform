#!/bin/bash
# Consul Cleanup Script
# Removes stale service registrations from Consul

CONSUL_URL="http://localhost:8500"

echo "=================================="
echo "Consul Cleanup Script"
echo "=================================="
echo ""

# Function to deregister a service
deregister_service() {
    local service_id=$1
    echo "  Deregistering: $service_id"
    curl -s -X PUT "$CONSUL_URL/v1/agent/service/deregister/$service_id" > /dev/null
}

# Function to list and clean stale services
cleanup_stale_services() {
    echo "Fetching current services..."
    
    # Get all services
    services=$(curl -s "$CONSUL_URL/v1/agent/services" | python3 -c "
import sys, json
data = json.load(sys.stdin)
for service_id, info in data.items():
    print(f\"{service_id}|{info['Service']}\")
")
    
    # Get health status for each service
    echo ""
    echo "Checking health status..."
    echo ""
    
    while IFS='|' read -r service_id service_name; do
        # Check health
        health=$(curl -s "$CONSUL_URL/v1/health/service/$service_name" | python3 -c "
import sys, json
data = json.load(sys.stdin)
for service in data:
    if service['Service']['ID'] == '$service_id':
        checks = service.get('Checks', [])
        for check in checks:
            if check.get('CheckID') == 'service:$service_id':
                print(check.get('Status', 'unknown'))
                break
" 2>/dev/null)
        
        if [ "$health" = "critical" ]; then
            echo "❌ $service_id - CRITICAL (will deregister)"
            deregister_service "$service_id"
        elif [ "$health" = "passing" ]; then
            echo "✓ $service_id - PASSING (keeping)"
        else
            echo "⚠️  $service_id - $health"
        fi
    done <<< "$services"
    
    echo ""
    echo "✓ Cleanup complete!"
}

# Function to purge ALL data (nuclear option)
purge_all_data() {
    echo "⚠️  WARNING: This will remove ALL Consul data!"
    echo "This includes:"
    echo "  - All service registrations"
    echo "  - All key-value data"
    echo "  - All health checks"
    echo ""
    read -p "Are you sure? (type 'yes' to confirm): " confirm
    
    if [ "$confirm" = "yes" ]; then
        echo ""
        echo "Stopping services..."
        docker-compose down consul
        
        echo "Removing Consul volume..."
        docker volume rm agent-platform-server_consul-data 2>/dev/null || echo "Volume already removed"
        
        echo "Restarting Consul..."
        docker-compose up -d consul
        
        echo ""
        echo "✓ Consul data purged! Services will re-register automatically."
    else
        echo "Aborted."
    fi
}

# Function to remove specific service type
remove_service_type() {
    local service_type=$1
    echo "Removing all '$service_type' services..."
    
    curl -s "$CONSUL_URL/v1/agent/services" | python3 -c "
import sys, json
data = json.load(sys.stdin)
for service_id, info in data.items():
    if info['Service'] == '$service_type':
        print(service_id)
" | while read -r service_id; do
        deregister_service "$service_id"
    done
    
    echo "✓ Removed all $service_type services"
}

# Main menu
case "${1:-menu}" in
    stale)
        cleanup_stale_services
        ;;
    purge)
        purge_all_data
        ;;
    remove)
        if [ -z "$2" ]; then
            echo "Usage: $0 remove <service-name>"
            echo "Example: $0 remove mcp-router"
            exit 1
        fi
        remove_service_type "$2"
        ;;
    list)
        echo "Current Services:"
        echo ""
        make check-consul 2>/dev/null || curl -s "$CONSUL_URL/v1/agent/services" | python3 -m json.tool
        ;;
    *)
        echo "Usage: $0 {stale|purge|remove|list}"
        echo ""
        echo "Commands:"
        echo "  stale   - Remove only stale/critical services (safe)"
        echo "  purge   - Remove ALL Consul data (nuclear option)"
        echo "  remove  - Remove all instances of a service type"
        echo "  list    - List all registered services"
        echo ""
        echo "Examples:"
        echo "  $0 stale                    # Clean up unhealthy services"
        echo "  $0 remove mcp-router        # Remove all router instances"
        echo "  $0 list                     # Show current services"
        echo "  $0 purge                    # DANGER: Delete everything"
        exit 1
        ;;
esac

