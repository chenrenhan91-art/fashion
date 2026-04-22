#!/usr/bin/env python3

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path


ALLOWED_RIGHTS_STATUSES = {
    "commissioned",
    "first_party_reference",
    "internal_archive",
    "licensed",
    "open_license",
    "owned_reference_pack",
    "public_domain",
    "self_created",
    "self_owned",
    "user_provided",
}


def main() -> None:
    args = parse_args()
    reviews_dir = args.reviews_dir.resolve()
    csv_paths = sorted(reviews_dir.glob("*.csv"))
    if not csv_paths:
        raise SystemExit(f"No review CSV files found in {reviews_dir}")

    summary = defaultdict(
        lambda: {
            "approved_rows": 0,
            "cleared_rows": 0,
            "fit_ready_rows": 0,
            "blocked_rows": 0,
            "rights_statuses": defaultdict(int),
            "source_files": set(),
        }
    )

    for csv_path in csv_paths:
        with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                style = str(row.get("style") or "").strip() or "unknown"
                approved = is_truthy(row.get("approved"), default=True)
                fit_score = parse_float(row.get("fit_for_lora")) or 0
                rights_status = normalize_token(row.get("rights_status")) or "missing"

                bucket = summary[style]
                bucket["source_files"].add(csv_path.name)
                bucket["rights_statuses"][rights_status] += 1

                if not approved:
                    continue

                bucket["approved_rows"] += 1
                if rights_status in ALLOWED_RIGHTS_STATUSES:
                    bucket["cleared_rows"] += 1
                    if fit_score >= args.min_fit_score:
                        bucket["fit_ready_rows"] += 1
                else:
                    bucket["blocked_rows"] += 1

    rendered = []
    for style, data in sorted(summary.items()):
        rendered.append(
            {
                "style": style,
                "approved_rows": data["approved_rows"],
                "cleared_rows": data["cleared_rows"],
                "fit_ready_rows": data["fit_ready_rows"],
                "blocked_rows": data["blocked_rows"],
                "source_files": sorted(data["source_files"]),
                "rights_statuses": dict(sorted(data["rights_statuses"].items())),
            }
        )

    if args.json:
        print(json.dumps(rendered, ensure_ascii=False, indent=2))
        return

    print(
        "style,approved_rows,cleared_rows,fit_ready_rows,blocked_rows,source_files"
    )
    for item in rendered:
        print(
            ",".join(
                [
                    item["style"],
                    str(item["approved_rows"]),
                    str(item["cleared_rows"]),
                    str(item["fit_ready_rows"]),
                    str(item["blocked_rows"]),
                    "|".join(item["source_files"]),
                ]
            )
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Summarize which style families have enough cleared references for LoRA training."
    )
    parser.add_argument(
        "--reviews-dir",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "reviews",
        help="Directory containing curation CSV files.",
    )
    parser.add_argument(
        "--min-fit-score",
        type=float,
        default=3,
        help="Minimum fit_for_lora score counted as training-ready once rights are cleared.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON instead of CSV-style text output.",
    )
    return parser.parse_args()


def parse_float(value: object) -> float | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def is_truthy(value: object, default: bool = False) -> bool:
    text = str(value or "").strip().lower()
    if not text:
        return default
    return text in {"1", "true", "yes", "y", "approved", "keep"}


def normalize_token(value: object) -> str:
    return str(value or "").strip().lower().replace("-", "_").replace(" ", "_")


if __name__ == "__main__":
    main()
