# Genealogical Tree Application
## Quick start

### Prerequisites

* [Docker](https://docs.docker.com/get-docker/) ≥ 20.10
* [Docker Compose](https://docs.docker.com/compose/) ≥ 2.x

### Run the Complete Application

1. Navigate to this folder:

   ```bash
   cd app
   ```

2. Build and start the full stack:

   ```bash
   docker compose up --build
   ```
3. **Wait for startup** (30-60 seconds) until you see:
   ```
   genealogy-api  | Uvicorn running on http://0.0.0.0:8000
   neo4j          | Started.
   ```

## 🛠️ Development & API Access
### API Endpoints

- `GET /health` - Check API status
- `POST /tree` - Submit complete family tree data

### Running Tests
```bash
cd app
uv pip install -r requirements.txt
PYTHONPATH=. pytest -q
```
