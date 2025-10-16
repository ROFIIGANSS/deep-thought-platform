FROM node:20-alpine as build

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy source code
COPY . .

# Build the app
RUN npm run build

# Production stage
FROM nginx:alpine

# Install Python and dependencies for Consul registration
RUN apk add --no-cache python3 py3-pip && \
    pip3 install --no-cache-dir python-consul --break-system-packages

# Copy built assets from build stage
COPY --from=build /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy Consul registration script
COPY register_consul.py /usr/local/bin/register_consul.py
RUN chmod +x /usr/local/bin/register_consul.py

# Copy startup script
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

EXPOSE 80

CMD ["/docker-entrypoint.sh"]

