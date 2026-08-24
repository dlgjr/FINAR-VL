"""Offline fixed-claim extraction using the Thinking judge service.

This command is run on DSW before DLC. The resulting JSON cache is an input to
``prepare_gspo_data.py``; training never calls the claim-splitting mode.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import urllib.request
from pathlib import Path
from typing import Any


def _request(url: str, model: str, question: str, solution: str) -> list[str]:
    prompt = (
        "将标准答案拆成最小、可独立核验的固定主张。只返回 JSON 数组，每项是主张文本；"
        "不要编号、Markdown 或解释。保留答案中的数值、单位、对象和条件。\n"
        f"问题：{question}\n标准答案：{solution}"
    )
    payload = json.dumps(
        {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.6,
            "top_p": 0.95,
            "top_k": 20,
            "max_tokens": 2048,
            "chat_template_kwargs": {"enable_thinking": True},
        },
        ensure_ascii=False,
    ).encode("utf-8")
    request = urllib.request.Request(url.rstrip("/") + "/v1/chat/completions", data=payload, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(request, timeout=300) as response:
        body = json.loads(response.read().decode("utf-8"))
    content = str(body["choices"][0]["message"]["content"])
    try:
        claims = json.loads(content)
    except json.JSONDecodeError:
        match = re.search(r"\[[\s\S]*\]", content)
        if match is None:
            raise
        claims = json.loads(match.group(0))
    if not isinstance(claims, list) or not claims or not all(isinstance(item, str) and item.strip() for item in claims):
        raise ValueError("claim response must be a non-empty JSON string array")
    return [item.strip() for item in claims]


def generate_claim_cache(input_path: str | Path, output_path: str | Path, *, url: str, model: str) -> dict[str, Any]:
    cache: dict[str, list[str]] = {}
    errors: list[dict[str, Any]] = []
    with open(input_path, encoding="utf-8") as source:
        for line_number, line in enumerate(source, 1):
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("output_format") not in {"free_text", "short_or_explanatory_text"} and row.get("output_format") is not None:
                continue
            sample_id = str((row.get("_pass_at_k") or {}).get("result_index") or f"line:{line_number}")
            messages = row.get("messages", [])
            question = "\n".join(str(message.get("content", "")) for message in messages if message.get("role") == "user")
            solution = next((str(message.get("content", "")) for message in reversed(messages) if message.get("role") == "assistant"), "")
            try:
                claims = _request(url, model, question, solution)
            except Exception as error:
                errors.append({"sample_id": sample_id, "line": line_number, "error": str(error)})
                continue
            cache[sample_id] = [{"id": f"G{index}", "text": claim} for index, claim in enumerate(claims, 1)]
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_path).write_text(json.dumps(cache, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report = {"total_claim_records": len(cache), "errors": errors, "model": model, "thinking": True}
    Path(str(output_path) + ".audit.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if errors:
        raise RuntimeError(f"gold claim generation failed for {len(errors)} records")
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input")
    parser.add_argument("output")
    parser.add_argument("--url", default=os.environ.get("GSPO_CLAIM_JUDGE_URL", "http://127.0.0.1:8001"))
    parser.add_argument("--model", default=os.environ.get("GSPO_JUDGE_SERVE_NAME", "qwen235-judge"))
    args = parser.parse_args()
    generate_claim_cache(args.input, args.output, url=args.url, model=args.model)


if __name__ == "__main__":
    main()
