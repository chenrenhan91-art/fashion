# FashionMarker Training Bootstrap

This folder is the practical bridge between the existing `fashionmarker-ai` inference tool and a later trainable sketch-style model.

## What This Does Today

The current deployed tool already has a working image-analysis and image-generation pipeline backed by the existing `QIANDAO_API_KEY` secret in the `fashionmarker-ai` Pages project.

This training flow now has three concrete stages:

1. `bootstrap-training-dataset.mjs`
   Converts reference fashion images into synthetic paired data by calling the deployed `fashionmarker-ai` API.
2. `prepare_lora_dataset.py`
   Converts the generated pair manifests into a diffusers-compatible `imagefolder` dataset with `metadata.jsonl`.
3. `train_lora_local.py`
   Launches the official Hugging Face diffusers LoRA trainer against the prepared dataset.

You can now add three more practical stages for the second-batch reference library:

4. `build_reference_curation_sheet.py`
   Scans saved sketch references and creates a review CSV with approval, provenance, and fit-for-LoRA columns.
5. `run_style_lora_pipeline.py`
   Merges generated pairs plus approved references into one dataset and launches local training in one command.
6. `run_foundation_lora_pipeline.py`
   Aggregates cleared training packs into a generic designer-hand-sketch foundation dataset before style-specific fine-tuning.

This is useful for:

- building a first training set
- testing style consistency
- creating synthetic paired data before a true LoRA / fine-tune run

Project-local batch helpers:

- `reference-library/second-batch-top8-tracker.csv`
- `training/reviews/second_batch_top8_runbook.md`
- `training/reviews/reference_screening_template.csv`
- `training/reviews/single_image_lora_screening_guide.md`

The remote-training side is handled as a provider-neutral bundle today: `prepare_lora_dataset.py --zip` creates a portable zip you can upload to a remote trainer.

## Scripts

`scripts/bootstrap-training-dataset.mjs`

`training/scripts/prepare_lora_dataset.py`

`training/scripts/build_reference_curation_sheet.py`

`training/scripts/apply_reference_screening_rules.py`

`training/scripts/export_open_access_search_manifest.py`

`training/scripts/fetch_open_access_candidates.py`

`training/scripts/build_open_access_shortlist.py`

`training/scripts/build_open_access_final_train_pack.py`

`training/scripts/setup_local_trainer.sh`

`training/scripts/train_lora_local.py`

`training/scripts/run_local_lora.sh`

`training/scripts/run_style_lora_pipeline.py`

`training/scripts/run_foundation_lora_pipeline.py`

`training/scripts/export_style_training_schema.py`

Example:

```bash
node scripts/bootstrap-training-dataset.mjs \
  --input-dir /path/to/source-images-or-one-image \
  --output-dir /path/to/output-dataset \
  --email your-login-email@example.com \
  --style atelier_luxe \
  --limit 20
```

Prepare a LoRA-ready dataset:

```bash
python3 training/scripts/prepare_lora_dataset.py \
  --source /path/to/generated-training-dir \
  --output-dir /path/to/lora-dataset \
  --style atelier_luxe \
  --zip
```

Build a curation sheet for saved Pinterest / archive references:

```bash
python3 training/scripts/build_reference_curation_sheet.py \
  --reference-dir /path/to/reference-library/approved/atelier_luxe \
  --output-csv /path/to/review/atelier_luxe_curation.csv \
  --style atelier_luxe
```

Prepare and train in one step:

```bash
python3 training/scripts/run_style_lora_pipeline.py \
  --style atelier_luxe \
  --source /Users/zhengruyue/Documents/Playground/fashionmarker-ai/training-data/smoke-atelier-luxe \
  --reference-dir /path/to/reference-library/approved/atelier_luxe \
  --curation-csv /path/to/review/atelier_luxe_curation.csv \
  --dataset-dir /Users/zhengruyue/Documents/Playground/fashionmarker-ai/lora-datasets/atelier-luxe-batch2 \
  --output-dir /Users/zhengruyue/Documents/Playground/fashionmarker-ai/training-runs/atelier-luxe-batch2 \
  --max-train-steps 200 \
  --rank 8 \
  --disable-checkpointing \
  --skip-validation
```

Prepare a stronger generic designer-hand foundation pack first:

```bash
python3 training/scripts/run_foundation_lora_pipeline.py \
  --prepare-only \
  --dataset-dir /Users/zhengruyue/Documents/Playground/fashionmarker-ai/output/datasets/designer_hand_foundation_smoke \
  --output-dir /Users/zhengruyue/Documents/Playground/fashionmarker-ai/training-runs/designer-hand-foundation-smoke
```

Then launch the real foundation run:

```bash
python3 training/scripts/run_foundation_lora_pipeline.py \
  --dataset-dir /Users/zhengruyue/Documents/Playground/fashionmarker-ai/output/datasets/designer_hand_foundation_v1 \
  --output-dir /Users/zhengruyue/Documents/Playground/fashionmarker-ai/training-runs/designer-hand-foundation-v1
```

Generate rights-cleared search prompts plus downloadable seed packs from official
open-access catalogs only:

```bash
python3 training/scripts/export_open_access_search_manifest.py

python3 training/scripts/fetch_open_access_candidates.py \
  --max-per-style 20 \
  --max-per-query 4 \
  --search-window 500 \
  --delay-ms 900 \
  --source met
```

This creates:

- `training/manifests/open_access_style_search_manifest.json`
- `training/manifests/open_access_style_search_manifest.csv`
- `output/open-access-candidates/<training_style>/images/`
- `output/open-access-candidates/<training_style>/candidates.json`
- `output/open-access-candidates/<training_style>/curation.csv`

Then build a first-pass shortlist that ranks the official candidates by how
useful they look for designer-sketch LoRA training:

```bash
python3 training/scripts/build_open_access_shortlist.py
```

This writes:

- `training/reviews/open_access_shortlist_round1_master.csv`
- `training/reviews/open_access_shortlist_round1_top_per_style.csv`
- `training/reviews/open_access_shortlist_round1_summary.json`

Then derive a first-pass final training pack with 8 ranked picks per style:

```bash
python3 training/scripts/build_open_access_final_train_pack.py
```

This writes:

- `training/reviews/open_access_final_train8_per_style.csv`
- `training/reviews/open_access_final_train8_summary.json`

By default, keep the fetcher on official museum APIs that behave reliably. Start with
`--source met`, then add `--source loc` only when you want a slower secondary pass and
are prepared for occasional rate limits.

Launch local LoRA training:

```bash
bash training/scripts/run_local_lora.sh \
  --dataset-dir /path/to/lora-dataset \
  --output-dir /path/to/lora-output \
  --max-train-steps 200 \
  --rank 8
```

## Available Styles

- `marker_clean`
- `paris_new_look`
- `elongated_drama`
- `atelier_luxe`
- `modern_croquis`
- `corset_cabaret`
- `punk_rococo`
- `artisanal_deconstruction`
- `pleated_motion`
- `architectural_volume`
- `surreal_gold`
- `hourglass_power`
- `bionic_couture`
- `maximalist_romance`
- `minimalist_chic`
- `space_age_clean`
- `metal_modular`
- `insect_power`
- `gothic_theatre`
- `baroque_narrative`

## Recommended Next Step

1. Use the bootstrap script to create `50+` pairs across 2-4 styles.
2. Review and delete weak outputs manually.
3. Split the remaining data by style into separate folders.
4. Train one generic designer-hand foundation LoRA.
5. Fine-tune one LoRA per style with `run_style_lora_pipeline.py --caption-profile hybrid`.

## Local Training Notes

- The local trainer uses the official Hugging Face diffusers `train_text_to_image_lora.py` example.
- On this Mac, training runs on Apple Silicon `mps`, which according to Accelerate only supports a single GPU process.
- The default base model path points at the local `dreamshaper_8.safetensors` checkpoint and will be converted once into diffusers format.
- For a first real style LoRA, aim for at least `30-100` reviewed sketch outputs per style.

## Important Note

The existing `QIANDAO_API_KEY` in `fashionmarker-ai` is currently wired for inference through the deployed Pages API. This bootstrap flow safely reuses that path without exposing the secret value locally.

`prepare_lora_dataset.py` now also supports `--skip-generated-pairs`, `--reference-repeat`, `--generated-repeat`, and `--caption-profile foundation|hybrid` so you can bias training toward real hand-drawn references instead of self-distilled outputs.

## Second-Batch Reference Workflow

For the Pinterest-led second batch, use this flow:

1. Save discovered images into local style folders such as:
   - `reference-library/discovery/atelier_luxe/`
   - `reference-library/approved/atelier_luxe/`
2. Run `build_reference_curation_sheet.py` on the approved folder.
3. Mark only the strongest rows as approved and add provenance notes plus `extra_tags`.
4. Feed the approved folder plus curation CSV into `run_style_lora_pipeline.py`.

Pinterest should stay a discovery layer. For commercial use, shortlist images with traceable provenance before using them in the final LoRA training mix.

If local disk is tight, add `--disable-checkpointing` during smoke tests or early experiments so `accelerate` does not try to write large intermediate training states.

## Style Prompt Archive

The exported prompt archive now lives here:

- `training/manifests/style_prompt_archive.json`
- `training/manifests/style_prompt_archive.csv`
- `training/manifests/style_manuscript_lexicon.json`
- `training/manifests/style_training_schema.json`
- `training/manifests/style_training_schema.csv`

Recommended usage:

- Use each style's `trigger_phrase` as the core LoRA trigger sentence.
- Maintain hand-drawn reinforcement tags in `style_manuscript_lexicon.json`; `export_style_training_schema.py` merges them into the derived schema automatically.
- Use `style_training_schema.csv` when you want the normalized training split: `trigger_phrase`, `manuscript_trigger_words`, `training_caption`, `validation_prompt`, and `negative_prompt`.
- Start captions with `token`, then describe medium, stroke language, silhouette cue, and page mood.
- Keep strong 2D material cues such as `correction-fluid`, `charcoal`, `xerox texture`, `metallic marker`, and `paper ground` so the model stays in illustrated editorial territory instead of drifting into generic photorealism.
- Keep negative constraints for typography, logos, signatures, watermarks, screenshots, and runway/editorial photos.
