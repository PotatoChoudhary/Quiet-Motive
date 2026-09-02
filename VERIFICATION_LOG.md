# Verification log — fill this in AS YOU GO, not on Friday

The application form asks, verbatim:

> How did you use LLMs in this research task and write-up? Which LLMs? How
> exactly did you make sure that they weren't just giving you slop? Please
> explain in detail, **including which parts you did and didn't check, how you
> prioritized, and how surprised you'd be to discover a major error in each
> part.**

That is not a question you can answer honestly from memory two days later. It
is a question about a record. This file is the record.

The word "didn't" is doing real work in that question. An answer claiming you
verified everything is either false or means you did very little. The strong
answer names what you skipped and why skipping it was the right call.

## How to use this

Add a row the moment you finish a component. Be specific about the *mechanism*
of verification, not the fact of it. "Checked the output" is worthless.
"Recomputed the arm-A accuracy by hand from 12 rows of forensics.jsonl in a
spreadsheet; matched to 2dp" is evidence.

Surprise scale, used consistently:

- **1** — would astonish me; I re-derived this independently
- **2** — would surprise me; I spot-checked against raw data
- **3** — plausible; I read the code but ran no independent check
- **4** — likely there is something wrong here; I accepted it on trust
- **5** — I did not look at this at all

Anything at 4 or 5 that touches a headline number must be either fixed or
stated in the limitations section. Anything at 4 or 5 that doesn't touch a
headline number is fine, and saying so plainly is a strength.

## Log

| # | Component | Written by | How I verified it | Surprise (1-5) |
|---|-----------|-----------|-------------------|----------------|
| 1 | `src/backend.py` — CoT extraction |  |  |  |
| 2 | `src/experiment.py` — scenarios |  |  |  |
| 3 | `src/experiment.py` — arm cause blocks |  |  |  |
| 4 | Arm D suppression mechanism |  |  |  |
| 5 | Action parsing / `valid` flag |  |  |  |
| 6 | GATE 1 behaviour-match numbers |  |  |  |
| 7 | Probe library + `state_true_fact` discrimination |  |  |  |
| 8 | Investigator prompt + blinding |  |  |  |
| 9 | Verdict parsing |  |  |  |
| 10 | Balanced accuracy + the gap |  |  |  |
| 11 | Bootstrap CI |  |  |  |
| 12 | Figures — do axes match the numbers? |  |  |  |
| 13 | `src/probe.py` — activation extraction |  |  |  |
| 14 | Probe cross-scenario control |  |  |  |
| 15 | Executive summary prose |  |  |  |

## Non-negotiable checks (do these, then log them)

- [ ] **Re-derive one headline number by hand.** Open `data/forensics.jsonl`,
      take arm D under condition `full`, count correct verdicts manually,
      divide. Match it against `results.json`. If it doesn't match, you have
      found a real bug and it was worth the twenty minutes.
- [ ] **Read the blinding yourself.** Print one full investigator prompt and
      confirm with your own eyes that the arm label and the hidden cause block
      are not in it. A blinding bug invalidates everything downstream and is
      invisible in the outputs.
- [ ] **Check `state_true_fact` actually discriminates.** Arm B's concerning
      rate should collapse under it; A and D should not. If all three move
      together, the probe isn't doing what the design claims.
- [ ] **Read 20 transcripts** (`python -m src.inspect_cli --export notes.md`).
- [ ] **If you ran the probe: check the cross-scenario number before anything
      else.** Below 70% and the arm-D result is not reportable, full stop.
- [ ] **Confirm the reasoning traces are real.** Spot-check five: is the model
      actually reasoning, or is `reasoning_content` echoing the answer?

## Prose

Every word of the executive summary and every form answer is written by you.
The form's own guidance: answers that read like LLM output are a stated
negative signal. Draft in your own words first; use an LLM to cut length, not
to generate.

## Evidence AGAINST the hypothesis

The form asks separately: *"What is the strongest evidence you found against
these hypotheses?"* This is not a limitations question — it wants a finding.
Log candidates here as you hit them, because you will not remember them Friday.

- 
