#!/usr/bin/env python3

from __future__ import annotations

import argparse
import csv
import json
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
from urllib.parse import urlparse

import requests

GLOBAL_REQUIRED_TERMS = {
    "fashion",
    "costume",
    "dress",
    "garment",
    "gown",
    "tailoring",
    "coat",
    "jacket",
    "skirt",
    "bodice",
    "corset",
    "robe",
    "ensemble",
    "clothing",
    "attire",
    "wear",
    "cloak",
}

VISUAL_REQUIRED_TERMS = {
    "sketch",
    "drawing",
    "illustration",
    "plate",
    "design",
    "croquis",
    "engraving",
    "print",
    "prints",
    "etching",
    "lithograph",
    "aquatint",
    "mezzotint",
    "graphite",
    "ink",
    "watercolor",
    "rendering",
}

GLOBAL_EXCLUDED_TERMS = {
    "desk",
    "chair",
    "table",
    "cabinet",
    "vase",
    "ceramic",
    "silver",
    "teapot",
    "furniture",
    "mirror",
    "building",
    "architecture",
    "map",
    "landscape",
    "still life",
    "painting",
    "sculpture",
    "stained glass",
    "sacrament",
    "coin",
    "armor",
    "sword",
    "weapon",
}

OBJECT_TYPE_PRIORITY = [
    "fashion plate",
    "costume design",
    "fashion design",
    "dress design",
    "fashion illustration",
    "costume sketch",
    "fashion sketch",
    "croquis",
    "drawing",
    "illustration",
    "print",
    "prints",
    "etching",
    "lithograph",
    "aquatint",
    "design",
]

GENERIC_QUERY_BACKSTOPS = [
    "fashion plate",
    "costume design drawing",
    "dress design drawing",
    "fashion sketch",
    "fashion illustration",
]

DESCRIPTOR_QUERY_SUFFIXES = [
    "fashion sketch",
    "costume design drawing",
    "fashion plate",
]

QUERY_VARIANT_LIMIT = 12

CANDIDATE_FIELDS = [
    "file_path",
    "file_name",
    "style",
    "source_bucket",
    "visual_type",
    "designer_house",
    "collection_or_year",
    "screening_decision",
    "screening_reason",
    "review_action",
    "approved",
    "fit_for_lora",
    "caption_override",
    "extra_tags",
    "rights_status",
    "traceable_original_found",
    "hand_drawn_score",
    "paper_texture_score",
    "designer_specificity_score",
    "garment_readability_score",
    "composition_clarity_score",
    "archive_value_score",
    "ai_generated_risk",
    "duplication_risk",
    "notes",
]

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"
)


@dataclass
class Candidate:
    style_id: str
    training_style: str
    source_key: str
    query: str
    external_id: str
    title: str
    creator: str
    date: str
    object_type: str
    classification: str
    source_url: str
    image_url: str
    rights_status: str
    rights_statement: str
    score: int
    prompt_hint: str
    search_focus: str
    notes: str
    raw: dict


class MetOpenAccessClient:
    search_url = "https://collectionapi.metmuseum.org/public/collection/v1/search"
    object_url = "https://collectionapi.metmuseum.org/public/collection/v1/objects/{object_id}"

    def __init__(self, session: requests.Session):
        self.session = session
        self.object_cache: dict[int, dict] = {}

    def get_json(self, url: str, *, params: dict | None = None) -> dict:
        last_error: Exception | None = None
        for attempt in range(4):
            try:
                response = self.session.get(url, params=params, timeout=30)
                response.raise_for_status()
                return response.json()
            except ValueError as error:
                last_error = error
                if attempt == 3:
                    raise
                time.sleep(1.5 * (attempt + 1))
            except requests.RequestException as error:
                last_error = error
                status = getattr(error.response, "status_code", None)
                if status not in {403, 429, 500, 502, 503, 504} or attempt == 3:
                    raise
                time.sleep(1.5 * (attempt + 1))
        raise last_error or RuntimeError(f"Failed to fetch {url}")

    def search(
        self,
        style_pack: dict,
        query: str,
        limit: int,
        search_window: int,
        delay_ms: int,
    ) -> list[Candidate]:
        payload = self.get_json(self.search_url, params={"hasImages": "true", "q": query})
        object_ids = payload.get("objectIDs") or []
        candidates: list[Candidate] = []

        for object_id in object_ids[: max(search_window, limit * 120)]:
            try:
                item = self.fetch_object(int(object_id))
            except requests.RequestException:
                continue
            candidate = build_met_candidate(style_pack, query, item)
            if not candidate:
                if delay_ms > 0:
                    time.sleep(delay_ms / 1000)
                continue
            candidates.append(candidate)
            if len(candidates) >= limit:
                break
            if delay_ms > 0:
                time.sleep(delay_ms / 1000)

        return candidates

    def fetch_object(self, object_id: int) -> dict:
        cached = self.object_cache.get(object_id)
        if cached is not None:
            return cached
        item = self.get_json(self.object_url.format(object_id=object_id))
        self.object_cache[object_id] = item
        return item


class LibraryOfCongressClient:
    search_url = "https://www.loc.gov/search/"

    def __init__(self, session: requests.Session):
        self.session = session
        self.item_cache: dict[str, dict] = {}

    def get_json(self, url: str, *, params: dict | None = None) -> dict:
        last_error: Exception | None = None
        for attempt in range(4):
            try:
                response = self.session.get(url, params=params, timeout=30)
                response.raise_for_status()
                return response.json()
            except ValueError as error:
                last_error = error
                if attempt == 3:
                    raise
                time.sleep(1.5 * (attempt + 1))
            except requests.RequestException as error:
                last_error = error
                status = getattr(error.response, "status_code", None)
                if status not in {403, 429, 500, 502, 503, 504} or attempt == 3:
                    raise
                time.sleep(1.5 * (attempt + 1))
        raise last_error or RuntimeError(f"Failed to fetch {url}")

    def search(
        self,
        style_pack: dict,
        query: str,
        limit: int,
        search_window: int,
        delay_ms: int,
    ) -> list[Candidate]:
        payload = self.get_json(
            self.search_url,
            params={"fo": "json", "q": query, "c": min(max(search_window, 25), 100)},
        )
        results = payload.get("results") or []
        candidates: list[Candidate] = []
        for item in results[: max(search_window, limit * 10)]:
            try:
                full_item = self.fetch_item(item)
            except requests.RequestException:
                continue
            candidate = build_loc_candidate(style_pack, query, full_item)
            if not candidate:
                if delay_ms > 0:
                    time.sleep(delay_ms / 1000)
                continue
            candidates.append(candidate)
            if len(candidates) >= limit:
                break
            if delay_ms > 0:
                time.sleep(delay_ms / 1000)
        return candidates

    def fetch_item(self, search_item: dict) -> dict:
        raw_url = str(search_item.get("url") or "").strip()
        if not raw_url:
            return search_item
        item_url = normalize_loc_url(raw_url)
        cache_key = item_url
        cached = self.item_cache.get(cache_key)
        if cached is not None:
            return cached
        payload = self.get_json(f"{item_url}?fo=json")
        item = payload.get("item") or search_item
        self.item_cache[cache_key] = item
        return item


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Download rights-cleared open-access fashion sketch candidates and emit "
            "a review-ready curation CSV per style family."
        )
    )
    parser.add_argument(
        "--manifest-json",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "manifests" / "open_access_style_search_manifest.json",
        help="Path to the open-access style manifest JSON.",
    )
    parser.add_argument(
        "--style",
        action="append",
        help="Optional training_style slug(s) to fetch. Defaults to all 16 styles.",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path(__file__).resolve().parents[2] / "output" / "open-access-candidates",
        help="Root folder for downloaded candidates.",
    )
    parser.add_argument(
        "--max-per-style",
        type=int,
        default=20,
        help="Maximum downloaded candidates per style.",
    )
    parser.add_argument(
        "--max-per-query",
        type=int,
        default=5,
        help="Maximum candidates taken from each precise query.",
    )
    parser.add_argument(
        "--delay-ms",
        type=int,
        default=120,
        help="Delay between object fetches to stay polite to source APIs.",
    )
    parser.add_argument(
        "--search-window",
        type=int,
        default=500,
        help="Maximum source records to inspect for each query before moving on.",
    )
    parser.add_argument(
        "--source",
        action="append",
        choices=["met", "loc"],
        default=["met"],
        help="Official source to query. Repeat to enable more than one source.",
    )
    return parser.parse_args()


def load_manifest(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def make_session() -> requests.Session:
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})
    return session


def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", (text or "").lower())


def slugify(value: str) -> str:
    value = re.sub(r"[^a-z0-9]+", "-", value.lower())
    return value.strip("-") or "candidate"


def flatten_text_list(values: object) -> str:
    if not isinstance(values, list):
        return str(values or "").strip()
    parts: list[str] = []
    for value in values:
        if isinstance(value, dict):
            parts.extend(str(key).strip() for key in value.keys() if str(key).strip())
        else:
            text = str(value or "").strip()
            if text:
                parts.append(text)
    return " ".join(parts)


def build_precise_queries(style_pack: dict) -> list[str]:
    queries: list[str] = []
    base_terms = (
        GENERIC_QUERY_BACKSTOPS
        + list(style_pack.get("preferred_object_types") or [])
        + list(style_pack.get("query_terms") or [])
    )
    for base in base_terms:
        cleaned = " ".join(str(base).split())
        if not cleaned:
            continue
        queries.append(cleaned)
        lowered = cleaned.lower()
        if any(
            token in lowered
            for token in ["fashion", "costume", "dress", "garment", "gown", "tailoring", "coat", "corset", "pleat"]
        ):
            if "fashion illustration" in lowered:
                queries.append("fashion illustration")
            if "fashion sketch" in lowered or "croquis" in lowered:
                queries.append("fashion sketch")
        else:
            if "fashion" in lowered and "plate" in lowered:
                queries.append("fashion plate")
                queries.append(cleaned)
            elif "costume" in lowered and "design" in lowered:
                queries.append("costume design drawing")
                queries.append(cleaned)
            elif "dress" in lowered and "design" in lowered:
                queries.append("dress design drawing")
                queries.append(cleaned)
            else:
                queries.append(cleaned)

        if len(tokenize(cleaned)) > 4:
            compact = " ".join(tokenize(cleaned)[:4])
            if compact:
                queries.append(compact)

    descriptor_terms = sorted(
        token
        for token in build_style_cue_terms(style_pack)
        if token not in GLOBAL_REQUIRED_TERMS and token not in VISUAL_REQUIRED_TERMS
    )
    for descriptor in descriptor_terms[:3]:
        for suffix in DESCRIPTOR_QUERY_SUFFIXES:
            queries.append(f"{descriptor} {suffix}")

    deduped: list[str] = []
    seen: set[str] = set()
    for query in queries:
        key = query.strip().lower()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(query)
    return deduped[:QUERY_VARIANT_LIMIT]


def build_style_cue_terms(style_pack: dict) -> set[str]:
    text_bits = [
        style_pack.get("display_name", ""),
        style_pack.get("search_focus", ""),
        " ".join(style_pack.get("preferred_object_types") or []),
        " ".join(style_pack.get("query_terms") or []),
    ]
    tokens = tokenize(" ".join(text_bits))
    banned = {
        "fashion",
        "design",
        "sketch",
        "drawing",
        "illustration",
        "costume",
        "study",
        "editorial",
        "page",
        "style",
        "the",
        "and",
        "with",
        "for",
    }
    return {token for token in tokens if len(token) > 3 and token not in banned}


def score_style_match(style_pack: dict, haystack: str, hay_tokens: set[str]) -> int:
    preferred_types = [part.lower() for part in style_pack.get("preferred_object_types") or []]
    cue_terms = build_style_cue_terms(style_pack)
    score = 0

    for phrase in preferred_types:
        if phrase and phrase in haystack:
            score += 12
    for phrase in OBJECT_TYPE_PRIORITY:
        if phrase in haystack:
            score += 6
    for cue in cue_terms:
        if cue in hay_tokens:
            score += 2

    return score


def score_query_overlap(query: str, hay_tokens: set[str]) -> int:
    score = 0
    for token in tokenize(query):
        if token not in hay_tokens:
            continue
        if token in {"fashion", "costume", "dress", "garment", "gown", "coat", "skirt", "corset", "tailoring"}:
            score += 2
        elif token in {"sketch", "drawing", "illustration", "plate", "design", "croquis", "print", "prints"}:
            score += 2
        elif len(token) > 4:
            score += 3
        else:
            score += 1
    return min(score, 12)


def build_met_candidate(style_pack: dict, query: str, item: dict) -> Candidate | None:
    if not item.get("isPublicDomain"):
        return None
    image_url = item.get("primaryImage") or item.get("primaryImageSmall") or ""
    if not image_url:
        return None

    text_fields = [
        item.get("title", ""),
        item.get("objectName", ""),
        item.get("classification", ""),
        item.get("department", ""),
        item.get("artistDisplayName", ""),
        item.get("artistDisplayBio", ""),
        item.get("culture", ""),
        item.get("medium", ""),
        item.get("objectDate", ""),
    ]
    haystack = " ".join(part for part in text_fields if part).lower()
    hay_tokens = set(tokenize(haystack))

    if hay_tokens.isdisjoint(GLOBAL_REQUIRED_TERMS):
        return None
    if hay_tokens.isdisjoint(VISUAL_REQUIRED_TERMS):
        return None
    if any(term in haystack for term in GLOBAL_EXCLUDED_TERMS):
        return None

    score = score_style_match(style_pack, haystack, hay_tokens)
    score += score_query_overlap(query, hay_tokens)
    if "costume institute" in haystack:
        score += 8
    if "drawings and prints" in haystack or "the libraries" in haystack:
        score += 4
    if score < 8:
        return None

    title = str(item.get("title") or "").strip()
    object_type = str(item.get("objectName") or "").strip()
    classification = str(item.get("classification") or "").strip()
    source_url = str(item.get("objectURL") or f"https://www.metmuseum.org/art/collection/search/{item.get('objectID')}")
    creator = str(item.get("artistDisplayName") or item.get("artistAlphaSort") or "").strip()
    date = str(item.get("objectDate") or "").strip()

    prompt_hint = "; ".join(
        [
            style_pack.get("search_focus", "").strip(),
            f"Prefer {', '.join(style_pack.get('preferred_object_types') or [])}.".strip(),
            "Keep only hand-drawn or plate-like fashion/costume references on paper.",
        ]
    )

    notes = " | ".join(
        part
        for part in [
            f"source=The Met Open Access",
            f"title={title}",
            f"object_type={object_type or classification}",
            f"creator={creator}" if creator else "",
            f"date={date}" if date else "",
            f"query={query}",
            f"url={source_url}",
            "rights=public_domain",
        ]
        if part
    )

    return Candidate(
        style_id=str(style_pack.get("style_id") or ""),
        training_style=str(style_pack.get("training_style") or ""),
        source_key="met_open_access",
        query=query,
        external_id=str(item.get("objectID") or ""),
        title=title,
        creator=creator,
        date=date,
        object_type=object_type,
        classification=classification,
        source_url=source_url,
        image_url=image_url,
        rights_status="public_domain",
        rights_statement="The Met Open Access public-domain image",
        score=score,
        prompt_hint=prompt_hint,
        search_focus=str(style_pack.get("search_focus") or "").strip(),
        notes=notes,
        raw={
            "objectID": item.get("objectID"),
            "title": title,
            "objectName": object_type,
            "classification": classification,
            "department": item.get("department"),
            "culture": item.get("culture"),
            "medium": item.get("medium"),
            "artistDisplayName": creator,
            "objectDate": date,
            "objectURL": source_url,
            "isPublicDomain": item.get("isPublicDomain"),
            "primaryImage": image_url,
        },
    )


def normalize_loc_url(url: str) -> str:
    text = str(url or "").strip()
    if text.startswith("//"):
        return f"https:{text}"
    return text.rstrip("/")


def loc_identifier(item: dict, source_url: str) -> str:
    control_number = str(item.get("control_number") or "").strip()
    if control_number:
        return control_number
    cleaned = source_url.rstrip("/").split("/")[-1]
    return cleaned or slugify(str(item.get("title") or "candidate"))


def choose_best_loc_image(image_urls: list[str]) -> str:
    cleaned = [str(url).split("#")[0] for url in image_urls if isinstance(url, str) and url]
    if not cleaned:
        return ""
    scored = []
    for url in cleaned:
        score = 0
        lower = url.lower()
        if lower.endswith(".svg") or "group-of-images.svg" in lower:
            continue
        if "pct:100" in lower or lower.endswith("v.jpg") or lower.endswith("r.jpg"):
            score += 8
        if lower.endswith(".jpg") or lower.endswith(".jpeg"):
            score += 4
        if "150px" in lower:
            score -= 5
        scored.append((score, url))
    if not scored:
        return ""
    scored.sort(key=lambda item: item[0], reverse=True)
    return scored[0][1]


def build_loc_candidate(style_pack: dict, query: str, item: dict) -> Candidate | None:
    access_restricted = bool(item.get("access_restricted"))
    rights_advisory = str(item.get("rights_advisory") or "").strip()
    if access_restricted:
        return None
    if rights_advisory and "no known restrictions" not in rights_advisory.lower():
        return None

    image_url = choose_best_loc_image(item.get("image_url") or [])
    if not image_url:
        return None

    original_format = ", ".join(
        key if isinstance(entry, dict) else str(entry)
        for entry in (item.get("format") or item.get("original_format") or [])
        for key in (entry.keys() if isinstance(entry, dict) else [entry])
    )
    subject = flatten_text_list(item.get("subject"))
    partof = flatten_text_list(item.get("partof"))
    description = flatten_text_list(item.get("description"))
    genre = flatten_text_list(item.get("genre") or item.get("format_headings"))
    title = str(item.get("title") or "").strip()
    date = str(item.get("date") or item.get("created_published_date") or "").strip()
    creator = ""
    contributor_names = item.get("contributor_names") or []
    if contributor_names:
        creator = str(contributor_names[0]).strip()

    text_fields = [
        title,
        original_format,
        subject,
        partof,
        description,
        genre,
        rights_advisory,
        date,
    ]
    haystack = " ".join(part for part in text_fields if part).lower()
    hay_tokens = set(tokenize(haystack))

    if hay_tokens.isdisjoint(GLOBAL_REQUIRED_TERMS):
        return None
    if hay_tokens.isdisjoint(VISUAL_REQUIRED_TERMS):
        return None
    if any(term in haystack for term in GLOBAL_EXCLUDED_TERMS):
        return None

    score = score_style_match(style_pack, haystack, hay_tokens)
    score += score_query_overlap(query, hay_tokens)
    if "fashion plates" in haystack or "fashion plate" in haystack:
        score += 8
    if "costume design" in haystack or "fashion design drawings" in haystack:
        score += 8
    if "graphite drawings" in haystack or "ink on paper" in haystack or "watercolor" in haystack:
        score += 4
    if score < 10:
        return None

    source_url = normalize_loc_url(str(item.get("id") or item.get("url") or ""))
    prompt_hint = "; ".join(
        [
            style_pack.get("search_focus", "").strip(),
            f"Prefer {', '.join(style_pack.get('preferred_object_types') or [])}.".strip(),
            "Keep only traceable fashion or costume design references with clean rights and visible hand-drawn or plate qualities.",
        ]
    )
    notes = " | ".join(
        part
        for part in [
            "source=Library of Congress",
            f"title={title}",
            f"object_type={genre or original_format}",
            f"creator={creator}" if creator else "",
            f"date={date}" if date else "",
            f"query={query}",
            f"url={source_url}",
            f"rights={rights_advisory or 'unrestricted_search_record'}",
        ]
        if part
    )

    return Candidate(
        style_id=str(style_pack.get("style_id") or ""),
        training_style=str(style_pack.get("training_style") or ""),
        source_key="library_of_congress",
        query=query,
        external_id=loc_identifier(item, source_url),
        title=title,
        creator=creator,
        date=date,
        object_type=genre or original_format,
        classification="Library of Congress",
        source_url=source_url,
        image_url=image_url,
        rights_status="public_domain" if rights_advisory else "review_required",
        rights_statement=rights_advisory or "No rights advisory surfaced in item JSON; manual review required.",
        score=score,
        prompt_hint=prompt_hint,
        search_focus=str(style_pack.get("search_focus") or "").strip(),
        notes=notes,
        raw={
            "title": title,
            "date": date,
            "original_format": original_format,
            "subject": item.get("subject"),
            "partof": item.get("partof"),
            "description": item.get("description"),
            "genre": item.get("genre"),
            "format_headings": item.get("format_headings"),
            "rights_advisory": rights_advisory,
            "access_restricted": access_restricted,
            "url": source_url,
            "image_url": image_url,
        },
    )


def extension_from_url(url: str) -> str:
    path = urlparse(url).path.lower()
    suffix = Path(path).suffix.lower()
    return suffix if suffix in {".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff"} else ".jpg"


def dedupe_candidates(candidates: Iterable[Candidate]) -> list[Candidate]:
    deduped: list[Candidate] = []
    seen: set[tuple[str, str]] = set()
    for candidate in sorted(candidates, key=lambda item: (-item.score, item.title, item.external_id)):
        key = (candidate.source_key, candidate.external_id)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(candidate)
    return deduped


def download_candidate(session: requests.Session, candidate: Candidate, output_dir: Path, index: int) -> tuple[Path, int]:
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = slugify(candidate.title or candidate.external_id)[:80]
    ext = extension_from_url(candidate.image_url)
    safe_id = slugify(candidate.external_id)[:32] or "candidate"
    path = output_dir / f"{index:02d}_{candidate.source_key}_{safe_id}_{stem}{ext}"
    response = session.get(candidate.image_url, timeout=60)
    response.raise_for_status()
    path.write_bytes(response.content)
    return path, len(response.content)


def build_curation_rows(downloaded: list[dict]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for item in downloaded:
        candidate = item["candidate"]
        image_path = item["file_path"]
        extra_tags = [
            candidate.style_id,
            candidate.source_key,
            candidate.object_type or candidate.classification,
            candidate.query,
        ]
        rows.append(
            {
                "file_path": str(image_path),
                "file_name": image_path.name,
                "style": candidate.training_style,
                "source_bucket": "discovery",
                "visual_type": infer_visual_type(candidate),
                "designer_house": "",
                "collection_or_year": candidate.date,
                "screening_decision": "",
                "screening_reason": "",
                "review_action": "review",
                "approved": "",
                "fit_for_lora": "",
                "caption_override": candidate.prompt_hint,
                "extra_tags": " | ".join(part for part in extra_tags if part),
                "rights_status": candidate.rights_status,
                "traceable_original_found": "yes",
                "hand_drawn_score": "",
                "paper_texture_score": "",
                "designer_specificity_score": "",
                "garment_readability_score": "",
                "composition_clarity_score": "",
                "archive_value_score": "",
                "ai_generated_risk": "low",
                "duplication_risk": "",
                "notes": candidate.notes,
            }
        )
    return rows


def infer_visual_type(candidate: Candidate) -> str:
    text = f"{candidate.object_type} {candidate.classification} {candidate.title}".lower()
    if any(term in text for term in ["sketch", "drawing", "illustration", "design"]):
        return "sketch"
    if "plate" in text or "print" in text:
        return "archive"
    return "archive"


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CANDIDATE_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def build_generic_fallback_style_pack(style_pack: dict) -> dict:
    fallback_pack = dict(style_pack)
    fallback_pack["preferred_object_types"] = GENERIC_QUERY_BACKSTOPS
    fallback_pack["query_terms"] = []
    return fallback_pack


def main() -> None:
    args = parse_args()
    manifest = load_manifest(args.manifest_json)
    requested_styles = {item.strip() for item in (args.style or []) if item and item.strip()}
    style_packs = manifest.get("style_packs") or []
    if requested_styles:
        style_packs = [pack for pack in style_packs if pack.get("training_style") in requested_styles]

    output_root = args.output_root.expanduser().resolve()
    session = make_session()
    met_client = MetOpenAccessClient(session)
    loc_client = LibraryOfCongressClient(session)
    enabled_sources = tuple(dict.fromkeys(args.source or ["met"]))
    summary: list[dict] = []

    for style_pack in style_packs:
        training_style = str(style_pack.get("training_style") or "").strip()
        if not training_style:
            continue
        style_dir = output_root / training_style
        images_dir = style_dir / "images"
        candidates_path = style_dir / "candidates.json"
        curation_path = style_dir / "curation.csv"

        precise_queries = build_precise_queries(style_pack)
        collected: list[Candidate] = []
        for query in precise_queries:
            if "met" in enabled_sources:
                try:
                    collected.extend(
                        met_client.search(
                            style_pack=style_pack,
                            query=query,
                            limit=args.max_per_query,
                            search_window=args.search_window,
                            delay_ms=args.delay_ms,
                        )
                    )
                except Exception as error:  # noqa: BLE001
                    print(f"[{training_style}] met query failed: {query} :: {error}")
            if "loc" in enabled_sources:
                try:
                    collected.extend(
                        loc_client.search(
                            style_pack=style_pack,
                            query=query,
                            limit=args.max_per_query,
                            search_window=args.search_window,
                            delay_ms=args.delay_ms,
                        )
                    )
                except Exception as error:  # noqa: BLE001
                    print(f"[{training_style}] loc query failed: {query} :: {error}")
            if len(dedupe_candidates(collected)) >= args.max_per_style:
                break
            time.sleep(max(args.delay_ms, 0) / 1000)

        if "met" in enabled_sources and len(dedupe_candidates(collected)) < args.max_per_style:
            fallback_style_pack = build_generic_fallback_style_pack(style_pack)
            for query in GENERIC_QUERY_BACKSTOPS:
                try:
                    collected.extend(
                        met_client.search(
                            style_pack=fallback_style_pack,
                            query=query,
                            limit=max(args.max_per_query, 6),
                            search_window=args.search_window,
                            delay_ms=args.delay_ms,
                        )
                    )
                except Exception as error:  # noqa: BLE001
                    print(f"[{training_style}] met fallback failed: {query} :: {error}")
                if len(dedupe_candidates(collected)) >= args.max_per_style:
                    break
                time.sleep(max(args.delay_ms, 0) / 1000)

        deduped = dedupe_candidates(collected)[: args.max_per_style]
        downloaded: list[dict] = []
        for index, candidate in enumerate(deduped, start=1):
            try:
                image_path, byte_size = download_candidate(session, candidate, images_dir, index)
            except Exception as error:  # noqa: BLE001
                print(f"[{training_style}] download failed: {candidate.image_url} :: {error}")
                continue
            downloaded.append(
                {
                    "candidate": candidate,
                    "file_path": image_path,
                    "byte_size": byte_size,
                }
            )
            time.sleep(max(args.delay_ms, 0) / 1000)

        manifest_payload = {
            "style_id": style_pack.get("style_id"),
            "training_style": training_style,
            "display_name": style_pack.get("display_name"),
            "search_focus": style_pack.get("search_focus"),
            "preferred_object_types": style_pack.get("preferred_object_types"),
            "queries": precise_queries,
            "sources": list(enabled_sources),
            "downloaded_count": len(downloaded),
            "downloaded": [
                {
                    "file_path": str(item["file_path"]),
                    "file_name": item["file_path"].name,
                    "byte_size": item["byte_size"],
                    **candidate_to_dict(item["candidate"]),
                }
                for item in downloaded
            ],
        }
        write_json(candidates_path, manifest_payload)
        write_csv(curation_path, build_curation_rows(downloaded))

        summary.append(
            {
                "training_style": training_style,
                "queries": len(precise_queries),
                "sources": list(enabled_sources),
                "downloaded_count": len(downloaded),
                "candidates_path": str(candidates_path),
                "curation_path": str(curation_path),
            }
        )
        print(f"[{training_style}] downloaded {len(downloaded)} candidate(s)")

    write_json(output_root / "summary.json", summary)
    print(f"Wrote {output_root / 'summary.json'}")


def candidate_to_dict(candidate: Candidate) -> dict:
    return {
        "style_id": candidate.style_id,
        "training_style": candidate.training_style,
        "source_key": candidate.source_key,
        "query": candidate.query,
        "external_id": candidate.external_id,
        "title": candidate.title,
        "creator": candidate.creator,
        "date": candidate.date,
        "object_type": candidate.object_type,
        "classification": candidate.classification,
        "source_url": candidate.source_url,
        "image_url": candidate.image_url,
        "rights_status": candidate.rights_status,
        "rights_statement": candidate.rights_statement,
        "score": candidate.score,
        "prompt_hint": candidate.prompt_hint,
        "search_focus": candidate.search_focus,
        "notes": candidate.notes,
        "raw": candidate.raw,
    }


if __name__ == "__main__":
    main()
