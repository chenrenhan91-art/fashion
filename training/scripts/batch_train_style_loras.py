#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import sys
from pathlib import Path


STYLE_BATCH = [
    {
        "id": "dior",
        "name": "Parisian Couture",
        "training_style": "paris_new_look",
        "run_slug": "paris-new-look-owned-v1",
        "validation_prompt": "couture fashion study, delicate graphite construction lines, soft watercolor restraint, archival presentation sketch",
    },
    {
        "id": "balenciaga",
        "name": "Sculptural Elegance",
        "training_style": "architectural_volume",
        "run_slug": "architectural-volume-owned-v1",
        "validation_prompt": "fashion design sketch, sculptural volume, restrained graphite contours, cool gouache shading, atelier presentation page",
    },
    {
        "id": "schiaparelli",
        "name": "Surreal Ornament",
        "training_style": "surreal_gold",
        "run_slug": "surreal-gold-owned-v1",
        "validation_prompt": "fashion illustration, sharp black ink outlines, luminous metallic accents, surreal couture page energy",
    },
    {
        "id": "chanel",
        "name": "Modern Croquis",
        "training_style": "modern_croquis",
        "run_slug": "modern-croquis-owned-v1",
        "validation_prompt": "fashion sketch, rapid backstage croquis, thick black marker strokes, correction-fluid highlights, editorial fitting energy",
    },
    {
        "id": "mugler",
        "name": "Futurist Glamour",
        "training_style": "insect_power",
        "run_slug": "insect-power-owned-v1",
        "validation_prompt": "fashion design sketch, sharp ink contour, high-contrast marker shading, engineered detail, futuristic couture drama",
    },
    {
        "id": "galliano",
        "name": "Baroque Narrative",
        "training_style": "baroque_narrative",
        "run_slug": "baroque-narrative-owned-v1",
        "validation_prompt": "fashion illustration, expressive ink linework, lavish watercolor layering, embellished costume notation, romantic theatrical movement",
    },
    {
        "id": "gaultier",
        "name": "Corset Cabaret",
        "training_style": "corset_cabaret",
        "run_slug": "corset-cabaret-owned-v1",
        "validation_prompt": "fashion design sketch, tattoo-like contour line, corsetry seam notation, performance styling cues, decadent editorial tension",
    },
    {
        "id": "westwood",
        "name": "Punk Aristocracy",
        "training_style": "punk_rococo",
        "run_slug": "punk-rococo-owned-v1",
        "validation_prompt": "fashion sketch, anarchic biro and ink line, collage blocking, disrupted historic drape, rebellious editorial attitude",
    },
    {
        "id": "maison_margiela",
        "name": "Deconstructed Modern",
        "training_style": "artisanal_deconstruction",
        "run_slug": "artisanal-deconstruction-owned-v1",
        "validation_prompt": "fashion study, faint graphite outline, erased construction marks, sparse pattern notation, grayscale archival texture",
    },
    {
        "id": "iris_van_herpen",
        "name": "Bionic Motion",
        "training_style": "bionic_couture",
        "run_slug": "bionic-couture-owned-v1",
        "validation_prompt": "fashion design sketch, ultra-fine technical drafting pen, kinetic movement, 3D geometry, wireframe grids on a clean page",
    },
    {
        "id": "issey_miyake",
        "name": "Pleated Velocity",
        "training_style": "pleated_motion",
        "run_slug": "pleated-motion-owned-v1",
        "validation_prompt": "fashion design sketch, precise pleat notation, origami fold logic, airy graphite line, fluid sculptural motion marks",
    },
    {
        "id": "courreges",
        "name": "Space Age Precision",
        "training_style": "space_age_clean",
        "run_slug": "space-age-clean-owned-v1",
        "validation_prompt": "fashion sketch, crisp geometric ink lines, minimal flat marker wash, optical white space, polished mod futurism",
    },
    {
        "id": "rabanne",
        "name": "Metallic Modularism",
        "training_style": "metal_modular",
        "run_slug": "metal-modular-owned-v1",
        "validation_prompt": "fashion design sketch, reflective ink edges, metallic marker shading, modular construction notes, precise industrial contrast",
    },
    {
        "id": "gucci",
        "name": "Romantic Maximalism",
        "training_style": "maximalist_romance",
        "run_slug": "maximalist-romance-owned-v1",
        "validation_prompt": "fashion illustration, layered colored pencils, saturated watercolor, quirky retro styling, vibrant expressive page",
    },
    {
        "id": "mcqueen",
        "name": "Dark Poise",
        "training_style": "gothic_theatre",
        "run_slug": "gothic-theatre-owned-v1",
        "validation_prompt": "fashion sketch, smudged charcoal atmosphere, sharp graphite scratchings, dramatic couture tension, composed gothic mood",
    },
    {
        "id": "ysl",
        "name": "Minimal Precision",
        "training_style": "minimalist_chic",
        "run_slug": "minimalist-chic-owned-v1",
        "validation_prompt": "fashion design sketch, sparse precise black ink lines, flat marker blocking, sleek tailoring, elegant negative space",
    },
]

SUPPORTED_IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"}


def main() -> None:
    args = parse_args()
    root_dir = Path(__file__).resolve().parents[2]
    reviews_dir = args.reviews_dir.expanduser().resolve()
    output_root = args.output_root.expanduser().resolve()
    training_runs_root = args.training_runs_root.expanduser().resolve()
    reference_root = (
        args.authorized_reference_root.expanduser().resolve()
        if args.authorized_reference_root
        else None
    )

    audit_by_style = load_audit(root_dir, reviews_dir, args.min_fit_score)
    selected_training_styles = set(args.style or [])
    plan = build_plan(
        audit_by_style=audit_by_style,
        reviews_dir=reviews_dir,
        output_root=output_root,
        training_runs_root=training_runs_root,
        reference_root=reference_root,
        min_cleared_rows=args.min_cleared_rows,
        min_fit_ready_rows=args.min_fit_ready_rows,
        selected_training_styles=selected_training_styles,
    )

    if args.json:
        print(json.dumps(plan, ensure_ascii=False, indent=2))
    else:
        print_plan(plan, args.min_cleared_rows, args.min_fit_ready_rows)

    ready_items = [item for item in plan if item["status"] == "ready"]
    if not args.prepare_ready_datasets and not args.launch_ready_training:
        return

    if not ready_items:
        print("\nNo style families meet the current rights/data thresholds, so nothing was launched.")
        return

    for item in ready_items:
        dataset_dir = Path(item["dataset_dir"])
        training_run_dir = Path(item["training_run_dir"])

        prepare_command = [
            sys.executable,
            str(root_dir / "training" / "scripts" / "prepare_lora_dataset.py"),
            "--output-dir",
            str(dataset_dir),
            "--style",
            item["training_style"],
            "--min-fit-score",
            str(args.min_fit_score),
        ]
        for curation_csv in item["curation_csvs"]:
            prepare_command.extend(["--curation-csv", curation_csv])
        for reference_dir in item["reference_dirs"]:
            prepare_command.extend(["--reference-dir", reference_dir])

        if args.prepare_ready_datasets or args.launch_ready_training:
            run_command("Preparing dataset", prepare_command)

        if not args.launch_ready_training:
            continue

        train_command = [
            sys.executable,
            str(root_dir / "training" / "scripts" / "train_lora_local.py"),
            "--dataset-dir",
            str(dataset_dir),
            "--output-dir",
            str(training_run_dir),
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
            "--validation-prompt",
            item["validation_prompt"],
        ]

        if args.skip_validation:
            train_command.append("--skip-validation")
        if args.disable_checkpointing:
            train_command.append("--disable-checkpointing")
        else:
            train_command.extend(["--checkpointing-steps", str(args.checkpointing_steps)])

        run_command("Launching training", train_command)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Audit all 16 Draftelier style families, then prepare/train only the ones "
            "backed by rights-cleared or user-owned reference data."
        )
    )
    parser.add_argument(
        "--reviews-dir",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "reviews",
        help="Directory containing curation CSV review sheets.",
    )
    parser.add_argument(
        "--authorized-reference-root",
        type=Path,
        help=(
            "Optional root folder of user-owned reference packs. Each style should live in "
            "<root>/<training_style>/."
        ),
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path(__file__).resolve().parents[2] / "output" / "style-batches",
        help="Root folder for prepared datasets.",
    )
    parser.add_argument(
        "--training-runs-root",
        type=Path,
        default=Path(__file__).resolve().parents[2] / "training-runs",
        help="Root folder for LoRA training outputs.",
    )
    parser.add_argument(
        "--style",
        action="append",
        help="Optional training_style slug filter. Repeat the flag to target specific style families.",
    )
    parser.add_argument(
        "--min-fit-score",
        type=float,
        default=3,
        help="Minimum fit_for_lora score counted as training-ready in review CSVs.",
    )
    parser.add_argument(
        "--min-cleared-rows",
        type=int,
        default=12,
        help="Minimum count of rights-cleared reference images before a style family is considered launchable.",
    )
    parser.add_argument(
        "--min-fit-ready-rows",
        type=int,
        default=8,
        help="Minimum count of training-ready references before a style family is considered launchable.",
    )
    parser.add_argument(
        "--prepare-ready-datasets",
        action="store_true",
        help="Build datasets for every style family that clears the current rights/data thresholds.",
    )
    parser.add_argument(
        "--launch-ready-training",
        action="store_true",
        help="After dataset prep, launch local training for every ready style family.",
    )
    parser.add_argument("--resolution", type=int, default=512)
    parser.add_argument("--train-batch-size", type=int, default=1)
    parser.add_argument("--gradient-accumulation-steps", type=int, default=4)
    parser.add_argument("--max-train-steps", type=int, default=400)
    parser.add_argument("--learning-rate", type=float, default=1e-4)
    parser.add_argument("--rank", type=int, default=16)
    parser.add_argument("--checkpointing-steps", type=int, default=100)
    parser.add_argument("--disable-checkpointing", action="store_true")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--skip-validation", action="store_true")
    parser.add_argument("--json", action="store_true", help="Emit the plan as JSON.")
    return parser.parse_args()


def load_audit(root_dir: Path, reviews_dir: Path, min_fit_score: float) -> dict[str, dict]:
    command = [
        sys.executable,
        str(root_dir / "training" / "scripts" / "audit_style_readiness.py"),
        "--reviews-dir",
        str(reviews_dir),
        "--min-fit-score",
        str(min_fit_score),
        "--json",
    ]
    completed = subprocess.run(command, check=True, capture_output=True, text=True)
    payload = json.loads(completed.stdout or "[]")
    return {item["style"]: item for item in payload}


def build_plan(
    audit_by_style: dict[str, dict],
    reviews_dir: Path,
    output_root: Path,
    training_runs_root: Path,
    reference_root: Path | None,
    min_cleared_rows: int,
    min_fit_ready_rows: int,
    selected_training_styles: set[str],
) -> list[dict]:
    plan: list[dict] = []

    for style in STYLE_BATCH:
        training_style = style["training_style"]
        if selected_training_styles and training_style not in selected_training_styles:
            continue

        audit = audit_by_style.get(
            training_style,
            {
                "approved_rows": 0,
                "cleared_rows": 0,
                "fit_ready_rows": 0,
                "blocked_rows": 0,
                "source_files": [],
            },
        )

        reference_dir = reference_root / training_style if reference_root else None
        owned_reference_count = count_reference_images(reference_dir)
        owned_reference_dirs = [str(reference_dir)] if owned_reference_count > 0 else []
        effective_cleared_rows = int(audit.get("cleared_rows", 0)) + owned_reference_count
        effective_fit_ready_rows = int(audit.get("fit_ready_rows", 0)) + owned_reference_count

        if (
            effective_cleared_rows >= min_cleared_rows
            and effective_fit_ready_rows >= min_fit_ready_rows
        ):
            status = "ready"
        elif effective_cleared_rows > 0 or owned_reference_count > 0:
            status = "needs_more_authorized_data"
        else:
            status = "blocked_no_cleared_rights"

        missing_cleared_rows = max(min_cleared_rows - effective_cleared_rows, 0)
        missing_fit_ready_rows = max(min_fit_ready_rows - effective_fit_ready_rows, 0)
        curation_csvs = [
            str((reviews_dir / file_name).resolve())
            for file_name in audit.get("source_files", [])
        ]

        plan.append(
            {
                "id": style["id"],
                "name": style["name"],
                "training_style": training_style,
                "status": status,
                "approved_rows": int(audit.get("approved_rows", 0)),
                "cleared_rows": int(audit.get("cleared_rows", 0)),
                "fit_ready_rows": int(audit.get("fit_ready_rows", 0)),
                "blocked_rows": int(audit.get("blocked_rows", 0)),
                "owned_reference_count": owned_reference_count,
                "effective_cleared_rows": effective_cleared_rows,
                "effective_fit_ready_rows": effective_fit_ready_rows,
                "missing_cleared_rows": missing_cleared_rows,
                "missing_fit_ready_rows": missing_fit_ready_rows,
                "reference_dirs": owned_reference_dirs,
                "expected_reference_dir": str(reference_dir) if reference_dir else None,
                "curation_csvs": curation_csvs,
                "dataset_dir": str((output_root / "datasets" / training_style).resolve()),
                "training_run_dir": str((training_runs_root / style["run_slug"]).resolve()),
                "validation_prompt": style["validation_prompt"],
            }
        )

    return plan


def print_plan(plan: list[dict], min_cleared_rows: int, min_fit_ready_rows: int) -> None:
    print(
        f"Style LoRA batch plan (ready requires >= {min_cleared_rows} cleared refs and "
        f">= {min_fit_ready_rows} training-ready refs)"
    )
    print(
        "training_style,status,cleared_rows,fit_ready_rows,owned_reference_count,"
        "effective_cleared_rows,effective_fit_ready_rows,missing_cleared_rows,missing_fit_ready_rows"
    )
    for item in plan:
        print(
            ",".join(
                [
                    item["training_style"],
                    item["status"],
                    str(item["cleared_rows"]),
                    str(item["fit_ready_rows"]),
                    str(item["owned_reference_count"]),
                    str(item["effective_cleared_rows"]),
                    str(item["effective_fit_ready_rows"]),
                    str(item["missing_cleared_rows"]),
                    str(item["missing_fit_ready_rows"]),
                ]
            )
        )

    blocked = [item for item in plan if item["status"] != "ready"]
    if not blocked:
        return

    print("\nBlocked or incomplete style families:")
    for item in blocked:
        print(
            f"- {item['training_style']}: {item['status']} "
            f"(cleared={item['effective_cleared_rows']}, fit_ready={item['effective_fit_ready_rows']}, "
            f"add_cleared={item['missing_cleared_rows']}, add_fit_ready={item['missing_fit_ready_rows']})"
        )
        if item["expected_reference_dir"]:
            print(f"  authorized_pack_dir: {item['expected_reference_dir']}")


def count_reference_images(path: Path | None) -> int:
    if path is None or not path.exists():
        return 0
    return sum(
        1
        for image_path in path.rglob("*")
        if image_path.is_file() and image_path.suffix.lower() in SUPPORTED_IMAGE_SUFFIXES
    )


def run_command(label: str, command: list[str]) -> None:
    print(f"\n{label}:")
    print(" ".join(shlex.quote(part) for part in command))
    subprocess.run(command, check=True)


if __name__ == "__main__":
    main()
