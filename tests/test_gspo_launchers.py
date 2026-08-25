from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_gspo_environment_exports_two_node_route_specific_topology_and_all_overrides():
    text = (ROOT / "scripts" / "dlc" / "gspo_env.sh").read_text(encoding="utf-8")
    for required in (
        'GSPO_NNODES:-2',
        'GSPO_DEFAULT_NPROC_PER_NODE=8',
        'GSPO_DEFAULT_NPROC_PER_NODE=4',
        'GSPO_DEFAULT_TRAIN_GPUS=0,1,2,3,4,5,6,7',
        'GSPO_DEFAULT_TRAIN_GPUS=0,1,2,3',
        'GSPO_JUDGE_GPU:-4,5,6,7',
        'GSPO_ENABLE_JUDGE:-$GSPO_DEFAULT_ENABLE_JUDGE',
        'GSPO_JUDGE_SERVE_NAME:-qwen235-judge',
        '/models/qwen235',
        'GSPO_JUDGE_MAX_TOKENS:-64',
        'GSPO_JUDGE_MAX_MODEL_LEN:-49152',
        'GSPO_JUDGE_TENSOR_PARALLEL_SIZE:-4',
        'GSPO_JUDGE_TOKENIZER_MODE:-auto',
        'GSPO_JUDGE_MAX_IMAGES:-32',
        'GSPO_JUDGE_BLOCK_SIZE:-32',
        'GSPO_NUM_TRAIN_EPOCHS:-4',
        'GSPO_NUM_GENERATIONS:-16',
        'GSPO_NUM_ITERATIONS:-4',
        'GSPO_STEPS_PER_GENERATION:-4',
        'GSPO_DEFAULT_GENERATION_BATCH_SIZE=64',
        'GSPO_DEFAULT_GENERATION_BATCH_SIZE=32',
        'GSPO_MAX_COMPLETION_LENGTH:-2048',
        'GSPO_MAX_LENGTH:-49152',
        'GSPO_GRADIENT_CHECKPOINTING:-true',
        'GSPO_VIT_GRADIENT_CHECKPOINTING:-true',
        'GSPO_VLLM_GPU_MEMORY_UTILIZATION:-0.60',
        'GSPO_DYNAMIC_SAMPLE:-true',
        'GSPO_MAX_RESAMPLE_TIMES:-3',
        'GSPO_BETA:-0.02',
        'GSPO_ENTROPY_COEF:-0.02',
        'GSPO_EPSILON:-0.01',
        'GSPO_EPSILON_HIGH:-0.02',
        'GSPO_SAVE_STEPS:-40',
    ):
        assert required in text


def test_gspo_launcher_uses_full_model_sequence_importance_and_offline_wandb():
    text = (ROOT / "scripts" / "dlc" / "start_gspo.sh").read_text(encoding="utf-8")
    for required in (
        'GSPO_JUDGE_MODEL must point',
        'GSPO_ENABLE_JUDGE" == "true',
        'GSPO_MODEL must be the merged full SFT model',
        'CUDA_VISIBLE_DEVICES="$GSPO_TRAIN_GPUS"',
        '--tuner_type full',
        '--importance_sampling_level sequence',
        '--freeze_vit false',
        '--freeze_aligner false',
        '--freeze_llm false',
        '--gradient_checkpointing',
        '--vit_gradient_checkpointing',
        '--num_train_epochs',
        '--num_generations',
        '--steps_per_generation',
        '--generation_batch_size',
        '--save_only_model true',
        '--report_to wandb',
        '--callbacks gspo_eval',
        'kl_beta=$GSPO_BETA entropy_coef=$GSPO_ENTROPY_COEF',
        'export WANDB_MODE=offline',
        'GSPO_LOCAL_TMPDIR="${GSPO_LOCAL_TMPDIR:-/tmp/qwen3vl-gspo-${GSPO_ROUTE_MODE}-node-${GSPO_NODE_RANK}}"',
        'TORCHINDUCTOR_CACHE_DIR="$TMPDIR/torchinductor"',
        'TRITON_CACHE_DIR="$TMPDIR/triton"',
        'export ROOT_IMAGE_DIR=',
        'cd "$ROOT_IMAGE_DIR"',
        '--root "$ROOT_IMAGE_DIR"',
        'GSPO_BENCHMARK_ALLOWLIST',
    ):
        assert required in text


def test_gspo_launcher_derives_expected_count_from_filtered_dataset():
    text = (ROOT / "scripts" / "dlc" / "start_gspo.sh").read_text(encoding="utf-8")
    assert 'GSPO_EXPECTED_COUNT="$(wc -l < "$GSPO_DATA"' in text
    assert '--expected-count "$GSPO_EXPECTED_COUNT"' in text
    assert '${GSPO_EXPECTED_COUNT:-6624}' not in text


def test_independent_generation_and_reasoning_launchers_share_only_sft_input():
    generation = (ROOT / "scripts" / "dlc" / "start_gspo_generation.sh").read_text(encoding="utf-8")
    reasoning = (ROOT / "scripts" / "dlc" / "start_gspo_reasoning.sh").read_text(encoding="utf-8")
    assert 'SFT_MODEL must point to the shared full SFT checkpoint' in generation
    assert 'GENERATION_RL_DATA must point' in generation
    assert 'GENERATION_RL_OUTPUT_DIR must be shared by all DLC nodes' in generation
    assert 'GSPO_ROUTE_MODE=generation' in generation
    assert 'SFT_MODEL must point to the shared full SFT checkpoint' in reasoning
    assert 'REASONING_RL_DATA must point' in reasoning
    assert 'REASONING_RL_OUTPUT_DIR must be shared by all DLC nodes' in reasoning
    assert 'GSPO_ROUTE_MODE=reasoning' in reasoning
    assert 'exec bash "$ROOT/scripts/dlc/start_gspo.sh"' in generation
    assert 'exec bash "$ROOT/scripts/dlc/start_gspo.sh"' in reasoning


def test_core_launcher_prepares_schedules_and_validates_explicit_routes():
    text = (ROOT / "scripts" / "dlc" / "start_gspo.sh").read_text(encoding="utf-8")
    assert '-m scripts.rl.prepare_gspo_data' in text
    assert '-m scripts.rl.schedule_gspo_data' in text
    assert '--route-mode "$GSPO_ROUTE_MODE"' in text
    assert 'data_validation.ready' in text


def test_judge_server_exposes_qwen3_vl_parallelism_images_and_is_eager():
    text = (ROOT / "scripts" / "dlc" / "start_gspo_judge.sh").read_text(encoding="utf-8")
    for required in (
        '--tensor-parallel-size "$GSPO_JUDGE_TENSOR_PARALLEL_SIZE"',
        '--tokenizer-mode "$GSPO_JUDGE_TOKENIZER_MODE"',
        '--allowed-local-media-path "$GSPO_JUDGE_ALLOWED_MEDIA_PATH"',
        '--limit-mm-per-prompt',
        '--kv-cache-dtype "$GSPO_JUDGE_KV_CACHE_DTYPE"',
        '--block-size "$GSPO_JUDGE_BLOCK_SIZE"',
        '--enable-expert-parallel',
        '--max-model-len',
        '--max-num-seqs',
        '--gpu-memory-utilization',
        '--enforce-eager',
        '--trust-remote-code',
    ):
        assert required in text


def test_start_dlc_can_dispatch_full_gspo_stage():
    text = (ROOT / "scripts" / "dlc" / "start_dlc.sh").read_text(encoding="utf-8")
    assert 'DLC_STAGE:-smoke' in text
    assert 'start_gspo.sh' in text
    assert 'start_gspo_generation.sh' in text
    assert 'start_gspo_reasoning.sh' in text
