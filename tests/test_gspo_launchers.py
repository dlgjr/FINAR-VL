from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_gspo_environment_exports_four_node_eight_gpu_topology_and_all_overrides():
    text = (ROOT / "scripts" / "dlc" / "gspo_env.sh").read_text(encoding="utf-8")
    for required in (
        'GSPO_NNODES:-4',
        'GSPO_NPROC_PER_NODE:-7',
        'GSPO_TRAIN_GPUS:-0,1,2,3,4,5,6',
        'GSPO_JUDGE_GPU:-7',
        'GSPO_NUM_TRAIN_EPOCHS:-4',
        'GSPO_NUM_GENERATIONS:-16',
        'GSPO_NUM_ITERATIONS:-4',
        'GSPO_STEPS_PER_GENERATION:-4',
        'GSPO_GENERATION_BATCH_SIZE:-112',
        'GSPO_MAX_COMPLETION_LENGTH:-2048',
        'GSPO_MAX_LENGTH:-49152',
        'GSPO_DYNAMIC_SAMPLE:-true',
        'GSPO_MAX_RESAMPLE_TIMES:-3',
        'GSPO_SAVE_STEPS:-200',
    ):
        assert required in text


def test_gspo_launcher_uses_full_model_sequence_importance_and_offline_wandb():
    text = (ROOT / "scripts" / "dlc" / "start_gspo.sh").read_text(encoding="utf-8")
    for required in (
        'GSPO_JUDGE_MODEL must point',
        'GSPO_MODEL must be the merged full SFT model',
        'CUDA_VISIBLE_DEVICES="$GSPO_TRAIN_GPUS"',
        '--tuner_type full',
        '--importance_sampling_level sequence',
        '--freeze_vit false',
        '--freeze_aligner false',
        '--freeze_llm false',
        '--num_train_epochs',
        '--num_generations',
        '--steps_per_generation',
        '--generation_batch_size',
        '--save_only_model true',
        '--report_to wandb',
        '--callbacks gspo_eval',
        'export WANDB_MODE=offline',
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


def test_judge_server_defaults_are_single_gpu_and_eager():
    text = (ROOT / "scripts" / "dlc" / "start_gspo_judge.sh").read_text(encoding="utf-8")
    for required in ('--tensor-parallel-size 1', '--max-model-len', '--max-num-seqs', '--gpu-memory-utilization', '--enforce-eager'):
        assert required in text


def test_start_dlc_can_dispatch_full_gspo_stage():
    text = (ROOT / "scripts" / "dlc" / "start_dlc.sh").read_text(encoding="utf-8")
    assert 'DLC_STAGE:-smoke' in text
    assert 'start_gspo.sh' in text
    assert 'start_gspo_generation.sh' in text
    assert 'start_gspo_reasoning.sh' in text
