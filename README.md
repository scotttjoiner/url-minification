# URL Minification API

A simple URL minification (shortening) service built with Flask‑RESTX, MongoDB, JWT authentication, and Celery for asynchronous click logging.

## Features

- **Create short links** for one or more URLs in a single request
- **Resolve and redirect** short links, with support for positional arguments
- **Link expiration** handling (returns 410 if expired)
- **Click logging** via asynchronous Celery tasks with retry/backoff
- **JWT Bearer token authentication** against an external JWKS endpoint
- **Swagger UI** documentation at `/api/docs`

## Tech Stack

- Python 3.9+
- Flask + Flask‑RESTX
- PyMongo (MongoDB)
- PyJWT / PyJWKClient (JWT validation)
- Celery + Redis (async tasks)
- Docker & Docker Compose
- pytest + pytest‑mock for unit and integration tests

## Getting Started

### Prerequisites

- Python 3.9 or later
- MongoDB instance (local or cloud URI)
- Redis instance (for Celery broker/backend)
- (Optional) Docker & Docker Compose for containerized setup

### Configuration

Copy `.env.example` to `.env` and adjust:

```ini
FLASK_APP=src.app:create_app
FLASK_ENV=development
FLASK_PORT=8888
MONGO_URI=mongodb://localhost:27017/url_minify
IDP_JWKS_URL=https://your‑idp/.well‑known/jwks.json
EXPECTED_AUDIENCE=your‑client‑id
EXPECTED_ISSUER=https://your‑idp/
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1
```

### Local Development (no Docker)

1. Create & activate a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
2. Install dependencies:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```
3. Run the Flask development server:
   ```bash
   flask run --host=0.0.0.0 --port=${FLASK_PORT}
   ```
4. Start a Celery worker (in another terminal):
   ```bash
   celery -A src.celery_app.celery worker --loglevel=info
   ```
5. Visit the Swagger UI at [http://localhost:\${FLASK\_PORT}/api/docs](http://localhost:\${FLASK_PORT}/api/docs)

### Docker Compose

Bring up the entire stack (Flask, Redis, Celery worker):

```bash
docker-compose up --build -d
```

- Flask app:   `http://localhost:8888/api/docs`
- Redis, MongoDB are internal services

Tear down:

```bash
docker-compose down
```

## Running Tests

```bash
pytest --maxfail=1 --disable-warnings -q
```

- **Unit tests** mock Mongo and other dependencies
- **Integration tests** use Flask `test_client` + monkeypatch

## API Endpoints

| Method | Path                      | Description                              |
| ------ | ------------------------- | ---------------------------------------- |
| GET    | `/api/links`              | List/search links                        |
| POST   | `/api/links`              | Create one or more short links           |
| GET    | `/api/links/<id>`         | Retrieve a single link                   |
| PUT    | `/api/links/<id>`         | Update a link                            |
| DELETE | `/api/links/<id>`         | Delete a link                            |
| GET    | `/<short_link>/[...args]` | Redirect to original URL (supports args) |

### Sample curl

```bash
# Create links
curl -X POST http://localhost:8888/api/links \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '[{ "url": "https://example.com" }]'

# Fetch a single link
curl http://localhost:8888/api/links/abc123 -H "Authorization: Bearer $TOKEN"

# Redirect
curl -i http://localhost:8888/abc123/
```

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

---

Happy shortening! Feel free to open issues or submit pull requests.

