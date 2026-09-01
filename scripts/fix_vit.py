#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import re
import shutil
import sys
from pathlib import Path


EXPORT_BLOCK = """\
export SFT_FREEZE_VIT="${SFT_FREEZE_VIT:-true}"
export SFT_FREEZE_ALIGNER="${SFT_FREEZE_ALIGNER:-false}"
export SFT_FREEZE_LLM="${SFT_FREEZE_LLM:-false}"
export SFT_VIT_GRADIENT_CHECKPOINTING="${SFT_VIT_GRADIENT_CHECKPOINTING:-false}"
"""

WRAPPER_TEXT = """\
#!/usr/bin/env bash
set -euo pipefail

# Stage 1: freeze only the vision encoder.
# The aligner and LLM remain trainable.
export SFT_FREEZE_VIT=true
export SFT_FREEZE_ALIGNER=false
export SFT_FREEZE_LLM=false
export SFT_VIT_GRADIENT_CHECKPOINTING=false

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
exec "$SCRIPT_DIR/start_sft.sh" "$@"
"""


def parse_args() -> argparse.Namespace:
    default_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(
        description="Patch FINAR-VL stage-1 SFT launcher to freeze ViT."
    )
    parser.add_argument(
        "repo_root",
        nargs="?",
        type=Path,
        default=default_root,
        help="FINAR-VL repository root; defaults to the parent of scripts/.",
    )
    return parser.parse_args()


def read_text_lf(path: Path) -> str:
    # newline=None converts CRLF to LF, avoiding mixed line endings in shell scripts.
    with path.open("r", encoding="utf-8", newline=None) as file:
        return file.read()


def write_text_lf(path: Path, text: str) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as file:
        file.write(text)


def insert_export_block(text: str) -> str:
    if "export SFT_FREEZE_VIT=" in text:
        return text

    anchors = [
        'export SFT_TRACE_STEPS="${SFT_TRACE_STEPS:-1049,1050,1051}"',
        'export SFT_TRACE_STEPS=',
    ]
    for anchor in anchors:
        if anchor in text:
            if anchor.endswith("="):
                line_end = text.find("\n", text.find(anchor))
                if line_end == -1:
                    line_end = len(text)
                return text[:line_end + 1] + EXPORT_BLOCK + text[line_end + 1:]
            return text.replace(anchor, anchor + "\n" + EXPORT_BLOCK.rstrip("\n"), 1)

    # Fallback: insert after the initial shebang/set/export section.
    lines = text.splitlines()
    insert_at = 1 if lines and lines[0].startswith("#!") else 0
    while insert_at < len(lines):
        stripped = lines[insert_at].strip()
        if (
            not stripped
            or stripped.startswith("#")
            or stripped.startswith("set ")
            or stripped.startswith("export ")
        ):
            insert_at += 1
            continue
        break

    block_lines = EXPORT_BLOCK.rstrip("\n").splitlines()
    lines[insert_at:insert_at] = block_lines + [""]
    return "\n".join(lines) + ("\n" if text.endswith("\n") else "")


def replace_cli_value(text: str, option: str, variable: str) -> str:
    desired = f'--{option} "${variable}"'
    if desired in text:
        return text

    # Replace true/false, quoted literals, or an existing shell variable.
    pattern = re.compile(
        rf'(?m)(--{re.escape(option)}\s+)'
        rf'(?:"(?:true|false|\$?[A-Za-z_][A-Za-z0-9_]*)"|'
        rf"'(?:true|false|\$?[A-Za-z_][A-Za-z0-9_]*)'|"
        rf'true|false|\$[A-Za-z_][A-Za-z0-9_]*)'
    )
    updated, count = pattern.subn(rf'\1"${variable}"', text, count=1)
    if count != 1:
        raise RuntimeError(
            f"Cannot patch --{option}: expected one existing option, found {count}."
        )
    return updated


def insert_config_log(text: str) -> str:
    log_line = (
        '  echo "freeze_vit=$SFT_FREEZE_VIT '
        'freeze_aligner=$SFT_FREEZE_ALIGNER '
        'freeze_llm=$SFT_FREEZE_LLM '
        'vit_gradient_checkpointing=$SFT_VIT_GRADIENT_CHECKPOINTING"'
    )
    if log_line in text:
        return text

    topology_pattern = re.compile(
        r'(?m)^(?P<indent>\s*)echo\s+"training_topology=[^"]*"\s*$'
    )
    match = topology_pattern.search(text)
    if match:
        return text[: match.end()] + "\n" + log_line + text[match.end() :]

    # Logging is helpful but not required for correctness.
    return text


def validate(text: str) -> None:
    required = {
        "ViT export": 'export SFT_FREEZE_VIT="${SFT_FREEZE_VIT:-true}"',
        "aligner export": 'export SFT_FREEZE_ALIGNER="${SFT_FREEZE_ALIGNER:-false}"',
        "LLM export": 'export SFT_FREEZE_LLM="${SFT_FREEZE_LLM:-false}"',
        "ViT checkpoint export": (
            'export SFT_VIT_GRADIENT_CHECKPOINTING='
            '"${SFT_VIT_GRADIENT_CHECKPOINTING:-false}"'
        ),
        "ViT CLI": '--freeze_vit "$SFT_FREEZE_VIT"',
        "aligner CLI": '--freeze_aligner "$SFT_FREEZE_ALIGNER"',
        "LLM CLI": '--freeze_llm "$SFT_FREEZE_LLM"',
        "ViT checkpoint CLI": (
            '--vit_gradient_checkpointing "$SFT_VIT_GRADIENT_CHECKPOINTING"'
        ),
    }
    missing = [name for name, marker in required.items() if marker not in text]
    if missing:
        raise RuntimeError("Patch validation failed: " + ", ".join(missing))


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.expanduser().resolve()
    target = repo_root / "scripts" / "dlc" / "start_sft.sh"
    wrapper = repo_root / "scripts" / "dlc" / "start_sft_stage1.sh"

    if not target.is_file():
        print(f"ERROR: target file not found: {target}", file=sys.stderr)
        return 2

    original = read_text_lf(target)
    required_options = [
        "--freeze_vit",
        "--freeze_aligner",
        "--freeze_llm",
        "--vit_gradient_checkpointing",
    ]
    absent = [item for item in required_options if item not in original]
    if absent:
        print(
            "ERROR: start_sft.sh does not match the expected launcher; "
            f"missing: {', '.join(absent)}",
            file=sys.stderr,
        )
        return 3

    patched = insert_export_block(original)
    patched = replace_cli_value(
        patched, "freeze_vit", "SFT_FREEZE_VIT"
    )
    patched = replace_cli_value(
        patched, "freeze_aligner", "SFT_FREEZE_ALIGNER"
    )
    patched = replace_cli_value(
        patched, "freeze_llm", "SFT_FREEZE_LLM"
    )
    patched = replace_cli_value(
        patched,
        "vit_gradient_checkpointing",
        "SFT_VIT_GRADIENT_CHECKPOINTING",
    )
    patched = insert_config_log(patched)
    validate(patched)

    if patched != original:
        stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup = target.with_name(f"{target.name}.bak.{stamp}")
        shutil.copy2(target, backup)
        write_text_lf(target, patched)
        print(f"Patched: {target}")
        print(f"Backup:  {backup}")
    else:
        print(f"Already patched: {target}")

    write_text_lf(wrapper, WRAPPER_TEXT)
    print(f"Created: {wrapper}")

    print("\nEffective stage-1 settings:")
    print("  freeze_vit=true")
    print("  freeze_aligner=false")
    print("  freeze_llm=false")
    print("  vit_gradient_checkpointing=false")
    print("\nRun on the Linux DLC machine:")
    print("  bash scripts/dlc/start_sft_stage1.sh")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())