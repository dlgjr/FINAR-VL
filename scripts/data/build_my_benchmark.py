from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, field
import csv
import json
import math
from pathlib import Path
import re
import shutil
from typing import Any
import zipfile

import pyarrow.parquet as pq


ROOT = Path(__file__).resolve().parents[2]
BENCHMARK_ROOT = ROOT / "data" / "benchmark"
OUTPUT_ROOT = BENCHMARK_ROOT / "my_benchmark"
ASSETS_ROOT = OUTPUT_ROOT / "assets"
OUTPUT_JSONL = OUTPUT_ROOT / "all.jsonl"

TASK_QUOTAS = {
    "image_caption": 7,
    "financial_ocr": 7,
    "entity_extraction_classification": 8,
    "spatial_localization": 7,
    "single_table_qa": 12,
    "multi_table_reasoning": 20,
    "chart_data_extraction": 10,
    "relationship_equity_structure": 7,
    "basic_arithmetic_metrics": 7,
    "statistics_comparison_ranking": 7,
    "candlestick_time_series": 7,
    "multi_step_numerical_reasoning": 12,
    "cross_modal_multi_hop": 10,
    "long_document_cross_page": 8,
    "evidence_retrieval": 8,
    "multimodal_financial_knowledge": 7,
    "explanation_anomaly_causality": 7,
    "financial_audit_fundamentals": 7,
    "industry_trend_inference": 7,
    "risk_sentiment_policy": 7,
    "investment_advice_strategy": 7,
    "portfolio_allocation_risk_return": 7,
    "summary_announcement": 7,
    "compliance_safety_suitability": 7,
}


@dataclass(frozen=True)
class MediaSpec:
    kind: str
    suffix: str
    path: Path | None = None
    data: bytes | None = None
    archive: Path | None = None
    member: str | None = None


@dataclass
class Candidate:
    task: str
    benchmark: str
    source_id: str
    question: str
    answer: Any
    choices: Any = None
    media: list[MediaSpec] = field(default_factory=list)

    @property
    def source(self) -> str:
        return f"{self.benchmark}/{self.source_id}"


def clean_text(value: Any) -> str:
    if isinstance(value, float) and math.isnan(value):
        return ""
    text = "" if value is None else str(value)
    if text.strip().lower() == "nan":
        return ""
    text = re.sub(r"<image(?:_\d+)?>", "", text)
    return text.replace("\\n", "\n").strip()


def format_choices(choices: Any) -> str:
    if not choices:
        return ""
    if isinstance(choices, dict):
        lines = [f"{key}. {value}" for key, value in choices.items()]
    else:
        lines = [str(value) for value in choices]
    return "\n" + "\n".join(lines)


def image_suffix(data: bytes, fallback: str = ".png") -> str:
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png"
    if data.startswith(b"\xff\xd8\xff"):
        return ".jpg"
    if data.startswith((b"GIF87a", b"GIF89a")):
        return ".gif"
    return fallback if fallback.startswith(".") else f".{fallback}"


def rubric_answer(row: dict[str, Any]) -> str:
    criteria = []
    for key in sorted(row):
        if not key.startswith("criterium"):
            continue
        value = row[key]
        if isinstance(value, dict):
            content = clean_text(value.get("content"))
        else:
            content = clean_text(value)
        if content:
            criteria.append(content)
    return "\n".join(criteria)


def add_choice_candidates(
    candidates: list[Candidate],
    task: str,
    benchmark: str,
    source_prefix: str,
    rows: list[dict[str, Any]],
) -> None:
    for index, row in enumerate(rows):
        answer = clean_text(row.get("answer"))
        question = clean_text(row.get("question"))
        if not question or not answer or answer.lower() == "nan":
            continue
        choices = {
            key: clean_text(row[key])
            for key in ("A", "B", "C", "D", "E")
            if clean_text(row.get(key))
        }
        candidates.append(
            Candidate(
                task=task,
                benchmark=benchmark,
                source_id=f"{source_prefix}-{row.get('id', index)}",
                question=question,
                answer=answer,
                choices=choices,
            )
        )


def load_cfbenchmark() -> list[Candidate]:
    base = (
        BENCHMARK_ROOT
        / "CFBenchmark-main"
        / "CFBenchmark-main"
        / "CFBenchmark-OpenFinData"
        / "data"
    )
    candidates: list[Candidate] = []

    entity_files = [
        ("金融判别/金融实体识别.json", "entity-recognition"),
        ("金融判别/金融实体消歧.json", "entity-disambiguation"),
        ("金融计算/金融数值提取.json", "value-extraction"),
    ]
    for relative, prefix in entity_files:
        rows = json.loads((base / relative).read_text(encoding="utf-8"))
        add_choice_candidates(
            candidates,
            "entity_extraction_classification",
            "CFBenchmark",
            prefix,
            rows,
        )

    metric_rows = json.loads(
        (base / "金融计算/金融指标计算.json").read_text(encoding="utf-8")
    )
    add_choice_candidates(
        candidates,
        "basic_arithmetic_metrics",
        "CFBenchmark",
        "metric-calculation",
        metric_rows,
    )

    rubric_sources = [
        (
            "金融分析/股票分析.json",
            "financial_audit_fundamentals",
            "stock-analysis",
        ),
        (
            "金融分析/基金分析.json",
            "portfolio_allocation_risk_return",
            "fund-analysis",
        ),
        (
            "金融分析/行业板块分析.json",
            "industry_trend_inference",
            "sector-analysis",
        ),
        (
            "金融解读/行业解读.json",
            "industry_trend_inference",
            "industry-interpretation",
        ),
        (
            "金融解读/公告解读.json",
            "summary_announcement",
            "announcement-interpretation",
        ),
    ]
    for relative, task, prefix in rubric_sources:
        rows = json.loads((base / relative).read_text(encoding="utf-8"))
        for index, row in enumerate(rows):
            question = clean_text(row.get("question"))
            answer = rubric_answer(row)
            if question and answer:
                candidates.append(
                    Candidate(
                        task=task,
                        benchmark="CFBenchmark",
                        source_id=f"{prefix}-{row.get('id', index)}",
                        question=question,
                        answer=answer,
                    )
                )
    return candidates


def load_mme_finance() -> list[Candidate]:
    base = BENCHMARK_ROOT / "MME-Finance" / "MME-Finance"
    archive = base / "MMfin_CN.zip"
    rows = list(
        csv.DictReader(
            (base / "MMfin_CN.tsv").open(encoding="utf-8"), delimiter="\t"
        )
    )
    with zipfile.ZipFile(archive) as zipped:
        members = {name.replace("\\", "/") for name in zipped.namelist()}

    category_tasks = {
        "Image Caption": "image_caption",
        "OCR": "financial_ocr",
        "Spatial Awareness": "spatial_localization",
        "Financial Knowledge": "multimodal_financial_knowledge",
        "Explain Reason": "explanation_anomaly_causality",
        "Risk Warning": "risk_sentiment_policy",
        "Investment Advice": "investment_advice_strategy",
    }
    compliance_pattern = re.compile(
        r"合规|监管|适当性|信息披露|退市|沪股通|陆股通|险资举牌|证券法"
    )
    candidates: list[Candidate] = []
    for row in rows:
        question = clean_text(row.get("question"))
        answer = clean_text(row.get("answer"))
        image_path = clean_text(row.get("image_path")).replace("\\", "/")
        member = f"MMfin_CN/{image_path}"
        if not question or not answer or member not in members:
            continue
        media = [
            MediaSpec(
                kind="zip",
                archive=archive,
                member=member,
                suffix=Path(image_path).suffix or ".png",
            )
        ]
        source_id = clean_text(row.get("index"))
        category = clean_text(row.get("task_category"))
        image_type = clean_text(row.get("image_type"))
        task = category_tasks.get(category)
        if (
            task == "spatial_localization"
            and "第一行" in question
            and "第二行" in answer
        ):
            task = None
        if task and not (task == "image_caption" and image_type == "candlestick"):
            candidates.append(
                Candidate(
                    task=task,
                    benchmark="MME-Finance",
                    source_id=source_id,
                    question=question,
                    answer=answer,
                    media=media,
                )
            )
        if image_type == "candlestick":
            candidates.append(
                Candidate(
                    task="candlestick_time_series",
                    benchmark="MME-Finance",
                    source_id=source_id,
                    question=question,
                    answer=answer,
                    media=media,
                )
            )
        if category == "Financial Knowledge" and compliance_pattern.search(
            f"{question}\n{answer}"
        ):
            candidates.append(
                Candidate(
                    task="compliance_safety_suitability",
                    benchmark="MME-Finance",
                    source_id=source_id,
                    question=question,
                    answer=answer,
                    media=media,
                )
            )
    return candidates


def parquet_media(row: dict[str, Any], fields: list[str]) -> list[MediaSpec]:
    media = []
    for field_name in fields:
        value = row.get(field_name)
        if not isinstance(value, dict) or not value.get("bytes"):
            continue
        data = value["bytes"]
        hint = Path(clean_text(value.get("path"))).suffix or ".png"
        media.append(
            MediaSpec(kind="bytes", data=data, suffix=image_suffix(data, hint))
        )
    return media


def load_famma() -> list[Candidate]:
    path = BENCHMARK_ROOT / "FAMMA" / "data" / "release_basic-00000-of-00001.parquet"
    columns = [
        "question_id",
        "context",
        "question",
        "options",
        "answers",
        "image_type",
        "image_1",
        "image_2",
        "image_3",
        "image_4",
        "image_5",
        "image_6",
        "image_7",
    ]
    compliance_pattern = re.compile(
        r"GIPS|in compliance|compliance with|suitability concern|fiduciary|"
        r"professional conduct|regulat",
        re.IGNORECASE,
    )
    candidates: list[Candidate] = []
    table_count = 0
    for batch in pq.ParquetFile(path).iter_batches(batch_size=64, columns=columns):
        for row in batch.to_pylist():
            question = "\n".join(
                part
                for part in (clean_text(row.get("context")), clean_text(row.get("question")))
                if part
            )
            answer = clean_text(row.get("answers"))
            media = parquet_media(row, [f"image_{index}" for index in range(1, 8)])
            if not question or not answer or not media:
                continue
            source_id = clean_text(row.get("question_id"))
            if row.get("image_type") == "table" and len(media) == 1 and table_count < 50:
                candidates.append(
                    Candidate(
                        task="single_table_qa",
                        benchmark="FAMMA",
                        source_id=source_id,
                        question=question,
                        answer=answer,
                        choices=row.get("options"),
                        media=media,
                    )
                )
                table_count += 1
            if compliance_pattern.search(clean_text(row.get("question"))):
                candidates.append(
                    Candidate(
                        task="compliance_safety_suitability",
                        benchmark="FAMMA",
                        source_id=source_id,
                        question=question,
                        answer=answer,
                        choices=row.get("options"),
                        media=media,
                    )
                )
    return candidates


def finchart_image(base: Path, subset: str, image_name: str) -> Path | None:
    normalized = re.sub(r"_q\d+(?=\.[^.]+$)", "", image_name)
    path = base / f"{subset}_images" / normalized
    return path if path.is_file() else None


def load_finchart_bench() -> list[Candidate]:
    base = BENCHMARK_ROOT / "FinChart-Bench"
    ranking_pattern = re.compile(
        r"highest|lowest|largest|smallest|rank|compare|maximum|minimum|"
        r"最高|最低|最大|最小|排名|比较",
        re.IGNORECASE,
    )
    candidates: list[Candidate] = []
    for subset in ("QA", "MC", "TF"):
        rows = json.loads((base / f"{subset}_data.json").read_text(encoding="utf-8"))
        for index, row in enumerate(rows):
            image = finchart_image(base, subset, clean_text(row.get("image")))
            question = clean_text(row.get("question"))
            answer = clean_text(row.get("answer"))
            if not image or not question or not answer:
                continue
            media = [MediaSpec(kind="file", path=image, suffix=image.suffix)]
            source_id = f"{subset.lower()}-{index}"
            candidates.append(
                Candidate(
                    task="chart_data_extraction",
                    benchmark="FinChart-Bench",
                    source_id=source_id,
                    question=question,
                    answer=answer,
                    choices=row.get("choices"),
                    media=media,
                )
            )
            if ranking_pattern.search(question):
                candidates.append(
                    Candidate(
                        task="statistics_comparison_ranking",
                        benchmark="FinChart-Bench",
                        source_id=source_id,
                        question=question,
                        answer=answer,
                        choices=row.get("choices"),
                        media=media,
                    )
                )
            if index >= 350 and subset == "QA":
                break
    return candidates


def load_finmme() -> list[Candidate]:
    path = BENCHMARK_ROOT / "FinMME" / "data" / "train-00000-of-00001.parquet"
    ranking_pattern = re.compile(
        r"highest|lowest|largest|smallest|rank|compare|maximum|minimum|"
        r"最高|最低|最大|最小|排名|比较",
        re.IGNORECASE,
    )
    candidates: list[Candidate] = []
    chart_count = 0
    ranking_count = 0
    columns = ["id", "image", "question_text", "options", "answer"]
    for batch in pq.ParquetFile(path).iter_batches(batch_size=64, columns=columns):
        for row in batch.to_pylist():
            media = parquet_media(row, ["image"])
            question = clean_text(row.get("question_text"))
            answer = clean_text(row.get("answer"))
            if not media or not question or not answer:
                continue
            source_id = str(row.get("id"))
            if chart_count < 80:
                candidates.append(
                    Candidate(
                        task="chart_data_extraction",
                        benchmark="FinMME",
                        source_id=source_id,
                        question=question,
                        answer=answer,
                        choices=row.get("options"),
                        media=media,
                    )
                )
                chart_count += 1
            if ranking_pattern.search(question) and ranking_count < 80:
                candidates.append(
                    Candidate(
                        task="statistics_comparison_ranking",
                        benchmark="FinMME",
                        source_id=source_id,
                        question=question,
                        answer=answer,
                        choices=row.get("options"),
                        media=media,
                    )
                )
                ranking_count += 1
        if chart_count >= 80 and ranking_count >= 80:
            break
    return candidates


def finmmr_media(row: dict[str, Any]) -> list[MediaSpec]:
    image_root = (
        BENCHMARK_ROOT
        / "FinMMR_code_main (2)"
        / "FinMMR-main"
        / "images"
    )
    references = row.get("ground_images") or row.get("images") or []
    media = []
    for reference in references:
        path = image_root / Path(reference).name
        if path.is_file():
            media.append(MediaSpec(kind="file", path=path, suffix=path.suffix))
    return media


def load_finmmr() -> list[Candidate]:
    data_root = BENCHMARK_ROOT / "FinMMR" / "data"
    paths = sorted((data_root / "validation").glob("*.json")) + sorted(
        (data_root / "test").glob("*.json")
    )
    ownership_pattern = re.compile(
        r"股东|持股|股权|控股|shareholder|ownership|subsidiar|parent company",
        re.IGNORECASE,
    )
    candidates: list[Candidate] = []
    for path in paths:
        for row in json.loads(path.read_text(encoding="utf-8")):
            question = clean_text(row.get("question"))
            answer = row.get("ground_truth")
            media = finmmr_media(row)
            source_id = clean_text(row.get("question_id"))
            if not question or answer is None or not media:
                continue
            if ownership_pattern.search(question):
                candidates.append(
                    Candidate(
                        task="relationship_equity_structure",
                        benchmark="FinMMR",
                        source_id=source_id,
                        question=question,
                        answer=answer,
                        media=media,
                    )
                )
            operator_count = (
                row.get("statistics", {})
                .get("operator_statistics", {})
                .get("total_operators", 0)
            )
            if row.get("grade") == "Hard" and operator_count >= 4:
                candidates.append(
                    Candidate(
                        task="multi_step_numerical_reasoning",
                        benchmark="FinMMR",
                        source_id=source_id,
                        question=question,
                        answer=answer,
                        media=media,
                    )
                )
    return candidates


def load_fcmr() -> list[Candidate]:
    base = BENCHMARK_ROOT / "FCMR" / "dataset"
    candidates: list[Candidate] = []
    for level in ("easy", "medium", "hard"):
        level_root = base / level
        csv_path = level_root / f"{level}_data.csv"
        rows = list(csv.DictReader(csv_path.open(encoding="utf-8-sig")))
        table_root = level_root / f"{level}_test_table_modality"
        text_root = level_root / f"{level}_test_text_modality_chunk"
        chart_root = level_root / "chart_images"
        for row in rows:
            anchor = clean_text(row.get("anchor_num"))
            table_path = table_root / f"table_modality_{anchor}.csv"
            text_path = text_root / f"anchor_table_test_{anchor}_text.txt"
            chart_path = chart_root / clean_text(row.get("filename"))
            if not table_path.is_file() or not text_path.is_file() or not chart_path.is_file():
                continue
            table_text = table_path.read_text(encoding="utf-8-sig").strip()
            source_text = text_path.read_text(encoding="utf-8").strip()
            question = (
                "根据以下文本、表格和图表，判断哪些陈述正确。\n\n"
                f"文本资料：\n{source_text}\n\n表格资料：\n{table_text}"
            )
            choices = [
                f"{index}. {clean_text(row.get(f'option{index}'))}"
                for index in (1, 2, 3)
                if clean_text(row.get(f"option{index}"))
            ]
            answer = clean_text(row.get("correct_answer"))
            if answer.lower() in {"", "none", "nan"}:
                continue
            candidates.append(
                Candidate(
                    task="cross_modal_multi_hop",
                    benchmark=f"FCMR-{level}",
                    source_id=anchor,
                    question=question,
                    answer=answer,
                    choices=choices,
                    media=[
                        MediaSpec(kind="file", path=chart_path, suffix=chart_path.suffix)
                    ],
                )
            )
    return candidates


def evidence_pages(row: dict[str, Any]) -> list[int]:
    return sorted(
        {
            int(page)
            for pages in row.get("evidence", {}).values()
            for page in pages
        }
    )


def doc_page_media(doc_dir: Path, pages: list[int]) -> list[MediaSpec]:
    media = []
    for page in pages:
        path = doc_dir / f"page_{page}.png"
        if not path.is_file():
            return []
        media.append(MediaSpec(kind="file", path=path, suffix=".png"))
    return media


def load_finmmdocr() -> list[Candidate]:
    data_path = (
        BENCHMARK_ROOT
        / "BUPT-Reasoning-Lab FinMMDocR main data"
        / "BUPT-Reasoning-Lab FinMMDocR main data"
        / "test.json"
    )
    image_root = BENCHMARK_ROOT / "FinMMDocR" / "images"
    candidates: list[Candidate] = []
    for row in json.loads(data_path.read_text(encoding="utf-8")):
        doc_dir = image_root / clean_text(row.get("doc_id"))
        if not doc_dir.is_dir():
            continue
        question = clean_text(row.get("question"))
        answer = row.get("ground_truth")
        source_id = clean_text(row.get("question_id"))
        if not question or answer is None:
            continue

        table_pages = sorted({int(page) for page in row["evidence"].get("table", [])})
        if len(table_pages) >= 2:
            media = doc_page_media(doc_dir, table_pages)
            if media:
                candidates.append(
                    Candidate(
                        task="multi_table_reasoning",
                        benchmark="FinMMDocR",
                        source_id=source_id,
                        question=question,
                        answer=answer,
                        media=media,
                    )
                )

        pages = evidence_pages(row)
        if len(pages) >= 2:
            media = doc_page_media(doc_dir, pages)
            if media:
                candidates.append(
                    Candidate(
                        task="long_document_cross_page",
                        benchmark="FinMMDocR",
                        source_id=source_id,
                        question=question,
                        answer=answer,
                        media=media,
                    )
                )

        page_count = int(row.get("pages_num") or 0)
        all_pages = list(range(1, page_count + 1))
        if pages and page_count and len(list(doc_dir.glob("page_*.png"))) >= page_count:
            media = doc_page_media(doc_dir, all_pages)
            if media:
                page_answer = "、".join(f"第{page}页" for page in pages)
                candidates.append(
                    Candidate(
                        task="evidence_retrieval",
                        benchmark="FinMMDocR",
                        source_id=source_id,
                        question=(
                            "请定位回答下列问题所需的证据页，并仅给出页码。"
                            f"文档图片按第1页至第{page_count}页顺序提供。\n原问题：{question}"
                        ),
                        answer=page_answer,
                        media=media,
                    )
                )
    return candidates


def load_candidates() -> list[Candidate]:
    candidates = []
    for loader in (
        load_cfbenchmark,
        load_mme_finance,
        load_famma,
        load_finchart_bench,
        load_finmme,
        load_finmmr,
        load_fcmr,
        load_finmmdocr,
    ):
        loaded = loader()
        candidates.extend(loaded)
        print(f"loaded {len(loaded):4d} candidates from {loader.__name__}")
    return candidates


def select_candidates(candidates: list[Candidate]) -> list[Candidate]:
    by_task: dict[str, list[Candidate]] = defaultdict(list)
    for candidate in candidates:
        by_task[candidate.task].append(candidate)

    selected = []
    used_sources: set[str] = set()
    used_content: set[tuple[str, str]] = set()
    for task, quota in TASK_QUOTAS.items():
        groups: dict[str, deque[Candidate]] = {}
        benchmarks = sorted({c.benchmark for c in by_task[task]})
        for benchmark_index, benchmark in enumerate(benchmarks):
            group_rows = sorted(
                (c for c in by_task[task] if c.benchmark == benchmark),
                key=lambda c: c.source_id,
            )
            if task == "cross_modal_multi_hop":
                by_answer: dict[str, deque[Candidate]] = defaultdict(deque)
                for candidate in group_rows:
                    by_answer[clean_text(candidate.answer)].append(candidate)
                group_rows = []
                answers = sorted(by_answer)
                offset = (benchmark_index * 2) % len(answers)
                answers = answers[offset:] + answers[:offset]
                while by_answer:
                    for answer in list(answers):
                        if answer not in by_answer:
                            continue
                        group_rows.append(by_answer[answer].popleft())
                        if not by_answer[answer]:
                            by_answer.pop(answer)
            groups[benchmark] = deque(group_rows)

        task_rows = []
        task_media: set[tuple[str, ...]] = set()
        while len(task_rows) < quota and groups:
            made_progress = False
            for benchmark in list(groups):
                group = groups[benchmark]
                while group:
                    candidate = group.popleft()
                    signature = (clean_text(candidate.question), clean_text(candidate.answer))
                    media_signature = []
                    for media in candidate.media:
                        if media.kind == "file" and media.path:
                            media_signature.append(str(media.path.resolve()))
                        elif media.kind == "zip" and media.member:
                            media_signature.append(f"{media.archive}:{media.member}")
                    media_key = tuple(media_signature)
                    if (
                        candidate.source in used_sources
                        or signature in used_content
                        or (media_key and media_key in task_media)
                    ):
                        continue
                    task_rows.append(candidate)
                    used_sources.add(candidate.source)
                    used_content.add(signature)
                    if media_key:
                        task_media.add(media_key)
                    made_progress = True
                    break
                if not group:
                    groups.pop(benchmark, None)
                if len(task_rows) >= quota:
                    break
            if not made_progress:
                break
        if len(task_rows) != quota:
            raise RuntimeError(
                f"task {task} needs {quota} candidates, selected {len(task_rows)} "
                f"from {len(by_task[task])} available rows"
            )
        selected.extend(task_rows)
    return selected


def materialize_media(
    candidate: Candidate, task_index: int, zip_cache: dict[Path, zipfile.ZipFile]
) -> list[str]:
    task_dir = ASSETS_ROOT / candidate.task
    task_dir.mkdir(parents=True, exist_ok=True)
    copied = []
    for media_index, media in enumerate(candidate.media, start=1):
        suffix = media.suffix.lower() or ".png"
        if suffix == ".jpeg":
            suffix = ".jpg"
        destination = task_dir / f"{task_index:04d}_{media_index:02d}{suffix}"
        if media.kind == "file":
            if media.path is None or not media.path.is_file():
                raise FileNotFoundError(media.path)
            shutil.copy2(media.path, destination)
        elif media.kind == "bytes":
            if media.data is None:
                raise ValueError(f"missing bytes for {candidate.source}")
            destination.write_bytes(media.data)
        elif media.kind == "zip":
            if media.archive is None or media.member is None:
                raise ValueError(f"missing zip source for {candidate.source}")
            archive = zip_cache.setdefault(
                media.archive, zipfile.ZipFile(media.archive)
            )
            destination.write_bytes(archive.read(media.member))
        else:
            raise ValueError(f"unsupported media kind: {media.kind}")
        copied.append(destination.relative_to(ROOT).as_posix())
    return copied


def make_record(candidate: Candidate, copied_images: list[str]) -> dict[str, Any]:
    prompt = (
        "<image>" * len(copied_images)
        + clean_text(candidate.question)
        + format_choices(candidate.choices)
    )
    return {
        "messages": [
            {"role": "user", "content": prompt},
            {"role": "assistant", "content": clean_text(candidate.answer)},
        ],
        "source": candidate.source,
        "split": "test",
        "images": copied_images,
        "task": candidate.task,
    }


def reset_output() -> None:
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    if ASSETS_ROOT.exists():
        if ASSETS_ROOT.resolve().parent != OUTPUT_ROOT.resolve():
            raise RuntimeError(f"refusing to remove unexpected path: {ASSETS_ROOT}")
        shutil.rmtree(ASSETS_ROOT)
    if OUTPUT_JSONL.exists():
        OUTPUT_JSONL.unlink()


def build() -> list[dict[str, Any]]:
    candidates = load_candidates()
    selected = select_candidates(candidates)
    reset_output()
    zip_cache: dict[Path, zipfile.ZipFile] = {}
    task_indices: dict[str, int] = defaultdict(int)
    records = []
    try:
        for candidate in selected:
            task_indices[candidate.task] += 1
            copied = materialize_media(
                candidate, task_indices[candidate.task], zip_cache
            )
            records.append(make_record(candidate, copied))
    finally:
        for archive in zip_cache.values():
            archive.close()

    with OUTPUT_JSONL.open("w", encoding="utf-8", newline="\n") as output:
        for record in records:
            output.write(json.dumps(record, ensure_ascii=False) + "\n")
    return records


def main() -> None:
    records = build()
    counts = defaultdict(int)
    for record in records:
        counts[record["task"]] += 1
    print(f"wrote {len(records)} records to {OUTPUT_JSONL}")
    for task in TASK_QUOTAS:
        print(f"{task}: {counts[task]}")


if __name__ == "__main__":
    main()
