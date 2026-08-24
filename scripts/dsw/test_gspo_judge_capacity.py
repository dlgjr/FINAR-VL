"""DSW-only judge capacity probe for concurrency 2 and 4."""

from __future__ import annotations

import argparse
import json
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


def request(url: str, model: str, prompt: str, max_tokens: int, image_urls: list[str]) -> tuple[float, bool]:
    content = [
        *({"type": "image_url", "image_url": {"url": image_url}} for image_url in image_urls),
        {"type": "text", "text": prompt},
    ]
    payload = json.dumps(
        {
            "model": model,
            "messages": [{"role": "user", "content": content}],
            "temperature": 0,
            "max_tokens": max_tokens,
            "response_format": {"type": "json_object"},
            "chat_template_kwargs": {"enable_thinking": False, "thinking": False},
        }
    ).encode()
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
    parser.add_argument("--model", default="qwen235-judge")
    parser.add_argument("--prompt", default="Return JSON {\"ok\":true}.")
    parser.add_argument("--max-tokens", type=int, default=64)
    parser.add_argument("--image", action="append", default=[])
    args = parser.parse_args()
    image_urls = [Path(image).expanduser().resolve().as_uri() for image in args.image]
    cases = [("text", [])]
    if image_urls:
        cases.append(("multimodal", image_urls))
    for case, case_images in cases:
        for concurrency in (2, 4):
            started = time.perf_counter()
            with ThreadPoolExecutor(max_workers=concurrency) as pool:
                results = list(
                    pool.map(
                        lambda _: request(args.url, args.model, args.prompt, args.max_tokens, case_images),
                        range(concurrency),
                    )
                )
            elapsed = time.perf_counter() - started
            print(json.dumps({"case": case, "concurrency": concurrency, "elapsed_seconds": elapsed, "latencies": [r[0] for r in results], "json_valid": sum(r[1] for r in results) / concurrency}, ensure_ascii=False))


if __name__ == "__main__":
    main()
