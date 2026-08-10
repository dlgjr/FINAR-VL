"""DSW-only judge capacity probe for concurrency 2 and 4."""

from __future__ import annotations

import argparse
import json
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor


def request(url: str, model: str, prompt: str) -> tuple[float, bool]:
    payload = json.dumps({"model": model, "messages": [{"role": "user", "content": prompt}], "temperature": 0, "max_tokens": 32, "response_format": {"type": "json_object"}}).encode()
    started = time.perf_counter()
    try:
        req = urllib.request.Request(url.rstrip("/") + "/v1/chat/completions", data=payload, headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=300) as response:
            body = json.loads(response.read().decode())
        valid = isinstance(body.get("choices", [{}])[0].get("message", {}).get("content"), str)
    except Exception:
        valid = False
    return time.perf_counter() - started, valid


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:8001")
    parser.add_argument("--model", default="qwen3-judge")
    parser.add_argument("--prompt", default="Return JSON {\"ok\":true}.")
    args = parser.parse_args()
    for concurrency in (2, 4):
        started = time.perf_counter()
        with ThreadPoolExecutor(max_workers=concurrency) as pool:
            results = list(pool.map(lambda _: request(args.url, args.model, args.prompt), range(concurrency)))
        elapsed = time.perf_counter() - started
        print(json.dumps({"concurrency": concurrency, "elapsed_seconds": elapsed, "latencies": [r[0] for r in results], "json_valid": sum(r[1] for r in results) / concurrency}, ensure_ascii=False))


if __name__ == "__main__":
    main()

