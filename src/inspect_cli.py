"""Hour 11.5-13: read twenty transcripts by hand. Yourself.

    python -m src.inspect_cli                 # 20 stratified cases, one at a time
    python -m src.inspect_cli --wrong         # only cases the investigator got wrong
    python -m src.inspect_cli --arm D
    python -m src.inspect_cli --export notes.md

This exists because Neel's single most important stated piece of advice is to
sanity-check your agents, and because "an agent did a project and a human
forwarded it" is a stated rejection criterion. Your notes from this session are
what prove a human was in the loop. Type them as you go; they become the
qualitative section of the write-up.
"""

from __future__ import annotations

import argparse
import random
import textwrap

from .backend import load_config, read_jsonl
from .experiment import GROUND_TRUTH, ARM_LABEL, SCENARIOS


def wrap(s: str, width: int = 96, indent: str = "    ") -> str:
    out = []
    for para in (s or "").split("\n"):
        out.append(textwrap.fill(para, width=width, initial_indent=indent,
                                 subsequent_indent=indent) if para.strip() else "")
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config.yaml")
    ap.add_argument("--n", type=int, default=20)
    ap.add_argument("--arm", default=None)
    ap.add_argument("--condition", default="full")
    ap.add_argument("--wrong", action="store_true")
    ap.add_argument("--export", default=None)
    args = ap.parse_args()

    cfg = load_config(args.config)
    traj = {r["traj_id"]: r for r in read_jsonl(cfg["paths"]["trajectories"])}
    fors = [r for r in read_jsonl(cfg["paths"]["forensics"])
            if r["condition"] == args.condition]
    if not fors:
        print(f"no forensics rows for condition={args.condition}")
        return 1

    if args.arm:
        fors = [r for r in fors if r["arm"] == args.arm]
    if args.wrong:
        fors = [r for r in fors if r.get("verdict") != GROUND_TRUTH[r["arm"]]]
    if not fors:
        print("nothing matches that filter")
        return 1

    # stratify across arms so you don't read twenty of the same thing
    rng = random.Random(7)
    by_arm: dict[str, list] = {}
    for r in fors:
        by_arm.setdefault(r["arm"], []).append(r)
    for v in by_arm.values():
        rng.shuffle(v)
    picked, i = [], 0
    while len(picked) < args.n and any(by_arm.values()):
        for a in sorted(by_arm):
            if by_arm[a] and len(picked) < args.n:
                picked.append(by_arm[a].pop())
        i += 1
        if i > 500:
            break

    notes = []
    for n, f in enumerate(picked, 1):
        t = traj.get(f["traj_id"], {})
        scen = SCENARIOS[f["scenario_id"]]
        gt = GROUND_TRUTH[f["arm"]]
        correct = f.get("verdict") == gt
        print("\n" + "=" * 100)
        print(f"[{n}/{len(picked)}]  {f['traj_id']}   arm {f['arm']} "
              f"({ARM_LABEL[f['arm']]})   scenario={f['scenario_id']}")
        print(f"ground truth = {gt}   verdict = {f.get('verdict')}   "
              f"confidence = {f.get('confidence')}   "
              f"{'CORRECT' if correct else '*** WRONG ***'}")
        print("=" * 100)
        print("\n-- SUBJECT REASONING " + "-" * 79)
        print(wrap(t.get("reasoning", "(none)")))
        print("\n-- SUBJECT OUTPUT " + "-" * 82)
        print(wrap(t.get("content", "")))
        if f.get("hypothesis"):
            print("\n-- INVESTIGATOR HYPOTHESIS + PROBE CHOICE " + "-" * 58)
            print(wrap(f["hypothesis"]))
        if f.get("probe_results"):
            print("\n-- PROBE RESULTS SHOWN TO INVESTIGATOR " + "-" * 61)
            print(wrap(f["probe_results"]))
        print("\n-- INVESTIGATOR VERDICT " + "-" * 76)
        print(wrap(f.get("final", "")))
        print("\n" + "-" * 100)
        try:
            note = input("your note (blank to skip, 'q' to stop): ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if note.lower() == "q":
            break
        if note:
            notes.append(f"- **{f['traj_id']}** (arm {f['arm']}, gt {gt}, "
                         f"verdict {f.get('verdict')}): {note}")

    if notes:
        text = ("# Hand-read transcript notes\n\n"
                f"Condition: `{args.condition}`. {len(notes)} notes.\n\n"
                + "\n".join(notes) + "\n")
        if args.export:
            with open(args.export, "w", encoding="utf-8") as fh:
                fh.write(text)
            print(f"\nwrote {args.export}")
        else:
            print("\n" + text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
