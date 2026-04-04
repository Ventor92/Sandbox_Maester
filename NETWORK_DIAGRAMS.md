# Network Architecture Diagrams

## Scenariusz 1: Lokalnie (Jeden komputer)

```
┌─────────────────────────────────────────┐
│         SINGLE COMPUTER                 │
│  192.168.1.16                           │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │  Terminal 1: Server             │   │
│  │  python -m server.main          │   │
│  │  :8000                          │   │
│  └────────────┬────────────────────┘   │
│               │                         │
│               ↓ localhost:8000          │
│               │                         │
│  ┌────────────┴────────────────────┐   │
│  │  Terminal 2: Client (Alice)     │   │
│  │  /r d20 attack                  │   │
│  └─────────────────────────────────┘   │
│               │                         │
│               ↓                         │
│  ┌────────────┴────────────────────┐   │
│  │  Terminal 3: Client (Bob)       │   │
│  │  /r 2d6+1 cast spell            │   │
│  └─────────────────────────────────┘   │
└─────────────────────────────────────────┘
```

**Polecenie:**
```bash
# Terminal 1
python -m server.main

# Terminal 2
python -m client.main room-1 Alice

# Terminal 3
python -m client.main room-1 Bob
```

---

## Scenariusz 2: Sieć Lokalna (LAN)

```
          INTERNET
             │
    ┌────────┴────────┐
    │    ROUTER       │
    │ 192.168.1.1     │
    └────────┬────────┘
             │
    ┌────────┼────────────┐
    │        │            │
    │        │            │
    │        │            │

┌───────────────────┐  ┌───────────────────┐  ┌───────────────────┐
│  COMPUTER A       │  │  COMPUTER B       │  │  COMPUTER C       │
│  192.168.1.16     │  │  192.168.1.20     │  │  192.168.1.21     │
│                   │  │                   │  │                   │
│  Server:8000      │  │  Client (Alice)   │  │  Client (Bob)     │
│  ✓ RUNNING        │  │  ws://192.168.1.16│  │  ws://192.168.1.16│
│                   │  │      :8000        │  │      :8000        │
│ python -m         │  │ python -m client  │  │ python -m client  │
│ server.main       │  │ room-1 Alice      │  │ room-1 Bob        │
│                   │  │                   │  │                   │
└───────────────────┘  └───────────────────┘  └───────────────────┘
        │◄─────────────────────────────┤◄─────────────────────────┤
        │                              │                          │
        └────── WebSocket events────────┴──────────────────────────┘
```

**Kroki:**

1. Znajdź IP Computer A:
   ```bash
   ipconfig  # Wynik: 192.168.1.16
   ```

2. Computer A - Uruchom serwer:
   ```bash
   python -m server.main
   ```

3. Computer B - Uruchom klienta:
   ```bash
   python -m client.main room-1 Alice ws://192.168.1.16:8000
   ```

4. Computer C - Uruchom klienta:
   ```bash
   python -m client.main room-1 Bob ws://192.168.1.16:8000
   ```

---

## Scenariusz 3: Internet (Port Forwarding)

```
                    INTERNET
                       │
                    ┌──┴──┐
                    │ DNS │
                    └──┬──┘
                       │
            PUBLIC IP: 203.0.113.42
                       │
         ┌─────────────┴─────────────┐
         │                           │
      ┌──┴──┐                       │
      │ ISP │                       │
      │     │                       │
      └──┬──┘                       │
         │                          │
    ┌────┴─────────────┐           │
    │  ROUTER          │           │
    │  Port Forwarding │           │
    │  8000→192.168... │◄──────────┘
    └────┬─────────────┘
         │
    ┌────┴────────────────┐
    │  SERVER             │
    │  192.168.1.16:8000  │
    │  python -m server.  │
    │  main               │
    └─────────────────────┘

Clients connect via:
  ws://203.0.113.42:8000
```

**Konfiguracja Router:**
1. Zaloguj się do routera (np. 192.168.1.1)
2. Przejdź do: Port Forwarding / UPnP
3. Ustaw: Port 8000 → 192.168.1.16:8000
4. Klienci podłączają się do: `ws://203.0.113.42:8000`

---

## Scenariusz 4: SSH Tunnel (Bezpieczne)

```
┌────────────────┐
│  Client PC     │
│  192.168.1.20  │
│                │
│  Terminal:     │
│  ssh -L        │
│  8000:...      │
└────┬───────────┘
     │ SSH Tunnel (szyfrowana)
     │
┌────┴───────────┐
│  Server PC     │
│  192.168.1.16  │
│                │
│  Localhost:    │
│  8000          │
└────────────────┘

Client code:
  ws://localhost:8000
```

**Polecenie SSH:**
```bash
ssh -L 8000:localhost:8000 user@192.168.1.16
# W innym terminalu na kliencie:
python -m client.main room-1 Alice ws://localhost:8000
```

---

## Przepływ Danych (WebSocket)

```
CLIENT                              SERVER
   │                                  │
   │ 1. /r d20 attack               │
   ├─────────────────────────────→  │
   │                                  │ 2. Parse expression
   │                                  │    Validate dice
   │                                  │    Roll: d20 = 17
   │                                  │    Create Event
   │                                  │    Save to Log
   │ 3. Event: {"type":"roll"...}  │
   ├─────────────────────────────← │
   │    Display in TUI               │
   │                                  │ 4. Broadcast to all clients
   │                                  │    (all Room 1 players)
   │ 5. Event: {"type":"roll"...}  │
   ├─────────────────────────────← │
   │    Display: "Alice rolled..."   │
   │                                  │
```

---

## Status Portu

```bash
# Sprawdź czy port 8000 jest otwarty i nasłuchuje

# Windows
netstat -an | findstr 8000

# Linux/Mac
netstat -an | grep 8000
# lub
lsof -i :8000
```

---

## Podsumowanie

| Scenariusz | IP | Port | Polecenie |
|-----------|----|----|-----------|
| Lokalnie | localhost | 8000 | `python -m client.main room-1 Alice` |
| LAN | 192.168.1.x | 8000 | `python -m client.main room-1 Alice ws://192.168.1.16:8000` |
| Internet | Public IP | 8000 | `python -m client.main room-1 Alice ws://203.0.113.42:8000` |
| SSH Tunnel | localhost | 8000 | `ssh -L 8000:... && python -m client...` |
