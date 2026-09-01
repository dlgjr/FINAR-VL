"""Normalize official external finance datasets into the repository SFT schema."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Iterable


CFBENCHMARK_SOURCE = "https://github.com/TongjiFinLab/CFBenchmark"
CHART_TO_TEXT_SOURCE = "https://github.com/vis-nlp/Chart-to-text"
MME_FINANCE_SOURCE = "https://github.com/HiThink-Research/MME-Finance"

CF_TASK_ORIGINAL = {
    "entity_extraction_classification": "CFBenchmark/financial-entity-disambiguation",
    "portfolio_allocation_risk_return": "CFBenchmark/fund-analysis",
    "summary_announcement": "CFBenchmark/announcement-interpretation",
    "financial_audit_fundamentals": "CFBenchmark/stock-analysis",
}

CF_FILES = {
    "entity_extraction_classification": Path("金融判别/金融实体消歧.json"),
    "portfolio_allocation_risk_return": Path("金融分析/基金分析.json"),
    "summary_announcement": Path("金融解读/公告解读.json"),
    "financial_audit_fundamentals": Path("金融分析/股票分析.json"),
}

FINANCE_CHART_TERMS = (
    "bank", "business", "company", "companies", "consumer", "cost", "credit", "currency",
    "debt", "economic", "economy", "employment", "exchange rate", "finance", "financial",
    "fund", "gdp", "income", "industry", "inflation", "insurance", "investment", "market",
    "money", "price", "profit", "revenue", "sales", "share", "spending", "stock", "tax",
    "trade", "unemployment", "wage", "wealth",
)


def _criteria_answer(raw: dict[str, Any]) -> str:
    criteria = [
        value.get("content", "").strip()
        for key, value in sorted(raw.items())
        if key.startswith("criterium") and isinstance(value, dict) and value.get("content")
    ]
    return "\n".join(criteria)


def normalize_cfbenchmark_row(raw: dict[str, Any], capability: str) -> dict[str, Any]:
    question = str(raw["question"]).strip()
    if capability == "entity_extraction_classification":
        question = "\n".join(
            (question, f"A. {raw['A']}", f"B. {raw['B']}", f"C. {raw['C']}")
        )
        answer = str(raw["answer"]).strip()
    else:
        answer = _criteria_answer(raw)
    return {
        "messages": [
            {"role": "user", "content": question},
            {"role": "assistant", "content": answer},
        ],
        "source": f"CFBenchmark/{capability}/{raw.get('id')}",
        "split": "external",
        "task": capability,
        "task_original": CF_TASK_ORIGINAL[capability],
        "target_capability": capability,
        "provenance": {
            "dataset_url": CFBENCHMARK_SOURCE,
            "license": "research preview; non-commercial use",
            "original_id": str(raw.get("id", "")),
        },
    }


def normalize_chart_to_text_row(
    *,
    item_id: str,
    title: str,
    caption: str,
    image_path: Path,
    subset: str,
) -> dict[str, Any]:
    answer = f"该图表显示：{title.strip()}。{caption.strip()}"
    return {
        "messages": [
            {"role": "user", "content": "<image>请完整描述图片中展示的主要内容和关键信息。"},
            {"role": "assistant", "content": answer},
        ],
        "images": [image_path.as_posix()],
        "source": f"Chart-to-Text/{subset}/{item_id}",
        "split": "external",
        "task": "image_caption",
        "task_original": "Chart-to-Text/chart-summarization",
        "target_capability": "image_caption",
        "external_image_local": True,
        "provenance": {
            "dataset_url": CHART_TO_TEXT_SOURCE,
            "license": "GPL-3.0",
            "original_id": str(item_id),
            "subset": subset,
        },
    }


def qa_fingerprint(question: str, answer: str) -> str:
    normalized_question = re.sub(r"<image(?:\s+\d+)?>", " ", question, flags=re.IGNORECASE)
    payload = "\n".join(
        " ".join(text.casefold().split())
        for text in (normalized_question, answer)
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def benchmark_qa_fingerprints(path: Path) -> set[str]:
    fingerprints: set[str] = set()
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            question = " ".join(
                str(message.get("content", ""))
                for message in row.get("messages", [])
                if message.get("role") == "user"
            )
            answer = " ".join(
                str(message.get("content", ""))
                for message in row.get("messages", [])
                if message.get("role") == "assistant"
            )
            fingerprints.add(qa_fingerprint(question, answer))
    return fingerprints


def normalize_mme_finance_row(raw: dict[str, Any], image_root: Path) -> dict[str, Any]:
    question = re.sub(r"^(?:<image>\s*)+", "", str(raw["question"]).strip(), flags=re.IGNORECASE)
    image_path = image_root / Path(str(raw["image_path"]).replace("\\", "/"))
    original_id = str(raw.get("index", ""))
    task_category = str(raw.get("task_category", "")).strip()
    return {
        "messages": [
            {"role": "user", "content": f"<image>{question}"},
            {"role": "assistant", "content": str(raw["answer"]).strip()},
        ],
        "images": [image_path.as_posix()],
        "source": f"MME-Finance/MMfin_CN/{original_id}",
        "split": "external",
        "task": "external_mme_finance",
        "task_original": f"MME-Finance/{task_category}",
        "external_image_local": True,
        "provenance": {
            "dataset_url": MME_FINANCE_SOURCE,
            "license": "Apache-2.0",
            "original_id": original_id,
            "image_type": str(raw.get("image_type", "")),
            "image_style": str(raw.get("image_style", "")),
            "task_category": task_category,
        },
    }


def iter_cfbenchmark_rows(data_root: Path) -> Iterable[dict[str, Any]]:
    for capability, relative_path in CF_FILES.items():
        raw_rows = json.loads((data_root / relative_path).read_text(encoding="utf-8"))
        for raw in raw_rows:
            yield normalize_cfbenchmark_row(raw, capability)


def iter_chart_to_text_rows(repository_root: Path, limit: int) -> Iterable[dict[str, Any]]:
    selected = 0
    for subset, relative_root in (
        ("statista", Path("statista_dataset/dataset")),
        ("statista_multicolumn", Path("statista_dataset/dataset/multiColumn")),
    ):
        data_root = repository_root / relative_root
        title_dir = data_root / "titles"
        caption_dir = data_root / "captions"
        for title_path in sorted(title_dir.glob("*.txt"), key=lambda path: int(path.stem)):
            caption_path = caption_dir / title_path.name
            if not caption_path.exists():
                continue
            title = title_path.read_text(encoding="utf-8", errors="replace").strip()
            caption = caption_path.read_text(encoding="utf-8", errors="replace").strip()
            combined = f"{title} {caption}".casefold()
            if not any(term in combined for term in FINANCE_CHART_TERMS) or len(caption) < 24:
                continue
            image_path = data_root / "imgs" / f"{title_path.stem}.png"
            yield normalize_chart_to_text_row(
                item_id=title_path.stem,
                title=title,
                caption=caption,
                image_path=image_path,
                subset=subset,
            )
            selected += 1
            if selected >= limit:
                return


def iter_mme_finance_rows(
    tsv_path: Path,
    image_root: Path,
    excluded_qa_fingerprints: set[str] | None = None,
) -> Iterable[dict[str, Any]]:
    excluded = excluded_qa_fingerprints or set()
    with tsv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        for raw in csv.DictReader(handle, delimiter="\t"):
            question = str(raw.get("question", ""))
            answer = str(raw.get("answer", ""))
            if not question.strip() or not answer.strip():
                continue
            if qa_fingerprint(question, answer) in excluded:
                continue
            yield normalize_mme_finance_row(raw, image_root)


def write_rows(rows: Iterable[dict[str, Any]], output_path: Path) -> int:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with output_path.open("w", encoding="utf-8", buffering=1) as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
            count += 1
    return count


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--cf-data-root",
        type=Path,
        default=Path("data/external_multimodal/cfbenchmark/CFBenchmark-OpenFinData/data"),
    )
    parser.add_argument(
        "--chart-repository-root",
        type=Path,
        default=Path("data/external_multimodal/chart_to_text"),
    )
    parser.add_argument("--chart-limit", type=int, default=2000)
    parser.add_argument(
        "--mme-tsv",
        type=Path,
        default=Path("data/external_multimodal/mme_finance/data/MMfin_CN.tsv"),
    )
    parser.add_argument(
        "--mme-image-root",
        type=Path,
        default=Path("data/external_multimodal/mme_finance/data/MMfin_CN"),
    )
    parser.add_argument(
        "--benchmark",
        type=Path,
        default=Path("data/benchmark/my_benchmark/all.jsonl"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/external_multimodal/normalized_external_candidates.jsonl"),
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rows = [
        *iter_cfbenchmark_rows(args.cf_data_root),
        *iter_chart_to_text_rows(args.chart_repository_root, args.chart_limit),
    ]
    if args.mme_tsv.exists() and args.mme_image_root.exists():
        rows.extend(
            iter_mme_finance_rows(
                args.mme_tsv,
                args.mme_image_root,
                benchmark_qa_fingerprints(args.benchmark),
            )
        )
    count = write_rows(rows, args.output)
    print(json.dumps({"rows": count}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
