#!/usr/bin/env python3
"""Generate traction-slide training curve from real training_logs.txt."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOG = ROOT / "outputs" / "logs" / "training_logs.txt"
OUT_SVG = ROOT / "outputs" / "figures" / "traction_training_curve.svg"


def parse_training_log(path: Path) -> list[dict]:
    rows: list[dict] = []
    pat = re.compile(
        r"epoch (\d+)/\d+\s+train_loss=([\d.]+)\s+train_acc=([\d.]+)\s+"
        r"val_EER=([\d.]+)\s+val_ROC_AUC=([\d.]+)\s+val_GAR@FAR1%=([\d.]+)\s+val_Rank1=([\d.]+)"
    )
    for line in path.read_text(encoding="utf-8").splitlines():
        m = pat.search(line)
        if m:
            rows.append(
                {
                    "epoch": int(m.group(1)),
                    "train_loss": float(m.group(2)),
                    "train_acc": float(m.group(3)),
                    "val_eer": float(m.group(4)),
                    "val_roc_auc": float(m.group(5)),
                    "val_gar": float(m.group(6)),
                    "val_rank1": float(m.group(7)),
                }
            )
    if not rows:
        raise ValueError(f"No epoch rows found in {path}")
    return rows


def _polyline_points(xs: list[float], ys: list[float]) -> str:
    return " ".join(f"{x:.1f},{y:.1f}" for x, y in zip(xs, ys))


def render_svg(rows: list[dict], *, width: int = 820, height: int = 480) -> str:
    pad_l, pad_r, pad_t, pad_b = 72, 36, 58, 78
    plot_l, plot_r = pad_l, width - pad_r
    plot_t, plot_b = pad_t, height - pad_b
    plot_w, plot_h = plot_r - plot_l, plot_b - plot_t

    def x_epoch(ep: int) -> float:
        n = len(rows)
        if n == 1:
            return (plot_l + plot_r) / 2
        return plot_l + (ep - 1) * plot_w / (n - 1)

    def y_val(v: float) -> float:
        return plot_b - v * plot_h

    xs = [x_epoch(r["epoch"]) for r in rows]
    eer_pts = [(x, y_val(r["val_eer"])) for x, r in zip(xs, rows)]
    auc_pts = [(x, y_val(r["val_roc_auc"])) for x, r in zip(xs, rows)]

    grid_lines = []
    y_ticks = []
    for i in range(6):
        v = i * 0.2
        y = y_val(v)
        grid_lines.append(
            f'<line x1="{plot_l}" y1="{y:.1f}" x2="{plot_r}" y2="{y:.1f}" '
            f'stroke="#1E3A5F" stroke-width="1" opacity="0.55"/>'
        )
        y_ticks.append(
            f'<text x="{plot_l - 12}" y="{y + 4:.1f}" text-anchor="end" '
            f'fill="#60A5FA" font-family="Segoe UI, Inter, Arial, sans-serif" '
            f'font-size="12" opacity="0.85">{v:.1f}</text>'
        )

    x_labels = []
    for r in rows:
        x = x_epoch(r["epoch"])
        x_labels.append(
            f'<text x="{x:.1f}" y="{plot_b + 24}" text-anchor="end" '
            f'fill="#60A5FA" font-family="Segoe UI, Inter, Arial, sans-serif" '
            f'font-size="11" opacity="0.8" transform="rotate(-35 {x:.1f} {plot_b + 24})">'
            f'Epoch {r["epoch"]}</text>'
        )

    eer_dots = "\n".join(
        f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4.5" fill="#22D3EE" stroke="#0A0E1A" stroke-width="1.5"/>'
        for x, y in eer_pts
    )
    auc_dots = "\n".join(
        f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4.5" fill="#334155" stroke="#94A3B8" stroke-width="1.5"/>'
        for x, y in auc_pts
    )

    best = min(rows, key=lambda r: r["val_eer"])
    best_x, best_y = x_epoch(best["epoch"]), y_val(best["val_eer"])

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#0A0E1A"/>
      <stop offset="100%" stop-color="#0D1424"/>
    </linearGradient>
    <filter id="eerGlow" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="2.2" result="b"/>
      <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
    <filter id="cardShadow" x="-5%" y="-5%" width="110%" height="110%">
      <feDropShadow dx="0" dy="8" stdDeviation="12" flood-color="#000000" flood-opacity="0.45"/>
    </filter>
  </defs>

  <rect width="{width}" height="{height}" rx="18" fill="url(#bg)" filter="url(#cardShadow)"/>
  <rect x="1" y="1" width="{width - 2}" height="{height - 2}" rx="17" fill="none" stroke="#1E293B" stroke-width="1"/>

  <!-- Legend -->
  <g transform="translate({width / 2 - 120}, 22)">
    <circle cx="0" cy="0" r="5" fill="#334155" stroke="#94A3B8" stroke-width="1.2"/>
    <text x="12" y="4" fill="#CBD5E1" font-family="Segoe UI, Inter, Arial, sans-serif" font-size="13">ROC-AUC</text>
    <circle cx="108" cy="0" r="5" fill="#22D3EE"/>
    <text x="120" y="4" fill="#CBD5E1" font-family="Segoe UI, Inter, Arial, sans-serif" font-size="13">EER</text>
  </g>

  {''.join(grid_lines)}
  {''.join(y_ticks)}
  {''.join(x_labels)}

  <line x1="{plot_l}" y1="{plot_b}" x2="{plot_r}" y2="{plot_b}" stroke="#334155" stroke-width="1.2" opacity="0.8"/>
  <line x1="{plot_l}" y1="{plot_t}" x2="{plot_l}" y2="{plot_b}" stroke="#334155" stroke-width="1.2" opacity="0.8"/>

  <!-- ROC-AUC -->
  <polyline points="{_polyline_points([p[0] for p in auc_pts], [p[1] for p in auc_pts])}"
    fill="none" stroke="#64748B" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>
  {auc_dots}

  <!-- EER -->
  <g filter="url(#eerGlow)">
    <polyline points="{_polyline_points([p[0] for p in eer_pts], [p[1] for p in eer_pts])}"
      fill="none" stroke="#22D3EE" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/>
    {eer_dots}
  </g>

  <!-- Best epoch marker -->
  <line x1="{best_x:.1f}" y1="{plot_t}" x2="{best_x:.1f}" y2="{plot_b}" stroke="#22D3EE" stroke-width="1" stroke-dasharray="4 4" opacity="0.25"/>
  <text x="{best_x:.1f}" y="{best_y - 10:.1f}" text-anchor="middle" fill="#67E8F9" font-family="Segoe UI, Inter, Arial, sans-serif" font-size="10" opacity="0.9">best EER {best['val_eer']:.3f}</text>

  <text x="{width / 2}" y="{height - 18}" text-anchor="middle" fill="#475569"
    font-family="Segoe UI, Inter, Arial, sans-serif" font-size="10">
    Source: outputs/logs/training_logs.txt · validation metrics during training (40 classes, CPU)
  </text>
</svg>
"""


def main() -> None:
    rows = parse_training_log(LOG)
    OUT_SVG.parent.mkdir(parents=True, exist_ok=True)
    OUT_SVG.write_text(render_svg(rows), encoding="utf-8")
    print(f"Wrote {OUT_SVG} ({len(rows)} epochs)")


if __name__ == "__main__":
    main()
