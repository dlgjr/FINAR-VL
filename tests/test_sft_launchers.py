from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_shared_environment_makes_project_modules_importable_to_swift_workers():
    text = (ROOT / "scripts" / "dlc" / "dlc_env.sh").read_text(encoding="utf-8")

    assert 'export PYTHONPATH="$QWEN3VL_ROOT:$PYTHON_USER_SITE${PYTHONPATH:+:$PYTHONPATH}"' in text


def test_dlc_launcher_uses_full_sft_sp2_and_dedicated_reference_gpu():
    text = (ROOT / "scripts" / "dlc" / "start_sft.sh").read_text(encoding="utf-8")

    for required in (
        'export BASE_MODEL="$ROOT/models/qwen4"',
        "--model_type qwen3_vl",
        "NPROC_PER_NODE=6",
        "CUDA_VISIBLE_DEVICES=0,1,2,3,4,5",
        'export SFT_MULTI_MEDIA_ROOT="${SFT_MULTI_MEDIA_ROOT:-$(cd "$(dirname "$TRAIN_MULTI")" && pwd -P)}"',
        'export ROOT_IMAGE_DIR="${ROOT_IMAGE_DIR:-$SFT_MULTI_MEDIA_ROOT}"',
        'test -d "$ROOT_IMAGE_DIR"',
        'cd "$ROOT_IMAGE_DIR"',
        'multi_media_root=$SFT_MULTI_MEDIA_ROOT root_image_dir=$ROOT_IMAGE_DIR',
        'export SFT_REF_GPU="${SFT_REF_GPU:-6}"',
        'export SFT_REF_PORT="${SFT_REF_PORT:-8003}"',
        'export SFT_REF_MODEL="${SFT_REF_MODEL:-$BASE_MODEL}"',
        'export SFT_REF_SERVED_MODEL="${SFT_REF_SERVED_MODEL:-qwen4-ref}"',
        'export SFT_REF_URL="http://127.0.0.1:${SFT_REF_PORT}"',
        'export SFT_REF_MAX_NUM_SEQS="${SFT_REF_MAX_NUM_SEQS:-8}"',
        "SFT_JUDGE_GPUS=7",
        'export SFT_TRACE_STEPS="${SFT_TRACE_STEPS:-1049,1050,1051}"',
        'export SFT_EVAL_STEPS="${SFT_EVAL_STEPS:-200}"',
        'export SFT_SAVE_STEPS="${SFT_SAVE_STEPS:-500}"',
        'export SFT_EPOCHS="${SFT_EPOCHS:-1}"',
        'export SFT_MAX_STEPS="${SFT_MAX_STEPS:-50000}"',
        'export SFT_MULTI_RATIO="${SFT_MULTI_RATIO:-0.40}"',
        'export SFT_SEQUENCE_PARALLEL_SIZE="${SFT_SEQUENCE_PARALLEL_SIZE:-2}"',
        'export SFT_GRAD_ACC="${SFT_GRAD_ACC:-5}"',
        'export SFT_LEARNING_RATE="${SFT_LEARNING_RATE:-5e-6}"',
        'export SFT_FREEZE_VIT="${SFT_FREEZE_VIT:-true}"',
        'export SFT_DDP_TIMEOUT="${SFT_DDP_TIMEOUT:-86400}"',
        "export SFT_KL_TASKS=generation",
        '"$ROOT/scripts/data/normalize_train_multi_sft_format.py" "$NORMALIZED_TRAIN_MULTI"',
        '"$ROOT/scripts/data/normalize_train_text_schema.py" "$TRAIN_TEXT" "$NORMALIZED_TRAIN_TEXT"',
        "export NORMALIZED_TRAIN_MULTI NORMALIZED_TRAIN_TEXT",
        "--dataset \"$NORMALIZED_TRAIN_MULTI\" \"$NORMALIZED_TRAIN_TEXT\"",
        '--train-multi "$NORMALIZED_TRAIN_MULTI"',
        '--train-text "$NORMALIZED_TRAIN_TEXT"',
        "--dataset_shuffle false",
        "--train_dataloader_shuffle false",
        "--lazy_tokenize true",
        '"$ROOT/scripts/sft/sample_plan.py"',
        '"$ROOT/scripts/sft/materialize_lazy_plan_indices.py"',
        'RAW_PLAN_READY="$SFT_PLAN_DIR/.raw_indices_ready"',
        '--plan-dir "$SFT_PLAN_DIR"',
        'index_mode=raw',
        '--epochs "$SFT_EPOCHS"',
        '--max-steps "$SFT_MAX_STEPS"',
        '--steps-per-block 200',
        '--dp-world-size "$SFT_DP_WORLD_SIZE"',
        "--per-device-batch 1",
        'export SFT_PLAN_DIR',
        "SFT_MAX_STEPS=\"$(",
        "json.load(open(sys.argv[1], encoding=\"utf-8\"))",
        "PYTORCH_ALLOC_CONF=expandable_segments:True",
        "CELOSS_PARALLEL_SIZE=4096",
        '--sequence_parallel_size "$SFT_SEQUENCE_PARALLEL_SIZE"',
        "--per_device_train_batch_size 1",
        '--ddp_timeout "$SFT_DDP_TIMEOUT"',
        "export FINAR_SFT_DDP_TIMEOUT_PATCH=1",
        "--max_length 49152",
        "--attn_impl flash_attn",
        "--truncation_strategy delete",
        "--tuner_type full",
        '--freeze_vit "$SFT_FREEZE_VIT"',
        '--freeze_aligner "$SFT_FREEZE_ALIGNER"',
        '--freeze_llm "$SFT_FREEZE_LLM"',
        '--gradient_accumulation_steps "$SFT_GRAD_ACC"',
        '--learning_rate "$SFT_LEARNING_RATE"',
        "--warmup_ratio 0.05",
        "--max_grad_norm 1.0",
        "--use_logits_to_keep false",
        "--deepspeed zero2",
        "--eval_strategy no",
        '--save_steps "$SFT_SAVE_STEPS"',
        'eval_steps=$SFT_EVAL_STEPS save_steps=$SFT_SAVE_STEPS',
        "--save_only_model true",
        "--report_to wandb",
        '"$ROOT/scripts/sft/swift_sft_plugin.py" "$ROOT/scripts/sft/kl_retention_plugin.py"',
        "--callbacks finar_log finar_kl finar_numerics finar_pass_at_8 finar_plan",
        "--strict false",
        "reference_gpus_per_node=1 judge_gpus_per_node=1",
        "pass_at_1=greedy",
        'export TMPDIR="/tmp/qwen3vl-sft-${RUN_ID}-node-${NODE_RANK}"',
        'export HF_HOME="$LOCAL_CACHE_ROOT/huggingface"',
        'export HF_DATASETS_CACHE="$HF_HOME/datasets"',
        'export HUGGINGFACE_HUB_CACHE="$HF_HOME/hub"',
        'export MODELSCOPE_CACHE="$LOCAL_CACHE_ROOT/modelscope"',
        'export TRITON_CACHE_DIR="$LOCAL_CACHE_ROOT/triton"',
        '--model "$SFT_REF_MODEL"',
        '--served-model-name "$SFT_REF_SERVED_MODEL"',
        '--port "$SFT_REF_PORT"',
        '--gpu-memory-utilization "$SFT_REF_GPU_MEMORY_UTILIZATION"',
        '--max-num-seqs "$SFT_REF_MAX_NUM_SEQS"',
        "--max-logprobs 1",
        '--allowed-local-media-path "$SFT_REF_ALLOWED_MEDIA_PATH"',
        'REF_LOG="$LOG_DIR/reference_node_${NODE_RANK}.log"',
        "--tensor-parallel-size 1",
        'export WANDB_VERSION="0.28.1"',
        'WANDB_READY_FILE="$RUN_SYNC_DIR/${RUN_ID}.wandb_ready"',
        'WANDB_ERROR_FILE="$RUN_SYNC_DIR/${RUN_ID}.wandb_error"',
        '"wandb==$WANDB_VERSION"',
        "WANDB_MODE=offline",
        'export WANDB_DIR="$LOG_ROOT/wandb"',
        "import flash_attn",
    ):
        assert required in text
    assert text.index('cd "$ROOT_IMAGE_DIR"') < text.index('"$PYTHON_BIN" "$ROOT/scripts/sft/sample_plan.py"')
    assert text.index('"$ROOT/scripts/sft/sample_plan.py"') < text.index('"$ROOT/scripts/sft/materialize_lazy_plan_indices.py"')
    assert text.index('"$ROOT/scripts/sft/materialize_lazy_plan_indices.py"') < text.index('"${SWIFT_CMD[@]}" sft')
    for forbidden in (
        "--tuner_type lora",
        "--target_modules all-linear",
        "--lora_rank",
        "--lora_alpha",
        "--lora_dropout",
        "SFT_PASS_AT_1_TEMPERATURE",
        "--deepspeed zero2_offload",
        "--attn_impl sdpa",
        "--lazy_tokenize false",
    ):
        assert forbidden not in text


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
        'export SFT_DEBUG_MAX_LENGTH="${SFT_DEBUG_MAX_LENGTH:-49152}"',
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
        "--lazy_tokenize true",
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
