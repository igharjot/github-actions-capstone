from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import psutil
import asyncio
import json
from datetime import datetime
from collections import deque
from typing import List, Dict
import platform
import os

app = FastAPI(title="Server Health Monitor", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory history store (last 60 data points per metric)
history: Dict[str, deque] = {
    "cpu": deque(maxlen=60),
    "memory": deque(maxlen=60),
    "disk": deque(maxlen=60),
    "timestamps": deque(maxlen=60),
}

# Alert thresholds (configurable)
ALERT_THRESHOLDS = {
    "cpu": 80.0,
    "memory": 85.0,
    "disk": 90.0,
}

active_alerts: List[dict] = []
connected_clients: List[WebSocket] = []


def get_system_metrics() -> dict:
    cpu = psutil.cpu_percent(interval=0.5)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    net = psutil.net_io_counters()
    boot_time = datetime.fromtimestamp(psutil.boot_time())
    uptime = datetime.now() - boot_time

    metrics = {
        "timestamp": datetime.now().isoformat(),
        "cpu": {
            "percent": cpu,
            "count": psutil.cpu_count(),
            "freq": psutil.cpu_freq().current if psutil.cpu_freq() else 0,
        },
        "memory": {
            "percent": memory.percent,
            "used_gb": round(memory.used / (1024**3), 2),
            "total_gb": round(memory.total / (1024**3), 2),
            "available_gb": round(memory.available / (1024**3), 2),
        },
        "disk": {
            "percent": disk.percent,
            "used_gb": round(disk.used / (1024**3), 2),
            "total_gb": round(disk.total / (1024**3), 2),
            "free_gb": round(disk.free / (1024**3), 2),
        },
        "network": {
            "bytes_sent_mb": round(net.bytes_sent / (1024**2), 2),
            "bytes_recv_mb": round(net.bytes_recv / (1024**2), 2),
        },
        "system": {
            "os": platform.system(),
            "hostname": platform.node(),
            "uptime_hours": round(uptime.total_seconds() / 3600, 1),
        },
        "alerts": [],
    }

    # Check thresholds and generate alerts
    if cpu > ALERT_THRESHOLDS["cpu"]:
        alert = {"type": "cpu", "message": f"CPU usage critical: {cpu:.1f}%", "time": datetime.now().isoformat(), "level": "critical"}
        metrics["alerts"].append(alert)
        if len(active_alerts) == 0 or active_alerts[-1].get("type") != "cpu":
            active_alerts.append(alert)
            if len(active_alerts) > 20:
                active_alerts.pop(0)

    if memory.percent > ALERT_THRESHOLDS["memory"]:
        alert = {"type": "memory", "message": f"Memory usage high: {memory.percent:.1f}%", "time": datetime.now().isoformat(), "level": "warning"}
        metrics["alerts"].append(alert)

    if disk.percent > ALERT_THRESHOLDS["disk"]:
        alert = {"type": "disk", "message": f"Disk usage critical: {disk.percent:.1f}%", "time": datetime.now().isoformat(), "level": "critical"}
        metrics["alerts"].append(alert)

    # Update history
    history["cpu"].append(cpu)
    history["memory"].append(memory.percent)
    history["disk"].append(disk.percent)
    history["timestamps"].append(datetime.now().strftime("%H:%M:%S"))

    return metrics


@app.get("/", response_class=HTMLResponse)
async def root():
    with open("templates/index.html", "r") as f:
        return HTMLResponse(content=f.read())


@app.get("/api/metrics")
async def get_metrics():
    return get_system_metrics()


@app.get("/api/history")
async def get_history():
    return {
        "cpu": list(history["cpu"]),
        "memory": list(history["memory"]),
        "disk": list(history["disk"]),
        "timestamps": list(history["timestamps"]),
    }


@app.get("/api/alerts")
async def get_alerts():
    return {"alerts": active_alerts, "thresholds": ALERT_THRESHOLDS}


@app.post("/api/thresholds")
async def update_thresholds(cpu: float = 80, memory: float = 85, disk: float = 90):
    ALERT_THRESHOLDS["cpu"] = cpu
    ALERT_THRESHOLDS["memory"] = memory
    ALERT_THRESHOLDS["disk"] = disk
    return {"message": "Thresholds updated", "thresholds": ALERT_THRESHOLDS}


@app.get("/api/processes")
async def get_top_processes():
    processes = []
    for proc in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent", "status"]):
        try:
            info = proc.info
            processes.append({
                "pid": info["pid"],
                "name": info["name"],
                "cpu": round(info["cpu_percent"] or 0, 2),
                "memory": round(info["memory_percent"] or 0, 2),
                "status": info["status"],
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    processes.sort(key=lambda x: x["cpu"], reverse=True)
    return {"processes": processes[:10]}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_clients.append(websocket)
    try:
        while True:
            metrics = get_system_metrics()
            await websocket.send_text(json.dumps(metrics))
            await asyncio.sleep(2)
    except WebSocketDisconnect:
        connected_clients.remove(websocket)
    except Exception:
        if websocket in connected_clients:
            connected_clients.remove(websocket)
