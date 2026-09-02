"""Three figures. One claim each. Nothing decorative.

fig1_gap.png       the headline: acc{A,B} vs acc{D,B} per condition, with CIs
fig2_per_arm.png   where the loss comes from — per-arm accuracy per condition
fig3_behaviour.png the validity check — concerning-action rates by arm (GATE 1)
"""

from __future__ import annotations

import os
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from .experiment import ARMS, ARM_LABEL, SCENARIOS

# deliberately plain, colour-blind safe, legible in greyscale
INK = "#1a1c1a"
C_LOUD = "#2f5c8f"   # {A,B} — cause is legible
C_QUIET = "#c0632a"  # {D,B} — cause is suppressed
C_ARM = {"A": "#2f5c8f", "B": "#6b7a86", "D": "#c0632a"}
CHANCE = "#9aa0a6"

plt.rcParams.update({
    "font.size": 10,
    "axes.edgecolor": INK,
    "axes.labelcolor": INK,
    "text.color": INK,
    "xtick.color": INK,
    "ytick.color": INK,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "figure.dpi": 150,
})


def _err(point, ci):
    lo = max(0.0, point - ci[0])
    hi = max(0.0, ci[1] - point)
    return [[lo], [hi]]


def fig_gap(results, outdir):
    conds = [c for c in ("full", "cot_only", "redacted") if c in results["conditions"]]
    if not conds:
        return
    fig, ax = plt.subplots(figsize=(1.9 * len(conds) + 2.4, 4.0))
    w = 0.34
    for i, cond in enumerate(conds):
        p = results["conditions"][cond]["point"]
        ci = results["conditions"][cond]["ci"]
        ax.bar(i - w / 2, p["acc_AB"], w, color=C_LOUD,
               label="acc{A,B} — cause legible" if i == 0 else None)
        ax.errorbar(i - w / 2, p["acc_AB"], yerr=_err(p["acc_AB"], ci["acc_AB"]),
                    fmt="none", ecolor=INK, capsize=3, lw=1)
        ax.bar(i + w / 2, p["acc_DB"], w, color=C_QUIET,
               label="acc{D,B} — cause suppressed" if i == 0 else None)
        ax.errorbar(i + w / 2, p["acc_DB"], yerr=_err(p["acc_DB"], ci["acc_DB"]),
                    fmt="none", ecolor=INK, capsize=3, lw=1)
        top = max(ci["acc_AB"][1], ci["acc_DB"][1])
        ax.text(i, min(top + 0.06, 1.02),
                f"gap {p['gap']:+.0%}\n[{ci['gap'][0]:+.0%}, {ci['gap'][1]:+.0%}]",
                ha="center", va="bottom", fontsize=9)
    ax.axhline(0.5, color=CHANCE, ls="--", lw=1)
    ax.text(-0.45, 0.515, "chance", color=CHANCE, fontsize=8, ha="left")
    ax.set_xticks(range(len(conds)))
    ax.set_xticklabels([c.replace("_", " ") for c in conds])
    ax.set_ylim(0, 1.30)
    ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
    ax.set_yticklabels(["0%", "25%", "50%", "75%", "100%"])
    ax.set_ylabel("balanced forensic accuracy")

    # the title states the finding only if the finding is actually there
    full = results["conditions"].get("full")
    if full and full["ci"]["gap"][0] > 0:
        title = "Forensic accuracy drops when the same cause is not verbalised"
    elif full and full["ci"]["gap"][1] < 0:
        title = "Forensic accuracy is HIGHER when the cause is suppressed — investigate"
    else:
        title = "No detected effect of cause legibility on forensic accuracy"
    ax.set_title(title, loc="left", fontsize=11)
    ax.legend(frameon=False, loc="lower left", fontsize=9)
    fig.tight_layout()
    fig.savefig(os.path.join(outdir, "fig1_gap.png"))
    plt.close(fig)


def fig_per_arm(results, outdir):
    conds = [c for c in ("full", "cot_only", "redacted") if c in results["conditions"]]
    if not conds:
        return
    fig, ax = plt.subplots(figsize=(1.9 * len(conds) + 2.4, 4.0))
    w = 0.26
    for i, cond in enumerate(conds):
        p = results["conditions"][cond]["point"]
        ci = results["conditions"][cond]["ci"]
        for j, arm in enumerate(ARMS):
            x = i + (j - 1) * w
            v = p[f"acc_{arm}"]
            ax.bar(x, v, w, color=C_ARM[arm],
                   label=f"{arm} — {ARM_LABEL[arm]}" if i == 0 else None)
            ax.errorbar(x, v, yerr=_err(v, ci[f"acc_{arm}"]), fmt="none",
                        ecolor=INK, capsize=2.5, lw=1)
    ax.axhline(0.5, color=CHANCE, ls="--", lw=1)
    ax.set_xticks(range(len(conds)))
    ax.set_xticklabels([c.replace("_", " ") for c in conds])
    ax.set_ylim(0, 1.1)
    ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
    ax.set_yticklabels(["0%", "25%", "50%", "75%", "100%"])
    ax.set_ylabel("accuracy vs ground truth")
    ax.set_title("Per-arm accuracy: A and D share a cause and differ only in legibility",
                 loc="left", fontsize=11)
    ax.legend(frameon=False, fontsize=9, loc="lower left")
    fig.tight_layout()
    fig.savefig(os.path.join(outdir, "fig2_per_arm.png"))
    plt.close(fig)


def fig_behaviour(traj, outdir):
    rates = defaultdict(dict)
    for sid in SCENARIOS:
        for arm in ARMS:
            sub = [r for r in traj if r["scenario_id"] == sid and r["arm"] == arm and r["valid"]]
            if sub:
                rates[sid][arm] = sum(r["concerning"] for r in sub) / len(sub)
    sids = [s for s in SCENARIOS if s in rates]
    if not sids:
        return
    fig, ax = plt.subplots(figsize=(1.9 * len(sids) + 2.6, 3.6))
    w = 0.26
    for i, sid in enumerate(sids):
        for j, arm in enumerate(ARMS):
            if arm not in rates[sid]:
                continue
            ax.bar(i + (j - 1) * w, rates[sid][arm], w, color=C_ARM[arm],
                   label=f"{arm} — {ARM_LABEL[arm]}" if i == 0 else None)
    ax.set_xticks(range(len(sids)))
    ax.set_xticklabels(sids)
    ax.set_ylim(0, 1.05)
    ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
    ax.set_yticklabels(["0%", "25%", "50%", "75%", "100%"])
    ax.set_ylabel("concerning-action rate")
    ax.set_title("Validity check: the arms are behaviourally matched",
                 loc="left", fontsize=11)
    ax.legend(frameon=False, fontsize=9, loc="lower right")
    fig.tight_layout()
    fig.savefig(os.path.join(outdir, "fig3_behaviour.png"))
    plt.close(fig)


def make_all(results, traj, fors, outdir):
    os.makedirs(outdir, exist_ok=True)
    fig_gap(results, outdir)
    fig_per_arm(results, outdir)
    fig_behaviour(traj, outdir)
