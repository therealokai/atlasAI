import os
import logging

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("gateway")

# "vllm" here is the Compose SERVICE NAME, same DNS trick your migrate
# service already relies on for postgres — only resolves inside the
# compose network, not from your host.
VLLM_BASE_URL = os.getenv("VLLM_BASE_URL", "http://vllm:8000")
REQUEST_TIMEOUT = float(os.getenv("GATEWAY_TIMEOUT", "60"))

app = FastAPI(title="Real Estate AI Gateway", version="0.1.0")


@app.get("/health")
async def health():
    """
    Checks that vLLM is actually reachable — not just "is this process
    alive" (trivially true if this code is running at all).
    """
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{VLLM_BASE_URL}/health")
        if resp.status_code == 200:
            return {"status": "ok", "vllm": "reachable"}
        return JSONResponse(
            status_code=503,
            content={"status": "degraded", "vllm": "unreachable", "vllm_status_code": resp.status_code},
        )
    except httpx.RequestError as e:
        logger.error(f"vLLM health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={"status": "degraded", "vllm": "unreachable", "error": str(e)},
        )


@app.post("/v1/chat")
async def chat(payload: dict):
    """
    Pure pass-through to vLLM's OpenAI-compatible endpoint. Deliberately
    dumb: no router, no PII scrubbing, no tools, no retries, no caching.
    Today's only job is proving gateway -> vLLM -> real response works.
    """
    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            resp = await client.post(
                f"{VLLM_BASE_URL}/v1/chat/completions",
                json=payload,
            )
        return JSONResponse(status_code=resp.status_code, content=resp.json())
    except httpx.RequestError as e:
        logger.error(f"vLLM request failed: {e}")
        raise HTTPException(status_code=502, detail=f"vLLM unreachable: {e}")