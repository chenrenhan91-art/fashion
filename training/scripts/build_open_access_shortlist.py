#!/usr/bin/env python3

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path


GENERIC_QUERIES = {
    "fashion plate",
    "costume design drawing",
    "dress design drawing",
    "fashion sketch",
    "fashion illustration",
}

TEXT_BONUSES = {
    "costume design": 28,
    "costume designs": 28,
    "costume design for": 30,
    "theater costume": 18,
    "preparatory drawing": 16,
    "fashion illustration": 22,
    "fashion sketch": 20,
    "fashion study": 18,
    "fashion magazine": 14,
    "gallery of fashion": 16,
    "day dress": 10,
    "evening dress": 10,
    "croquis": 18,
    "drawing": 14,
    "drawings": 14,
    "graphite": 12,
    "ink": 12,
    "watercolor": 12,
    "gouache": 12,
    "charcoal": 12,
    "marker": 10,
    "pen": 8,
    "pastel": 8,
    "study": 8,
    "plate": 6,
    "print": 4,
    "prints": 4,
    "etching": 4,
    "lithograph": 4,
    "aquatint": 4,
}

TEXT_PENALTIES = {
    "coat of arms": -30,
    "vaulted ceiling": -30,
    "ceiling": -22,
    "architecture": -18,
    "architectural": -18,
    "ornament": -10,
    "furniture": -30,
    "portrait": -18,
    "actor": -12,
    "actress": -12,
    "military": -16,
    "monument": -30,
    "crucifix": -22,
    "helmet": -16,
    "inscription": -12,
    "sketchbook": -8,
    "manner of dress": -14,
    "oriental costume": -10,
}


@dataclass
class ShortlistRow:
    style: str
    file_path: str
    file_name: str
    source_key: str
    external_id: str
    query: str
    title: str
    object_type: str
    classification: str
    source_url: str
    rights_status: str
    original_score: int
    shortlist_score: int
    duplicate_style_count: int
    duplicate_styles: str
    owner_style: str
    owner_match: str
    shortlist_tier: str
    recommended_role: str
    style_rank: int
    heuristic_reason: str
    notes: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build a first-pass shortlist from the downloaded official open-access "
            "fashion sketch candidate packs."
        )
    )
    parser.add_argument(
        "--candidates-root",
        type=Path,
        default=Path(__file__).resolve().parents[2] / "output" / "open-access-candidates",
        help="Root folder that contains one candidates.json per training style.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "reviews",
        help="Folder where shortlist CSV/JSON files should be written.",
    )
    parser.add_argument(
        "--top-per-style",
        type=int,
        default=8,
        help="How many ranked picks to surface per style in the top-per-style CSV.",
    )
    parser.add_argument(
        "--core-per-style",
        type=int,
        default=6,
        help="How many top picks per style should be tagged as core training references.",
    )
    return parser.parse_args()


def normalize_text(*parts: object) -> str:
    return " ".join(str(part or "").strip().lower() for part in parts if str(part or "").strip())


def compute_shortlist_score(item: dict, duplicate_style_count: int) -> tuple[int, list[str]]:
    text = normalize_text(
        item.get("title"),
        item.get("object_type"),
        item.get("classification"),
        item.get("query"),
        item.get("notes"),
    )
    score = int(item.get("score") or 0)
    reasons: list[str] = [f"base={score}"]

    for term, bonus in TEXT_BONUSES.items():
        if term in text:
            score += bonus
            reasons.append(f"+{bonus}:{term}")

    for term, penalty in TEXT_PENALTIES.items():
        if term in text:
            score += penalty
            reasons.append(f"{penalty}:{term}")

    title = str(item.get("title") or "").strip().lower()
    if title == "fashion":
        score -= 10
        reasons.append("-10:generic_title")

    query = str(item.get("query") or "").strip().lower()
    if query and query not in GENERIC_QUERIES:
        score += 6
        reasons.append("+6:specific_query")

    if str(item.get("rights_status") or "").strip().lower() == "public_domain":
        score += 5
        reasons.append("+5:public_domain")

    duplicate_penalty = max(0, duplicate_style_count - 1) * 4
    if duplicate_penalty:
        score -= duplicate_penalty
        reasons.append(f"-{duplicate_penalty}:cross_style_duplicate")

    return score, reasons


def shortlist_tier(score: int) -> str:
    if score >= 78:
        return "A"
    if score >= 60:
        return "B"
    if score >= 44:
        return "C"
    return "D"


def recommended_role(rank: int, owner_match: bool, tier: str, core_per_style: int, top_per_style: int) -> str:
    if owner_match and rank <= core_per_style and tier in {"A", "B"}:
        return "core_train"
    if owner_match and rank <= top_per_style and tier in {"A", "B", "C"}:
        return "style_support"
    if rank <= top_per_style:
        return "cross_style_review"
    if tier in {"A", "B"}:
        return "holdout_review"
    return "backup_only"


def main() -> None:
    args = parse_args()
    rows_by_style = load_candidate_rows(args.candidates_root)
    fingerprints = Counter()
    styles_by_fingerprint: dict[tuple[str, str], set[str]] = defaultdict(set)

    for style, items in rows_by_style.items():
        for item in items:
            key = fingerprint(item)
            fingerprints[key] += 1
            styles_by_fingerprint[key].add(style)

    owner_by_fingerprint = choose_owner_styles(rows_by_style, fingerprints)
    shortlist_rows = build_shortlist_rows(
        rows_by_style,
        fingerprints,
        styles_by_fingerprint,
        owner_by_fingerprint,
        args.core_per_style,
        args.top_per_style,
    )

    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    master_path = output_dir / "open_access_shortlist_round1_master.csv"
    top_path = output_dir / "open_access_shortlist_round1_top_per_style.csv"
    summary_path = output_dir / "open_access_shortlist_round1_summary.json"

    write_csv(master_path, shortlist_rows)
    top_rows = select_top_rows(shortlist_rows, args.top_per_style)
    write_csv(top_path, top_rows)
    write_summary(summary_path, shortlist_rows, top_rows)

    print(f"Wrote {len(shortlist_rows)} master shortlist rows to {master_path}")
    print(f"Wrote {len(top_rows)} ranked top rows to {top_path}")
    print(f"Wrote summary to {summary_path}")


def load_candidate_rows(candidates_root: Path) -> dict[str, list[dict]]:
    rows_by_style: dict[str, list[dict]] = {}
    for candidates_path in sorted(candidates_root.glob("*/candidates.json")):
        payload = json.loads(candidates_path.read_text(encoding="utf-8"))
        rows_by_style[candidates_path.parent.name] = list(payload.get("downloaded") or [])
    return rows_by_style


def fingerprint(item: dict) -> tuple[str, str]:
    return (
        str(item.get("source_key") or "").strip(),
        str(item.get("external_id") or "").strip(),
    )


def choose_owner_styles(
    rows_by_style: dict[str, list[dict]],
    fingerprints: Counter,
) -> dict[tuple[str, str], str]:
    best_by_fingerprint: dict[tuple[str, str], tuple[int, int, str]] = {}

    for style, items in rows_by_style.items():
        for item in items:
            key = fingerprint(item)
            score, _ = compute_shortlist_score(item, fingerprints[key])
            query_bonus = 1 if str(item.get("query") or "").strip().lower() not in GENERIC_QUERIES else 0
            current = best_by_fingerprint.get(key)
            candidate = (score, query_bonus, style)
            if current is None or candidate > current:
                best_by_fingerprint[key] = candidate

    return {key: value[2] for key, value in best_by_fingerprint.items()}


def build_shortlist_rows(
    rows_by_style: dict[str, list[dict]],
    fingerprints: Counter,
    styles_by_fingerprint: dict[tuple[str, str], set[str]],
    owner_by_fingerprint: dict[tuple[str, str], str],
    core_per_style: int,
    top_per_style: int,
) -> list[ShortlistRow]:
    rows: list[ShortlistRow] = []

    for style, items in sorted(rows_by_style.items()):
        scored_rows: list[ShortlistRow] = []
        for item in items:
            key = fingerprint(item)
            duplicate_style_count = len(styles_by_fingerprint[key])
            score, reasons = compute_shortlist_score(item, duplicate_style_count)
            owner_style = owner_by_fingerprint.get(key, style)
            owner_match = owner_style == style

            scored_rows.append(
                ShortlistRow(
                    style=style,
                    file_path=str(item.get("file_path") or ""),
                    file_name=str(item.get("file_name") or ""),
                    source_key=str(item.get("source_key") or ""),
                    external_id=str(item.get("external_id") or ""),
                    query=str(item.get("query") or ""),
                    title=str(item.get("title") or ""),
                    object_type=str(item.get("object_type") or ""),
                    classification=str(item.get("classification") or ""),
                    source_url=str(item.get("source_url") or ""),
                    rights_status=str(item.get("rights_status") or ""),
                    original_score=int(item.get("score") or 0),
                    shortlist_score=score,
                    duplicate_style_count=duplicate_style_count,
                    duplicate_styles=" | ".join(sorted(styles_by_fingerprint[key])),
                    owner_style=owner_style,
                    owner_match="yes" if owner_match else "no",
                    shortlist_tier=shortlist_tier(score),
                    recommended_role="",
                    style_rank=0,
                    heuristic_reason="; ".join(reasons),
                    notes=str(item.get("notes") or ""),
                )
            )

        scored_rows.sort(
            key=lambda row: (
                row.owner_match != "yes",
                -row.shortlist_score,
                -row.original_score,
                row.title.lower(),
                row.file_name.lower(),
            )
        )

        for index, row in enumerate(scored_rows, start=1):
            row.style_rank = index
            row.recommended_role = recommended_role(
                rank=index,
                owner_match=row.owner_match == "yes",
                tier=row.shortlist_tier,
                core_per_style=core_per_style,
                top_per_style=top_per_style,
            )

        rows.extend(scored_rows)

    return rows


def select_top_rows(rows: list[ShortlistRow], top_per_style: int) -> list[ShortlistRow]:
    selected: list[ShortlistRow] = []
    by_style: dict[str, list[ShortlistRow]] = defaultdict(list)
    for row in rows:
        by_style[row.style].append(row)

    for style in sorted(by_style):
        selected.extend(by_style[style][:top_per_style])
    return selected


def write_csv(path: Path, rows: list[ShortlistRow]) -> None:
    fieldnames = [
        "style",
        "style_rank",
        "shortlist_tier",
        "recommended_role",
        "owner_style",
        "owner_match",
        "shortlist_score",
        "original_score",
        "duplicate_style_count",
        "duplicate_styles",
        "query",
        "title",
        "object_type",
        "classification",
        "rights_status",
        "file_path",
        "file_name",
        "source_key",
        "external_id",
        "source_url",
        "heuristic_reason",
        "notes",
    ]

    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row.__dict__)


def write_summary(path: Path, all_rows: list[ShortlistRow], top_rows: list[ShortlistRow]) -> None:
    summary = {
        "generated_by": "build_open_access_shortlist.py",
        "master_row_count": len(all_rows),
        "top_row_count": len(top_rows),
        "styles": {},
    }

    by_style: dict[str, list[ShortlistRow]] = defaultdict(list)
    for row in all_rows:
        by_style[row.style].append(row)

    for style in sorted(by_style):
        rows = by_style[style]
        summary["styles"][style] = {
            "total_candidates": len(rows),
            "owner_matches": sum(1 for row in rows if row.owner_match == "yes"),
            "core_train": sum(1 for row in rows if row.recommended_role == "core_train"),
            "style_support": sum(1 for row in rows if row.recommended_role == "style_support"),
            "top_pick_titles": [row.title for row in rows[:3]],
        }

    path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
