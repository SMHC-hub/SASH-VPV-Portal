#!/usr/bin/env python3
"""Generate IEEE-style publication SVG figures from research_pipeline.json."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "paper_figures"
PIPELINE = ROOT / "research_pipeline.json"

# IEEE academic monochrome palette
C_BG = "#FFFFFF"
C_BOX = "#F8F8F8"
C_BORDER = "#1A1A1A"
C_TEXT = "#1A1A1A"
C_MUTED = "#4A4A4A"
C_ARROW = "#333333"
C_ACCENT = "#666666"

FONT = "Arial, Helvetica, sans-serif"
TITLE_SIZE = 13
LABEL_SIZE = 10
SMALL_SIZE = 8


def svg_header(w: int, h: int) -> str:
    return (
        f'<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
        f'viewBox="0 0 {w} {h}" font-family="{FONT}">\n'
        f'<defs>\n'
        f'  <marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto">\n'
        f'    <path d="M0,0 L7,3 L0,6 Z" fill="{C_ARROW}"/>\n'
        f'  </marker>\n'
        f'</defs>\n'
        f'<rect width="100%" height="100%" fill="{C_BG}"/>\n'
    )


def svg_footer() -> str:
    return "</svg>\n"


def esc(t: str) -> str:
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def title(svg: list, text: str, y: int = 28) -> None:
    svg.append(
        f'<text x="400" y="{y}" text-anchor="middle" font-size="{TITLE_SIZE}" '
        f'font-weight="bold" fill="{C_TEXT}">{esc(text)}</text>\n'
    )


def box(svg: list, x: int, y: int, w: int, h: int, label: str, sub: str = "") -> None:
    svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="4" fill="{C_BOX}" stroke="{C_BORDER}" stroke-width="1.2"/>\n')
    ly = y + h // 2 - (6 if sub else 0)
    svg.append(
        f'<text x="{x + w//2}" y="{ly}" text-anchor="middle" font-size="{LABEL_SIZE}" '
        f'font-weight="bold" fill="{C_TEXT}">{esc(label)}</text>\n'
    )
    if sub:
        for i, line in enumerate(sub.split("\n")):
            svg.append(
                f'<text x="{x + w//2}" y="{ly + 14 + i*11}" text-anchor="middle" '
                f'font-size="{SMALL_SIZE}" fill="{C_MUTED}">{esc(line)}</text>\n'
            )


def arrow_h(svg: list, x1: int, y: int, x2: int) -> None:
    svg.append(
        f'<line x1="{x1}" y1="{y}" x2="{x2}" y2="{y}" stroke="{C_ARROW}" '
        f'stroke-width="1.2" marker-end="url(#arrow)"/>\n'
    )


def arrow_v(svg: list, x: int, y1: int, y2: int) -> None:
    svg.append(
        f'<line x1="{x}" y1="{y1}" x2="{x}" y2="{y2}" stroke="{C_ARROW}" '
        f'stroke-width="1.2" marker-end="url(#arrow)"/>\n'
    )


def fig01_data_acquisition() -> str:
    svg = [svg_header(800, 420)]
    title(svg, "Fig. 1. Data Acquisition Pipeline")
    # Offline branch
    svg.append(f'<text x="200" y="52" text-anchor="middle" font-size="{SMALL_SIZE}" fill="{C_MUTED}">Offline Dataset (SASH-VPV)</text>\n')
    boxes = [
        (40, 70, 130, 50, "SASH-VPV Corpus", "2,667 imgs · 122 subjects"),
        (200, 70, 130, 50, "build_metadata", "metadata.csv"),
        (360, 70, 130, 50, "tag_visibility", "Frangi tiers"),
        (520, 70, 130, 50, "split_folds", "5-fold CV"),
    ]
    for b in boxes:
        box(svg, *b)
    for i in range(len(boxes) - 1):
        arrow_h(svg, boxes[i][0] + boxes[i][2], boxes[i][1] + 25, boxes[i + 1][0])
    # Live branch
    svg.append(f'<text x="400" y="155" text-anchor="middle" font-size="{SMALL_SIZE}" fill="{C_MUTED}">Live Capture (XRTECH MagicVein Plus)</text>\n')
    live = [
        (80, 175, 140, 55, "USB Scanner", "480×640 L8 · 850nm NIR"),
        (260, 175, 140, 55, "XR_Vein SDK", "ctypes wrapper"),
        (440, 175, 140, 55, "Capture Thread", "15 FPS cache"),
        (620, 175, 140, 55, "Quality Gate", "landmarks + vis≥15%"),
    ]
    for b in live:
        box(svg, *b)
    for i in range(len(live) - 1):
        arrow_h(svg, live[i][0] + live[i][2], live[i][1] + 27, live[i + 1][0])
    # Storage
    arrow_v(svg, 400, 125, 165)
    box(svg, 300, 270, 200, 50, "Storage", "data/raw/img · data/users/\nSQLite + templates")
    arrow_v(svg, 400, 230, 265)
    svg.append(
        f'<text x="400" y="360" text-anchor="middle" font-size="{SMALL_SIZE}" '
        f'fill="{C_MUTED}">Sources: build_metadata.py, xrtech_device.py, device/singleton.py</text>\n'
    )
    svg.append(svg_footer())
    return "".join(svg)


def fig02_preprocessing() -> str:
    svg = [svg_header(800, 520)]
    title(svg, "Fig. 2. Data Preprocessing Pipeline")
    steps = [
        ("Grayscale Input", "PNG or 480×640 raw"),
        ("Otsu + Morphology", "hand segmentation"),
        ("Landmark Detection", "valleys + palm center"),
        ("Affine ROI Warp", "110px scale → 224×224"),
        ("CLAHE", "clip=1.0, tile 16×16"),
        ("Bilateral Filter", "d=7"),
        ("Frangi Vesselness", "σ=1–3, scale 0.6"),
        ("Gabor Bank", "4 θ, scale 0.055"),
        ("3-Channel Stack", "224×224×3 [0,1]"),
    ]
    bw, bh, gap = 155, 48, 18
    x0, y = 55, 60
    for i, (lab, sub) in enumerate(steps):
        col, row = i % 3, i // 3
        x = x0 + col * (bw + gap)
        yy = y + row * (bh + gap + 8)
        box(svg, x, yy, bw, bh, lab, sub)
        if col < 2 and i < len(steps) - 1 and row == i // 3:
            nxt_col = (i + 1) % 3
            if nxt_col > col:
                arrow_h(svg, x + bw, yy + bh // 2, x + bw + gap)
        if col == 2 and i < len(steps) - 1:
            arrow_v(svg, x + bw // 2, yy + bh, yy + bh + gap + 8)
    svg.append(
        f'<text x="400" y="500" text-anchor="middle" font-size="{SMALL_SIZE}" '
        f'fill="{C_MUTED}">segment_and_landmarks.py → roi_extraction.py → vein_enhancement.py</text>\n'
    )
    svg.append(svg_footer())
    return "".join(svg)


def fig03_augmentation() -> str:
    svg = [svg_header(800, 400)]
    title(svg, "Fig. 3. Dataset Augmentation Pipeline (Training Only)")
    box(svg, 300, 55, 200, 45, "224×224 Grayscale ROI", "before enhance()")
    augs = [
        (60, 150, 150, 60, "Rotate/Translate/Scale", "±10° · 5% · 0.92–1.08"),
        (230, 150, 150, 60, "Brightness", "×0.85–1.15"),
        (400, 150, 150, 60, "Contrast", "0.85–1.15"),
        (570, 150, 150, 60, "Gaussian Noise", "σ 2–5"),
    ]
    for b in augs:
        box(svg, *b)
    arrow_v(svg, 400, 100, 145)
    for b in augs:
        arrow_v(svg, b[0] + b[2] // 2, 100, 145)
    box(svg, 250, 260, 300, 55, "Random 1–3 ops (no replacement)", "NO horizontal/vertical flip")
    arrow_v(svg, 400, 210, 255)
    for b in augs:
        arrow_v(svg, b[0] + b[2] // 2, 210, 255)
    box(svg, 275, 340, 250, 40, "→ vein_enhancement()", "")
    arrow_v(svg, 400, 315, 335)
    svg.append(
        f'<text x="400" y="390" text-anchor="middle" font-size="{SMALL_SIZE}" '
        f'fill="{C_MUTED}">src/palm_vein/augmentation.py — biometric-safe (no flips)</text>\n'
    )
    svg.append(svg_footer())
    return "".join(svg)


def fig04_model_architecture() -> str:
    svg = [svg_header(800, 620)]
    title(svg, "Fig. 4. PalmVeinEmbeddingNet Architecture")
    box(svg, 310, 50, 180, 40, "Input", "3 × 224 × 224")
    arrow_v(svg, 400, 90, 108)
    box(svg, 250, 110, 300, 50, "EfficientNet-B0 (timm)", "ImageNet pretrained · features_only")
    # stages
    stages = ["S0:16×112²", "S1:24×56²", "S2:40×28²", "S3:112×14²", "S4:320×7²"]
    for i, s in enumerate(stages):
        x = 80 + i * 130
        box(svg, x, 180, 110, 35, s, "")
    arrow_v(svg, 400, 160, 175)
    # CBAM
    box(svg, 200, 240, 180, 50, "CBAM Stage 3", "Ch.Attn + Sp.Attn\n112 ch")
    box(svg, 420, 240, 180, 50, "CBAM Stage 4", "Ch.Attn + Sp.Attn\n320 ch")
    arrow_v(svg, 290, 215, 235)
    arrow_v(svg, 510, 215, 235)
    # pool
    box(svg, 200, 320, 180, 40, "GAP Stage 3", "112-d")
    box(svg, 420, 320, 180, 40, "GAP Stage 4", "320-d")
    arrow_v(svg, 290, 290, 315)
    arrow_v(svg, 510, 290, 315)
    # concat
    box(svg, 275, 390, 250, 40, "Concatenate", "432-d")
    arrow_v(svg, 290, 360, 385)
    arrow_v(svg, 510, 360, 385)
    box(svg, 275, 455, 250, 40, "Dropout (p=0.4)", "")
    arrow_v(svg, 400, 430, 450)
    box(svg, 275, 515, 250, 40, "Linear → 512-d", "")
    arrow_v(svg, 400, 495, 510)
    box(svg, 275, 570, 250, 40, "L2 Normalize", "cosine-ready embedding")
    arrow_v(svg, 400, 555, 565)
    # ArcFace side
    box(svg, 580, 515, 170, 50, "ArcFace Loss", "s=64, m=0.5\ntrain only")
    svg.append(f'<line x1="525" y1="535" x2="580" y2="535" stroke="{C_ARROW}" stroke-width="1" stroke-dasharray="4,3"/>\n')
    svg.append(
        f'<text x="400" y="610" text-anchor="middle" font-size="{SMALL_SIZE}" '
        f'fill="{C_MUTED}">src/palm_vein/model.py + arcface_loss.py</text>\n'
    )
    svg.append(svg_footer())
    return "".join(svg)


def fig05_training() -> str:
    svg = [svg_header(800, 480)]
    title(svg, "Fig. 5. Training Pipeline")
    flow = [
        (40, 60, 120, 45, "metadata.csv", ""),
        (190, 60, 120, 45, "cv_folds.csv", ""),
        (340, 60, 120, 45, "PalmVeinDataset", "ROI+aug+enhance"),
        (490, 60, 120, 45, "DataLoader", "batch=16"),
        (640, 60, 120, 45, "PalmVeinEmbeddingNet", ""),
    ]
    for b in flow:
        box(svg, *b)
    for i in range(len(flow) - 1):
        arrow_h(svg, flow[i][0] + flow[i][2], flow[i][1] + 22, flow[i + 1][0])
    # training block
    box(svg, 150, 150, 500, 120, "Training Loop", "")
    details = [
        "Optimizer: Adam (lr=1e-3, wd=1e-4)",
        "Loss: ArcFace + CE (label_smoothing=0.1)",
        "Epochs: 60 (production) · Early stop: val EER, patience=5",
        "Anti-overfit: dropout 0.4, augmentation, weight decay",
        "Scheduler: NONE",
    ]
    for i, d in enumerate(details):
        svg.append(
            f'<text x="400" y="{175 + i*18}" text-anchor="middle" font-size="{SMALL_SIZE}" '
            f'fill="{C_TEXT}">{esc(d)}</text>\n'
        )
    arrow_v(svg, 550, 105, 145)
    box(svg, 250, 300, 300, 50, "Checkpoint (best val EER)", "checkpoint_production_full.pt")
    arrow_v(svg, 400, 270, 295)
    box(svg, 250, 380, 300, 45, "244 classes · 2,667 images", "held_out_fold=null (production)")
    arrow_v(svg, 400, 350, 375)
    svg.append(
        f'<text x="400" y="460" text-anchor="middle" font-size="{SMALL_SIZE}" '
        f'fill="{C_MUTED}">scripts/train_production.py → src/palm_vein/train.py</text>\n'
    )
    svg.append(svg_footer())
    return "".join(svg)


def fig06_evaluation() -> str:
    svg = [svg_header(800, 520)]
    title(svg, "Fig. 6. Evaluation Pipeline (Open-Set)")
    flow = [
        (50, 55, 130, 45, "Held-out Fold 0", "49 classes · 547 imgs"),
        (210, 55, 130, 45, "Preprocess", "ROI + enhance"),
        (370, 55, 130, 45, "Embed (512-d)", "L2 normalized"),
        (530, 55, 130, 45, "Pair Scores", "genuine vs impostor"),
        (690, 55, 80, 45, "Metrics", ""),
    ]
    for b in flow:
        box(svg, *b)
    for i in range(len(flow) - 1):
        arrow_h(svg, flow[i][0] + flow[i][2], flow[i][1] + 22, flow[i + 1][0])
    # metrics table
    metrics = [
        ("EER", "0.204", "Equal error rate"),
        ("ROC-AUC", "0.877", "Discrimination"),
        ("GAR@FAR1%", "0.481", "Security operating point"),
        ("Rank-1", "0.498", "Identification"),
        ("Rank-5", "0.703", "Identification"),
        ("Threshold", "0.40", "EER crossover (deploy)"),
    ]
    svg.append(f'<text x="80" y="140" font-size="{LABEL_SIZE}" font-weight="bold" fill="{C_TEXT}">Open-Set Results (docs/FINAL_SUMMARY.md):</text>\n')
    y0 = 160
    for i, (m, v, note) in enumerate(metrics):
        y = y0 + i * 28
        svg.append(f'<rect x="60" y="{y}" width="680" height="24" fill="{"#F0F0F0" if i%2==0 else C_BG}" stroke="{C_BORDER}" stroke-width="0.5"/>\n')
        svg.append(f'<text x="80" y="{y+16}" font-size="{SMALL_SIZE}" fill="{C_TEXT}">{esc(m)}</text>\n')
        svg.append(f'<text x="220" y="{y+16}" font-size="{SMALL_SIZE}" font-weight="bold" fill="{C_TEXT}">{esc(v)}</text>\n')
        svg.append(f'<text x="320" y="{y+16}" font-size="{SMALL_SIZE}" fill="{C_MUTED}">{esc(note)}</text>\n')
    # proxy note
    box(svg, 60, 350, 680, 55, "Seen-Class Proxy (training only — NOT open-set)", "EER=0.024 · AUC=0.991 · Rank-1=0.925 (40-class subset)")
    svg.append(
        f'<text x="400" y="440" text-anchor="middle" font-size="{SMALL_SIZE}" '
        f'fill="{C_MUTED}">Outputs: outputs/metrics/metrics.csv · similarity_distribution.png · tsne_umap.png</text>\n'
    )
    svg.append(
        f'<text x="400" y="458" text-anchor="middle" font-size="{SMALL_SIZE}" '
        f'fill="{C_MUTED}">src/palm_vein/evaluate.py — cosine similarity, ArcFace head NOT used at eval</text>\n'
    )
    svg.append(svg_footer())
    return "".join(svg)


def fig07_inference_deployment() -> str:
    svg = [svg_header(800, 500)]
    title(svg, "Fig. 7. Inference & Deployment Pipeline")
    steps = [
        (30, 60, 110, 50, "XRTECH Scanner", "USB 480×640"),
        (160, 60, 110, 50, "Capture Thread", "get_fresh_frame"),
        (290, 60, 110, 50, "Landmarks", "visibility ≥15%"),
        (420, 60, 110, 50, "ROI + Enhance", "224×224×3"),
        (550, 60, 110, 50, "EfficientNet", "+ CBAM embed"),
        (680, 60, 90, 50, "512-d", "L2 norm"),
    ]
    for b in steps:
        box(svg, *b)
    for i in range(len(steps) - 1):
        arrow_h(svg, steps[i][0] + steps[i][2], steps[i][1] + 25, steps[i + 1][0])
    # match branches
    box(svg, 80, 160, 200, 55, "1:1 Verify", "/api/recognize/verify\nclaimed identity check")
    box(svg, 310, 160, 200, 55, "1:N Identify", "/api/recognize/identify\nFAISS gallery search")
    box(svg, 540, 160, 200, 55, "Enroll Session", "/api/enroll/session/*\ntemplate storage")
    arrow_v(svg, 400, 110, 155)
    # secure match
    box(svg, 200, 260, 400, 55, "Secure Match", "threshold=0.40 · min_margin=0.06 · CaptureQualityError on fail")
    arrow_v(svg, 200, 215, 255)
    arrow_v(svg, 410, 215, 255)
    arrow_v(svg, 640, 215, 255)
    # backend
    box(svg, 100, 350, 600, 55, "FastAPI Backend + React Portal", "MJPEG stream · audit logs · SQLite · JWT auth")
    arrow_v(svg, 400, 315, 345)
    box(svg, 200, 430, 400, 45, "Dashboard / API Response", "matched · similarity · confidence · latency_ms")
    arrow_v(svg, 400, 405, 425)
    svg.append(
        f'<text x="400" y="495" text-anchor="middle" font-size="{SMALL_SIZE}" '
        f'fill="{C_MUTED}">deployment.py · recognize.py · enroll.py · matcher/singleton.py</text>\n'
    )
    svg.append(svg_footer())
    return "".join(svg)


def fig08_contributions() -> str:
    svg = [svg_header(800, 560)]
    title(svg, "Fig. 8. Research Contributions")
    contribs = [
        ("Custom Dataset", "SASH-VPV: 2,667 NIR images\n122 subjects · 244 hand-classes"),
        ("Landmark ROI", "PCA-axis invariant detection\nAffine 224×224 normalization"),
        ("Vein Enhancement", "CLAHE + Frangi + Gabor\n3-channel calibrated stack"),
        ("Architecture", "EfficientNet-B0 + dual CBAM\n512-d L2 embedding"),
        ("Metric Learning", "ArcFace (s=64, m=0.5)\nLabel smoothing + early stop"),
        ("Open-Set Eval", "5-fold visibility-stratified CV\nFold-0 held-out protocol"),
        ("Quality Gating", "Landmark + visibility ratio\nPre-inference rejection"),
        ("Live Deployment", "FastAPI + XRTECH scanner\nEnroll / verify / identify API"),
    ]
    cw, ch, gap = 175, 75, 20
    for i, (title_c, body) in enumerate(contribs):
        col, row = i % 4, i // 4
        x = 40 + col * (cw + gap)
        y = 55 + row * (ch + gap + 10)
        box(svg, x, y, cw, ch, title_c, body)
    svg.append(
        f'<text x="400" y="545" text-anchor="middle" font-size="{SMALL_SIZE}" '
        f'fill="{C_MUTED}">Extracted from implemented codebase — NUTECH SASH-VPV project</text>\n'
    )
    svg.append(svg_footer())
    return "".join(svg)


def fig09_complete() -> str:
    svg = [svg_header(800, 1100)]
    title(svg, "Fig. 9. Complete SASH-VPV Methodology")
    blocks = [
        ("Dataset", "SASH-VPV · 2,667 · 122 · 244 classes"),
        ("Acquisition", "NIR scanner + metadata pipeline"),
        ("Preprocessing", "Landmarks → ROI → CLAHE/Frangi/Gabor"),
        ("Augmentation", "Rotate · brightness · contrast · noise (no flip)"),
        ("Architecture", "EfficientNet-B0 + CBAM → 512-d"),
        ("Training", "ArcFace · Adam · 60 ep · early stop EER"),
        ("Evaluation", "Open-set fold-0 · EER 0.204 · AUC 0.877"),
        ("Deployment", "FAISS gallery · FastAPI · live scanner"),
        ("Contributions", "Dataset · pipeline · live biometric system"),
    ]
    bw, bh = 320, 42
    x = 240
    y = 50
    for i, (lab, sub) in enumerate(blocks):
        yy = y + i * (bh + 28)
        box(svg, x, yy, bw, bh, lab, sub)
        if i < len(blocks) - 1:
            arrow_v(svg, x + bw // 2, yy + bh, yy + bh + 22)
    # side annotations
    notes = [
        (580, 50, "data/raw/img"),
        (580, 120, "xrtech_device.py"),
        (580, 190, "segment · roi · enhance"),
        (580, 260, "augmentation.py"),
        (580, 330, "model.py"),
        (580, 400, "train_production.py"),
        (580, 470, "evaluate.py"),
        (580, 540, "deployment.py + backend/"),
        (580, 610, "Full-stack portal"),
    ]
    for nx, ny, note in notes:
        svg.append(
            f'<text x="{nx}" y="{ny + 26}" font-size="{SMALL_SIZE}" fill="{C_ACCENT}">→ {esc(note)}</text>\n'
        )
    svg.append(
        f'<text x="400" y="1080" text-anchor="middle" font-size="{SMALL_SIZE}" '
        f'fill="{C_MUTED}">End-to-end pipeline: dataset → model → open-set evaluation → production deployment</text>\n'
    )
    svg.append(svg_footer())
    return "".join(svg)


FIGURES = {
    "figure_01_data_acquisition.svg": fig01_data_acquisition,
    "figure_02_preprocessing.svg": fig02_preprocessing,
    "figure_03_augmentation.svg": fig03_augmentation,
    "figure_04_model_architecture.svg": fig04_model_architecture,
    "figure_05_training_pipeline.svg": fig05_training,
    "figure_06_evaluation.svg": fig06_evaluation,
    "figure_07_inference_deployment.svg": fig07_inference_deployment,
    "figure_08_contributions.svg": fig08_contributions,
    "figure_09_complete_methodology.svg": fig09_complete,
}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for name, fn in FIGURES.items():
        path = OUT / name
        path.write_text(fn(), encoding="utf-8")
        print(f"Wrote {path}")
    print(f"Done — {len(FIGURES)} figures in {OUT}")


if __name__ == "__main__":
    main()
