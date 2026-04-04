# Docker Deployment Guide

## Quick Start with Docker Compose

### Prerequisites
- Docker (https://www.docker.com/products/docker-desktop)
- Docker Compose (usually included with Docker Desktop)

### Run Everything with One Command

```bash
docker-compose up
```

This will:
1. Build the server image
2. Build the client image
3. Start server on port 8000
4. Connect Alice and Bob clients automatically
5. They immediately start in the same room

### Stop All Services

```bash
docker-compose down
```

---

## Manual Docker Usage

### Build Server Image

```bash
docker build -f Dockerfile.server -t dice-roller-server .
```

### Run Server

```bash
docker run -p 8000:8000 --name server dice-roller-server
```

### Build Client Image

```bash
docker build -f Dockerfile.client -t dice-roller-client .
```

### Run Client

```bash
docker run \
  --name client-alice \
  --link server:server \
  dice-roller-client \
  room-1 Alice ws://server:8000
```

---

## Docker Network

### Default Compose Network

Services communicate via service names:
- `server:8000` - Server address for clients
- `client-alice` - Alice client container
- `client-bob` - Bob client container

### Custom Network

```bash
# Create network
docker network create dice-network

# Run server on network
docker run -p 8000:8000 \
  --network dice-network \
  --name server \
  dice-roller-server

# Run client on network
docker run \
  --network dice-network \
  --name client-alice \
  dice-roller-client \
  room-1 Alice ws://server:8000
```

---

## Scaling with Docker Compose

### Add More Clients

Edit `docker-compose.yml`:

```yaml
  client-charlie:
    build:
      context: .
      dockerfile: Dockerfile.client
    container_name: dice-roller-charlie
    command: ["room-1", "Charlie", "ws://server:8000"]
    depends_on:
      server:
        condition: service_healthy
    networks:
      - dice-network
    stdin_open: true
    tty: true
    restart: unless-stopped
```

Then run:
```bash
docker-compose up
```

---

## Docker Images

### Server Image

- **Base**: Python 3.11-slim
- **Size**: ~200MB (slim base)
- **Port**: 8000
- **Health Check**: HTTP GET /health

### Client Image

- **Base**: Python 3.11-slim
- **Size**: ~200MB (slim base)
- **Arguments**: room_id, player_name, server_url

---

## Debugging

### View Logs

```bash
# All services
docker-compose logs

# Specific service
docker-compose logs server
docker-compose logs client-alice

# Follow logs
docker-compose logs -f
```

### Enter Container Shell

```bash
# Server
docker exec -it dice-roller-server /bin/bash

# Client
docker exec -it dice-roller-alice /bin/bash
```

### Check Container Status

```bash
docker-compose ps
```

### Inspect Network

```bash
docker network inspect dice-network
```

---

## Production Deployment

### Docker Compose Override

Create `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  server:
    ports:
      - "0.0.0.0:8000:8000"
    restart: always
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 5s
      timeout: 5s
      retries: 5

  client-alice:
    restart: always

  client-bob:
    restart: always
```

Run:
```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

---

## Kubernetes (Advanced)

### Convert to Kubernetes

```bash
# Use Kompose to convert docker-compose to k8s
kompose convert -f docker-compose.yml -o k8s/

# Deploy
kubectl apply -f k8s/
```

### Kubernetes Manifest Example

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: dice-roller-server
spec:
  replicas: 1
  selector:
    matchLabels:
      app: dice-roller-server
  template:
    metadata:
      labels:
        app: dice-roller-server
    spec:
      containers:
      - name: server
        image: dice-roller-server:latest
        ports:
        - containerPort: 8000
        healthCheck:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: dice-roller-server
spec:
  selector:
    app: dice-roller-server
  ports:
  - port: 8000
    targetPort: 8000
  type: LoadBalancer
```

---

## Docker Hub Publishing

### Tag Image

```bash
docker tag dice-roller-server myusername/dice-roller-server:1.0
docker tag dice-roller-client myusername/dice-roller-client:1.0
```

### Push to Docker Hub

```bash
docker push myusername/dice-roller-server:1.0
docker push myusername/dice-roller-client:1.0
```

### Pull and Run

```bash
docker run -p 8000:8000 myusername/dice-roller-server:1.0
```

---

## Docker Compose Environment Variables

### .env File

Create `.env`:

```
ROOM_ID=adventure-1
PLAYER_ALICE=Alice
PLAYER_BOB=Bob
SERVER_HOST=server
SERVER_PORT=8000
LOG_LEVEL=info
```

Update `docker-compose.yml`:

```yaml
services:
  client-alice:
    command: ["${ROOM_ID}", "${PLAYER_ALICE}", "ws://${SERVER_HOST}:${SERVER_PORT}"]
```

---

## Cleanup

### Remove Stopped Containers

```bash
docker-compose rm
```

### Remove Images

```bash
docker rmi dice-roller-server dice-roller-client
```

### Remove All (Dangerous!)

```bash
docker system prune -a
```

---

## Troubleshooting

### Port Already in Use

```bash
# Change port in docker-compose.yml
ports:
  - "9000:8000"  # Host port 9000 → Container port 8000

# Or kill process on port 8000
lsof -i :8000
kill -9 <PID>
```

### Network Issues

```bash
# Check network connectivity
docker network ls
docker network inspect dice-network

# Test DNS
docker exec client-alice ping server
```

### Client Won't Connect

1. Ensure server is healthy: `docker-compose ps`
2. Check server logs: `docker-compose logs server`
3. Verify network: `docker network inspect dice-network`
4. Try manual connection: `docker exec client-alice python -c "import websockets"`

---

## Performance Tuning

### Resource Limits

```yaml
services:
  server:
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 512M
        reservations:
          cpus: '0.5'
          memory: 256M
```

### Volume Mounts for Development

```yaml
services:
  server:
    volumes:
      - .:/app
      - /app/__pycache__
```

---

## Summary

✅ **Quick Start**: `docker-compose up`
✅ **Easy Scaling**: Add services to docker-compose.yml
✅ **Production Ready**: Health checks, restarts, networks
✅ **Development Friendly**: Logs, shell access, volume mounts
✅ **Cloud Ready**: Kubernetes compatible

🐳 **Docker makes deployment simple!** 🐳
