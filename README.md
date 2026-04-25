# 🖥️ Server Health Monitor

A real-time FastAPI app that monitors server resources — CPU, memory, disk, and running processes — with live WebSocket updates, alert thresholds, and a terminal-style dashboard.

## Features

| Feature | Description |
|---|---|
| **Live Metrics** | CPU, memory, disk via WebSocket (2s updates) |
| **Process Monitor** | Top 10 processes by CPU consumption |
| **Custom Alert Thresholds** | Configurable per-metric via UI or API |
| **History Trending** | 60-point sparkline chart per metric |
| **Network I/O** | Bytes sent/received stats |

## API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/` | GET | Dashboard UI |
| `/api/metrics` | GET | Current snapshot |
| `/api/history` | GET | Last 60 data points |
| `/api/processes` | GET | Top 10 processes by CPU |
| `/api/alerts` | GET | Active alerts + thresholds |
| `/api/thresholds` | POST | Update alert thresholds |
| `/ws` | WebSocket | Live stream (2s interval) |

## Local Setup

```bash
# Install
pip install -r requirements.txt

# Run
cd app
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Open browser
open http://localhost:8000
```

## Docker

```bash
docker build -t server-health-monitor .
docker run -p 8000:8000 server-health-monitor
```

## GitHub Actions Pipeline

The `.github/workflows/ci.yml` runs 3 jobs on every push:

1. **lint-and-test** — runs `pytest tests/` with 6 unit tests
2. **health-check** — starts the server, hits every API endpoint, prints results
3. **docker-build** — builds the Docker image and runs a smoke test

### Trigger manually
```
Actions → Server Health Monitor CI/CD → Run workflow
```

## Project Structure

```
server-health-monitor/
├── app/
│   └── main.py              # FastAPI app
├── templates/
│   └── index.html           # Dashboard UI
├── tests/
│   └── test_api.py          # 6 pytest tests
├── .github/workflows/
│   └── ci.yml               # GitHub Actions pipeline
├── Dockerfile
├── requirements.txt
└── README.md
```
