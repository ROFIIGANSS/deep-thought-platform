FROM haproxy:2.9-alpine

# Copy HAProxy configuration
COPY haproxy/haproxy.cfg /usr/local/etc/haproxy/haproxy.cfg

# Expose ports
EXPOSE 50051 8404

# Health check
HEALTHCHECK --interval=10s --timeout=5s --retries=3 \
    CMD wget -q --spider http://localhost:8404 || exit 1

# Run HAProxy
CMD ["haproxy", "-f", "/usr/local/etc/haproxy/haproxy.cfg"]

