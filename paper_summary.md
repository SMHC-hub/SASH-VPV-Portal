# SASH-VPV Research Paper Summary

**Auto-generated from codebase analysis.** All architecture, preprocessing, training, and deployment claims below are extracted from the implementation — not assumed.

---

## Project

| Field | Value |
|-------|-------|
| Name | SASH-VPV Palm Vein Recognition System |
| Institution | National University of Technology (NUTECH), Islamabad |
| Sensor | XRTECH MagicVein Plus (850 nm NIR, 480×640) |
| Model | EfficientNet-B0 + CBAM → 512-d L2 embedding |
| Deployment | FastAPI + React + FAISS cosine gallery |

---

## Dataset

- **2,667** grayscale palm-vein images  
- **122** subjects, **244** classes (subject × {Left, Right})  
- Path: `data/raw/img/<subject>/<hand>/`  
- Metadata: `build_metadata.py` → `metadata.csv`  
- Visibility tags: `tag_visibility.py` (Frangi vesselness tiers)  
- CV splits: `split_folds.py` — 5-fold stratified at class level (visibility-stratified)

---

## Preprocessing (exact order)

**Training:** read → ROI (landmarks) → augment → enhance → tensor  
**Deployment:** frame → landmarks + quality gate → ROI → enhance → embed

1. **Segmentation & landmarks** — Otsu, morphology, contour, valley peaks, PCA finger-side, distance-transform palm center  
2. **ROI extraction** — affine warp (110 px inter-landmark scale), 224×224 crop  
3. **Vein enhancement** — CLAHE + bilateral + Frangi (σ=1–3) + Gabor (4 orientations) → 3-channel stack

---

## Augmentation (training only)

- Rotate/translate/scale (±10°, 5%, 0.92–1.08)  
- Brightness, contrast, Gaussian noise  
- **Excluded:** horizontal/vertical flip (biometric safety)  
- Applied **before** enhancement (`augmentation.py`)

---

## Model Architecture

```
Input (3×224×224)
  → EfficientNet-B0 (timm, ImageNet, features_only)
  → CBAM on stage 3 (112 ch) and stage 4 (320 ch)
  → Global average pool → concat (432-d)
  → Dropout (0.4) → Linear (512-d) → L2 normalize
Training head: ArcFace (s=64, m=0.5) — not used at inference
```

---

## Training

| Parameter | Value |
|-----------|-------|
| Optimizer | Adam, lr=1e-3, weight_decay=1e-4 |
| Loss | ArcFace + CE, label_smoothing=0.1 |
| Epochs | 60 (production), batch=16 |
| Early stopping | val EER, patience=5 |
| Scheduler | None |
| Checkpoint | `checkpoint_production_full.pt` |
| Classes | 244 (production, no fold held out) |

---

## Evaluation (open-set, fold 0)

| Metric | Value | Source |
|--------|-------|--------|
| EER | 0.204 | docs/FINAL_SUMMARY.md |
| ROC-AUC | 0.877 | docs/FINAL_SUMMARY.md |
| GAR@FAR 1% | 0.481 | docs/FINAL_SUMMARY.md |
| Rank-1 | 0.498 | docs/FINAL_SUMMARY.md |
| Rank-5 | 0.703 | docs/FINAL_SUMMARY.md |
| Threshold | 0.40 | EER crossover (deployment) |

**Note:** Seen-class proxy EER (0.024) is for training-time early stopping only — not open-set.

---

## Deployment

1. XRTECH scanner → 480×640 raw frame  
2. Quality gate (landmarks, visibility ≥ 15%)  
3. Same ROI + enhancement + EfficientNet embed  
4. FAISS IndexFlatIP cosine match  
5. Secure match: threshold 0.40 + min margin 0.06  
6. FastAPI: `/api/enroll`, `/api/recognize/verify`, `/api/recognize/identify`

---

## Figures

All publication SVGs are in `paper_figures/`:

| File | Content |
|------|---------|
| `figure_01_data_acquisition.svg` | SASH-VPV + live XRTECH capture |
| `figure_02_preprocessing.svg` | Landmark → ROI → enhancement chain |
| `figure_03_augmentation.svg` | Training augmentation (no flips) |
| `figure_04_model_architecture.svg` | EfficientNet-B0 + CBAM + 512-d head |
| `figure_05_training_pipeline.svg` | DataLoader → ArcFace → checkpoint |
| `figure_06_evaluation.svg` | Open-set metrics (real values) |
| `figure_07_inference_deployment.svg` | Scanner → API → dashboard |
| `figure_08_contributions.svg` | Eight contribution cards |
| `figure_09_complete_methodology.svg` | End-to-end composite |

Structured pipeline data: `research_pipeline.json`

Regenerate figures: `python scripts/generate_paper_figures.py`

---

## Key Contributions (codebase-verified)

1. Custom SASH-VPV NIR palm-vein dataset  
2. PCA-axis invariant landmark detection + affine ROI  
3. Three-channel CLAHE/Frangi/Gabor enhancement with calibrated global scaling  
4. EfficientNet-B0 + dual CBAM multi-scale 512-d embedding  
5. ArcFace metric learning with anti-overfitting stack  
6. Visibility-stratified 5-fold open-set CV protocol  
7. Capture quality gating before inference  
8. FAISS cosine gallery with margin-based secure matching  
9. Full-stack live enrollment/verify/identify with XRTECH USB integration

---

*Document version: 1.0 — generated from repository analysis.*
