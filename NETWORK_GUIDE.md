# Network Connectivity Guide

## Quick Answer

Aby połączyć się z innego komputera:

```bash
# 1. Na komputerze z serwerem:
python -m server.main

# 2. Na innym komputerze (zastąp IP):
python -m client.main room-1 YourName ws://192.168.1.16:8000
```

---

## Znalezienie IP Adresu Serwera

### Windows
```powershell
ipconfig
# Szukaj IPv4 Address w sieci lokalnej (np. 192.168.1.x)
```

### Linux/Mac
```bash
ifconfig
# lub
hostname -I
```

### Online
```bash
# Jeśli chcesz publiczny IP (internet)
curl https://api.ipify.org
```

---

## Scenariusze Połączeń

### Scenariusz 1: Sieć Lokalna (LAN)

```
┌─────────────────┐
│  Computer A     │  192.168.1.16
│  Server         │  Port 8000
└─────────────────┘
      ↑
      │ WiFi/Ethernet
      │
┌─────────────────┐
│  Computer B     │  192.168.1.20
│  Client (Alice) │
└─────────────────┘
```

**Na Computer A:**
```bash
python -m server.main
```

**Na Computer B:**
```bash
python -m client.main room-1 Alice ws://192.168.1.16:8000
```

---

### Scenariusz 2: Internet (Zdalny Dostęp)

Potrzebujesz publicznego IP lub port forwardingu.

**Opcja A: Port Forwarding (Router)**
1. Zaloguj się do routera (192.168.1.1 lub 192.168.0.1)
2. Przejdź do Port Forwarding
3. Przekieruj port 8000 na IP serwera
4. Klient łączy się z publicznym IP routera

**Opcja B: SSH Tunnel**
```bash
# Z komputera klienta:
ssh -L 8000:localhost:8000 user@server.public.ip

# W innym terminalu:
python -m client.main room-1 Alice ws://localhost:8000
```

---

## Firewall

### Windows (Otwórz Port)

```powershell
# Uruchom jako Administrator
netsh advfirewall firewall add rule name="Dice Roller" dir=in action=allow protocol=tcp localport=8000
```

### Linux

```bash
# UFW
sudo ufw allow 8000/tcp

# Firewalld
sudo firewall-cmd --permanent --add-port=8000/tcp
sudo firewall-cmd --reload
```

### macOS

System Preferences → Security & Privacy → Firewall Options

---

## Testowanie Połączenia

### Test 1: Server Działa?
```bash
curl http://localhost:8000/health
# Powinna być odpowiedź: {"status":"ok"}
```

### Test 2: Server Dostępny ze Zdalnie?
```bash
# Z innego komputera:
curl http://192.168.1.16:8000/health
```

### Test 3: WebSocket Działa?
```bash
python check_connectivity.py
```

---

## Typowe Problemy

| Problem | Przyczyna | Rozwiązanie |
|---------|-----------|------------|
| Connection refused | Server nie słucha | `python -m server.main` |
| Timeout | Firewall blokuje | Otwórz port 8000 |
| Connection reset | Zła IP/Port | Sprawdź IP: `ipconfig` |
| "localhost" nie działa | Używasz 127.0.0.1 | Użyj rzeczywistego IP (np. 192.168.1.16) |
| Slow connection | Przeciążona sieć | Sprawdź przepustowość WiFi |

---

## Konfiguracja Serwera

### Zmiana Portu
Edytuj `server/main.py`:
```python
def main():
    uvicorn.run(
        "server.app:app",
        host="0.0.0.0",  # Wszystkie interfejsy
        port=9000,       # ← Zmień tutaj
        reload=True,
        log_level="info",
    )
```

### Zmiana Interfejsu
```python
host="192.168.1.16",  # Tylko ten interfejs
# lub
host="0.0.0.0",       # Wszystkie interfejsy (domyślnie)
```

---

## IPv6

Jeśli sieć używa IPv6:

```bash
# IPv6 Server
python -m client.main room-1 Alice ws://[::1]:8000

# Ze zdalnego IPv6
python -m client.main room-1 Alice ws://[2001:db8::1]:8000
```

---

## Docker (Advanced)

Jeśli chcesz wdrożyć w Docker:

```dockerfile
FROM python:3.11
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["python", "-m", "server.main"]
```

```bash
# Build
docker build -t dice-roller .

# Run
docker run -p 8000:8000 dice-roller
```

---

## Podsumowanie

✅ **Sieć lokalna**: Użyj IP z `ipconfig` (np. 192.168.1.x)
✅ **Internet**: Port forwarding + publiczne IP
✅ **SSH**: Bezpieczny tunel do serwera
✅ **Docker**: Konteneryzacja dla produkcji

Powodzenia w grze! 🎲
