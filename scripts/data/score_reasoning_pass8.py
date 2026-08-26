#!/usr/bin/env python3

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from collections import Counter
from pathlib import Path
from statistics import mean

ROOT = Path('/mnt/nas/bihaoran/qwen3vl')
DATA = ROOT / 'data/train_multi/train_rl_reasoning.jsonl'
OUTPUT_ROOT = ROOT / 'output/reasoning_pass8_compare'
MODELS = [
    ('sft_ckpt15500', ROOT / 'output/sft/sft_qwen3vl4b_20260821_183115/v0-20260821-185530/checkpoint-15500'),
    ('unclean_ckpt1372', ROOT / 'output/sft_test_unclean/checkpoint15500_ep2_lr1e5/checkpoint-1372'),
]


def stable_seed(base_seed: int, model_tag: str, line_number: int) -> int:
    payload = f'{base_seed}\0{model_tag}\0{line_number}'.encode('utf-8')
    return int.from_bytes(hashlib.sha256(payload).digest()[:4], 'big')


def difficulty(correct_count: int) -> str:
    if correct_count == 0:
        return 'hard'
    if correct_count <= 3:
        return 'medium'
    return 'easy'


def worker(args: argparse.Namespace) -> None:
    root = Path(args.root)
    data = Path(args.data)
    model = Path(args.model)
    output_dir = Path(args.output_dir)
    sys.path.insert(0, str(root))
    os.environ['VLLM_WORKER_MULTIPROC_METHOD'] = 'spawn'

    from scripts.pass_at_k import build_prompt_input
    from scripts.rl.gspo_reward import MixedReward
    from scripts.rl.prepare_gspo_data import prepare_record
    from transformers import AutoProcessor
    from vllm import LLM, SamplingParams

    processor = AutoProcessor.from_pretrained(str(model))
    llm = LLM(
        model=str(model),
        tensor_parallel_size=1,
        dtype='bfloat16',
        max_model_len=args.max_model_len,
        max_num_seqs=args.max_num_seqs,
        gpu_memory_utilization=args.gpu_memory_utilization,
        limit_mm_per_prompt={'image': args.max_images_per_prompt, 'video': 0},
        mm_processor_cache_gb=0,
        generation_config='vllm',
    )
    scorer = MixedReward()
    image_root = data.parent
    part_path = output_dir / 'parts' / f'rank_{args.rank:02d}.jsonl'
    part_path.parent.mkdir(parents=True, exist_ok=True)

    batch_rows: list[tuple[int, dict, dict, dict]] = []
    with data.open(encoding='utf-8') as source, part_path.open('w', encoding='utf-8') as output:
        def run_batch() -> None:
            if not batch_rows:
                return
            sampling_params = [
                SamplingParams(
                    n=args.k,
                    temperature=args.temperature,
                    top_p=args.top_p,
                    max_tokens=args.max_tokens,
                    seed=stable_seed(args.seed, args.model_tag, line_number),
                )
                for line_number, _, _, _ in batch_rows
            ]
            generations = llm.generate(
                [prompt_input for _, _, prompt_input, _ in batch_rows],
                sampling_params=sampling_params,
                use_tqdm=False,
            )
            for (line_number, row, _, prepared), generated in zip(batch_rows, generations):
                candidates = [candidate.text for candidate in generated.outputs]
                rewards = [float(value) for value in scorer(candidates, records=[prepared] * len(candidates))]
                correct_count = sum(value >= 1.0 for value in rewards)
                annotated = dict(row)
                if '_pass_at_k' in annotated:
                    annotated['_pass_at_k_original'] = annotated['_pass_at_k']
                annotated['_pass_at_k'] = {
                    'k': args.k,
                    'correct_count': correct_count,
                    'pass_8': int(correct_count > 0),
                    'success_rate': correct_count / args.k,
                    'mean_reward': mean(rewards),
                    'difficulty': difficulty(correct_count),
                    'model': str(model),
                    'model_tag': args.model_tag,
                    'dataset': data.name,
                    'result_index': f'{data.name}:{line_number}',
                }
                output.write(json.dumps({'line_number': line_number, 'row': annotated}, ensure_ascii=False) + '\n')
                output.flush()
            batch_rows.clear()

        for line_number, line in enumerate(source, 1):
            if line_number % args.workers != args.rank:
                continue
            row = json.loads(line)
            prepared = prepare_record(row, line_number)
            prompt_row = dict(prepared)
            prompt_row['messages'] = [*prepared['messages'], {'role': 'assistant', 'content': ''}]
            prompt_input = build_prompt_input(prompt_row, processor, image_root)
            batch_rows.append((line_number, row, prompt_input, prepared))
            if len(batch_rows) >= args.batch_size:
                run_batch()
        run_batch()


def merge(args: argparse.Namespace) -> None:
    output_dir = Path(args.output_dir)
    records = []
    for part_path in sorted((output_dir / 'parts').glob('rank_*.jsonl')):
        with part_path.open(encoding='utf-8') as handle:
            records.extend(json.loads(line) for line in handle if line.strip())
    records.sort(key=lambda item: item['line_number'])
    with Path(args.data).open(encoding='utf-8') as source:
        expected = sum(1 for line in source if line.strip())
    if len(records) != expected:
        raise RuntimeError(f'annotated record count mismatch: expected {expected}, got {len(records)}')

    annotated_path = output_dir / 'train_rl_reasoning_pass8.jsonl'
    with annotated_path.open('w', encoding='utf-8') as handle:
        for item in records:
            handle.write(json.dumps(item['row'], ensure_ascii=False) + '\n')

    metrics = [item['row']['_pass_at_k'] for item in records]
    counts = Counter(metric['difficulty'] for metric in metrics)
    summary = {
        'model': args.model,
        'model_tag': args.model_tag,
        'data': args.data,
        'k': args.k,
        'temperature': args.temperature,
        'total': len(metrics),
        'pass_8_rate': sum(metric['pass_8'] for metric in metrics) / len(metrics),
        'mean_correct_count': mean(metric['correct_count'] for metric in metrics),
        'mean_reward': mean(metric['mean_reward'] for metric in metrics),
        'difficulty_counts': dict(counts),
        'annotated_data': str(annotated_path),
    }
    (output_dir / 'summary.json').write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + '\n',
        encoding='utf-8',
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


def run_model(args: argparse.Namespace, slot: int) -> None:
    model_tag, model = MODELS[slot]
    output_dir = Path(args.output_root) / model_tag
    output_dir.mkdir(parents=True, exist_ok=True)
    visible = [value.strip() for value in os.environ.get('CUDA_VISIBLE_DEVICES', '0,1,2,3,4,5,6,7').split(',') if value.strip()]
    if len(visible) < args.workers:
        raise RuntimeError(f'need {args.workers} visible GPUs, found {len(visible)}')
    processes = []
    for rank, gpu in enumerate(visible[: args.workers]):
        env = os.environ.copy()
        env['CUDA_VISIBLE_DEVICES'] = gpu
        command = [
            sys.executable,
            __file__,
            '--worker',
            '--root', str(args.root),
            '--data', str(args.data),
            '--model', str(model),
            '--model-tag', model_tag,
            '--output-dir', str(output_dir),
            '--rank', str(rank),
            '--workers', str(args.workers),
            '--k', str(args.k),
            '--temperature', str(args.temperature),
            '--top-p', str(args.top_p),
            '--max-tokens', str(args.max_tokens),
            '--max-model-len', str(args.max_model_len),
            '--max-num-seqs', str(args.max_num_seqs),
            '--max-images-per-prompt', str(args.max_images_per_prompt),
            '--gpu-memory-utilization', str(args.gpu_memory_utilization),
            '--batch-size', str(args.batch_size),
            '--seed', str(args.seed),
        ]
        processes.append(subprocess.Popen(command, env=env))
    for process in processes:
        process.wait()
    if any(process.returncode != 0 for process in processes):
        raise RuntimeError('pass@8 worker failed')

    merge_args = argparse.Namespace(**vars(args))
    merge_args.model = str(model)
    merge_args.model_tag = model_tag
    merge_args.output_dir = str(output_dir)
    merge(merge_args)

    summaries = []
    for tag, _ in MODELS:
        path = Path(args.output_root) / tag / 'summary.json'
        if path.is_file():
            summaries.append(json.loads(path.read_text(encoding='utf-8')))
    if len(summaries) == len(MODELS):
        summaries.sort(key=lambda item: item['model_tag'])
        better = max(summaries, key=lambda item: (item['pass_8_rate'], item['mean_correct_count']))
        comparison = {'models': summaries, 'better_model': better['model_tag']}
        (Path(args.output_root) / 'comparison.json').write_text(
            json.dumps(comparison, ensure_ascii=False, indent=2) + '\n',
            encoding='utf-8',
        )


def inferred_slot() -> str:
    for key in ('PASS8_MODEL_SLOT', 'GSPO_NODE_RANK', 'NODE_RANK', 'RANK'):
        value = os.environ.get(key)
        if value in {'0', '1'}:
            return value
    return '0'


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='Score reasoning training data with two Qwen3-VL checkpoints using pass@8.')
    parser.add_argument('--slot', choices=('0', '1', 'all'), default=inferred_slot())
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--data', type=Path, default=DATA)
    parser.add_argument('--output-root', type=Path, default=OUTPUT_ROOT)
    parser.add_argument('--workers', type=int, default=8)
    parser.add_argument('--k', type=int, default=8)
    parser.add_argument('--temperature', type=float, default=1.2)
    parser.add_argument('--top-p', type=float, default=1.0)
    parser.add_argument('--max-tokens', type=int, default=2048)
    parser.add_argument('--max-model-len', type=int, default=49152)
    parser.add_argument('--max-num-seqs', type=int, default=32)
    parser.add_argument('--max-images-per-prompt', type=int, default=32)
    parser.add_argument('--gpu-memory-utilization', type=float, default=0.90)
    parser.add_argument('--batch-size', type=int, default=4)
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--worker', action='store_true')
    parser.add_argument('--model')
    parser.add_argument('--model-tag')
    parser.add_argument('--output-dir')
    parser.add_argument('--rank', type=int)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.worker:
        worker(args)
        return
    slots = (0, 1) if args.slot == 'all' else (int(args.slot),)
    for slot in slots:
        run_model(args, slot)


if __name__ == '__main__':
    main()
