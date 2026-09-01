#!/usr/bin/env python3
import argparse
import json
import re
from pathlib import Path


def user_prompt(row):
    return "\n".join(
        str(message.get("content", ""))
        for message in row["messages"][:-1]
        if message.get("role") == "user"
    )


def parse_options(text):
    pattern = re.compile(
        r"(?ms)^\s*([A-F])[\.\:：、\)]\s*(.*?)(?=^\s*[A-F][\.\:：、\)]\s*|\Z)"
    )
    return {m.group(1).upper(): m.group(2).strip() for m in pattern.finditer(text)}


def normalize_text(text):
    text = str(text).strip().lower()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r'^[\[\("\']+|[\]\)"\'。.!！]+$', "", text)
    return text.strip()


def extract_letters(answer):
    text = str(answer).strip()
    matches = []
    patterns = [
        re.compile(r"(?i)(?:最终答案|答案|answer)\s*[:：]?\s*([A-F](?:\s*[,，、/]\s*[A-F])*)\b"),
        re.compile(r"(?i)(?:最终答案|答案|answer)\s*[:：]?\s*([A-F]{1,6})\b"),
        re.compile(r"(?i)^\s*([A-F](?:\s*[,，、/]\s*[A-F])*)\s*[。.]?\s*$"),
        re.compile(r"(?i)^\s*([A-F]{1,6})\s*[。.]?\s*$"),
    ]
    for pattern in patterns:
        for match in pattern.finditer(text):
            matches.append((match.start(), match.group(1)))
    if not matches:
        return None
    raw = max(matches, key=lambda item: item[0])[1]
    letters = re.findall(r"[A-F]", raw.upper())
    return "".join(sorted(set(letters)))


def extract_true_false(answer):
    text = str(answer).strip()
    matches = list(
        re.finditer(
            r"(?i)(?:最终答案|答案|answer)\s*[:：]?\s*(正确|错误|对|错|true|false)",
            text,
        )
    )
    value = matches[-1].group(1).lower() if matches else text.splitlines()[-1].strip().lower()
    if value in {"正确", "对", "true", "a"}:
        return "正确"
    if value in {"错误", "错", "false", "b"}:
        return "错误"
    match = re.search(r"(?:^|\n)\s*(正确|错误)\s*$", text)
    return match.group(1) if match else None


def classify(row):
    fmt = row.get("output_format", "")
    answer = str(row["messages"][-1].get("content", ""))
    prompt = user_prompt(row)
    options = parse_options(prompt)

    if fmt == "true_false":
        gold = extract_true_false(answer)
        if gold:
            return "rule", "true_false", gold, options

    if fmt in {"single_choice", "multiple_choice"}:
        gold = extract_letters(answer)
        if gold:
            return "rule", fmt, gold, options

    if fmt == "classification_label":
        return "rule", "classification_label", answer.strip(), options

    if len(options) >= 2:
        gold = extract_letters(answer)
        if gold:
            subtype = "multiple_choice" if len(gold) > 1 else "single_choice"
            return "rule", subtype, gold, options

        normalized_answer = normalize_text(answer)
        hits = [
            label
            for label, option_text in options.items()
            if normalize_text(option_text) == normalized_answer
            or normalize_text(option_text) in normalized_answer
            or normalized_answer in normalize_text(option_text)
        ]
        if len(hits) == 1:
            return "rule", "single_choice", hits[0], options

    return "judge", "free_text", answer.strip(), options


def convert(row):
    reward_type, subtype, solution, options = classify(row)
    result = {
        "messages": row["messages"][:-1],
        "question": user_prompt(row),
        "solution": solution,
        "reward_type": reward_type,
        "reward_subtype": subtype,
        "source": row.get("source", ""),
        "task": row.get("task", ""),
        "output_format": subtype if reward_type == "rule" else row.get("output_format", "free_text"),
    }

    if reward_type == "rule" and options:
        result["gold_option_text"] = " || ".join(
            options[label] for label in solution if label in options
        )

    for key in ("images", "videos", "audios"):
        if row.get(key):
            result[key] = row[key]

    return reward_type, result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input_jsonl")
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    rule_path = output_dir / "train_rl_rule.jsonl"
    judge_path = output_dir / "train_rl_judge.jsonl"

    counts = {"rule": 0, "judge": 0}
    with open(args.input_jsonl, "r", encoding="utf-8") as src, \
         open(rule_path, "w", encoding="utf-8") as rule_out, \
         open(judge_path, "w", encoding="utf-8") as judge_out:
        for line in src:
            if not line.strip():
                continue
            row = json.loads(line)
            reward_type, converted = convert(row)
            handle = rule_out if reward_type == "rule" else judge_out
            handle.write(json.dumps(converted, ensure_ascii=False) + "\n")
            counts[reward_type] += 1

    print(json.dumps({
        "rule": counts["rule"],
        "judge": counts["judge"],
        "total": counts["rule"] + counts["judge"],
        "rule_path": str(rule_path),
        "judge_path": str(judge_path),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
