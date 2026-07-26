"""
eval/run_golden_set.py

Day 8 — runs every prompt in eval/golden-set-v1.json through the serving
endpoint (gateway's /v1/chat pass-through, or vLLM directly) and writes
a new file with the model's actual completions alongside the reference
responses, so you can eyeball quality across all 200 records instead of
curl-ing them one at a time.

Usage:
    python eval/run_golden_set.py
    python eval/run_golden_set.py --target vllm        # hit vLLM directly, bypass gateway
    python eval/run_golden_set.py --concurrency 8       # more parallel requests
    python eval/run_golden_set.py --limit 10            # smoke-test on first 10 only
"""

import argparse
import asyncio
import json
import sys
import time
from pathlib import Path

import httpx

MODEL_NAME = "Qwen/Qwen2.5-3B-Instruct-AWQ"

# Not wired into the gateway itself yet (Day 7's gateway is a pure
# pass-through, no router, no system prompt injection). Adding it here,
# in the eval harness, keeps that separation honest — the gateway stays
# dumb, but we still evaluate the model with the persona AtlasAI will
# actually use in production.
SYSTEM_PROMPT = (
    "أنت أطلس، مساعد عقاري ذكي. تتحدث دائمًا باللغة العربية الفصحى، "
    "بأسلوب مختصر وواضح ومباشر، مثل محادثة إنسانية طبيعية وليس كإجابة رسمية طويلة."
)

ENDPOINTS = {
    "gateway": "http://localhost:8081/v1/chat",
    "vllm": "http://localhost:8000/v1/chat/completions",
}


def build_payload(prompt: str) -> dict:
    return {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        "max_tokens": 300,
        "temperature": 0.3,
    }


def extract_text(resp_json: dict) -> str:
    """Pull the assistant's text out of an OpenAI-style chat completion response."""
    try:
        return resp_json["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError, TypeError):
        return f"[UNPARSEABLE RESPONSE: {json.dumps(resp_json, ensure_ascii=False)[:300]}]"


async def run_one(client: httpx.AsyncClient, url: str, record: dict, sem: asyncio.Semaphore) -> dict:
    async with sem:
        payload = build_payload(record["prompt"])
        start = time.monotonic()
        try:
            resp = await client.post(url, json=payload, timeout=60.0)
            resp.raise_for_status()
            model_response = extract_text(resp.json())
            error = None
        except (httpx.HTTPError, httpx.TimeoutException) as e:
            model_response = ""
            error = str(e)
        latency_ms = round((time.monotonic() - start) * 1000, 1)

    return {
        "id": record["id"],
        "prompt": record["prompt"],
        "reference_response": record["response"],
        "model_response": model_response,
        "message_type": record["message_type"],
        "dialect": record["dialect"],
        "model_name": MODEL_NAME,
        "latency_ms": latency_ms,
        "error": error,
    }


async def main(input_path: Path, output_path: Path, url: str, concurrency: int, limit: int | None):
    records = json.loads(input_path.read_text(encoding="utf-8"))
    if limit:
        records = records[:limit]

    total = len(records)
    print(f"Running {total} records against {url} (concurrency={concurrency})")

    sem = asyncio.Semaphore(concurrency)
    results = []
    checkpoint_every = 20

    async with httpx.AsyncClient() as client:
        tasks = [asyncio.create_task(run_one(client, url, r, sem)) for r in records]

        for i, task in enumerate(asyncio.as_completed(tasks), start=1):
            result = await task
            results.append(result)

            status = "OK" if not result["error"] else f"ERROR: {result['error'][:80]}"
            print(f"[{i}/{total}] {result['id']} ({result['latency_ms']}ms) — {status}")

            # Checkpoint periodically so a crash mid-run doesn't lose everything.
            if i % checkpoint_every == 0:
                _write(output_path.with_suffix(".partial.json"), results)

    # Results arrive out of order (asyncio.as_completed) — restore original order by id.
    results.sort(key=lambda r: r["id"])
    _write(output_path, results)

    errors = [r for r in results if r["error"]]
    avg_latency = sum(r["latency_ms"] for r in results) / len(results) if results else 0
    print(f"\nDone. {len(results)} records written to {output_path}")
    print(f"Errors: {len(errors)} | Avg latency: {avg_latency:.1f}ms")
    if errors:
        print("First few errors:")
        for e in errors[:5]:
            print(f"  {e['id']}: {e['error']}")

    partial = output_path.with_suffix(".partial.json")
    if partial.exists():
        partial.unlink()


def _write(path: Path, results: list[dict]):
    path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="eval/golden-set-v1.json")
    parser.add_argument("--output", default="eval/golden-set-v1-results.json")
    parser.add_argument("--target", choices=["gateway", "vllm"], default="vllm")
    parser.add_argument("--concurrency", type=int, default=4)
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    url = ENDPOINTS[args.target]
    asyncio.run(main(input_path, Path(args.output), url, args.concurrency, args.limit))