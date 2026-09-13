import asyncio
import random
import time

from fastapi import FastAPI, Request, Response
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Histogram,
    generate_latest,
)


app = FastAPI(title="AEGIS Orders Service")

chaos_mode = "normal"


REQUEST_COUNT = Counter(
    "orders_requests_total",
    "Total requests",
    ["method", "endpoint", "status_code"],
)

REQUEST_LATENCY = Histogram(
    "orders_request_latency_seconds",
    "Request latency",
    ["method", "endpoint"],
)

ERROR_COUNT = Counter(
    "orders_errors_total",
    "Total errors",
    ["endpoint"],
)


@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start = time.perf_counter()
    status_code = 500

    try:
        response = await call_next(request)
        status_code = response.status_code

        if status_code >= 500:
            ERROR_COUNT.labels(
                endpoint=request.url.path
            ).inc()

        return response

    except Exception:
        ERROR_COUNT.labels(
            endpoint=request.url.path
        ).inc()
        raise

    finally:
        duration = time.perf_counter() - start

        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.url.path,
            status_code=str(status_code),
        ).inc()

        REQUEST_LATENCY.labels(
            method=request.method,
            endpoint=request.url.path,
        ).observe(duration)


@app.get("/")
async def root(response: Response):
    if chaos_mode == "latency":
        await asyncio.sleep(1.5)

    elif chaos_mode == "errors":
        if random.random() < 0.70:
            response.status_code = 500

            return {
                "service": "orders",
                "status": "error",
                "reason": "simulated request failure",
            }

    return {
        "service": "orders",
        "status": "running",
        "chaos_mode": chaos_mode,
    }


@app.get("/health")
async def health(response: Response):
    if chaos_mode == "health_error":
        response.status_code = 500

        return {
            "service": "orders",
            "status": "unhealthy",
        }

    if chaos_mode == "health_slow":
        await asyncio.sleep(5)

    return {
        "service": "orders",
        "status": "healthy",
        "chaos_mode": chaos_mode,
    }


@app.get("/metrics")
def metrics():
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )


@app.post("/chaos/latency")
def chaos_latency():
    global chaos_mode
    chaos_mode = "latency"

    return {"chaos_mode": chaos_mode}


@app.post("/chaos/errors")
def chaos_errors():
    global chaos_mode
    chaos_mode = "errors"

    return {"chaos_mode": chaos_mode}


@app.post("/chaos/error")
def chaos_health_error():
    global chaos_mode
    chaos_mode = "health_error"

    return {"chaos_mode": chaos_mode}


@app.post("/chaos/slow")
def chaos_health_slow():
    global chaos_mode
    chaos_mode = "health_slow"

    return {"chaos_mode": chaos_mode}


@app.post("/chaos/reset")
def chaos_reset():
    global chaos_mode
    chaos_mode = "normal"

    return {"chaos_mode": chaos_mode}
