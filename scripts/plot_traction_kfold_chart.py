#!/usr/bin/env python3
"""Generate 5-fold open-set CV chart from archive Long02 results (authentic)."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_SVG = ROOT / "outputs" / "figures" / "traction_kfold_openset.svg"
OUT_PNG = ROOT / "outputs" / "figures" / "traction_kfold_openset.png"

# Source: archive/testing_archive_2026-06-18.zip
#   testing/reports/summary/kfold_cv_comparison.md
#   testing/reports/models/long02_fold*.md
#   outputs/metrics/metrics.csv (fold 0)
FOLDS = [
    {"fold": 0, "eer": 0.2039, "roc_auc": 0.8772, "n_images": 547},
    {"fold": 1, "eer": 0.1416, "roc_auc": 0.9345, "n_images": 517},
    {"fold": 2, "eer": 0.1654, "roc_auc": 0.9102, "n_images": 526},
    {"fold": 3, "eer": 0.1933, "roc_auc": 0.8845, "n_images": 532},
    {"fold": 4, "eer": 0.1757, "roc_auc": 0.9041, "n_images": 545},
]
MEAN_EER = sum(f["eer"] for f in FOLDS) / len(FOLDS)
MEAN_AUC = sum(f["roc_auc"] for f in FOLDS) / len(FOLDS)
STD_EER = (sum((f["eer"] - MEAN_EER) ** 2 for f in FOLDS) / len(FOLDS)) ** 0.5


def render_svg(width: int = 820, height: int = 480) -> str:
    pad_l, pad_r, pad_t, pad_b = 72, 36, 58, 88
    plot_l, plot_r = pad_l, width - pad_r
    plot_t, plot_b = pad_t, height - pad_b
    plot_w, plot_h = plot_r - plot_l, plot_b - plot_t

    def x_fold(i: int) -> float:
        return plot_l + i * plot_w / (len(FOLDS) - 1)

    def y_val(v: float) -> float:
        return plot_b - v * plot_h

    xs = [x_fold(i) for i in range(len(FOLDS))]
    eer_pts = " ".join(f"{x:.1f},{y_val(f['eer']):.1f}" for x, f in zip(xs, FOLDS))
    auc_pts = " ".join(f"{x:.1f},{y_val(f['roc_auc']):.1f}" for x, f in zip(xs, FOLDS))
    mean_eer_y = y_val(MEAN_EER)

    grid = []
    ticks = []
    for i in range(6):
        v = i * 0.2
        y = y_val(v)
        grid.append(
            f'<line x1="{plot_l}" y1="{y:.1f}" x2="{plot_r}" y2="{y:.1f}" stroke="#1E3A5F" stroke-width="1" opacity="0.55"/>'
        )
        ticks.append(
            f'<text x="{plot_l - 12}" y="{y + 4:.1f}" text-anchor="end" fill="#60A5FA" font-size="12" opacity="0.85">{v:.1f}</text>'
        )

    xlabels = []
    for i, f in enumerate(FOLDS):
        x = xs[i]
        xlabels.append(
            f'<text x="{x:.1f}" y="{plot_b + 22}" text-anchor="middle" fill="#60A5FA" font-size="11">Fold {f["fold"]}</text>'
        )

    eer_dots = "\n".join(
        f'<circle cx="{x:.1f}" cy="{y_val(f["eer"]):.1f}" r="5" fill="#22D3EE" stroke="#0A0E1A" stroke-width="1.5"/>'
        for x, f in zip(xs, FOLDS)
    )
    auc_dots = "\n".join(
        f'<circle cx="{x:.1f}" cy="{y_val(f["roc_auc"]):.1f}" r="5" fill="#64748B" stroke="#94A3B8" stroke-width="1.5"/>'
        for x, f in zip(xs, FOLDS)
    )

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#0A0E1A"/><stop offset="100%" stop-color="#0D1424"/>
    </linearGradient>
    <filter id="glow"><feGaussianBlur stdDeviation="2"/><feMerge><feMergeNode/><feMergeNode in="SourceGraphic"/></feMerge></filter>
  </defs>
  <rect width="{width}" height="{height}" rx="18" fill="url(#bg)"/>
  <g transform="translate({width/2 - 120}, 22)">
    <circle cx="0" cy="0" r="5" fill="#64748B" stroke="#94A3B8"/><text x="12" y="4" fill="#CBD5E1" font-size="13" font-family="Segoe UI, Inter, Arial, sans-serif">ROC-AUC</text>
    <circle cx="108" cy="0" r="5" fill="#22D3EE"/><text x="120" y="4" fill="#CBD5E1" font-size="13" font-family="Segoe UI, Inter, Arial, sans-serif">EER</text>
  </g>
  {''.join(grid)}{''.join(ticks)}{''.join(xlabels)}
  <line x1="{plot_l}" y1="{plot_b}" x2="{plot_r}" y2="{plot_b}" stroke="#334155" stroke-width="1.2"/>
  <line x1="{plot_l}" y1="{mean_eer_y:.1f}" x2="{plot_r}" y2="{mean_eer_y:.1f}" stroke="#22D3EE" stroke-width="1" stroke-dasharray="5 4" opacity="0.45"/>
  <text x="{plot_r - 4}" y="{mean_eer_y - 6:.1f}" text-anchor="end" fill="#67E8F9" font-size="10" font-family="Segoe UI, Inter, Arial, sans-serif">mean EER {MEAN_EER:.3f}</text>
  <polyline points="{auc_pts}" fill="none" stroke="#64748B" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>
  {auc_dots}
  <g filter="url(#glow)">
    <polyline points="{eer_pts}" fill="none" stroke="#22D3EE" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/>
    {eer_dots}
  </g>
  <text x="{width/2}" y="{height - 52}" text-anchor="middle" fill="#94A3B8" font-size="11" font-family="Segoe UI, Inter, Arial, sans-serif">
    5-fold open-set CV · 49 held-out classes per fold · EfficientNet-B0 + CBAM + ArcFace
  </text>
  <text x="{width/2}" y="{height - 34}" text-anchor="middle" fill="#64748B" font-size="10" font-family="Segoe UI, Inter, Arial, sans-serif">
  Source: archive/testing_archive_2026-06-18.zip · Long02 kfold_cv_comparison.md · mean EER {MEAN_EER:.3f} ± {STD_EER:.3f}
  </text>
</svg>"""


def main() -> None:
    OUT_SVG.parent.mkdir(parents=True, exist_ok=True)
    OUT_SVG.write_text(render_svg(), encoding="utf-8")
    print(f"Wrote {OUT_SVG}")
    try:
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=(8.2, 4.8), facecolor="#0A0E1A")
        ax.set_facecolor("#0A0E1A")
        folds = [f["fold"] for f in FOLDS]
        ax.plot(folds, [f["roc_auc"] for f in FOLDS], color="#64748B", marker="o", linewidth=2.2, label="ROC-AUC")
        ax.plot(folds, [f["eer"] for f in FOLDS], color="#22D3EE", marker="o", linewidth=2.4, label="EER")
        ax.axhline(MEAN_EER, color="#22D3EE", linestyle="--", alpha=0.45, linewidth=1)
        ax.set_ylim(0, 1)
        ax.set_xticks(folds)
        ax.set_xticklabels([f"Fold {f}" for f in folds], color="#60A5FA")
        ax.tick_params(axis="y", colors="#60A5FA")
        ax.grid(True, color="#1E3A5F", alpha=0.55)
        for s in ax.spines.values():
            s.set_color("#334155")
        leg = ax.legend(loc="upper center", bbox_to_anchor=(0.5, 1.08), ncol=2, frameon=False)
        for t in leg.get_texts():
            t.set_color("#CBD5E1")
        ax.text(
            0.5, -0.2,
            f"5-fold open-set CV · Source: archive Long02 · mean EER {MEAN_EER:.3f} ± {STD_EER:.3f}",
            transform=ax.transAxes, ha="center", color="#64748B", fontsize=8.5,
        )
        fig.savefig(OUT_PNG, dpi=200, bbox_inches="tight", facecolor="#0A0E1A")
        print(f"Wrote {OUT_PNG}")
    except ImportError:
        pass


if __name__ == "__main__":
    main()
