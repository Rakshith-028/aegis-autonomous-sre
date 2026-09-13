import os


PROMETHEUS_URL = os.getenv(
    "PROMETHEUS_URL",
    "http://localhost:9090",
)

ORDERS_URL = os.getenv(
    "ORDERS_URL",
    "http://localhost:8001",
)

HEALTH_URL = os.getenv(
    "HEALTH_URL",
    f"{ORDERS_URL}/health",
)

CONTAINER_NAME = os.getenv(
    "CONTAINER_NAME",
    "aegis-orders",
)

SERVICE_NAME = os.getenv(
    "SERVICE_NAME",
    "orders",
)

MAX_REMEDIATION_ATTEMPTS = int(
    os.getenv(
        "MAX_REMEDIATION_ATTEMPTS",
        "2",
    )
)
