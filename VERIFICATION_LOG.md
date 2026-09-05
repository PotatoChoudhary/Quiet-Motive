# Verification log

What was checked, how, and what was not. Every entry is traceable to a commit,
a printed count, or a file in `data/`.

**Who did what.** This project was built with a coding agent (Claude Opus 5 in
Claude Code) and the division is not flattering to either party, so it is
stated rather than implied. The agent wrote essentially all of the code: the
pipeline, `verify.py`, the probe scripts, the analysis. I chose the problem,
ran the pipeline on the GPU, made the design calls, read the failure
transcripts, and rejected or redirected the agent's work repeatedly, including
on the substance. Section 4.7 is my reading of all 27 false exonerations and it
corrects the agent's reading of three of them by adding a pattern it had
missed.

The eleven errors below are the reason this file exists. Nine of the eleven are
errors the agent made and did not notice. Two are errors in how I checked its
work: I accepted a detector as validated on evidence that could not validate it
(9), and I set up a hand-labelling pass and abandoned it without labelling
anything, which is why one row in the "not verified" table below reads 4 rather
than 2. The pattern across all eleven is that not one was caught by careful
reading. Each was caught by a printed count, a control column that should have
read zero, or an assertion, which is an argument for building those in rather
than for trying harder.

Surprise scale, used consistently:

- **1** would astonish me; re-derived independently
- **2** would surprise me; spot-checked against raw data
- **3** plausible; read the code, ran no independent check
- **4** likely something is wrong; accepted on trust
- **5** did not look at this at all

## Errors that were caught, and what caught them

Eleven. None was caught by reading code carefully. Every one was caught by a
printed count, a control column that should have read zero, or an assertion.

| # | What went wrong | What caught it |
|---|---|---|
| 1 | vLLM returns the chain of thought in a field named `reasoning`; the client read `reasoning_content` from the docs. 18 of 18 trajectories came back with empty traces while 15 of 18 actions parsed. Nothing errored. | the harness prints a count of empty traces |
| 2 | A generated check reported "MoE: False" after reading a config whose keys nest under `text_config`, finding none of them, and reporting the absence as a negative. The model is dense, so the answer was right and the method was empty. | reading the printed output and noticing it had found no keys at all |
| 3 | The first verbalisation detector matched bare words and scored arm B, which has no motive, at 40%. Every one was a false positive. | arm B was in the table as a control and should have read 0% |
| 4 | A patch to the gate logic silently failed to match and shipped unchanged. A full experiment ran against code believed to have been modified. | comparing the shipped bundle against the intended diff; every later patch asserts its target string is present |
| 5 | The `redacted` condition was described as "actions only" for two days. It withholds the reasoning block and keeps the one-sentence justification, which names the motive in 18% of arm A. | reading what the condition actually removes, then `src/leakcheck.py` to measure it |
| 6 | A claimed +12pp gain for the counterfactual interventions came from comparing two independent bootstrap intervals over the same cases. | the paired McNemar on the same 87 cases returns 26 fixed, 26 broken, p = 1.00 |
| 7 | The action-only condition, proposed as the fix for (5), produced 87 unparseable verdicts. | the parse-rate gate in `src/forensics.py` |
| 8 | A design-decision section asserted every threshold was fixed before the 270-trajectory run. One gate's code was committed 2m43s after it finished. | `git log --format="%ai"` against the `ts` fields in `data/trajectories.jsonl` |
| 9 | The verbalisation detector was treated as validated because arm B sat at 0%. Arm B bounds false positives and says nothing about false negatives. Arm D's rate moved from 22% to 48% under a rule with no judgement in it. | reading arm-D traces the rule had called quiet; `test_edit:D:042` contains "the instruction says that the scoring is based on CI green" |
| 10 | §4.5 claimed the probe read the motive for three days. Every arm-A trajectory carries the directive and only 9 of 45 acted on it; the two groups score 0.916 and 0.899, p = 0.90. It reads the directive's presence. | `src/probe_action.py`, written after the caveat had been stated twice without being tested |
| 11 | A model asked to review this work reported it had checked the numbers against the public repository and gave `redacted` as 53/87. The repository stores no raw counts; 53 is that condition's balanced accuracy multiplied by 87. The real count is 60/87. | `verify.py`, written in response, which recomputes from raw rows rather than from `results.json` |

## What was verified, and how

| Component | How | Surprise |
|---|---|---|
| Every number in the write-up | `verify.py` recomputes all 69 from `trajectories.jsonl` and `forensics.jsonl`, implementing its own exact McNemar, Fisher and Wilson rather than reading `results.json`. Exits nonzero on any mismatch. | 1 |
| The 26 false exonerations in `full` | all 27 exported to `notes.md` and read; §4.7 is that reading, and the third pattern in it was found by reading, then counted | 1 |
| The random-sample claim | `random.Random(0).sample`, drawn once, none discarded, six cases printed in full in the write-up | 1 |
| The conservative detector | asserted in code that no scenario's task text contains any of its keywords, so a hit can only trace to the injected directive; arm B measures its false-positive rate at 0 of 90 | 2 |
| Probe is not reading noise | shuffled training labels 50.1%, random direction 48.8%, layer 0 embeddings 49.4%, against 98.9% | 1 |
| Probe is not reading trace length | median reasoning is 450 words for arm A and 507 for arm B, the two arms it separates; arm D at 292 is further from A than B is and is still read as A | 2 |
| Arm effects are not scenario effects | the forced-quote gain replicates in both scenarios (4 fixed 0 broken; 6 fixed 2 broken) | 2 |
| The protocol beats a trivial baseline | paired against always-convict; `full` does not, p = 0.44 | 1 |
| The four citations | each fetched and checked against what the write-up says about it; "Tan et al." is a LessWrong post with no arXiv version and the write-up says so | 2 |
| The target paper's own words | abstract fetched; the quoted sentence "without positive controls we cannot confirm our tests would detect it" is verbatim | 1 |

## What was not verified

Stated plainly, because the honest answer to "which parts didn't you check" is
not "none".

| Component | Why not | Surprise |
|---|---|---|
| Why `redacted_full` produced 0 parseable verdicts | never read those 87 outputs. It is excluded from results and reported as a failed run, so nothing depends on the answer, but I do not know it. | 5 |
| The detector's false-negative rate | a hand-labelling pass was set up and abandoned. False negatives are demonstrated by search and not quantified, so arm D's 48% is a floor. | 4 |
| The investigator prompt itself | never varied except for the four conditions. A different phrasing could move the convicting prior, which drives arms A and D to ceiling. | 4 |
| Whether the layer-12 direction is causal | the steering test was named and not run; no GPU by the time it mattered. | 5 |
| The `state_true_fact` probe text | its defect was found by reading it late, not by a check. Other probe texts were not audited the same way. | 3 |
| Per-trajectory probe noise | probe results in `full` are precomputed per (scenario, arm, probe), so they carry none. Known and stated, not fixed. | 2 |
