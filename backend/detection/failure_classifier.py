def classify_failure(detail: str) -> str:
    detail_lower = detail.lower()

    if "500" in detail_lower:
        return "HTTP_ERROR"

    if "timed out" in detail_lower or "timeout" in detail_lower:
        return "TIMEOUT"

    if (
        "connection refused" in detail_lower
        or "max retries exceeded" in detail_lower
        or "connection aborted" in detail_lower
    ):
        return "SERVICE_DOWN"

    return "UNKNOWN_FAILURE"
