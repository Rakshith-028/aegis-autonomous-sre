import json
from datetime import datetime
from pathlib import Path


POSTMORTEM_DIR = Path(
    "backend/incidents/data/postmortems"
)


def generate_postmortem(
    incident: dict,
    rca: dict,
    policy: dict,
    remediation: dict,
    verification: list[dict],
) -> Path:

    POSTMORTEM_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    created_at = datetime.now().isoformat(
        timespec="seconds"
    )

    document = {
        "incident_id": incident["id"],
        "service": incident["service"],
        "created_at": created_at,
        "incident": incident,
        "root_cause_analysis": rca,
        "policy_decision": policy,
        "remediation": remediation,
        "verification": verification,
        "summary": (
            f"AEGIS detected {rca['root_cause']} "
            f"with confidence "
            f"{rca['confidence']:.2f}. "
            f"Selected action "
            f"{rca['recommended_action']}."
        ),
    }

    path = (
        POSTMORTEM_DIR
        / f"{incident['id']}.json"
    )

    with path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            document,
            file,
            indent=2,
            ensure_ascii=False,
        )

    return path
