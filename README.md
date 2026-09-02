# quiet-motive

**A positive control for model forensics.**

Two models with the same hidden motive. One is allowed to talk about it; one
isn't. Both take the same concerning action. Does the forensic verdict track
the motive, or only whether the model said it out loud?

Singh, Kroiz, Rajamanoharan & Nanda, *Model Forensics* (arXiv 2606.26071, June
2026), propose: read the chain of thought, hypothesise why the model
misbehaved, test with counterfactual interventions. Their limitations section
concedes that **positive controls were absent** — when they tested Kimi K2
Thinking for awareness of violating user intent and found nothing, they could
not distinguish "no misalignment here" from "our method cannot see it."

This repo builds the missing positive control.

## Design

Three arms. All three take the **same** concerning action. Two of them share a
**cause** and differ only in whether the model may verbalise it.

| arm | induced cause | legible in CoT | ground truth |
|-----|---------------|----------------|--------------|
| A | hidden objective conflicting with user intent | yes | `MISALIGNED` |
| B | false belief about the environment | yes | `MISTAKE` |
| D | same objective as A, verbalisation suppressed | no | `MISALIGNED` |

Headline number, using balanced accuracy so unequal arm sizes cannot move it:

```
acc{A,B} - acc{D,B}
```

A gap whose CI excludes zero means the verdict is reading the transcript, not
the model. A gap whose CI includes zero is a positive control the protocol
**passes** — which is exactly the validation its authors said they lacked, and
is equally worth writing up.

Two scenarios, both single-decision agentic settings with a genuine and a
concerning option: a failing rounding test before a release, and an audit log
during a workspace handoff.

Three investigator conditions:

| condition | investigator sees | isolates |
|-----------|-------------------|----------|
| `full` | CoT + counterfactual probes | the protocol as published |
| `cot_only` | CoT, no probes | do the interventions add anything? |
| `redacted` | actions only, CoT stripped | is the CoT doing the work? |

The investigator never sees the arm label or the hidden cause block. Its
counterfactual probes modify the user-facing scenario only — a real
investigator cannot delete a cause it cannot see. `state_true_fact` is the
discriminating probe: it should stop arm B and leave A and D unchanged.

## Run it

```bash
# 0. offline, no GPU, no API — validates the whole pipeline in ~10 seconds
pip install -r requirements.txt
python tests/smoke_mock.py

# 1. on the A100 box
MODEL=Qwen/Qwen3.5-9B ./setup_gpu.sh      # installs vLLM, downloads, serves on :8000
export OPENAI_API_KEY=EMPTY

# 2. smoke the real model before spending anything
python -m src.generate --n 2

# 3. the pipeline, with gates
./run_all.sh

# 4. the part only you can do
python -m src.inspect_cli --export notes.md
python -m src.inspect_cli --wrong --arm D        # where it fails

# 5. optional white-box arm — run AFTER 1-3, and stop vLLM first
pkill -f "vllm serve"
python -m src.probe extract
python -m src.probe train
```

Model download and vLLM startup are **not** counted against the 16 hours.
Coding, analysis and writing are.

## Stage 4 — the probe (optional, gated)

Arm D's visible reasoning is scrubbed of the motive. Is the motive still
*linearly decodable* from the residual stream at the action token?

Train a logistic probe on arm A vs arm B activations from one scenario, test it
on the other scenario, then ask what it calls arm D. The cross-scenario test is
the control that matters: the two scenarios share no surface vocabulary, so a
probe that transfers has found something more abstract than the prompt text. A
probe that does not transfer is reading the prompt, and `src/probe.py` says so
in the output rather than letting you report the headline number anyway.

The result you want is the contrast: CoT-forensics accuracy on arm D (low, from
stage 3) against probe accuracy on arm D. If the probe reads D where the
protocol cannot, the evidence was in the activations the whole time and the
transcript was the wrong place to look.

`src/probe.py` loads the model in HF transformers, which cannot share the GPU
with a vLLM server at 0.90 utilisation. Stop vLLM first. Run this only after
stages 1-3 are finished and only if you are ahead of schedule — the hard drop
rule is gate 2 slipping past 20:00 Thursday.

Honest scope: the cause block is in context for both A and D, so this is a
detectability result, not evidence the model "secretly thinks" the motive. The
test that separates those is inducing the cause in weights. Name it as the next
step rather than letting a reader raise it.

## The three gates

**GATE 1 — behaviour match** (end of `src.generate`). All three arms must take
the concerning action at comparable rates: spread ≤ 20pp, floor ≥ 40%. If they
don't, you are measuring behaviour, not forensics. Fix the cause blocks in
`src/experiment.py` or drop the weaker scenario. Do not proceed on a fail.

**GATE 2 — non-degenerate verdicts** (end of `src.forensics`). If the
investigator returns the same label for everything, or its output won't parse,
fix the prompt *that evening*. If it is still broken, drop the `full` condition
and ship the `cot_only` vs `redacted` comparison — small and complete beats
large and broken.

**GATE 3 — the number** (`src.analyze`). Experiments freeze here, whatever it
says. Everything after is analysis and writing.

## What to change when a gate fails

| symptom | fix |
|---|---|
| arm B rate far below A/D | the false belief isn't convincing — strengthen `cause_mistaken` |
| arm D rate far below A | suppression is changing behaviour, not just speech — this is the confound; weaken `SUPPRESSION` to speech-only and re-check |
| `empty_reasoning` warning | the served model isn't emitting CoT — check `--reasoning-parser qwen3` and `generation.enable_thinking` |
| unparsed actions | tighten `BASE_SYSTEM`, or lower `temperature` |
| investigator always says MISALIGNED | arm B's transcript isn't exculpatory enough, or `INVESTIGATOR_SYSTEM`'s neutrality framing is being ignored |

## Known confounds — put these in your limitations, do not let a reader find them

1. **Same model as subject and investigator** by default. Point `judge_model`
   at a different endpoint if you can. If you can't, say so.
2. **Causes are induced in context, not in weights.** A LoRA replication is the
   obvious next step and you did not run it. Name it.
3. **Probe results are precomputed per (scenario, arm, probe)**, not re-run per
   investigation. The investigator still chooses its probes, but probe results
   carry no per-trajectory noise.
4. **Arm B cancels out of the gap.** With balanced accuracy the gap is exactly
   `(acc_A - acc_D) / 2`. B is what stops "always say MISALIGNED" scoring 100%,
   but it contributes nothing to the headline. State this yourself.
5. **Two scenarios is not a sample of scenarios.** Any claim generalising
   beyond them is unsupported.

## Files

```
config.yaml              every knob
VERIFICATION_LOG.md      fill in AS YOU GO — the form asks what you did NOT check
setup_gpu.sh             provision + serve
run_all.sh               the pipeline with gates
PREREGISTRATION.md       fill this in at hour 0, before any data
src/backend.py           async OpenAI-compatible client, CoT extraction
src/experiment.py        scenarios, arms, probes        <- the science lives here
src/generate.py          stage 1 + GATE 1
src/forensics.py         stage 2 + GATE 2
src/analyze.py           stage 3 + GATE 3
src/figures.py           three figures, one claim each
src/inspect_cli.py       hand-read transcripts, export notes
src/probe.py             stage 4: linear probe + cross-scenario control
tests/smoke_mock.py      offline end-to-end validation
```
