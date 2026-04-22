#!/usr/bin/env python3

from __future__ import annotations

import argparse
import csv
import json
from datetime import date
from pathlib import Path


FOUNDATION_PREFIX = (
    "fashion designer hand sketch, atelier croquis, expressive graphite construction "
    "lines, black ink definition, translucent marker and watercolor rendering, clean "
    "ivory paper background, couture presentation page"
)


def parse_args() -> argparse.Namespace:
    root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(
        description=(
            "Convert the Draftelier prompt archive into a LoRA-oriented training schema "
            "with trigger, short caption, validation prompt, and negative prompt fields."
        )
    )
    parser.add_argument(
        "--input-json",
        type=Path,
        default=root / "training" / "manifests" / "style_prompt_archive.json",
        help="Source prompt archive JSON.",
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=root / "training" / "manifests" / "style_training_schema.json",
        help="Output training schema JSON.",
    )
    parser.add_argument(
        "--output-csv",
        type=Path,
        default=root / "training" / "manifests" / "style_training_schema.csv",
        help="Output training schema CSV.",
    )
    parser.add_argument(
        "--manuscript-json",
        type=Path,
        default=root / "training" / "manifests" / "style_manuscript_lexicon.json",
        help="Optional designer manuscript reinforcement lexicon JSON.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    archive = json.loads(args.input_json.expanduser().resolve().read_text(encoding="utf-8"))
    manuscript_lexicon = load_manuscript_lexicon(args.manuscript_json.expanduser().resolve())
    styles = [
        build_style_schema(style, manuscript_lexicon.get(resolve_style_key(style), {}))
        for style in archive.get("styles", [])
    ]

    payload = {
        "title": "Draftelier Style Training Schema",
        "subtitle": "LoRA-ready trigger, short caption, validation prompt, and negative prompt archive",
        "version": archive.get("version") or "1.0",
        "created_on": date.today().isoformat(),
        "foundation_prefix": FOUNDATION_PREFIX,
        "field_usage": {
            "trigger_phrase": "Short style trigger for inference and validation prompts.",
            "manuscript_trigger_words": (
                "Hand-drawn reinforcement tags that bias LoRA training away from digital "
                "realism and toward designer manuscript texture."
            ),
            "training_caption": "Recommended short LoRA caption for style-specific training.",
            "training_caption_foundation": "Generic hand-sketch caption that suppresses house-specific identity.",
            "training_caption_hybrid": "Recommended caption for second-stage style LoRAs built on a hand-sketch foundation.",
            "validation_prompt": "Prompt to sample during checkpoints and final validation.",
            "negative_prompt": "Negative prompt to keep training and inference out of photoreal/editorial drift.",
        },
        "styles": styles,
    }

    write_json(args.output_json.expanduser().resolve(), payload)
    write_csv(args.output_csv.expanduser().resolve(), styles)

    print(f"Wrote training schema JSON to {args.output_json.expanduser().resolve()}")
    print(f"Wrote training schema CSV to {args.output_csv.expanduser().resolve()}")


def build_style_schema(
    style: dict[str, object], manuscript_meta: dict[str, str] | None = None
) -> dict[str, object]:
    token = normalize(str(style.get("token") or "marker_clean"))
    style_en = str(style.get("style_en") or "").strip()
    medium = strip_trailing_period(str(style.get("medium") or ""))
    strokes = strip_trailing_period(str(style.get("strokes") or ""))
    vibe = strip_trailing_period(str(style.get("vibe") or ""))
    trigger_phrase = str(style.get("trigger_phrase") or "").strip()
    negative_prompt = str(style.get("negative_prompt") or "").strip()
    master_prompt = str(style.get("master_prompt") or "").strip()
    manuscript_trigger_words = strip_trailing_period(
        str((manuscript_meta or {}).get("manuscript_trigger_words") or "")
    )

    style_label = normalize_phrase(style_en)
    descriptors = build_descriptor_stack(
        manuscript_trigger_words=manuscript_trigger_words,
        medium=medium,
        strokes=strokes,
        vibe=vibe,
    )
    style_caption = compact_join(
        [
            token,
            "fashion designer hand sketch",
            f"{style_label} fashion illustration" if style_label else "fashion illustration",
            *descriptors,
            "clean paper ground",
        ]
    )
    foundation_caption = compact_join(
        [
            FOUNDATION_PREFIX,
            *descriptors,
        ]
    )
    hybrid_caption = compact_join(
        [
            FOUNDATION_PREFIX,
            token,
            f"{style_label} fashion illustration" if style_label else "fashion illustration",
            *descriptors,
        ]
    )
    validation_prompt = build_validation_prompt(
        master_prompt=master_prompt,
        trigger_phrase=trigger_phrase,
        medium=medium,
        strokes=strokes,
        vibe=vibe,
        manuscript_trigger_words=manuscript_trigger_words,
    )

    return {
        "order": style.get("order"),
        "id": style.get("id"),
        "repo_style_id": style.get("repo_style_id"),
        "designer": style.get("designer"),
        "style_en": style.get("style_en"),
        "style_cn": style.get("style_cn"),
        "token": token,
        "trigger_phrase": trigger_phrase,
        "manuscript_trigger_words": manuscript_trigger_words,
        "training_caption": style_caption,
        "training_caption_foundation": foundation_caption,
        "training_caption_hybrid": hybrid_caption,
        "validation_prompt": validation_prompt,
        "negative_prompt": negative_prompt,
        "research_notes_cn": style.get("research_notes_cn"),
        "medium": medium,
        "strokes": strokes,
        "vibe": vibe,
        "active_lora_run": style.get("active_lora_run"),
        "lora_ready": style.get("lora_ready"),
    }


def load_manuscript_lexicon(path: Path) -> dict[str, dict[str, str]]:
    if not path.exists():
        return {}

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}

    lexicon: dict[str, dict[str, str]] = {}
    for style in payload.get("styles", []):
        entry = {
            "manuscript_trigger_words": str(style.get("manuscript_trigger_words") or "").strip(),
        }
        for raw_key in (style.get("token"), style.get("id"), style.get("repo_style_id")):
            key = normalize(str(raw_key or ""))
            if key:
                lexicon[key] = entry
    return lexicon


def resolve_style_key(style: dict[str, object]) -> str:
    for raw_key in (style.get("token"), style.get("id"), style.get("repo_style_id")):
        key = normalize(str(raw_key or ""))
        if key:
            return key
    return "marker_clean"


def build_descriptor_stack(
    *,
    manuscript_trigger_words: str,
    medium: str,
    strokes: str,
    vibe: str,
) -> list[str]:
    if not manuscript_trigger_words:
        return [item for item in [medium, strokes, vibe] if item]

    seen: set[str] = set()
    descriptors: list[str] = []
    for chunk in (manuscript_trigger_words, medium, strokes, vibe):
        for descriptor in split_descriptors(chunk):
            normalized_key = normalize_descriptor_key(descriptor)
            if not normalized_key or normalized_key in seen:
                continue
            seen.add(normalized_key)
            descriptors.append(descriptor)
    return descriptors


def build_validation_prompt(
    *,
    master_prompt: str,
    trigger_phrase: str,
    medium: str,
    strokes: str,
    vibe: str,
    manuscript_trigger_words: str,
) -> str:
    base_prompt = master_prompt or compact_join(
        [
            trigger_phrase,
            f"Medium: {medium}" if medium else "",
            strokes,
            vibe,
            "clean paper ground",
        ]
    )
    if not manuscript_trigger_words:
        return base_prompt

    reinforcement = f"Hand-drawn manuscript reinforcement: {manuscript_trigger_words}."
    if not base_prompt:
        return reinforcement
    return f"{base_prompt.rstrip()} {reinforcement}".strip()


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_csv(path: Path, styles: list[dict[str, object]]) -> None:
    if not styles:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(styles[0].keys())
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(styles)


def compact_join(parts: list[str]) -> str:
    usable = [normalize_phrase(part) for part in parts if normalize_phrase(part)]
    return ", ".join(usable)


def split_descriptors(value: str) -> list[str]:
    return [
        normalize_phrase(part)
        for part in str(value or "").split(",")
        if normalize_phrase(part)
    ]


def normalize_descriptor_key(value: str) -> str:
    return normalize_phrase(value).lower().replace("’", "'")


def normalize(value: str) -> str:
    return value.strip().lower().replace("-", "_").replace(" ", "_")


def normalize_phrase(value: str) -> str:
    return " ".join(str(value or "").strip().split())


def strip_trailing_period(value: str) -> str:
    return normalize_phrase(value).rstrip(".")


if __name__ == "__main__":
    main()
