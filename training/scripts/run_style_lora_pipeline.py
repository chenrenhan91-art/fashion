#!/usr/bin/env python3

from __future__ import annotations

import argparse
import shlex
import subprocess
import sys
from pathlib import Path


def main() -> None:
    args = parse_args()
    root_dir = Path(__file__).resolve().parents[2]
    dataset_dir = Path(args.dataset_dir).expanduser().resolve()
    output_dir = Path(args.output_dir).expanduser().resolve()

    prepare_command = [
        sys.executable,
        str(root_dir / "training" / "scripts" / "prepare_lora_dataset.py"),
        "--output-dir",
        str(dataset_dir),
        "--min-fit-score",
        str(args.min_fit_score),
    ]
    if args.style:
        prepare_command.extend(["--style", args.style])
    if args.source:
        prepare_command.extend(["--source", *args.source])
    else:
        prepare_command.extend(["--source", str(root_dir / "training-data")])
    if args.reference_dir:
        prepare_command.extend(["--reference-dir", *args.reference_dir])
    for curation_csv in args.curation_csv or []:
        prepare_command.extend(
            ["--curation-csv", str(Path(curation_csv).expanduser().resolve())]
        )
    if args.zip:
        prepare_command.append("--zip")

    train_command = [
        str(root_dir / ".venv-lora" / "bin" / "python"),
        str(root_dir / "training" / "scripts" / "train_lora_local.py"),
        "--dataset-dir",
        str(dataset_dir),
        "--output-dir",
        str(output_dir),
        "--resolution",
        str(args.resolution),
        "--train-batch-size",
        str(args.train_batch_size),
        "--gradient-accumulation-steps",
        str(args.gradient_accumulation_steps),
        "--max-train-steps",
        str(args.max_train_steps),
        "--learning-rate",
        str(args.learning_rate),
        "--rank",
        str(args.rank),
        "--seed",
        str(args.seed),
    ]
    if not args.disable_checkpointing:
        train_command.extend(["--checkpointing-steps", str(args.checkpointing_steps)])
    else:
        train_command.append("--disable-checkpointing")
    if args.skip_validation:
        train_command.append("--skip-validation")
    elif args.validation_prompt:
        train_command.extend(["--validation-prompt", args.validation_prompt])

    print("Preparing LoRA dataset:")
    print(" ".join(shlex.quote(part) for part in prepare_command))
    subprocess.run(prepare_command, check=True)

    print("Launching LoRA training:")
    print(" ".join(shlex.quote(part) for part in train_command))
    subprocess.run(train_command, check=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Prepare a style-specific LoRA dataset and launch local training."
    )
    parser.add_argument("--source", nargs="*", help="Manifest file(s) or generated training-data directories.")
    parser.add_argument("--reference-dir", nargs="*", help="Curated reference image directories to merge in.")
    parser.add_argument(
        "--curation-csv",
        action="append",
        help=(
            "Optional review sheet CSV created from build_reference_curation_sheet.py. "
            "Repeat the flag to merge multiple curation sheets."
        ),
    )
    parser.add_argument("--style", help="Style slug to filter or assign, for example atelier_luxe.")
    parser.add_argument("--dataset-dir", required=True, help="Prepared dataset output directory.")
    parser.add_argument("--output-dir", required=True, help="Training run output directory.")
    parser.add_argument("--min-fit-score", type=float, default=0)
    parser.add_argument("--zip", action="store_true", help="Also package the prepared dataset as a zip bundle.")
    parser.add_argument("--resolution", type=int, default=512)
    parser.add_argument("--train-batch-size", type=int, default=1)
    parser.add_argument("--gradient-accumulation-steps", type=int, default=4)
    parser.add_argument("--max-train-steps", type=int, default=200)
    parser.add_argument("--learning-rate", type=float, default=1e-4)
    parser.add_argument("--rank", type=int, default=8)
    parser.add_argument("--checkpointing-steps", type=int, default=50)
    parser.add_argument("--disable-checkpointing", action="store_true")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--skip-validation", action="store_true")
    parser.add_argument("--validation-prompt")
    return parser.parse_args()


if __name__ == "__main__":
    main()
