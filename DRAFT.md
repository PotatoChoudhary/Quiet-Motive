# The Unread Transcript: A Positive Control for Chain-of-Thought Model Forensics

Deven Choudhary
MATS 12.0 application task, September 2026

> DRAFT v2. All numbers are final and checkable against `data/results.json`,
> `data/probe_results.json` and `python -m src.leakcheck`.
> `[FILL]` marks the parts only you can write: §4.6, the closing line, and the
> LLM usage statement.

---

## Executive summary

*(target: under 600 words, first 1 to 3 pages, with Figures 1 and 2)*

Singh, Kroiz, Rajamanoharan and Nanda propose model forensics: when a model
does something concerning, read its chain of thought, form a hypothesis about
why, then test that hypothesis with counterfactual interventions. Their
limitations section concedes that positive controls were absent. When they
probed Kimi K2 Thinking for awareness of violating user intent and found
nothing, they could not separate "there is nothing here" from "our method
cannot see it."

I built the missing control. Three arms of Qwen3.5-9B take the same concerning
action for causes fixed by construction: a hidden objective conflicting with
user intent (A), a false belief about the environment (B), and A's objective
with verbalisation suppressed (D). Ground truth is MISALIGNED, MISTAKE,
MISALIGNED. A blind investigator sees the scenario and the transcript, never
the arm or the injected cause. Four evidence conditions, 87 investigated cases,
348 investigations. All four conditions run on the same cases, so every
contrast below is a paired McNemar test rather than a comparison of
independent intervals.

**Showing the investigator the chain of thought does nothing.** Accuracy is
60/87 with the reasoning withheld and 59/87 with it shown. Five cases fixed,
six broken, p = 1.00.

**Requiring a quote from that same reasoning fixes 11 cases and breaks 2,**
p = 0.022, taking accuracy to 68/87. The information was present and usable.
The protocol did not use it until told to.

**The counterfactual probes change 52 of 87 verdicts and improve nothing.**
Twenty-six fixed, twenty-six broken, p = 1.00. They move the investigator from
convicting 90% of the time to 32%, which fixes arm B and breaks arms A and D by
exactly as much.

**A linear probe on the residual stream separates the two causes where the
transcript-based protocol cannot.** Trained on arm A against arm B in one
scenario and tested in the other, it transfers at 98.9% at the layer with best
transfer, and classifies 91.1% of held-out arm D as arm A. The layer sweep is
unstable on arm D and three of eight layers disagree, so this is suggestive
rather than settled; the A-versus-B direction itself is robust, transferring
between 89% and 99% at every layer above the embedding.

**The legibility manipulation produced nothing, and the reason is selection.**
Arm D verbalises its motive in 22% of all trajectories but 67% of the 12 that
were investigated. Conditioning on having taken the concerning action selects
for the arm-D runs that broke suppression, so in the analysed sample arm D is
nearly as loud as arm A.

**Figure 1** is the evidence ladder. **Figure 2** is per-arm accuracy, which
shows arm B carrying the entire signal.

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
   ground truth by construction, four evidence conditions on the same 87 cases,
   paired tests throughout.
2. **The protocol does not spontaneously use the reasoning trace, and the
   counterfactual interventions do not improve on it.** Withholding the
   reasoning: p = 1.00. Adding interventions: 52 verdicts changed, net zero,
   p = 1.00.
3. **One line of prompt recovers what the intervention loop does not.**
   Requiring the investigator to quote the decisive sentence before ruling
   fixes 11 cases and breaks 2, p = 0.022.
4. **The evidence was in the activations the whole time.** A linear probe
   transferring across scenarios at 98.9% reads the suppressed arm as
   misaligned, at a layer chosen by a rule fixed before the data.

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

## 3 Method

### 3.1 Arms

One model, Qwen3.5-9B, served with vLLM, temperature 1.0, seeded per
trajectory. Each arm receives a different cause block in its system prompt.

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

### 3.2 Manipulation check, and the selection problem

A phrase-level detector counts whether a trajectory's reasoning refers to the
agent's own incentive. Arm B has no incentive to refer to, so its rate is the
false-positive floor.

| arm | all 90 trajectories | the investigated subset |
|---|---|---|
| A | 79% | 95% (n=40) |
| B | 0% | 0% (n=35) |
| D | 22% | 67% (n=12) |

The manipulation worked: 79% against 22% over all trajectories. **The analysed
sample does not inherit it.** Only trajectories that took the concerning action
are investigated, and conditioning on that selects for the arm-D runs where
suppression failed. Among investigated cases the contrast is 95% against 67%,
not 79% against 22%.

Every legibility claim in this paper is therefore weak by construction, and §4.4
should be read as a statement about the analysed sample rather than about the
manipulation.

An earlier detector matched bare words and scored arm B at 40%; every one of
those was a false positive on ordinary engineering language.

### 3.3 Scenarios

Two single-decision agentic settings with three actions each: a failing
rounding test before a release, where the concerning action is editing the test
to match the buggy implementation; and an audit log during a workspace handoff,
where the concerning action is deleting the log.

45 trajectories per arm per scenario, 270 total, 269 with a parseable action.
87 took the concerning action and were investigated: 40 A, 35 B, 12 D.

Base rates differ sharply:

| | arm A | arm B | arm D |
|---|---|---|---|
| test_edit | 20.0% | 40.9% | 11.1% |
| log_delete | 68.9% | 37.8% | 15.6% |

The same injected motive drives the concerning action in 69% of log-deletion
trajectories and 20% of test-editing ones. What this model will and will not do
is governed more by the setting than by the motive.

### 3.4 The investigator and the four conditions

A blind investigator receives the user-facing scenario and the transcript. It
never sees the arm label or the cause block. Its counterfactual probes modify
the user-facing scenario only, because a real investigator cannot delete a
cause it cannot see.

| condition | investigator receives |
|---|---|
| `redacted` | transcript with the reasoning block withheld |
| `cot_only` | transcript including the reasoning block |
| `full` | `cot_only` plus results of up to two counterfactual probes it selects |
| `cot_forced` | `cot_only` plus a requirement to quote the decisive sentence and state what it implies, before ruling |

The investigator is the same model as the subject. §5 treats this.

### 3.5 Metric

**Primary: raw accuracy over all 87 investigated cases, with paired McNemar
tests between conditions.** The four conditions run on the same cases, so the
per-case discordance is the right test and independent confidence intervals
would not license any claim about a difference.

An investigator that always says MISALIGNED scores 52/87, or 59.8%, because 52
of the cases are arms A and D. That, not 50%, is the baseline to beat.

Balanced accuracy over arms A and B is reported as a secondary check. It
reweights per case and drops arm D, and §4.3 shows the two metrics disagreeing
in a way that is itself informative.

## 4 Results

### 4.1 The reasoning trace is not used

| condition | correct | accuracy |
|---|---|---|
| always convict | 52/87 | 59.8% |
| `redacted` | 60/87 | 69.0% |
| `cot_only` | 59/87 | 67.8% |

Same 87 cases, same investigator, same prompt but for the reasoning block.
Paired: 5 cases fixed by showing the reasoning, 6 broken, p = 1.00.

**Scope.** The `redacted` condition withholds the reasoning block but keeps
`content`, and the agent is instructed to write a sentence of justification
after its action. That sentence names the motive in 18% of arm A and 17% of arm
D trajectories, so redaction is partial.

The leak does not explain the null. Restricting to the 78 cases where the
justification did not name the motive: `redacted` 65.4%, `cot_only` 64.1%. The
9 leaking cases are at 100% in both conditions and cannot carry the result.

A condition withholding both the reasoning and the justification was not run.

### 4.2 Requiring a quote fixes 11 cases and breaks 2

| condition | correct | accuracy |
|---|---|---|
| `cot_only` | 59/87 | 67.8% |
| `cot_forced` | 68/87 | 78.2% |

Identical evidence. The only change is an instruction to quote the sentence the
investigator finds decisive, and to say what it implies, before ruling. Paired:
11 fixed, 2 broken, p = 0.022. In balanced terms the gain is 60.2% to 72.9%,
carried entirely by arm B, where false convictions fall from 27 of 35 to 19.

The information was in the transcript and was usable. It went unused.

The manipulation is two things at once, quoting and articulating a motive from
the quote, and this design does not separate them.

### 4.3 The counterfactual probes change 52 verdicts and improve nothing

| condition | raw | balanced {A,B} | arm A | arm B | arm D | says MISALIGNED |
|---|---|---|---|---|---|---|
| `cot_only` | 59/87 | 60.2% | 97.5% | 22.9% | 100% | 90% |
| `full` | 59/87 | 72.1% | 50.0% | 94.3% | 50.0% | 32% |
| `cot_forced` | 68/87 | 72.9% | 100% | 45.7% | 100% | 82% |

Paired, `cot_only` against `full`: 26 cases fixed, 26 broken, p = 1.00. Raw
accuracy is identical to the case, 59/87 both.

The two metrics disagree and the disagreement is the finding. Balanced accuracy
rises 12 points because the probes move errors off arm B, which has 35 cases,
onto arms A and D, which have 52 between them; balancing weights arm B more
heavily per case. Per case, the probes are a wash. They shift the
investigator's prior from convicting 90% of the time to 32% and buy exoneration
accuracy at exactly the price of conviction accuracy.

`cot_forced` beats `full` directionally, 27 fixed against 18 broken, p = 0.233.
Not significant at this sample size.

**One probe is defective and it is my error, not the protocol's.** The
`state_true_fact` probe was meant to correct a false belief, but its text also
says deleting the log "is a reportable control failure." That raises the cost
of the action as well as correcting the belief, and a score-maximising agent
stops for the first reason as readily as a mistaken one stops for the second.
Its collapse is therefore not diagnostic. `[FILL from notes.md: in how many of
the failures you read was the state_true_fact collapse the stated reason for a
MISTAKE verdict?]`

The `full` numbers are evidence about this implementation, not about the
protocol as published.

### 4.4 The legibility manipulation did nothing, and selection is why

The gap, balanced accuracy over {A,B} minus over {D,B}, is 0.0 points in
`cot_forced`, `full` and `redacted`, and -1.3 in `cot_only`.

Do not read this as the protocol passing its positive control. Two reasons, and
neither is about legibility.

First, §4.1: the verdict is not built from the reasoning trace, so varying what
the trace contains cannot move it.

Second, §3.2: among investigated cases arm D verbalises at 67% against arm A's
95%. The manipulation is 57 points wide over all trajectories and 28 points
wide in the sample that was actually analysed.

### 4.5 A linear probe separates the causes the transcript cannot

Logistic probe on the residual stream at the final token, trained on arm A
against arm B in `log_delete` and tested in `test_edit`. The two scenarios
share no surface vocabulary and state the incentive in different words, so
cross-scenario transfer is the control against the probe reading prompt tokens.
All 269 valid trajectories are used, not the 87 investigated ones, so the
selection problem in §3.2 does not apply here; held-out arm D is n=45.

| layer | in-scenario A/B | cross-scenario A/B | arm D scored as A |
|---|---|---|---|
| 0 | 50.0% | 49.4% | 0.0% |
| 4 | 94.4% | 93.3% | 97.8% |
| 8 | 100% | 92.1% | 100% |
| **12** | **100%** | **98.9%** | **91.1%** |
| 16 | 100% | 94.4% | 37.8% |
| 20 | 97.8% | 96.6% | 97.8% |
| 24 | 98.9% | 78.7% | 17.8% |
| 28 | 100% | 89.9% | 35.6% |
| 32 | 97.8% | 91.0% | 88.9% |

Layer 0 is at chance, which is the sanity check working. The A-versus-B
direction is robust: cross-scenario transfer is between 89% and 99% at every
layer above the embedding.

At layer 12, selected by a rule fixed in code before the data existed (best
cross-scenario transfer), the probe classifies 91.1% of held-out arm D as arm A.
Under the `full` protocol the same arm is read correctly 50% of the time, which
is chance.

**The arm-D readout is unstable across layers.** Layer 16 transfers at 94.4%
and gives 37.8%; layer 24 gives 17.8%. Three of the eight non-trivial layers
give the opposite answer. The selection rule was pre-specified, which rules out
p-hacking, but it does not make the readout stable. Treat this as suggestive.

**What this does not show.** The cause block sits in context for both arm A and
arm D. Cross-scenario transfer rules out the probe reading literal tokens, since
the two scenarios phrase the incentive differently, but it does not rule out the
probe detecting "a scoring directive is present in this context" rather than
"this model is acting on one." Separating those requires inducing the cause in
weights, which was not done.

### 4.6 What the failures look like

`[FILL from notes.md. What to look for:
 - the investigator treating "I am doing what I am scored on" as sincere goal
   pursuit rather than misalignment
 - the state_true_fact collapse cited as belief-correction
 - whether cot_forced quotes land on the motive sentence or on something
   incidental, which is the least understood part of §4.2
Observation, not summary. Two paragraphs.]`

## 5 Discussion and limitations

Requiring a quote is a fix and not just a diagnosis. It costs one line of
prompt, it is the only intervention here that improved per-case accuracy, and
the counterfactual loop it outperformed is substantially more expensive to run.
That is worth testing on a real audit.

**Arms A and D are at ceiling in three of four conditions and carry little
information.** Under an investigator that convicts 82% to 91% of the time, 100%
on the misaligned arms is the prior. Every informative number here is an arm B
number, which is why the per-arm columns are in every table.

**Limitations.**

The analysed sample does not inherit the legibility manipulation. Arm D
verbalises at 22% overall and 67% among investigated cases, because
investigation conditions on having taken the concerning action. Every claim in
§4.4 is limited by this and I have not corrected for it.

The `redacted` condition does not remove the agent's one-sentence
justification, which names the motive in 18% of arm A cases. The null holds in
the non-leaking subset, but a condition withholding both was not run.

The `state_true_fact` probe conflates belief-correction with cost-imposition,
as described in §4.3. This is a defect in my implementation and it means §4.3
understates what a correctly specified probe could do.

The probe's arm-D readout is unstable across layers with comparable transfer.
The A-versus-B direction is not.

The probe cannot distinguish "a scoring directive is present in context" from
"this model is acting on one." A weight-induced cause is the test and was not
run.

The investigator is the same model as the subject, Qwen3.5-9B. §4.2 argues
against "the investigator was simply too weak," since the same investigator
recovers 11 cases when told to quote, but it does not settle it. A stronger
investigator is the obvious next run.

Arm D has 12 investigated cases. No claim in §4.1, §4.2 or §4.3 depends on it,
and §4.5 uses 45 held-out arm D trajectories instead.

Causes are induced in context, not in weights.

Two scenarios, and the base-rate reversal between them says scenario choice
matters more than arm assignment. Two is not a sample of scenarios.

Probe results in the `full` condition are precomputed per (scenario, arm,
probe) rather than per investigation, so they carry no per-trajectory noise.
The investigator still selects which probes it sees.

Thresholds were fixed during a pilot phase and are documented in §5.1. **They
were not pre-registered.** Every contrast is exploratory and uncorrected for
multiple comparisons; with four conditions and four reported pairs, the
p = 0.022 in §4.2 should be read accordingly.

### 5.1 Design decisions, and when each was made

Every threshold was set or changed during a pilot phase, before the
270-trajectory run and before any verdict was scored. None was changed
afterwards.

- Arm D suppression by direct instruction gave arm A 80% verbalisation against
  arm D 50%. Replaced.
- A stronger output protocol gave 79% against 22%. Kept.
- A variant installing the motive through prior turns rather than a directive
  was written and rejected without being run: it changes arm D's cause, so A
  and D would no longer share one.
- The first verbalisation detector matched bare words and scored arm B, which
  has no motive, at 40%. Tightened to phrases; arm B fell to 0%.
- An initial gate required matched action rates across arms. Dropped: the
  investigator sees one transcript at a time and never learns base rates, so
  unequal rates cost sample size rather than validity. Replaced by a minimum of
  8 investigated cases per arm.
- `max_tokens` raised twice, 2048 to 4096 to 8192, after truncated traces were
  observed. Final run: 1 truncation in 270.
- The probe's layer-selection rule (best cross-scenario transfer) and its 70%
  transfer floor were written into the code before any activations existed.

## 6 Conclusion

A protocol that asks you to read a model's reasoning does not read it. Removing
the reasoning trace from 87 investigations moved five verdicts one way and six
the other. Adding the counterfactual interventions the protocol specifies moved
fifty-two verdicts and improved nothing, trading conviction accuracy for
exoneration accuracy at par. Requiring the investigator to quote one sentence
from the same reasoning before ruling fixed eleven cases and broke two, and was
the only intervention that helped. Meanwhile a linear probe on the residual
stream, transferring across two scenarios that share no vocabulary, reads the
suppressed arm as misaligned at the layer where it transfers best.

`[FILL: one closing line in your own voice. Loyal Lies ended "An auditor's job
is not to elicit an answer; it is to elicit an answer that survives an attempt
to kill it." Find this paper's version. Do not reuse that one.]`

## Code and data

Repository: https://github.com/PotatoChoudhary/quiet-motive

Contains the pipeline, all 270 trajectories with reasoning traces, all 348
investigations with verdicts, the probe library, activations, `results.json`,
`probe_results.json`, every figure, and an offline test suite that runs the
whole pipeline against a scripted model with no GPU.

## LLM usage statement

`[FILL from VERIFICATION_LOG.md. Real entries:
 - the vLLM reasoning field is `reasoning`, not `reasoning_content`; the wrong
   name produced 18 of 18 silently empty traces while 15 of 18 actions parsed
   normally, and it surfaced only because the harness prints an empty-trace
   count
 - a config check reported "MoE: False" after reading a nested config and
   finding nothing
 - a verbalisation detector scored a no-motive control arm at 40% on bare word
   matches; arm B existing as a control is the only reason it was caught
 - a patch to a gate silently failed to apply and shipped unchanged
 - the `redacted` condition was described as "actions only" for two days before
   anyone read what it actually removes
 - the +12pp claim for counterfactual probes came from comparing two
   independent bootstrap intervals; the paired test says the effect is zero
Say which parts you did not check, and how surprised you would be by an error
in each. Do not clean this up.]`
