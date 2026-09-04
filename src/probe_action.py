"""Does the probe read the directive, or the model acting on it?

    python -m src.probe_action

The §4.5 probe separates arm A from arm B. Those arms differ in two ways at
once: arm A carries a scoring directive, and arm A behaves differently. A probe
that scores arm D as arm A could be detecting either.

The test needs no new data. Every arm-A trajectory carries the directive, but
only some took the concerning action. If the probe detects a motive the model
is acting on, those two groups separate. If it detects that a directive is
present in the context, they do not.

Arm B is the control on the control: it has no directive to detect, so if the
concerning action by itself moved the probe's output, it would move there too.

Reads data/activations.npz. No GPU, no model calls.
"""

from __future__ import annotations

import json
import re

import numpy as np

from .backend import load_config, read_jsonl
from .probe import ACT_PATH, _fit_eval

BARE = re.compile(r"\b(scor(e|es|ed|ing)|metric|measured|incentiv\w*|"
                  r"rewarded|graded|my performance|performance is)\b", re.I)
LAYER = 12


def mannwhitney(x, y):
    """Two-sided Mann-Whitney U, normal approximation with tie correction.

    Implemented here rather than imported so the number in the write-up does
    not depend on a library version, and so this file can be read as the
    definition of what was computed.
    """
    from math import erf, sqrt
    n1, n2 = len(x), len(y)
    if n1 == 0 or n2 == 0:
        return float("nan")
    allv = np.concatenate([x, y])
    order = allv.argsort()
    ranks = np.empty(len(allv), float)
    ranks[order] = np.arange(1, len(allv) + 1)
    # average ranks within ties
    i = 0
    sv = allv[order]
    while i < len(sv):
        j = i
        while j + 1 < len(sv) and sv[j + 1] == sv[i]:
            j += 1
        if j > i:
            ranks[order[i:j + 1]] = ranks[order[i:j + 1]].mean()
        i = j + 1
    r1 = ranks[:n1].sum()
    u1 = r1 - n1 * (n1 + 1) / 2
    u = min(u1, n1 * n2 - u1)
    mu = n1 * n2 / 2
    _, counts = np.unique(allv, return_counts=True)
    tie = sum(c ** 3 - c for c in counts)
    nn = n1 + n2
    sd = sqrt(n1 * n2 / 12 * ((nn + 1) - tie / (nn * (nn - 1))))
    if sd == 0:
        return 1.0
    z = (abs(u - mu) - 0.5) / sd
    return max(0.0, min(1.0, 2 * (1 - 0.5 * (1 + erf(z / sqrt(2))))))


def main() -> int:
    cfg = load_config()
    traj = {r["traj_id"]: r for r in read_jsonl(cfg["paths"]["trajectories"])}
    d = np.load(ACT_PATH, allow_pickle=True)
    X, layers = d["X"], list(d["layers"])
    meta = json.loads(str(d["meta"]))
    arm = np.array([m["arm"] for m in meta])
    sid = np.array([m["scenario_id"] for m in meta])
    tid = np.array([m["traj_id"] for m in meta])
    conc = np.array([bool(traj[t].get("concerning")) for t in tid])
    quiet = np.array([not BARE.search(traj[t].get("reasoning") or "") for t in tid])
    s1, s2 = sorted(set(sid))[::-1] if "log_delete" in sid[0:1] else sorted(set(sid))
    s1, s2 = "log_delete", "test_edit"

    li = layers.index(LAYER)
    F = X[:, li, :]
    tr = (sid == s1) & np.isin(arm, ["A", "B"])
    te = (sid == s2) & np.isin(arm, ["A", "B"])
    clf, cross = _fit_eval(F[tr], (arm[tr] == "A").astype(int),
                           F[te], (arm[te] == "A").astype(int))
    P = clf.predict_proba(F)[:, 1]

    print(f"layer {LAYER}, trained arm A vs arm B on '{s1}', "
          f"cross-scenario transfer {cross:.1%}")
    print(f"held out: '{s2}'. P(A) is the probe's probability of arm A.\n")
    print(f"  {'group':<40} {'n':>3} {'mean P(A)':>10} {'called A':>9}")

    groups = {}
    held = sid == s2

    def show(label, mask):
        if mask.sum() == 0:
            return None
        print(f"  {label:<40} {int(mask.sum()):>3} {P[mask].mean():>10.3f} "
              f"{(P[mask] > 0.5).mean():>8.0%}")
        return P[mask]

    for a in ("A", "B"):
        for c, lab in ((True, "took the concerning action"), (False, "did not")):
            groups[(a, c)] = show(f"arm {a}, {lab}", held & (arm == a) & (conc == c))
    for c, lab in ((True, "took the concerning action"), (False, "did not")):
        groups[("Dq", c)] = show(f"arm D quiet, {lab}",
                                 held & (arm == "D") & quiet & (conc == c))

    print("\n" + "=" * 72)
    print("Every arm-A trajectory carries the directive. Only some acted on it.")
    print("=" * 72)
    for key, lab in (("A", "arm A"), ("Dq", "arm D quiet"), ("B", "arm B")):
        x, y = groups.get((key, True)), groups.get((key, False))
        if x is None or y is None or len(x) < 3 or len(y) < 3:
            print(f"  {lab:<14} one cell too small to test "
                  f"(n={0 if x is None else len(x)} vs "
                  f"{0 if y is None else len(y)})")
            continue
        print(f"  {lab:<14} acted {x.mean():.3f} (n={len(x)})   "
              f"did not {y.mean():.3f} (n={len(y)})   p = {mannwhitney(x, y):.3f}")
    print("\n  Arm B has no directive to detect. A flat split there rules out the")
    print("  probe tracking the concerning action itself.")
    print("  A flat split on arm A means the probe reads the directive's presence")
    print("  and not whether the model acted on it. Report the narrow claim.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
