# Server-Only Setup Guide

## Quick Answer

To uruchomić **TYLKO serwer** (bez klientów):

```bash
# Opcja 1: Python (Najszybciej)
python -m server.main

# Opcja 2: Docker Compose (Czysty plik)
docker-compose -f docker-compose.server-only.yml up

# Opcja 3: Docker Compose (Partial)
docker-compose up server

# Opcja 4: Docker (Ręcznie)
docker build -f Dockerfile.server -t dice-roller-server .
docker run -p 8000:8000 dice-roller-server
```

---

## Scenariusze

### Scenariusz 1: Development (Python)

Najprostsze dla developmentu:

```bash
python -m server.main
```

Server słucha na:
- `http://localhost:8000/health` (status)
- `ws://localhost:8000/ws/{room_id}` (WebSocket)

Stop: `Ctrl+C`

### Scenariusz 2: Server dla Wielu Graczy

```
Computer A (Server):
  > python -m server.main

Computer B (Alice):
  > python -m client.main room-1 Alice ws://192.168.1.16:8000

Computer C (Bob):
  > python -m client.main room-1 Bob ws://192.168.1.16:8000

Computer D (Charlie):
  > python -m client.main room-1 Charlie ws://192.168.1.16:8000
```

Wszyscy graczy podłączają się do jednego servera na IP `192.168.1.16`

### Scenariusz 3: Production (Docker)

Dla produkcji - użyj osobnego pliku compose:

```bash
docker-compose -f docker-compose.server-only.yml up
```

Server będzie dostępny na `localhost:8000` (lub publicznym IP)

### Scenariusz 4: Docker Hub

Opublikuj obraz:

```bash
docker tag dice-roller-server myuser/dice-roller-server:1.0
docker push myuser/dice-roller-server:1.0
```

Uruchom gdziekolwiek:

```bash
docker run -p 8000:8000 myuser/dice-roller-server:1.0
```

---

## Pliki Compose

### Główny: docker-compose.yml
Zawiera: Server + Alice + Bob (wszystko)

### Server-Only: docker-compose.server-only.yml
Zawiera: Tylko Server

### Sposób użycia:

```bash
# Wszystko
docker-compose up

# Tylko server (z głównego pliku)
docker-compose up server

# Tylko server (z osobnego pliku)
docker-compose -f docker-compose.server-only.yml up
```

---

## Dostęp do Servera

### Localhost (Ten sam komputer)

```bash
# Python client
python -m client.main room-1 Alice

# Check health
curl http://localhost:8000/health
```

### Network (Inny komputer)

```bash
# Znajdź IP servera
ipconfig  # Windows
ifconfig  # Linux/Mac

# Połącz się z IP
python -m client.main room-1 Alice ws://192.168.1.16:8000
```

### Internet (SSH Tunnel)

```bash
# Z komputera klienta
ssh -L 8000:localhost:8000 user@server.ip

# W innym terminalu na kliencie
python -m client.main room-1 Alice ws://localhost:8000
```

---

## Konfiguracja Servera

### Zmiana Portu

Edytuj `server/main.py`:

```python
def main():
    uvicorn.run(
        "server.app:app",
        host="0.0.0.0",
        port=9000,  # ← Zmień tutaj
        reload=True,
        log_level="info",
    )
```

Lub w Docker (edytuj `Dockerfile.server`):

```dockerfile
ENV PORT=9000
EXPOSE 9000
CMD ["python", "-m", "server.main"]  # zmień port w kodu
```

### Zmiana Hosta

```python
# Tylko localhost
host="127.0.0.1"

# Wszystkie interfejsy (domyślnie)
host="0.0.0.0"

# Konkretny interfejs
host="192.168.1.16"
```

---

## Monitorowanie Servera

### Status

```bash
# Health check
curl http://localhost:8000/health

# Response
{"status":"ok"}
```

### Logi

```bash
# Python
python -m server.main  # Logi w terminalu

# Docker
docker logs -f dice-roller-server

# Docker Compose
docker-compose logs -f server
```

### Diagnoza

```bash
# Port nasłuchuje?
netstat -an | findstr 8000  # Windows
netstat -an | grep 8000      # Linux

# Proces żyje?
tasklist | findstr python    # Windows
ps aux | grep server.main    # Linux

# Network
docker network inspect dice-network  # Docker
```

---

## Skalowanie

### Dodaj drugą pokój

Client podłączający się do innej pokoju:

```bash
python -m client.main room-2 Alice ws://192.168.1.16:8000
```

Server automatycznie skaluje!

### Limit Równoczesnych Połączeń

Server wspiera nieograniczoną ilość pokoi i graczy.

Aby ograniczyć zasoby (Docker):

```yaml
services:
  server:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 1G
```

---

## Troubleshooting

| Problem | Przyczyna | Rozwiązanie |
|---------|-----------|------------|
| Port 8000 w użyciu | Inny proces | Zmień port lub zabij proces |
| Connection refused | Server nie słucha | Sprawdź czy server działa |
| Timeout | Firewall | Otwórz port 8000 |
| Slow response | Przeciążenie | Ogranicz liczbę klientów lub połączeń |

### Port już używany

```bash
# Windows
netstat -ano | findstr 8000
taskkill /PID <PID> /F

# Linux
lsof -i :8000
kill -9 <PID>
```

### Firewall

```bash
# Windows (Admin)
netsh advfirewall firewall add rule name="Dice Server" dir=in action=allow protocol=tcp localport=8000

# Linux
sudo ufw allow 8000/tcp

# macOS
# System Preferences → Security → Firewall
```

---

## Performance Tips

1. **Use Python for development** - Szybciej, łatwiej
2. **Use Docker for production** - Odizolowany, skaluje się
3. **Monitor health endpoint** - `curl http://localhost:8000/health`
4. **Use separate rooms** - Każda pokój ma własny event log
5. **Limit concurrent clients** - Z użyciem resource limits w Docker

---

## Zaawansowane: Własny Client

Napisz dowolny klient w swoim języku:

```json
// Client → Server (WebSocket)
{ "type": "join", "name": "Alice" }
{ "type": "roll", "expr": "d20", "intent": "attack" }

// Server → Client (WebSocket)
{ "type": "event", "event": { ... } }
{ "type": "error", "message": "..." }
```

Szczegóły w: README.md → WebSocket Protocol

---

## Podsumowanie

| Przypadek | Polecenie |
|-----------|-----------|
| Lokalnie | `python -m server.main` |
| Docker | `docker-compose up server` |
| Server-only | `docker-compose -f docker-compose.server-only.yml up` |
| Produkcja | `docker run -p 8000:8000 dice-roller-server` |

Gotowe! 🎲
