# Integracja zewnętrznych klientów — wysyłanie i odbieranie eventów

Krótki przewodnik pokazujący, jak zewnętrzny klient (np. skrypt, serwis lub aplikacja) może połączyć się z serwerem Relay i wysyłać oraz odbierać eventy (w tym `custom_event` / tabelki losowe).

## Endpoints

- WebSocket (real-time): ws://<host>:8000/ws/{room_id}
  - Przykład lokalnie: ws://localhost:8000/ws/dungeon-01
- REST (meta):
  - GET /health  — prosty health check
  - GET /rooms   — lista aktywnych pokojów (tylko pokoje z >=1 klientem)
  - GET /auth/token?room_id=<room>&name=<player> — issue a short-lived JWT for joining the room (MVP; protect in production)

## Krok 1 — Połączenie i identyfikacja

1. Najpierw pobrać krótkożyciowy token JWT z `/auth/token?room_id=<room_id>&name=<player_name>`.
2. Otworzyć połączenie WebSocket do `/ws/{room_id}?token=<JWT>` (token musi być obecny w query param podczas handshake).
3. Po zaakceptowaniu połączenia wysłać wiadomość JOIN:

```json
{ "type": "join", "name": "Alice" }
```

3. Serwer odpowie (po wysłaniu cache) potwierdzeniem dla dołączającego klienta:

```json
{ "type": "player_joined", "player_name": "Alice", "client_id": "client_3" }
```

Dodatkowo serwer powiadomi pozostałych już połączonych klientów w tym samym pokoju poprzez wysłanie tej samej wiadomości `player_joined` (z `player_name` i `client_id`). Klient powinien zapamiętać otrzymane `client_id` jeśli chce je używać lokalnie.

Autoryzacja (JWT)

- Aby dołączyć, klient musi najpierw pobrać krótkożyciowy token JWT z endpointu REST:

```bash
curl 'http://localhost:8000/auth/token?room_id=dungeon-01&name=Alice'
```

Odpowiedź:

```json
{"token": "<JWT>", "expires_in": 300}
```

- Token musi być przekazany w query param przy otwieraniu WebSocket (podczas handshake): ws://host:8000/ws/room-id?token=<JWT>

- Serwer weryfikuje token: token musi być ważny, a jego claim `room_id` oraz `sub` (nazwa gracza) muszą pasować do proszonej sesji. Jeśli weryfikacja nie powiedzie się, połączenie zostanie odrzucone.
- Tokeny są krótkotrwałe (domyślnie 300s). Odśwież token przed wygaśnięciem.

Przykłady (Python)

```python
from urllib.request import urlopen
import json

# Pobierz token
r = urlopen('http://localhost:8000/auth/token?room_id=dungeon-01&name=Alice')
token = json.load(r)['token']

# Połącz używając query param
ws = await websockets.connect(f'ws://localhost:8000/ws/dungeon-01?token={token}')
await ws.send(json.dumps({"type": "join", "name": "Alice"}))
```

Uwaga: W środowisku produkcyjnym endpoint `/auth/token` powinien być chroniony (np. przez upstream auth) i komunikacja powinna korzystać z HTTPS/WSS. Nie eksponuj publicznie mechanizmu wydawania tokenów bez dodatkowego uwierzytelnienia.

## Krok 2 — Wysyłanie eventów

Dwa rekomendowane podejścia:

1) Złożone, ustrukturyzowane eventy (REKOMENDOWANE — cache + spójność)
- Klient generuje kompletny obiekt event i wysyła go jako "event":

```json
{
  "type": "event",
  "event": {
    "id": "uuid",
    "type": "roll",
    "version": 1,
    "timestamp": 1680000000.0,
    "payload": { /* struktura zależna od typu eventu */ }
  }
}
```

- Takie eventy są cache'owane przez serwer (ostatnie 100) i broadcastowane do wszystkich klientów w pokoju.

2) Custom events (tabele losowe, lokalne generatory)
- Klient wysyła event typu `custom_event` z własnym payloadem:

```json
{
  "type": "custom_event",
  "event": {
    "subtype": "table_roll",
    "payload": { "table_id": "loot", "choice": "sword" },
    "metadata": { "client_generated_id": "local-123" }
  }
}
```

- Serwer doda pod `event.metadata` następujące pola:
  - `server_assigned_id` (UUID)
  - `timestamp` (Unix float)
  - `sender_client_id` (np. "client_3")

- Custom events są również cache'owane (ostatnie 100) — late-joiner otrzyma historię.

## Krok 3 — Odbieranie eventów

Po dołączeniu klient otrzyma kolejno: historyczne eventy (jeśli istnieją) jako wiadomości typu `event`/`custom_event`, a następnie wszystkie nowe broadcasty. Przykładowa pętla odbioru w Pythonie:

```python
import asyncio, json, websockets

async def run():
    # Fetch token first (example)
    from urllib.request import urlopen
    import json as _json
    r = urlopen('http://localhost:8000/auth/token?room_id=dungeon-01&name=Alice')
    token = _json.load(r)['token']
    ws = await websockets.connect(f"ws://localhost:8000/ws/dungeon-01?token={token}", ping_interval=None)
    await ws.send(json.dumps({"type":"join","name":"Alice"}))
    while True:
        raw = await ws.recv()
        msg = json.loads(raw)
        t = msg.get('type')
        if t == 'event' or t == 'custom_event':
            evt = msg.get('event', {})
            print('Got event:', evt)
        elif t == 'player_joined':
            print('Joined as', msg.get('client_id'))
        elif t == 'error':
            print('Error:', msg.get('message'))

asyncio.run(run())
```

## REST: quick checks

- Health: curl http://localhost:8000/health
- Rooms: curl http://localhost:8000/rooms

Przykłady:

```bash
curl http://localhost:8000/health
curl http://localhost:8000/rooms
```

## Przykładowy scenariusz (table roll)

1. Klient A wykonuje losowanie lokalnie i wysyła `custom_event` jak wyżej.
2. Serwer dopisuje metadata i cache'uje event.
3. Serwer broadcastuje do klientów B, C...
4. Klient B otrzymuje `custom_event` z `metadata.server_assigned_id` i `metadata.sender_client_id`.

## Bezpieczeństwo i ograniczenia

- Serwer jest relay'em: nie ufa ani nie interpretuje payloadu custom_event — to pozostaje po stronie klienta.
- Nie wysyłaj w payloadach poufnych danych (tokenów, kluczy).
- Dla produkcji używać wss:// i autoryzacji (nie dostarczone w MVP).
- Payloady powinny być rozsądnych rozmiarów; rozważ ograniczenia po stronie klienta.

## Debug i testowanie

- Uruchom serwer: `python -m server.main` lub `uvicorn server.app:app --host 0.0.0.0 --port 8000`
- Użyj `websockets` w Pythonie lub dowolnego klienta WebSocket (js, Go, etc.).
- Sprawdź REST: /health i /rooms.

---

Plik stworzony, zawiera przykłady JSON i wskazówki praktyczne dla zewnętrznych integratorów.