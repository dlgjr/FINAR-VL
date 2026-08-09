from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_shared_environment_makes_project_modules_importable_to_swift_workers():
    text = (ROOT / "scripts" / "dlc" / "dlc_env.sh").read_text(encoding="utf-8")

    assert 'export PYTHONPATH="$QWEN3VL_ROOT:$PYTHON_USER_SITE${PYTHONPATH:+:$PYTHONPATH}"' in text


def test_dlc_launcher_uses_local_caches_and_two_gpu_judge():
    text = (ROOT / "scripts" / "dlc" / "start_sft.sh").read_text(encoding="utf-8")

    for required in (
        'export BASE_MODEL="$ROOT/models/qwen4"',
        "--model_type qwen3_vl",
        "NPROC_PER_NODE=7",
        "CUDA_VISIBLE_DEVICES=0,1,2,3,4,5,6",
        "SFT_JUDGE_GPUS=7",
        'export SFT_TRACE_STEPS="${SFT_TRACE_STEPS:-1049,1050,1051}"',
        'export SFT_SAVE_STEPS="${SFT_SAVE_STEPS:-500}"',
        'export SFT_EPOCHS="${SFT_EPOCHS:-1}"',
        "expected 2 DLC nodes",
        "--dataset \"$TRAIN_MULTI\" \"$TRAIN_TEXT\"",
        "--dataset_shuffle false",
        "--train_dataloader_shuffle false",
        "--max_steps \"$SFT_MAX_STEPS\"",
        '"$ROOT/scripts/sft/sample_plan.py"',
        '--epochs "$SFT_EPOCHS"',
        "--dp-world-size 14",
        "--per-device-batch 1",
        'export SFT_PLAN_DIR',
        "SFT_MAX_STEPS=\"$(",
        "json.load(open(sys.argv[1], encoding=\"utf-8\"))",
        "PYTORCH_ALLOC_CONF=expandable_segments:True",
        "CELOSS_PARALLEL_SIZE=4096",
        "--sequence_parallel_size 1",
        "--per_device_train_batch_size 1",
        "--ddp_timeout 86400",
        "--max_length 49152",
        "--attn_impl flash_attn",
        "--truncation_strategy delete",
        "--tuner_type lora",
        "--target_modules all-linear",
        "--lora_rank 16",
        "--lora_alpha 32",
        "--lora_dropout 0.05",
        "--gradient_accumulation_steps 2",
        "--learning_rate 1e-5",
        "--warmup_ratio 0.05",
        "--max_grad_norm 1.0",
        "--eval_strategy no",
        '--save_steps "$SFT_SAVE_STEPS"',
        "--save_only_model true",
        "--report_to wandb",
        "--callbacks finar_log finar_numerics finar_pass_at_8 finar_plan",
        "--strict false",
        "global_batch=28 per_device_batch=1 grad_accum=2",
        "training_gpus_per_node=7 judge_gpus_per_node=1",
        "sequence_parallel:1,data_parallel:14",
        "tuner=lora rank=16 alpha=32 dropout=0.05 target_modules=all-linear",
        "pass_at_1=greedy",
        'export TMPDIR="/tmp/qwen3vl-sft-${RUN_ID}-node-${NODE_RANK}"',
        'export HF_HOME="$LOCAL_CACHE_ROOT/huggingface"',
        'export HF_DATASETS_CACHE="$HF_HOME/datasets"',
        'export HUGGINGFACE_HUB_CACHE="$HF_HOME/hub"',
        'export MODELSCOPE_CACHE="$LOCAL_CACHE_ROOT/modelscope"',
        'export TRITON_CACHE_DIR="$LOCAL_CACHE_ROOT/triton"',
        "--tensor-parallel-size 1",
        "--gpu-memory-utilization 0.5",
        "--max-num-seqs 8",
        "--dataset_num_proc 1",
        "--dataloader_num_workers 1",
        'export WANDB_VERSION="0.28.1"',
        'WANDB_READY_FILE="$RUN_SYNC_DIR/${RUN_ID}.wandb_ready"',
        'WANDB_ERROR_FILE="$RUN_SYNC_DIR/${RUN_ID}.wandb_error"',
        '"wandb==$WANDB_VERSION"',
        "WANDB_MODE=offline",
        'export WANDB_DIR="$LOG_ROOT/wandb"',
        "import flash_attn",
    ):
        assert required in text
    assert "SFT_PASS_AT_1_TEMPERATURE" not in text
    assert "--deepspeed zero2_offload" not in text
    assert "--attn_impl sdpa" not in text


def test_dsw_launcher_runs_five_steps_without_wandb_and_limits_eval_to_one_sample():
    text = (ROOT / "scripts" / "dsw" / "run_sft_debug.sh").read_text(encoding="utf-8")

    for required in (
        'export BASE_MODEL="$ROOT/models/qwen4"',
        "--model_type qwen3_vl",
        'test -f "$BASE_MODEL/config.json"',
        'source "$ROOT/scripts/dlc/dlc_env.sh"',
        'PYTHON_BIN="${PYTHON_BIN:-/opt/ac2/bin/python}"',
        'SWIFT_BIN="${SWIFT_BIN:-$PYTHONUSERBASE/bin/swift}"',
        'export NPROC_PER_NODE=1',
        'export CUDA_VISIBLE_DEVICES=0',
        '"ms-swift==4.4.2"',
        '"wandb==0.28.1"',
        "import wandb",
        "WANDB_DISABLED=true",
        "SFT_EVAL_MAX_SAMPLES=1",
        "--dataset \"$TRAIN_MULTI\" \"$TRAIN_TEXT\"",
        "--dataset_shuffle false",
        "--train_dataloader_shuffle false",
        "--dp-world-size 1",
        "--per-device-batch 1",
        "--max-steps 5",
        '"$ROOT/scripts/sft/sample_plan.py"',
        'export SFT_PLAN_DIR',
        "PYTORCH_ALLOC_CONF=expandable_segments:True",
        'export SFT_ATTN_IMPL="${SFT_ATTN_IMPL:-sdpa}"',
        'export SFT_CELOSS_PARALLEL_SIZE="${SFT_CELOSS_PARALLEL_SIZE:-4096}"',
        'export SFT_DEBUG_MAX_LENGTH="${SFT_DEBUG_MAX_LENGTH:-81920}"',
        'export CELOSS_PARALLEL_SIZE="$SFT_CELOSS_PARALLEL_SIZE"',
        "--per_device_train_batch_size 1",
        "--tuner_type lora",
        "--freeze_vit true",
        "--freeze_aligner false",
        "--target_modules all-linear",
        "--lora_rank 16",
        "--lora_alpha 32",
        "--lora_dropout 0.05",
        "--gradient_accumulation_steps 2",
        "--learning_rate 1e-5",
        "--warmup_ratio 0.05",
        "--max_grad_norm 1.0",
        "  --deepspeed zero2 \\",
        "--sequence_parallel_size 1",
        '--attn_impl "$SFT_ATTN_IMPL"',
        '--max_length "$SFT_DEBUG_MAX_LENGTH"',
        "--logging_nan_inf_filter false",
        "--strict false",
        "--report_to none",
        "--callbacks finar_log finar_numerics finar_pass_at_8 finar_plan",
    ):
        assert required in text
    assert "fixed_batch=1" in text
    assert "--deepspeed zero2_offload" not in text
    assert "--use_logits_to_keep true" not in text
    assert "PYTORCH_ALLOC_CONF=expandable_segments:True" in text
    assert "PYTORCH_CUDA_ALLOC_CONF=" not in text


def test_dlc_environment_exports_python_user_base_on_its_own_line():
    text = (ROOT / "scripts" / "dlc" / "dlc_env.sh").read_text(encoding="utf-8")

    assert 'export PYTHONUSERBASE="${PYTHONUSERBASE:-$QWEN3VL_ROOT/python-user}"' in text


def test_sequence_parallel_step_inspector_uses_seeded_torch_permutation():
    text = (ROOT / "scripts" / "sft" / "inspect_sequence_parallel_step.py").read_text(encoding="utf-8")
    assert "torch.randperm" in text
    assert "manual_seed(seed)" in text
    assert 'dp_world_size: int = 12' in text
    assert '"source"' in text and '"length"' in text
    assert 'encoded_estimated' in text
    assert 'image_max_token_num' in text
