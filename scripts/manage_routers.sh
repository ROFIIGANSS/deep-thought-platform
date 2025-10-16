#!/bin/bash

# MCP Router Management Script
# Helps manage scaling and monitoring of load-balanced MCP Router instances

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if services are running
check_services() {
    print_info "Checking service status..."
    cd "$PROJECT_DIR"
    
    if ! docker-compose ps | grep -q "Up"; then
        print_error "No services are running. Start services first with: docker-compose up -d"
        exit 1
    fi
    
    print_success "Services are running"
}

# Function to scale router instances
scale_routers() {
    local count=$1
    
    if [[ ! "$count" =~ ^[0-9]+$ ]] || [ "$count" -lt 1 ]; then
        print_error "Invalid count. Please provide a positive number."
        exit 1
    fi
    
    print_info "Scaling MCP Router to $count instance(s)..."
    cd "$PROJECT_DIR"
    
    docker-compose up -d --scale mcp-router="$count" --no-recreate
    
    print_success "Scaled to $count router instance(s)"
    sleep 5  # Wait for services to register
    
    # Show status
    show_status
}

# Function to show router status
show_status() {
    print_info "Router Instance Status:"
    cd "$PROJECT_DIR"
    
    echo ""
    docker-compose ps mcp-router
    
    echo ""
    print_info "Consul Service Registry:"
    
    if command -v curl &> /dev/null; then
        local instances=$(curl -s http://localhost:8500/v1/health/service/mcp-router?passing=true | \
            jq -r '. | length')
        
        if [ -n "$instances" ]; then
            echo "  Healthy instances: $instances"
            curl -s http://localhost:8500/v1/health/service/mcp-router?passing=true | \
                jq -r '.[] | "  - \(.Service.ID) @ \(.Service.Address):\(.Service.Port)"'
        else
            print_warning "Could not query Consul (might not be ready yet)"
        fi
    else
        print_warning "curl not available. Install curl to see Consul status."
    fi
    
    echo ""
    print_info "Monitoring URLs:"
    echo "  HAProxy Stats:  http://localhost:8404"
    echo "  Consul UI:      http://localhost:8500/ui/dc1/services/mcp-router"
}

# Function to show HAProxy stats
show_haproxy_stats() {
    print_info "Opening HAProxy statistics dashboard..."
    
    if command -v open &> /dev/null; then
        open http://localhost:8404
    elif command -v xdg-open &> /dev/null; then
        xdg-open http://localhost:8404
    else
        echo "HAProxy stats available at: http://localhost:8404"
    fi
}

# Function to show Consul UI
show_consul_ui() {
    print_info "Opening Consul service discovery UI..."
    
    if command -v open &> /dev/null; then
        open http://localhost:8500/ui/dc1/services/mcp-router
    elif command -v xdg-open &> /dev/null; then
        xdg-open http://localhost:8500/ui/dc1/services/mcp-router
    else
        echo "Consul UI available at: http://localhost:8500/ui/dc1/services/mcp-router"
    fi
}

# Function to tail logs
tail_logs() {
    print_info "Tailing logs from all MCP Router instances..."
    cd "$PROJECT_DIR"
    docker-compose logs -f mcp-router
}

# Function to show health
show_health() {
    print_info "Checking health of all services..."
    cd "$PROJECT_DIR"
    
    echo ""
    echo "=== HAProxy Health ==="
    if curl -s http://localhost:8404/stats > /dev/null; then
        print_success "HAProxy is healthy"
    else
        print_error "HAProxy is not responding"
    fi
    
    echo ""
    echo "=== Consul Health ==="
    if curl -s http://localhost:8500/v1/status/leader > /dev/null; then
        print_success "Consul is healthy"
        echo "  Leader: $(curl -s http://localhost:8500/v1/status/leader)"
    else
        print_error "Consul is not responding"
    fi
    
    echo ""
    echo "=== MCP Router Instances ==="
    local healthy=$(curl -s http://localhost:8500/v1/health/service/mcp-router?passing=true | jq -r '. | length')
    local total=$(curl -s http://localhost:8500/v1/health/service/mcp-router | jq -r '. | length')
    
    if [ "$healthy" = "$total" ] && [ "$healthy" != "0" ]; then
        print_success "All $total router instance(s) are healthy"
    elif [ "$healthy" != "0" ]; then
        print_warning "$healthy out of $total router instance(s) are healthy"
    else
        print_error "No healthy router instances found"
    fi
}

# Function to restart routers
restart_routers() {
    print_info "Restarting MCP Router instances..."
    cd "$PROJECT_DIR"
    
    docker-compose restart mcp-router
    sleep 5
    
    print_success "MCP Router instances restarted"
    show_status
}

# Function to show usage
show_usage() {
    echo "MCP Router Management Script"
    echo ""
    echo "Usage: $0 <command> [options]"
    echo ""
    echo "Commands:"
    echo "  scale <n>       Scale MCP Router to n instances"
    echo "  status          Show status of all router instances"
    echo "  health          Check health of all services"
    echo "  haproxy         Open HAProxy statistics dashboard"
    echo "  consul          Open Consul service discovery UI"
    echo "  logs            Tail logs from all router instances"
    echo "  restart         Restart all router instances"
    echo "  help            Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 scale 3      # Scale to 3 router instances"
    echo "  $0 status       # Show current status"
    echo "  $0 health       # Check health of services"
    echo "  $0 logs         # Tail router logs"
}

# Main script logic
main() {
    if [ $# -eq 0 ]; then
        show_usage
        exit 0
    fi
    
    command=$1
    shift
    
    case "$command" in
        scale)
            if [ $# -eq 0 ]; then
                print_error "Please provide the number of instances"
                echo "Usage: $0 scale <n>"
                exit 1
            fi
            check_services
            scale_routers "$1"
            ;;
        status)
            check_services
            show_status
            ;;
        health)
            check_services
            show_health
            ;;
        haproxy)
            check_services
            show_haproxy_stats
            ;;
        consul)
            check_services
            show_consul_ui
            ;;
        logs)
            check_services
            tail_logs
            ;;
        restart)
            check_services
            restart_routers
            ;;
        help|--help|-h)
            show_usage
            ;;
        *)
            print_error "Unknown command: $command"
            echo ""
            show_usage
            exit 1
            ;;
    esac
}

main "$@"

