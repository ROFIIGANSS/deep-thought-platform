#!/usr/bin/env python3
"""
Consul registration sidecar for Catalog UI (nginx)
"""

import os
import sys
import time
import socket
import signal
import logging
import consul

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
CONSUL_HOST = os.getenv('CONSUL_HOST', 'consul')
CONSUL_PORT = int(os.getenv('CONSUL_PORT', '8500'))
CATALOG_UI_PORT = int(os.getenv('CATALOG_UI_PORT', '80'))
CATALOG_UI_HOST = os.getenv('CATALOG_UI_HOST', socket.gethostname())

consul_client = None
service_id = None
running = True


def signal_handler(signum, frame):
    """Handle shutdown signals"""
    global running
    logger.info(f"Received signal {signum}, shutting down...")
    running = False


def register_with_consul():
    """Register service with Consul"""
    global consul_client, service_id
    
    try:
        consul_client = consul.Consul(host=CONSUL_HOST, port=CONSUL_PORT)
        service_id = f"catalog-ui-{CATALOG_UI_HOST}-{CATALOG_UI_PORT}"
        
        # Register service
        consul_client.agent.service.register(
            name="catalog-ui",
            service_id=service_id,
            address=CATALOG_UI_HOST,
            port=CATALOG_UI_PORT,
            tags=["catalog", "ui", "http", "nginx"],
            check=consul.Check.http(
                f"http://{CATALOG_UI_HOST}:{CATALOG_UI_PORT}/health",
                interval="10s",
                timeout="5s",
                deregister="30s"
            )
        )
        logger.info(f"Registered with Consul: {service_id} at {CATALOG_UI_HOST}:{CATALOG_UI_PORT}")
        return True
    except Exception as e:
        logger.error(f"Failed to register with Consul: {e}")
        return False


def deregister_from_consul():
    """Deregister service from Consul"""
    global consul_client, service_id
    
    if consul_client and service_id:
        try:
            consul_client.agent.service.deregister(service_id)
            logger.info(f"Deregistered from Consul: {service_id}")
        except Exception as e:
            logger.error(f"Failed to deregister from Consul: {e}")


def maintain_registration():
    """Keep the registration active and re-register if needed"""
    global running
    
    while running:
        time.sleep(30)  # Check every 30 seconds
        
        if not running:
            break
        
        # Verify registration is still active
        try:
            if consul_client:
                services = consul_client.agent.services()
                if service_id not in services:
                    logger.warning(f"Service {service_id} not found in Consul, re-registering...")
                    register_with_consul()
        except Exception as e:
            logger.error(f"Error checking registration: {e}")


if __name__ == "__main__":
    # Setup signal handlers
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    # Wait for Consul to be available
    logger.info(f"Waiting for Consul at {CONSUL_HOST}:{CONSUL_PORT}...")
    time.sleep(5)
    
    # Register with Consul
    if not register_with_consul():
        logger.error("Failed to register with Consul, exiting...")
        sys.exit(1)
    
    # Maintain registration
    try:
        maintain_registration()
    finally:
        deregister_from_consul()
        logger.info("Shutdown complete")

