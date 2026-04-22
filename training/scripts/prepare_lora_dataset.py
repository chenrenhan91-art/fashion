#!/usr/bin/env python3

from __future__ import annotations

import argparse
import csv
import json
import shutil
from pathlib import Path
from typing import Iterable


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

BLOCKED_RIGHTS_STATUSES = {
    "editorial_scan",
    "screen_capture",
    "third_party_reference",
    "third_party_reference_pinterest",
    "third_party_reference_pinterest_user_requested_training",
    "unlicensed_editorial",
    "unverified",
}

KNOWN_BRAND_TOKENS = {
    "alexander",
    "balenciaga",
    "chanel",
    "christian",
    "courreges",
    "cristobal",
    "dior",
    "elsa",
    "galliano",
    "gaultier",
    "gucci",
    "herpen",
    "iris",
    "issey",
    "jean",
    "john",
    "karl",
    "lagerfeld",
    "lee",
    "maison",
    "margiela",
    "martin",
    "mcqueen",
    "michele",
    "miyake",
    "mugler",
    "paco",
    "paris",
    "paul",
    "rabanne",
    "saint",
    "schiaparelli",
    "thierry",
    "van",
    "vivienne",
    "westwood",
    "yves",
    "ysl",
}

STYLE_CAPTION_PREFIX = {
    "marker_clean": "fashion design sketch, premium fashion marker illustration, full body figure, clean ivory background, black ink outlines, translucent marker layering",
    "paris_new_look": "fashion design sketch, delicate graphite construction lines, soft watercolor washes, archival couture presentation, hand-rendered paper texture",
    "elongated_drama": "fashion design sketch, expressive editorial linework, theatrical gouache and marker rendering, fashion archive presentation page",
    "atelier_luxe": "fashion design sketch, luxury atelier sketch, fast marker gestures, correction-fluid highlights, couture page finish, hand-drawn black linework",
    "modern_croquis": "fashion design sketch, rapid backstage croquis, thick black marker strokes, correction-fluid highlight accents, spontaneous couture page energy",
    "corset_cabaret": "fashion design sketch, corset seam notation, tattoo-like contour lines, cabaret couture attitude, decadent Paris page drama, precise erotic tailoring cues",
    "punk_rococo": "fashion design sketch, tartan marker blocks, anarchic biro gestures, historical drape disruption, punk couture collage energy, rebellious atelier page styling",
    "artisanal_deconstruction": "fashion design sketch, faint graphite outline, erased construction traces, deconstructed tailoring notes, archival xerox texture, artisanal atelier dossier, radical minimal fashion page",
    "pleated_motion": "fashion design sketch, engineered pleat notation, origami fold logic, fluid kinetic movement, luminous technical rendering, sculptural Japanese fashion page",
    "architectural_volume": "fashion design sketch, sculptural couture study, architectural tailoring notes, cool restrained rendering, clean volume emphasis, archive presentation page",
    "surreal_gold": "fashion design sketch, heavy black ink outlines, gold-leaf accent feel, surreal couture page language, unfinished luxury rendering",
    "hourglass_power": "fashion design sketch, sculpted couture rendering, sharp editorial linework, body-conscious luxury presentation drawing",
    "bionic_couture": "fashion design sketch, ultra-fine fineliner linework, geometric blueprint grids, futuristic couture draft, technical hand-rendered page",
    "space_age_clean": "fashion design sketch, crisp mod geometry, clean white-space composition, precise linework, 1960s space-age fashion plate, minimal futuristic rendering",
    "metal_modular": "fashion design sketch, metallic modular construction, linked-disc material language, industrial couture rendering, sharp structural page presentation",
    "insect_power": "fashion design sketch, sharp power silhouette, insect-mechanical couture details, strong editorial contrast, sculpted dramatic presentation drawing",
    "maximalist_romance": "fashion design sketch, layered colored pencil gestures, saturated watercolor blooms, retro-maximalist ornament, romantic archival page styling",
    "gothic_theatre": "fashion design sketch, smudged charcoal atmosphere, graphite scratch marks, dark theatrical couture page, emotionally charged hand-drawn process energy",
    "baroque_narrative": "fashion design sketch, densely layered couture page, historical costume drama, expressive rendering, opulent showpiece fashion illustration",
    "minimalist_chic": "fashion design sketch, sparse black ink linework, bold monochrome marker blocking, disciplined white space, elegant modern couture presentation page",
}

GARMENT_TRANSLATIONS = {
    "晚礼服": "evening gown",
    "礼服": "gown",
    "连衣裙": "dress",
    "长裙": "long skirt",
    "半裙": "skirt",
    "上衣": "top",
    "衬衫": "shirt",
    "外套": "coat",
    "大衣": "coat",
    "夹克": "jacket",
    "西装": "tailored suit",
    "西装外套": "tailored jacket",
    "裤子": "trousers",
    "长裤": "trousers",
    "背心": "vest",
    "马甲": "waistcoat",
    "胸衣": "bustier",
    "紧身衣": "bodysuit",
    "披风": "cape",
    "斗篷": "cape",
}


def main() -> None:
    args = parse_args()
    output_dir = args.output_dir.resolve()
    train_dir = output_dir / "train"
    if train_dir.exists():
        shutil.rmtree(train_dir)
    train_dir.mkdir(parents=True, exist_ok=True)

    generated_records = load_records(args.source)
    if args.style:
        generated_records = [
            record for record in generated_records if record.get("style") == args.style
        ]

    reference_rows = load_reference_rows(
        reference_dirs=args.reference_dir or [],
        curation_csvs=args.curation_csv or [],
        style=args.style,
        min_fit_score=args.min_fit_score,
        allow_unverified_rights=args.allow_unverified_rights,
    )

    if not generated_records and not reference_rows:
        raise SystemExit("No generated records or reference rows matched the requested source/style.")

    metadata_path = train_dir / "metadata.jsonl"
    captions_path = output_dir / "captions.csv"
    manifest_copy_path = output_dir / "source_manifest.jsonl"
    metadata_lines: list[str] = []
    captions_lines = ["file_name,caption"]
    styles: set[str] = set()
    source_counts = {"generated_pair": 0, "reference_image": 0}

    with manifest_copy_path.open("w", encoding="utf-8") as manifest_file:
        for record in generated_records:
            output_image = Path(record["output_path"])
            if not output_image.exists():
                continue

            file_name = next_file_name(train_dir, output_image.suffix)
            destination = train_dir / file_name
            shutil.copy2(output_image, destination)

            caption = build_generated_caption(record)
            metadata = {
                "file_name": file_name,
                "text": caption,
                "style": record.get("style"),
                "source_type": "generated_pair",
                "source_path": record.get("output_path"),
                "prompt": record.get("prompt"),
                "input_path": record.get("input_path"),
                "output_path": record.get("output_path"),
                "analysis_path": record.get("analysis_path"),
            }
            metadata_lines.append(json.dumps(metadata, ensure_ascii=False))
            captions_lines.append(f"{file_name},{csv_escape(caption)}")
            manifest_file.write(json.dumps(record, ensure_ascii=False) + "\n")
            if record.get("style"):
                styles.add(str(record.get("style")))
            source_counts["generated_pair"] += 1

        for row in reference_rows:
            image_path = Path(row["file_path"])
            if not image_path.exists():
                continue

            file_name = next_file_name(train_dir, image_path.suffix)
            destination = train_dir / file_name
            shutil.copy2(image_path, destination)

            caption = build_reference_caption(row)
            metadata = {
                "file_name": file_name,
                "text": caption,
                "style": row.get("style"),
                "source_type": "reference_image",
                "source_path": row.get("file_path"),
                "prompt": row.get("caption_override"),
                "analysis_path": None,
                "rights_status": row.get("rights_status"),
                "traceable_original_found": row.get("traceable_original_found"),
                "fit_for_lora": row.get("fit_for_lora"),
                "notes": row.get("notes"),
            }
            metadata_lines.append(json.dumps(metadata, ensure_ascii=False))
            captions_lines.append(f"{file_name},{csv_escape(caption)}")
            manifest_file.write(json.dumps(row, ensure_ascii=False) + "\n")
            if row.get("style"):
                styles.add(str(row.get("style")))
            source_counts["reference_image"] += 1

    metadata_path.write_text("\n".join(metadata_lines) + "\n", encoding="utf-8")
    captions_path.write_text("\n".join(captions_lines) + "\n", encoding="utf-8")

    dataset_card = {
        "num_images": len(metadata_lines),
        "styles": sorted(styles),
        "source_count": source_counts["generated_pair"] + source_counts["reference_image"],
        "source_types": source_counts,
    }
    (output_dir / "dataset_info.json").write_text(
        json.dumps(dataset_card, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    if args.zip:
        archive_base = shutil.make_archive(str(output_dir), "zip", root_dir=output_dir)
        print(f"Created remote bundle: {archive_base}")

    print(f"Prepared {len(metadata_lines)} LoRA training image(s) in {train_dir}")
    print(f"Generated pairs: {source_counts['generated_pair']}")
    print(f"Reference images: {source_counts['reference_image']}")
    print(f"Metadata: {metadata_path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert generated manifests and curated references into a diffusers-ready imagefolder dataset."
    )
    parser.add_argument(
        "--source",
        nargs="*",
        default=[],
        help="Optional manifest file(s) or directories containing manifest.jsonl files.",
    )
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--style", help="Optional style slug filter, for example atelier_luxe.")
    parser.add_argument(
        "--reference-dir",
        nargs="*",
        help="Optional directory or directories containing curated sketch reference images.",
    )
    parser.add_argument(
        "--curation-csv",
        action="append",
        type=Path,
        help=(
            "Optional review sheet CSV for reference images. Repeat the flag to merge multiple "
            "curation sheets. Supports approved filtering, fit score, and caption overrides."
        ),
    )
    parser.add_argument(
        "--min-fit-score",
        type=float,
        default=0,
        help="Optional minimum fit_for_lora score to keep rows from the curation CSV.",
    )
    parser.add_argument(
        "--allow-unverified-rights",
        action="store_true",
        help="Include rows whose rights_status is not explicitly cleared. Use only after you verify rights offline.",
    )
    parser.add_argument(
        "--zip",
        action="store_true",
        help="Also package the prepared dataset directory as a zip bundle for remote training providers.",
    )
    return parser.parse_args()


def load_records(sources: Iterable[str]) -> list[dict]:
    manifests: list[Path] = []
    for source in sources:
        source_path = Path(source).expanduser().resolve()
        if source_path.is_dir():
            manifests.extend(sorted(source_path.rglob("manifest.jsonl")))
        elif source_path.is_file():
            manifests.append(source_path)

    records: list[dict] = []
    for manifest in manifests:
        for line in manifest.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            records.append(json.loads(line))
    return records


def load_reference_rows(
    reference_dirs: Iterable[str],
    curation_csvs: Iterable[Path],
    style: str | None,
    min_fit_score: float,
    allow_unverified_rights: bool,
) -> list[dict]:
    rows: list[dict] = []
    seen: set[tuple[str, str]] = set()

    for curation_csv in curation_csvs:
        rows.extend(
            load_reference_rows_from_csv(
                curation_csv=Path(curation_csv).expanduser().resolve(),
                style=style,
                min_fit_score=min_fit_score,
                allow_unverified_rights=allow_unverified_rights,
            )
        )

    for reference_dir in reference_dirs:
        root = Path(reference_dir).expanduser().resolve()
        if not root.exists():
            continue
        for image_path in sorted(root.rglob("*")):
            if not image_path.is_file() or not is_supported_image(image_path):
                continue
            rows.append(
                {
                    "file_path": str(image_path),
                    "style": style or infer_style_from_path(image_path),
                    "approved": "1",
                    "fit_for_lora": "",
                    "caption_override": "",
                    "extra_tags": "",
                    "rights_status": "self_owned",
                    "traceable_original_found": "1",
                    "notes": "",
                }
            )

    deduped_rows: list[dict] = []
    for row in rows:
        file_path = str(row.get("file_path") or "").strip()
        row_style = str(row.get("style") or style or "marker_clean").strip() or "marker_clean"
        key = (file_path, row_style)
        if key in seen:
            continue
        seen.add(key)
        deduped_rows.append(row)
    return deduped_rows


def load_reference_rows_from_csv(
    curation_csv: Path,
    style: str | None,
    min_fit_score: float,
    allow_unverified_rights: bool,
) -> list[dict]:
    if not curation_csv.exists():
        raise SystemExit(f"Curation CSV does not exist: {curation_csv}")

    rows: list[dict] = []
    with curation_csv.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for raw_row in reader:
            row = dict(raw_row)
            file_path = Path(str(row.get("file_path") or "")).expanduser()
            if not file_path.is_absolute():
                file_path = (Path.cwd() / file_path).resolve()
            if not file_path.exists() or not is_supported_image(file_path):
                continue

            row_style = str(row.get("style") or style or infer_style_from_path(file_path)).strip()
            if style and row_style != style:
                continue
            if not is_truthy(row.get("approved"), default=True):
                continue

            fit_score = parse_float(row.get("fit_for_lora"))
            if fit_score is not None and fit_score < min_fit_score:
                continue
            if not allow_unverified_rights and not has_cleared_rights(row):
                continue

            row["file_path"] = str(file_path)
            row["style"] = row_style or "marker_clean"
            rows.append(row)
    return rows


def build_generated_caption(record: dict) -> str:
    style = record.get("style") or "marker_clean"
    prefix = STYLE_CAPTION_PREFIX.get(style, STYLE_CAPTION_PREFIX["marker_clean"])
    prompt = normalize_prompt(record.get("prompt"))
    analysis_terms = analysis_tags(record.get("analysis_path"))

    parts = [prefix]
    if analysis_terms:
        parts.append(", ".join(analysis_terms))
    if prompt:
        parts.append(prompt)
    parts.append("full body fashion illustration")

    return sanitize_caption(", ".join(part.strip(" ,.") for part in parts if part))


def build_reference_caption(row: dict) -> str:
    caption_override = str(row.get("caption_override") or "").strip()
    if caption_override:
        return sanitize_caption(caption_override)

    style = str(row.get("style") or "marker_clean").strip() or "marker_clean"
    prefix = STYLE_CAPTION_PREFIX.get(style, STYLE_CAPTION_PREFIX["marker_clean"])
    parts = [prefix]

    extra_tags = split_tags(row.get("extra_tags"))
    if extra_tags:
        parts.append(", ".join(extra_tags))

    name_tags = filename_tokens(Path(str(row.get("file_path") or "")))
    if name_tags:
        parts.append(", ".join(name_tags))

    parts.append("fashion sketch reference image")
    return sanitize_caption(", ".join(part.strip(" ,.") for part in parts if part))


def analysis_tags(analysis_path: str | None) -> list[str]:
    if not analysis_path:
        return []
    path = Path(analysis_path)
    if not path.exists():
        return []

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []

    items = payload.get("items") or []
    tags = []
    for item in items:
        name = str(item.get("item") or "").strip()
        if not name:
            continue
        tags.append(GARMENT_TRANSLATIONS.get(name, name))
    return tags[:4]


def normalize_prompt(value: str | None) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    replacements = [
        ("Create a ", ""),
        ("Create ", ""),
        ("Transform ", ""),
        ("that preserves the original outfit identity while ", ""),
        ("preserving the original outfit identity while ", ""),
    ]
    for old, new in replacements:
        text = text.replace(old, new)
    return text.strip(" .")


def csv_escape(value: str) -> str:
    return '"' + value.replace('"', '""') + '"'


def next_file_name(train_dir: Path, suffix: str | None) -> str:
    extension = (suffix or ".jpg").lower() or ".jpg"
    existing = sorted(train_dir.glob("*"))
    return f"{len(existing) + 1:05d}{extension}"


def split_tags(value: object) -> list[str]:
    text = str(value or "").strip()
    if not text:
        return []
    for separator in (";", "|"):
        text = text.replace(separator, ",")
    return [item.strip() for item in text.split(",") if item.strip()]


def filename_tokens(path: Path) -> list[str]:
    stem = path.stem.replace("_", " ").replace("-", " ").strip().lower()
    if not stem:
        return []
    tokens = [
        token for token in stem.split()
        if len(token) > 2 and token not in KNOWN_BRAND_TOKENS
    ]
    return tokens[:4]


def has_cleared_rights(row: dict) -> bool:
    rights_status = normalize_token(row.get("rights_status"))
    if rights_status in ALLOWED_RIGHTS_STATUSES:
        return True
    if rights_status in BLOCKED_RIGHTS_STATUSES:
        return False
    return False


def sanitize_caption(text: str) -> str:
    if not text:
        return ""
    kept_tokens = []
    for raw_token in text.replace("/", " ").replace("|", " ").split():
        cleaned = raw_token.strip(" ,.;:()[]{}\"'").lower()
        if cleaned and cleaned in KNOWN_BRAND_TOKENS:
            continue
        kept_tokens.append(raw_token)
    sanitized = " ".join(kept_tokens)
    while "  " in sanitized:
        sanitized = sanitized.replace("  ", " ")
    return sanitized.strip(" ,.;:")


def normalize_token(value: object) -> str:
    return str(value or "").strip().lower().replace("-", "_").replace(" ", "_")


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


def is_supported_image(path: Path) -> bool:
    return path.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}


def infer_style_from_path(path: Path) -> str:
    known_styles = set(STYLE_CAPTION_PREFIX)
    for part in reversed(path.parts):
        candidate = part.strip().lower().replace("-", "_")
        if candidate in known_styles:
            return candidate
    return "marker_clean"


if __name__ == "__main__":
    main()
