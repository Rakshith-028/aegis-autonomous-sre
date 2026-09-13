import json
import threading
import uuid
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any


INCIDENT_DIR = Path("backend/incidents/data")
INCIDENT_LOG_PATH = INCIDENT_DIR / "incidents.jsonl"
STATE_PATH = INCIDENT_DIR / "incident_state.json"

_lock = threading.Lock()


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _load_state() -> dict:
    if not STATE_PATH.exists():
        return {"incidents": []}

    try:
        with STATE_PATH.open("r", encoding="utf-8") as file:
            data = json.load(file)

        if not isinstance(data, dict):
            return {"incidents": []}

        data.setdefault("incidents", [])
        return data

    except (json.JSONDecodeError, OSError):
        return {"incidents": []}


def _save_state(state: dict) -> None:
    INCIDENT_DIR.mkdir(parents=True, exist_ok=True)

    temporary_path = STATE_PATH.with_suffix(".tmp")

    with temporary_path.open("w", encoding="utf-8") as file:
        json.dump(
            state,
            file,
            indent=2,
            ensure_ascii=False,
        )

    temporary_path.replace(STATE_PATH)


def _append_event(event: dict) -> None:
    INCIDENT_DIR.mkdir(parents=True, exist_ok=True)

    with INCIDENT_LOG_PATH.open("a", encoding="utf-8") as file:
        file.write(
            json.dumps(
                event,
                ensure_ascii=False,
            )
            + "\n"
        )


def _make_incident(
    service_name: str,
    reason: str,
    incident_key: str,
    severity: str,
    source: str,
    failure_type: str,
    metadata: dict[str, Any] | None,
) -> dict:
    timestamp = _now()

    return {
        "id": f"INC-{uuid.uuid4().hex[:8].upper()}",
        "incident_key": incident_key,
        "service": service_name,
        "status": "OPEN",
        "severity": severity,
        "source": source,
        "failure_type": failure_type,
        "reason": reason,
        "started_at": timestamp,
        "updated_at": timestamp,
        "resolved_at": None,
        "remediation": None,
        "metadata": metadata or {},
    }


def create_or_get_incident(
    service_name: str,
    incident_key: str,
    reason: str,
    severity: str = "MEDIUM",
    source: str = "unknown",
    failure_type: str = "UNKNOWN",
    metadata: dict[str, Any] | None = None,
) -> tuple[dict, bool]:
    with _lock:
        state = _load_state()

        for incident in state["incidents"]:
            if (
                incident.get("service") == service_name
                and incident.get("incident_key") == incident_key
                and incident.get("status") == "OPEN"
            ):
                incident["updated_at"] = _now()
                incident["reason"] = reason

                if metadata:
                    incident.setdefault("metadata", {}).update(metadata)

                _save_state(state)

                return deepcopy(incident), False

        incident = _make_incident(
            service_name=service_name,
            reason=reason,
            incident_key=incident_key,
            severity=severity,
            source=source,
            failure_type=failure_type,
            metadata=metadata,
        )

        state["incidents"].append(incident)
        _save_state(state)

        _append_event(
            {
                "event": "INCIDENT_OPENED",
                "timestamp": _now(),
                **incident,
            }
        )

        return deepcopy(incident), True


def create_incident(
    service_name: str,
    reason: str,
    severity: str = "HIGH",
    source: str = "health_monitor",
    failure_type: str = "SERVICE_FAILURE",
    metadata: dict[str, Any] | None = None,
) -> dict:
    unique_key = (
        f"{source}:{failure_type}:"
        f"{uuid.uuid4().hex[:8]}"
    )

    incident, _ = create_or_get_incident(
        service_name=service_name,
        incident_key=unique_key,
        reason=reason,
        severity=severity,
        source=source,
        failure_type=failure_type,
        metadata=metadata,
    )

    return incident


def get_active_incident(
    service_name: str,
    incident_key: str,
) -> dict | None:
    with _lock:
        state = _load_state()

        for incident in state["incidents"]:
            if (
                incident.get("service") == service_name
                and incident.get("incident_key") == incident_key
                and incident.get("status") == "OPEN"
            ):
                return deepcopy(incident)

    return None


def resolve_incident(
    incident: dict,
    remediation: str,
    metadata: dict[str, Any] | None = None,
) -> dict:
    with _lock:
        state = _load_state()

        for stored_incident in state["incidents"]:
            if stored_incident.get("id") != incident.get("id"):
                continue

            if stored_incident.get("status") == "RESOLVED":
                return deepcopy(stored_incident)

            timestamp = _now()

            stored_incident["status"] = "RESOLVED"
            stored_incident["updated_at"] = timestamp
            stored_incident["resolved_at"] = timestamp
            stored_incident["remediation"] = remediation

            if metadata:
                stored_incident.setdefault(
                    "metadata",
                    {}
                ).update(metadata)

            _save_state(state)

            _append_event(
                {
                    "event": "INCIDENT_RESOLVED",
                    "timestamp": timestamp,
                    **stored_incident,
                }
            )

            return deepcopy(stored_incident)

    return incident


def list_incidents() -> list[dict]:
    with _lock:
        state = _load_state()

    return deepcopy(state["incidents"])


def list_active_incidents() -> list[dict]:
    return [
        incident
        for incident in list_incidents()
        if incident.get("status") == "OPEN"
    ]

def initialize_incident_state() -> None:
    with _lock:
        INCIDENT_DIR.mkdir(parents=True, exist_ok=True)

        if not STATE_PATH.exists():
            _save_state({"incidents": []})


initialize_incident_state()
