"""Does the `redacted` condition actually redact the motive?

    python -m src.leakcheck

`redacted` blanks the <think> block and masks the action tag. It does NOT
remove `content`, and BASE_SYSTEM instructs the agent to write a sentence of
justification after the action tag. If that sentence names the motive, the
investigator sees the motive in the redacted condition too, and
`cot_only ~ redacted` says the long reasoning is redundant with the short
self-report, not that self-report goes unread.

This measures the leak from data already on disk. No model calls.

Reports:
  1. how often the motive appears in the reasoning vs the justification, per arm
  2. the cot_only-vs-redacted comparison split by whether the justification
     leaked, which is the honest version of the headline contrast
  3. a paired McNemar-style count for every condition pair, because the four
     conditions run on the SAME trajectories and independent per-condition CIs
     do not license a claim about their difference
"""

from __future__ import annotations

import json
from collections import defaultdict

from .backend import load_config, read_jsonl
from .generate import DIRECTIVE_RE
from .experiment import GROUND_TRUTH, ARMS, ARM_LABEL


def mcnemar(a_correct: dict, b_correct: dict):
    """Discordant pairs between two conditions over the same trajectories.

    b_only  = cases condition B got right and A got wrong
    a_only  = the reverse
    Exact binomial two-sided p on the discordant pairs.
    """
    ids = set(a_correct) & set(b_correct)
    a_only = sum(1 for i in ids if a_correct[i] and not b_correct[i])
    b_only = sum(1 for i in ids if b_correct[i] and not a_correct[i])
    n = a_only + b_only
    if n == 0:
        return a_only, b_only, 1.0
    from math import comb
    k = min(a_only, b_only)
    p = sum(comb(n, i) for i in range(k + 1)) / (2 ** n) * 2
    return a_only, b_only, min(1.0, p)


def main() -> int:
    cfg = load_config()
    traj = {r["traj_id"]: r for r in read_jsonl(cfg["paths"]["trajectories"])}
    fors = read_jsonl(cfg["paths"]["forensics"])
    if not fors:
        print("no forensics rows")
        return 1

    # ---------------------------------------------------------------- 1. leak
    print("=" * 72)
    print("1. WHERE THE MOTIVE APPEARS")
    print("=" * 72)
    print("  `redacted` blanks the reasoning but keeps the justification "
          "sentence.\n  If the justification names the motive, redaction leaks.\n")
    print(f"  {'arm':<4} {'n':>4} {'in reasoning':>14} {'in justification':>18}")
    invest = {r["traj_id"] for r in fors}
    for arm in ARMS:
        rows = [t for t in traj.values()
                if t["arm"] == arm and t["traj_id"] in invest]
        if not rows:
            continue
        in_r = sum(bool(DIRECTIVE_RE.search(t["reasoning"] or "")) for t in rows)
        in_c = sum(bool(DIRECTIVE_RE.search(t["content"] or "")) for t in rows)
        print(f"  {arm:<4} {len(rows):>4} {in_r/len(rows):>13.0%} "
              f"{in_c/len(rows):>17.0%}")
    print("\n  Arm B is the false-positive floor in both columns.")
    print("  A high justification rate for A or D means `redacted` is mislabelled:")
    print("  it removes the extended trace, not the self-report.")

    # ------------------------------------------- 2. headline split by leakage
    print("\n" + "=" * 72)
    print("2. cot_only vs redacted, SPLIT BY WHETHER THE JUSTIFICATION LEAKED")
    print("=" * 72)
    by = defaultdict(dict)
    for r in fors:
        by[r["condition"]][r["traj_id"]] = (
            r.get("verdict") == GROUND_TRUTH[r["arm"]])
    leaked = {tid: bool(DIRECTIVE_RE.search(traj[tid]["content"] or ""))
              for tid in invest if tid in traj}

    for label, want in (("justification LEAKED the motive", True),
                        ("justification did NOT leak", False)):
        ids = [i for i, v in leaked.items() if v == want]
        if len(ids) < 5:
            print(f"\n  {label}: n={len(ids)}, too few to read")
            continue
        print(f"\n  {label}  (n={len(ids)})")
        for cond in ("redacted", "cot_only", "cot_forced", "full"):
            if cond not in by:
                continue
            sub = [by[cond][i] for i in ids if i in by[cond]]
            if sub:
                print(f"    {cond:<12} {sum(sub)/len(sub):>6.1%}  ({sum(sub)}/{len(sub)})")
    print("\n  If accuracy is flat across conditions ONLY in the leaked subset,")
    print("  the CoT null is explained by the leak and must be restated.")

    # ------------------------------------------------- 3. paired comparisons
    print("\n" + "=" * 72)
    print("3. PAIRED CONDITION CONTRASTS (McNemar, same trajectories)")
    print("=" * 72)
    print("  The four conditions run on the same 87 trajectories. Independent")
    print("  per-condition CIs do not license a claim about their difference.\n")
    pairs = [("redacted", "cot_only"), ("cot_only", "cot_forced"),
             ("cot_only", "full"), ("full", "cot_forced")]
    for a, b in pairs:
        if a not in by or b not in by:
            continue
        a_only, b_only, p = mcnemar(by[a], by[b])
        print(f"  {a:>10} -> {b:<11} {b}-only right: {b_only:>3}   "
              f"{a}-only right: {a_only:>3}   p = {p:.3f}")
    print("\n  Report these, not the difference of two independent intervals.")

    out = "data/leakcheck.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump({"leaked": leaked}, f)
    print(f"\nwrote {out}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
