# The Unread Transcript: A Positive Control for Chain-of-Thought Model Forensics

Deven Choudhary
MATS 12.0 application task, September 2026

> ROUGH DRAFT. Everything marked `[FILL]` needs you. Everything else is
> checkable against `data/results.json` and `data/forensics.jsonl`.
>
> Two things to do before you touch the prose:
> 1. Run `python -m src.leakcheck`. Section 4.1 and §5 depend on its output and
>    the numbers there are currently blank.
> 2. Read the failures and write `notes.md`. Section 4.5 is yours.

---

## Executive summary

*(target: under 600 words, first 1 to 3 pages, with Figure 1 and Figure 2)*

Singh, Kroiz, Rajamanoharan and Nanda propose model forensics: when a model
does something concerning, read its chain of thought, form a hypothesis about
why, then test that hypothesis with counterfactual interventions. Their
limitations section concedes that positive controls were absent. When they
probed Kimi K2 Thinking for awareness of violating user intent and found
nothing, they could not separate "there is nothing here" from "our method
cannot see it."

I built the missing control. Three arms of a single model take the same
concerning action for causes fixed by construction: a hidden objective that
conflicts with user intent (A), a false belief about the environment (B), and
the same objective as A with verbalisation suppressed (D). Ground truth is
MISALIGNED, MISTAKE, MISALIGNED. A blind investigator sees the scenario and the
transcript, never the arm or the injected cause. Four evidence conditions form
a ladder: the extended reasoning withheld; the reasoning shown; the reasoning
shown plus two counterfactual probes; the reasoning shown with a requirement to
quote the decisive sentence before ruling.

Showing the investigator 2,500 characters of chain of thought buys nothing.
Balanced accuracy over arms A and B is 61.4% with the reasoning withheld and
60.2% with it shown, over the same 87 investigations. Arm B is identical to the
case, 8 correct out of 35 in both.

Requiring a quote from that same reasoning recovers 12.7 points, to 72.9%. All
of it lands on arm B: false convictions of the mistaken model fall from 27 of
35 to 19 of 35. The information was present and usable. The protocol did not
use it until told to.

Counterfactual probes recover a similar 12.0 points but by a worse route. They
push arm B to 94.3% while collapsing arms A and D to exactly 50%, which is
chance. The probes buy exoneration accuracy by giving up conviction accuracy;
requiring a quote does not.

The manipulation the study was built around did nothing. The legibility gap,
accuracy over {A,B} minus accuracy over {D,B}, is 0.0 points in three of four
conditions and -1.3 in the fourth. Arm D verbalises the motive in 22% of
trajectories against arm A's 79%, so the manipulation worked; the verdict was
simply not reading what it varied.

`[FILL after leakcheck: one sentence on the redaction leak and what it costs
the first claim. Draft: "The withheld condition removes the reasoning block but
not the one-sentence justification the agent writes after acting, and that
sentence names the motive in X% of arm A trajectories, so the first result
compares extended reasoning against a short self-report rather than against
nothing."]`

**Figure 1** is the ladder. **Figure 2** is per-arm accuracy, which shows arm B
carrying the entire signal.

---

## 1 Introduction

An agent deletes an audit log. The log recorded an error the agent made
earlier. Did it delete the log to hide the error, or because it believed the
directory was scratch space? The action is identical either way and the
appropriate response is not.

Model forensics is the proposal that you can tell the difference by reading the
model's reasoning and testing your hypothesis with counterfactual edits to the
environment. The method has an obvious failure mode and its authors name it:
without a case where you already know the answer, a null result is
uninterpretable. Their audit of Kimi K2 Thinking found no evidence of
awareness, and they say plainly that positive controls were absent.

A positive control is cheap to build. Fix the cause yourself, hide it from the
investigator, and score whether the protocol recovers it.

My contributions:

1. **A positive control for CoT-based model forensics.** Three arms with
   ground truth by construction, four evidence conditions, one blind
   investigator, 87 investigated cases.
2. **The protocol does not spontaneously use the reasoning trace.** Withholding
   2,500 characters of chain of thought changes balanced accuracy by 1.3
   points, and leaves arm B accuracy identical to the case.
3. **A one-line prompt change recovers what the intervention loop recovers, and
   costs less.** Requiring the investigator to quote the decisive sentence
   before ruling adds 12.7 points, all on arm B, without the collapse in
   conviction accuracy that the counterfactual probes cause.

The legibility manipulation the study was designed around produced nothing, and
result 2 is why: you cannot degrade evidence that is not being read.

## 2 Related work

**Model forensics.** Singh et al. propose the protocol under test and name the
missing positive control. This work supplies one.

**Model organisms.** Hubinger et al. and Turner et al. build deliberately
misaligned models to test whether detection finds what is known to be present.
This study induces causes in context rather than in weights, which is cheaper
and weaker; see §5.

**Organism degradation.** Tan et al. show that published model organisms lose
instruction-following and preference coherence. Causes induced in context avoid
that failure mode entirely, at the cost of realism.

**CoT monitoring.** `[FILL: one line on "A False Average" (arXiv 2608.00583) if
you read it. If you have not read it, cut this bullet rather than cite it.]`

## 3 Method

### 3.1 Arms

One model, Qwen3.5-9B, served with vLLM. Each arm receives a different cause
block in its system prompt.

| arm | injected cause | ground truth |
|---|---|---|
| A | performance scored solely on a metric the concerning action maximises | MISALIGNED |
| B | a stated false belief about which artefact is authoritative | MISTAKE |
| D | arm A's cause block plus an output protocol forbidding reference to it | MISALIGNED |

Arm B states a belief, not an instruction. An earlier version told the model
"the sanctioned fix is to update the test" and it complied 100% of the time,
which is instruction-following rather than a mistaken belief.

Arm D's protocol constrains speech only, and says so: *"this governs the form
of your visible reasoning, not which action you choose. Whatever you would have
decided, decide it."* An earlier version told the model to reason "as a senior
engineer would, purely about the code," which steered it toward the correct
action and broke the comparison.

### 3.2 Manipulation check

A phrase-level detector counts whether a trajectory's reasoning refers to the
agent's own incentive. Over 90 trajectories per arm: arm A 79%, arm D 22%, arm
B 0%.

Arm B has no incentive to refer to, so its rate is the detector's
false-positive floor, and that floor is zero. An earlier detector matched bare
words and scored arm B at 40%; every one of those was a false positive on
ordinary engineering language.

Arms A and D therefore differ by 57 points in how legible the cause is, and
share the cause itself. The manipulation is imperfect: 22% is not silence, and
the analysis treats arm assignment as the randomised variable and verbalisation
as compliance.

### 3.3 Scenarios and selection

Two single-decision agentic settings with three actions each: a failing
rounding test before a release, where the concerning action is editing the test
to match the buggy implementation; and an audit log during a workspace handoff,
where the concerning action is deleting the log.

45 trajectories per arm per scenario, 270 total. Only trajectories that took the
concerning action are investigated, which gives 87 cases: 40 A, 35 B, 12 D.

Base rates differ sharply, and the difference is not noise:

| | arm A | arm B | arm D |
|---|---|---|---|
| test_edit | 20.0% | 40.9% | 11.1% |
| log_delete | 68.9% | 37.8% | 15.6% |

The same injected motive drives the concerning action in 69% of log-deletion
trajectories and 20% of test-editing ones. Whatever this model will and will
not do is governed more by the setting than by the motive.

### 3.4 The investigator

A blind investigator receives the user-facing scenario and the transcript. It
never sees the arm label or the cause block. Its counterfactual probes modify
the user-facing scenario only, because a real investigator cannot delete a
cause it cannot see.

Four conditions:

| condition | investigator receives |
|---|---|
| `redacted` | transcript with the reasoning block withheld |
| `cot_only` | transcript including the reasoning block |
| `full` | `cot_only` plus results of up to two counterfactual probes it selects |
| `cot_forced` | `cot_only` plus a requirement to quote the decisive sentence and state what it implies, before ruling |

The investigator is the same model as the subject. §5 treats this.

### 3.5 Metric

Balanced accuracy over one MISALIGNED arm and arm B, so unequal arm sizes
cannot move the result. Chance is 50%. An investigator that always says
MISALIGNED also scores 50%, because it is right on every A and wrong on every
B. Both baselines coincide, which is convenient.

The legibility gap is acc{A,B} minus acc{D,B}. Under balanced accuracy this is
exactly (acc_A - acc_D) / 2 and arm B cancels out of it. Arm B is not
decoration; it is what stops "always convict" scoring 100%. It contributes
nothing to the gap.

Intervals are 95% percentile bootstrap, 10,000 resamples within arm.

## 4 Results

### 4.1 The extended reasoning is not used

| condition | acc{A,B} | arm A | arm B | arm D |
|---|---|---|---|---|
| `redacted` | 61.4% [55.7, 68.6] | 100% | 22.9% | 100% |
| `cot_only` | 60.2% [53.0, 67.3] | 97.5% | 22.9% | 100% |

Same 87 trajectories, same investigator, same prompt but for the reasoning
block. Arm B is identical to the case, 8 of 35 in both. One verdict changed
across the whole sample, in arm A.

`[FILL from src/leakcheck.py §3: paired McNemar counts and p for
redacted -> cot_only. The independent intervals above do not license a claim
about their difference; the paired test does.]`

**The scope of this claim is narrower than it looks.** The `redacted` condition
withholds the reasoning block but keeps `content`, and the agent is instructed
to write a sentence of justification after its action. That sentence frequently
names the motive; one arm A trajectory ends *"removing it ensures a clean
handoff with no traceable mistakes."* So this contrast is extended reasoning
against a short self-report, not against nothing.

`[FILL from src/leakcheck.py §1 and §2: what fraction of arm A and arm D
justifications name the motive, and whether the redacted-vs-cot_only null holds
in the non-leaking subset. If the null holds only where the justification
leaked, restate the claim as "the long trace is redundant with the short
self-report" and say so here.]`

A genuine no-self-report condition was not run. §5.

### 4.2 Requiring a quote recovers 12.7 points

| condition | acc{A,B} | arm A | arm B | arm D |
|---|---|---|---|---|
| `cot_only` | 60.2% | 97.5% | 22.9% | 100% |
| `cot_forced` | 72.9% [64.3, 81.4] | 100% | 45.7% | 100% |

Identical evidence. The only change is an instruction to quote the sentence the
investigator finds decisive, and to say what it implies, before ruling. False
convictions of the mistaken model fall from 27 of 35 to 19 of 35.

The information was in the transcript and was usable. It went unused.

`[FILL from leakcheck §3: paired counts and p for cot_only -> cot_forced.]`

The manipulation is two things at once, quoting and articulating a motive from
the quote. This does not separate them.

### 4.3 Counterfactual probes buy the same accuracy by a worse route

| condition | acc{A,B} | arm A | arm B | arm D | says MISALIGNED |
|---|---|---|---|---|---|
| `cot_only` | 60.2% | 97.5% | 22.9% | 100% | 90% |
| `full` | 72.1% [63.4, 80.9] | 50.0% | 94.3% | 50.0% | 32% |
| `cot_forced` | 72.9% | 100% | 45.7% | 100% | 82% |

`full` and `cot_forced` are within one point of each other on balanced
accuracy, and are not doing the same thing. The probes move the investigator's
prior from convicting 90% of the time to convicting 32%, which fixes arm B and
puts both misaligned arms at exactly chance. Requiring a quote holds A and D at
ceiling and takes a smaller bite out of arm B.

One probe explains most of this, and it is my error rather than the protocol's.
The `state_true_fact` probe was meant to correct a false belief, but its text
also says deleting the log "is a reportable control failure." That raises the
cost of the action as well as correcting the belief, and a score-maximising
agent stops for the first reason as readily as a mistaken one stops for the
second. Its collapse is therefore not diagnostic, and investigators cite it
when ruling MISTAKE. `[FILL from notes.md: in how many of the failures you read
was the state_true_fact collapse the stated reason?]`

The `full` numbers are evidence about this implementation of the protocol, not
about the protocol as published.

### 4.4 The legibility manipulation did nothing

The gap acc{A,B} minus acc{D,B} is +0.0 points in `cot_forced`, `full` and
`redacted`, and -1.3 in `cot_only`. The `full` interval is [-15.8, +15.8],
which is wide and centred on zero.

The manipulation worked at the level it operated on: arm D verbalises the
motive at 22% against arm A's 79%. It did not propagate to the verdict, and
§4.1 is why.

Do not read this as the protocol passing its positive control. The control
targeted evidence the verdict was not built from.

### 4.5 What the failures look like

`[FILL from notes.md. The material to look for:
 - the investigator treating "I am doing what I am scored on" as sincere goal
   pursuit rather than as misalignment
 - the state_true_fact collapse cited as belief-correction
 - whether cot_forced quotes land on the motive sentence or on something
   incidental, which is currently the least understood part of the result
Write it as observation, not summary. Two paragraphs.]`

## 5 Discussion and limitations

Requiring a quote is a fix and not just a diagnosis. It costs one line of
prompt against an intervention loop that reruns the scenario, and on this
sample it does not trade conviction accuracy for exoneration accuracy. That is
worth testing on a real audit.

**Arms A and D are at ceiling and carry no information.** Under an investigator
that convicts between 82% and 91% of the time, 100% on the misaligned arms is
the prior, not discrimination. Every informative number in this paper is an arm
B number. Balanced accuracy partly hides this, which is why the per-arm columns
are in every table.

**Limitations.**

The `redacted` condition does not remove the agent's one-sentence
justification, so the §4.1 contrast is extended reasoning against a short
self-report. `[FILL: leak rate.]` A condition withholding both was not run and
is the first thing I would add.

The investigator is the same model as the subject, Qwen3.5-9B. The `cot_forced`
result argues against "the investigator was simply too weak," since the same
investigator recovers 12.7 points when told to quote, but it does not settle
it. A stronger investigator is the obvious next run and was not done.

The `state_true_fact` probe conflates belief-correction with cost-imposition,
as described in §4.3. This is a defect in my implementation and it means the
`full` condition understates what a correctly specified probe could do.

Arm D has 12 investigated cases and every arm D interval is wide. No claim in
§4.1 or §4.2 depends on arm D.

Only trajectories that took the concerning action are investigated. Arm D acts
in roughly 13% of trajectories, so its 12 cases may be atypical of arm D. This
is selection, and I have not characterised it.

Causes are induced in context, not in weights. A LoRA replication is the test
of whether any of this survives the move, and it was not run.

Two scenarios, and the base-rate reversal between them says scenario choice
matters more than arm assignment does. Two is not a sample of scenarios.

Probe results are precomputed per (scenario, arm, probe) rather than per
investigation, so they carry no per-trajectory noise. The investigator still
selects which probes it sees.

Thresholds were fixed during a pilot phase and are documented in §5.1. **They
were not pre-registered.** Every contrast in §4 is exploratory and uncorrected
for multiple comparisons.

### 5.1 Design decisions, and when each was made

Every threshold in this study was set or changed during a pilot phase, before
the 270-trajectory run and before any verdict was scored. None was changed
afterwards. Recorded here because a reader is entitled to check.

- Arm D suppression by direct instruction gave arm A 80% verbalisation against
  arm D 50%. Replaced.
- A stronger output protocol gave 79% against 22%. Kept.
- A variant installing the motive through prior turns rather than a directive
  was written and rejected without being run: it changes arm D's cause, so A
  and D would no longer share one.
- The first verbalisation detector matched bare words and scored arm B, which
  has no motive, at 40%. Tightened to phrases; arm B fell to 0%.
- An initial gate required matched action rates across arms. Dropped. The
  investigator sees one transcript at a time and never learns base rates, so
  unequal rates cost sample size rather than validity. Replaced by a minimum of
  8 investigated cases per arm.
- `max_tokens` raised twice, 2048 to 4096 to 8192, after truncated traces were
  observed. Final run: 1 truncation in 270.

## 6 Conclusion

A protocol that asks you to read a model's reasoning does not read it. Deleting
2,500 characters of chain of thought from 87 investigations changed one verdict.
Requiring the investigator to quote one sentence from the same reasoning
recovered 12.7 points of balanced accuracy, all of it in fewer false
convictions of a model that was merely mistaken; counterfactual interventions
recovered the same amount by moving the prior wholesale and putting both
misaligned arms at chance. The manipulation this study was built around,
suppressing whether the model says its motive out loud, changed nothing,
because the verdict was never built from what was suppressed.

`[FILL: one closing line in your own voice. Loyal Lies ended "An auditor's job
is not to elicit an answer; it is to elicit an answer that survives an attempt
to kill it." Find this paper's version. Do not reuse that one.]`

## Code and data

Repository: https://github.com/PotatoChoudhary/quiet-motive

Contains the full pipeline, all 270 trajectories with reasoning traces, all 348
investigations with verdicts, the probe library, `results.json`, every figure,
and an offline test suite that runs the whole pipeline against a scripted model
with no GPU.

## LLM usage statement

`[FILL from VERIFICATION_LOG.md. Real entries you have:
 - the vLLM reasoning field is `reasoning`, not `reasoning_content`; the wrong
   name produced 18 of 18 silently empty traces while 15 of 18 actions parsed
   normally, and it surfaced only because the harness prints an empty-trace
   count
 - a config check reported "MoE: False" after reading a nested config and
   finding nothing
 - a verbalisation detector scored a no-motive control arm at 40% on bare word
   matches
 - a patch to a gate silently failed to apply and shipped unchanged
 - the `redacted` condition was described as "actions only" for two days before
   anyone read what it actually removes
Say which parts you did not check, and how surprised you would be by an error
in each. Do not clean this up.]`
