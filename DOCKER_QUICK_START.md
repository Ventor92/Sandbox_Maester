# Docker Quick Start

## One Command - Everything

```bash
docker-compose up
```

This starts:
- Server on http://localhost:8000
- Client: Alice
- Client: Bob
- All connected and ready to play!

---

## Available Commands

### Start All Services
```bash
docker-compose up
```

### Start in Background
```bash
docker-compose up -d
```

### Stop All Services
```bash
docker-compose down
```

### View Logs
```bash
docker-compose logs -f
```

### View Specific Service Logs
```bash
docker-compose logs -f server
docker-compose logs -f client-alice
```

### Check Status
```bash
docker-compose ps
```

### Enter Container Shell
```bash
docker exec -it dice-roller-server bash
docker exec -it dice-roller-alice bash
```

### Rebuild Images
```bash
docker-compose build --no-cache
```

### Remove Everything
```bash
docker-compose down -v
```

---

## Manual Build & Run

### Build Server
```bash
docker build -f Dockerfile.server -t dice-roller-server .
docker run -p 8000:8000 dice-roller-server
```

### Build Client
```bash
docker build -f Dockerfile.client -t dice-roller-client .
docker run dice-roller-client room-1 Alice ws://server:8000
```

---

## Modify Setup

### Add New Client (Charlie)

In `docker-compose.yml`, add:

```yaml
  client-charlie:
    build:
      context: .
      dockerfile: Dockerfile.client
    command: ["room-1", "Charlie", "ws://server:8000"]
    depends_on:
      server:
        condition: service_healthy
    networks:
      - dice-network
```

Then: `docker-compose up`

### Change Server Port

Edit `docker-compose.yml`:

```yaml
services:
  server:
    ports:
      - "9000:8000"  # Host:Container
```

---

## Docker Hub

### Publish Your Image

```bash
docker tag dice-roller-server myuser/dice-roller-server:1.0
docker push myuser/dice-roller-server:1.0
```

### Use Published Image

```bash
docker run -p 8000:8000 myuser/dice-roller-server:1.0
```

---

## Kubernetes (Advanced)

```bash
kompose convert -f docker-compose.yml -o k8s/
kubectl apply -f k8s/
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Port 8000 in use | Change port in docker-compose.yml |
| Container won't start | `docker-compose logs` |
| Can't connect to server | Check network: `docker network ls` |
| Memory issues | Add resource limits to docker-compose.yml |

---

## Files

- `Dockerfile.server` - Server image definition
- `Dockerfile.client` - Client image definition
- `docker-compose.yml` - Compose configuration
- `.dockerignore` - Files to exclude from images

See `DOCKER_GUIDE.md` for full documentation.
