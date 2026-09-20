import argparse
import json
import os
import subprocess
from pathlib import Path

REGISTRY_PATH = Path(__file__).with_name("benchmarks.json")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmarks", nargs="+", default=["all"])
    parser.add_argument("--model", default=os.environ.get("MODEL_NAME", "FINAR-VL-4B"))
    parser.add_argument("--api-base", default=os.environ.get("API_BASE", "http://127.0.0.1:8000/v1"))
    parser.add_argument("--api-key", default=os.environ.get("API_KEY", "EMPTY"))
    parser.add_argument("--output-dir", default=os.environ.get("OUTPUT_DIR", "evaluation/results"))
    args = parser.parse_args()

    registry = json.loads(REGISTRY_PATH.read_text())
    names = list(registry) if args.benchmarks == ["all"] else args.benchmarks
    env = os.environ.copy()
    env["MODEL_NAME"] = args.model
    env["API_BASE"] = args.api_base
    env["API_KEY"] = args.api_key
    env["OUTPUT_DIR"] = args.output_dir
    Path(args.output_dir).mkdir(parents=True, exist_ok=True)

    for name in names:
        cfg = registry[name]
        root = env.get(cfg["root_env"], "")
        command = cfg.get("command", "")
        if cfg.get("command_env"):
            command = env.get(cfg["command_env"], command)
        if not root or not command:
            print(f"[skip] {name}: set {cfg['root_env']} and {cfg.get('command_env', 'the benchmark command')}")
            continue
        print(f"[run] {name}: {command}")
        subprocess.run(command, shell=True, cwd=root, env=env)

if __name__ == "__main__":
    main()
