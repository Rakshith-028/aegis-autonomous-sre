import asyncio
import json
from pathlib import Path

import requests
from fastapi import (
    FastAPI,
    HTTPException,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.middleware.cors import (
    CORSMiddleware,
)

from backend.api.autonomous_engine import (
    AutonomousEngine,
)
from backend.config import ORDERS_URL
from backend.incidents.incident_manager import (
    list_active_incidents,
    list_incidents,
)
from backend.rca.evidence_collector import (
    EvidenceCollector,
)
from backend.rca.rca_engine import RCAEngine


app = FastAPI(
    title="AEGIS Control Plane",
    version="1.0.0",
    description=(
        "Autonomous AI SRE and "
        "self-healing control plane"
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


collector = EvidenceCollector()
rca_engine = RCAEngine()


@app.get("/")
def root():
    return {
        "system": "AEGIS",
        "role": "Autonomous AI SRE",
        "status": "online",
        "version": "1.0.0",
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "component": (
            "aegis-control-plane"
        ),
    }


@app.get("/api/status")
def system_status():
    evidence = collector.collect()

    rca = rca_engine.analyze(
        evidence
    )

    return {
        "system": "AEGIS",
        "service": "orders",
        "evidence": evidence,
        "rca": rca.to_dict(),
        "active_incidents": (
            list_active_incidents()
        ),
    }


@app.get("/api/incidents")
def incidents():
    data = list_incidents()

    data.sort(
        key=lambda item: item.get(
            "started_at",
            "",
        ),
        reverse=True,
    )

    return {
        "count": len(data),
        "incidents": data,
    }


@app.get("/api/incidents/active")
def active_incidents():
    data = list_active_incidents()

    return {
        "count": len(data),
        "incidents": data,
    }


@app.post("/api/cycle/run")
def run_autonomous_cycle():
    engine = AutonomousEngine()

    return engine.run_once()


@app.post("/api/chaos/{mode}")
def inject_chaos(mode: str):
    allowed = {
        "latency": "latency",
        "errors": "errors",
        "health-error": "error",
        "health-slow": "slow",
        "reset": "reset",
    }

    endpoint = allowed.get(mode)

    if endpoint is None:
        raise HTTPException(
            status_code=400,
            detail=(
                "Supported modes: latency, "
                "errors, health-error, "
                "health-slow, reset"
            ),
        )

    try:
        response = requests.post(
            f"{ORDERS_URL}/chaos/{endpoint}",
            timeout=5,
        )

        response.raise_for_status()

        return {
            "success": True,
            "mode": mode,
            "service_response": (
                response.json()
            ),
        }

    except requests.RequestException as error:
        raise HTTPException(
            status_code=503,
            detail=str(error),
        )


@app.get("/api/postmortems")
def postmortems():
    directory = Path(
        "backend/incidents/data/"
        "postmortems"
    )

    if not directory.exists():
        return {
            "count": 0,
            "postmortems": [],
        }

    results = []

    paths = sorted(
        directory.glob("*.json"),
        key=lambda path: (
            path.stat().st_mtime
        ),
        reverse=True,
    )

    for path in paths:
        try:
            with path.open(
                "r",
                encoding="utf-8",
            ) as file:
                results.append(
                    json.load(file)
                )

        except (
            OSError,
            json.JSONDecodeError,
        ):
            continue

    return {
        "count": len(results),
        "postmortems": results,
    }


@app.websocket("/ws/live")
async def live_socket(
    websocket: WebSocket,
):
    await websocket.accept()

    try:
        while True:
            evidence = await asyncio.to_thread(
                collector.collect
            )

            rca = await asyncio.to_thread(
                rca_engine.analyze,
                evidence,
            )

            active = await asyncio.to_thread(
                list_active_incidents
            )

            await websocket.send_json(
                {
                    "type": "SYSTEM_UPDATE",
                    "service": "orders",
                    "evidence": evidence,
                    "rca": rca.to_dict(),
                    "active_incidents": active,
                }
            )

            await asyncio.sleep(3)

    except WebSocketDisconnect:
        return

    except Exception as error:
        try:
            await websocket.send_json(
                {
                    "type": "ERROR",
                    "detail": str(error),
                }
            )
        except Exception:
            pass
