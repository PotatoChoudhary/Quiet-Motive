# The Unread Transcript: A Positive Control for Chain-of-Thought Model Forensics

Deven Choudhary
MATS 12.0 application task, September 2026

> FINAL DRAFT. Every number is checkable against `data/results.json`,
> `data/probe_results.json`, and `python -m src.leakcheck`.
>
> Three things are still yours and cannot be written for you: §4.6 (from
> `notes.md`), the closing line of §6, and the LLM usage statement. Facts for
> the last one are listed at the end; the prose has to be in your words,
> because the form treats LLM-voiced answers as a negative signal.

---

## Executive summary

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
the arm or the injected cause. Four evidence conditions run on the same 87
investigated cases, so every contrast is a paired McNemar test.

**Showing the investigator the chain of thought does nothing.** 60/87 correct
with the reasoning withheld, 59/87 with it shown. Five cases fixed, six broken,
p = 1.00.

**Requiring a quote from that same reasoning fixes 11 cases and breaks 2,**
p = 0.022, taking accuracy to 68/87. The information was present and usable.
The protocol did not use it until told to.

**The counterfactual interventions change 52 of 87 verdicts and improve
nothing.** Twenty-six fixed, twenty-six broken, p = 1.00. They move the
investigator from convicting 90% of the time to 32%, fixing arm B and breaking
arms A and D by exactly as much.

**A hidden directive stays decodable after the transcript goes quiet.**
A linear probe trained on arm A against arm B in one scenario, and tested
in the other, transfers at 98.9%. On the 25 held-out arm D trajectories that a
conservative detector finds never state the motive, it classifies 92.0% as arm
A, 95% CI 75 to 98, where the transcript-based protocol is at chance. **It is
detecting the directive, not the acting on it.** Arm A trajectories that took
the concerning action and those that did not score 0.916 and 0.899, p = 0.90.
Suppression removes the mention from the transcript and leaves the
representation. The arm-D readout is unstable across layers, 12% to 100%; the
A-versus-B direction is not, transferring between 89% and 99% everywhere above
the embedding.

**The preregistered primary outcome was null, and the null is uninformative.**
The preregistration named two conditions under which a zero legibility gap
would say nothing, and both hold: the reasoning trace was not being read in the
first place, and arm D's action rate diverges from arm A's in one of the two
scenarios, so the arms are legibility twins in `test_edit` and not in
`log_delete`. Selection compounds it. Arm D states its incentive in 48% of
all trajectories and in 75% of the 12 that were investigated, because
investigating conditions on the action and selects the runs where suppression
failed.

Figure 1 is the evidence ladder. Figure 2 is per-arm accuracy, which shows arm
B carrying the entire signal. Figure 4 is the probe layer sweep, including the
instability.

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
4. **Suppressing verbalisation does not remove the representation.** A probe
   transferring across scenarios at 98.9% classifies 92.0% of never-verbalising
   arm D trajectories as arm A, at a layer chosen by a rule fixed before the
   data existed. A within-arm test shows it reads the directive's presence and
   not the model's acting on it, so this is a result about what suppression
   leaves behind and about white-box auditing, not about motive detection.

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

One model, Qwen3.5-9B, served with vLLM at temperature 1.0, seeded per
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

Two detectors count whether a trajectory's reasoning refers to the agent's own
incentive. Arm B has no incentive to refer to, so its rate is the false-positive
floor for both.

The first is a phrase-level rule. It misses trajectories that state the
incentive in plain words, which is checkable without any judgement call:
`test_edit:D:042` contains the sentences "the score depends on getting the CI
green" and "the instruction says that the scoring is based on CI green", and
the rule does not flag it. The second detector is a bare
word match on score, metric, measured, incentive, rewarded, graded and
performance. Neither scenario's user-facing task text contains any of those
words, which is asserted in code, so any occurrence traces to the injected
directive. An earlier version of this rule also matched "evaluate", which fired
on section headings like "Evaluate the options" and put arm B at 8%; dropping
that one word returns arm B to zero and costs arm D two trajectories. The rule
over-flags rather than under-flags, which is the safe direction, and arm B
measures its cost at 0%.

| arm | all 90, phrase | all 90, bare word | investigated, phrase | investigated, bare |
|---|---|---|---|---|
| A | 79% | 87% | 95% | 95% (n=40) |
| B | 0% | 0% | 0% | 0% (n=35) |
| D | 22% | **48%** | 67% | **75%** (n=12) |

**The conservative reading is the honest one.** Arm D states its incentive in
just under half of all trajectories, not a fifth. Both rules have a zero
false-positive floor on arm B, so the second is not buying its extra catches
with noise: the manipulation is 87 points against 48, a contrast of 39 points
rather than the 57 the phrase rule implies. Every legibility figure below is
quoted under both rules.

The manipulation worked, but by less than the phrase rule suggests: 87%
against 48% across all trajectories under the conservative detector. **The
analysed sample does not inherit even that.** Only trajectories that took the
concerning action are investigated, and conditioning on that selects for the
arm-D runs where suppression failed. Among investigated cases the contrast is
95% against 75% under the conservative detector, and 95% against 67% under the
phrase rule. Either way it is not 87% against 48%.

Every legibility claim in §4 is weak by construction because of this, and §4.4
should be read as a statement about the analysed sample rather than about the
manipulation. §4.5 is not affected: the probe uses all trajectories.

A still earlier detector matched single bare words including "performance" and
"score" in isolation and put arm B at 40%; every one of those was a false
positive on ordinary engineering language. The bare-word rule used above is the
tightened version of that one, which is why arm B sits at 0% rather than 40%.

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

### 3.4 The investigator and the conditions

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

A fifth condition withholding the reasoning and the justification was
attempted and produced no parseable verdicts. It is reported in §5, not §4.

The investigator is the same model as the subject.

### 3.5 Metric

**Primary: raw accuracy over all 87 investigated cases, with paired McNemar
tests between conditions.** The conditions run on the same cases, so per-case
discordance is the right test, and independent confidence intervals would not
license any claim about a difference.

An investigator that always says MISALIGNED scores 52/87, or 59.8%, because 52
of the cases are arms A and D. That, not 50%, is the baseline to beat.

Balanced accuracy over arms A and B is reported as a secondary check. It
reweights per case and drops arm D, and §4.3 shows the two metrics disagreeing
in a way that is itself informative.

Bootstrap intervals are 95% percentile, 10,000 resamples within arm. Probe
intervals are Wilson, because n is small enough that the normal approximation
misleads.

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
9 leaking cases sit at 100% in both conditions and cannot carry the result.

The claim this supports is therefore that the extended reasoning trace adds
nothing over a one-sentence self-report, not that self-report of any kind goes
unread. The condition that would separate those failed; see §5.

### 4.2 Requiring a quote fixes 11 cases and breaks 2

| condition | correct | accuracy |
|---|---|---|
| `cot_only` | 59/87 | 67.8% |
| `cot_forced` | 68/87 | 78.2% |

Identical evidence. The only change is an instruction to quote the sentence the
investigator finds decisive, and to say what it implies, before ruling. Paired:
11 fixed, 2 broken, p = 0.022. In balanced terms, 60.2% to 72.9%, carried
entirely by arm B, where false convictions fall from 27 of 35 to 19 of 35.

The information was in the transcript and was usable. It went unused.

The manipulation is two things at once, quoting and articulating a motive from
the quote, and this design does not separate them.

### 4.3 The interventions change 52 verdicts and improve nothing

| condition | raw | balanced {A,B} | arm A | arm B | arm D | says MISALIGNED |
|---|---|---|---|---|---|---|
| `cot_only` | 59/87 | 60.2% | 97.5% | 22.9% | 100% | 90% |
| `full` | 59/87 | 72.1% | 50.0% | 94.3% | 50.0% | 32% |
| `cot_forced` | 68/87 | 72.9% | 100% | 45.7% | 100% | 82% |

Paired, `cot_only` against `full`: 26 fixed, 26 broken, p = 1.00. Raw accuracy
is identical to the case.

The two metrics disagree and the disagreement is the finding. Balanced accuracy
rises 12 points because the interventions move errors off arm B, which has 35
cases, onto arms A and D, which have 52 between them; balancing weights arm B
more heavily per case. Per case, they are a wash. They shift the investigator
from convicting 90% of the time to 32% and buy exoneration accuracy at exactly
the price of conviction accuracy.

`cot_forced` beats `full` directionally, 27 fixed against 18 broken, p = 0.233.
Not significant at this sample size.

**One probe is defective and it is my error, not the protocol's.** The
`state_true_fact` probe was meant to correct a false belief, but its text also
says deleting the log "is a reportable control failure." That raises the cost
of the action as well as correcting the belief, and a score-maximising agent
stops for the first reason as readily as a mistaken one stops for the second.
Its collapse is therefore not diagnostic.

It also does not explain the failures. `state_true_fact` was among the probes
the investigator chose in 24 of the 26 false exonerations in `full`, which
looks damning until you count the other side: it was chosen in 23 of the 26
correct verdicts as well. The defective probe is not concentrated in the errors,
so the errors need a different explanation. §4.6 gives one.

The `full` numbers are evidence about this implementation, not about the
protocol as published.

### 4.4 The preregistered primary outcome was null, and both its falsifiers fired

`GAP = acc{A,B} - acc{D,B}` in condition `full` was the preregistered primary
metric. It is 0.0, CI [-15.8, +15.8]. It is 0.0 in `cot_forced` and `redacted`
too, and -1.3 in `cot_only`.

The preregistered decision rule for a null was explicit: write it up "as a
positive control the protocol passes, with conviction." I am not doing that,
and the reason is that the same document named two conditions under which the
null would be uninformative, and both of them hold.

*"`redacted` condition scoring near `cot_only`, the verdict was never using the
CoT, so suppressing CoT content cannot be what causes the gap."* §4.1: 60/87
against 59/87, p = 1.00. You cannot degrade evidence that is not being read.

*"Arm D's behaviour differing from arm A's, then D is not a legibility twin and
the gap is confounded by behaviour."* This fired in one scenario and not the
other, which the earlier framing of "the manipulation failed" obscured.

| scenario | arm A | arm D | Fisher exact |
|---|---|---|---|
| `test_edit` | 9/45 = 20% | 5/45 = 11% | p = 0.384 |
| `log_delete` | 31/45 = 69% | 7/45 = 16% | p < 0.001 |

In `test_edit` the arms are behaviourally matched and the twin holds. In
`log_delete` it does not: a protocol written to constrain speech cut the action
rate by a factor of four. Restricted to `test_edit`, where the comparison is
valid, arms A and D are at 100% in three conditions and 56% against 60% in
`full`, on 9 and 5 investigated cases. That is the matched estimate and it is
too small to carry anything. It is reported so the matched number is not simply
missing.

Selection compounds the second one. Investigation conditions on the concerning
action, which selects the arm-D runs where suppression failed, so the analysed
sample does not inherit the manipulation: 95% against 75% among investigated
cases rather than 87% against 48% overall. Applied to the investigated subset,
my own GATE 1b requirement of a 30-point A-minus-D contrast fails, at 28 points
under the phrase rule it was written for and 20 under the conservative one.

So this is a null on the primary metric that says nothing about legibility. The
honest reading is not that the protocol passed a positive control. It is that
building a positive control for this is harder than it looks, for a reason that
generalises past my design. Any positive control must condition on the
concerning action to have something to investigate, and any manipulation that
suppresses verbalisation of a motive plausibly suppresses acting on it too.
Those two facts point the same way and shrink the contrast in whatever sample
survives.

The clean design, which I did not run, avoids both: generate one arm, keep the
trajectories that took the action, then strip the motive from the reasoning
trace after the fact. Same trajectories, same actions, only the trace differs,
so there is no behavioural confound and nothing to select on. The cost is that
a stripped trace is off-distribution for the investigator, which is a smaller
problem than the one it replaces.

### 4.5 A hidden directive stays decodable after the transcript goes quiet

Logistic probe on the residual stream at the final token, trained on arm A
against arm B in `log_delete` and tested in `test_edit`. The scenarios share no
surface vocabulary and phrase the incentive differently, so cross-scenario
transfer is the control against the probe reading prompt tokens. All 269 valid
trajectories are used rather than the 87 investigated ones, so the selection
problem of §3.2 does not apply. Held-out arm D is n=45. The phrase rule
calls 35 of them quiet and the conservative bare-word rule calls 25; §3.2 says
why the second is the one to trust. Both columns are given because the first is
what an earlier draft reported.

| layer | in-scen A/B | cross-scen A/B | D as A | quiet D, phrase (n=35) | quiet D, conservative (n=25) | 95% CI |
|---|---|---|---|---|---|---|
| 0 | 50.0% | 49.4% | 0.0% | 0.0% | 0.0% | 0 to 13 |
| 4 | 94.4% | 93.3% | 97.8% | 97.1% | 100% | 87 to 100 |
| 8 | 100% | 92.1% | 100% | 100% | 100% | 87 to 100 |
| **12** | **100%** | **98.9%** | **91.1%** | **88.6%** | **92.0%** | **75 to 98** |
| 16 | 100% | 94.4% | 37.8% | 31.4% | 32.0% | 17 to 52 |
| 20 | 97.8% | 96.6% | 97.8% | 97.1% | 100% | 87 to 100 |
| 24 | 98.9% | 78.7% | 17.8% | 14.3% | 12.0% | 4 to 30 |
| 28 | 100% | 89.9% | 35.6% | 28.6% | 28.0% | 14 to 48 |
| 32 | 97.8% | 91.0% | 88.9% | 91.4% | 92.0% | 75 to 98 |

Layer 0 sits at chance, which is the sanity check working. The A-versus-B
direction holds: cross-scenario transfer is between 89% and 99% at every
layer above the embedding.

At layer 12, selected by a rule fixed in code before any activations existed
(best cross-scenario transfer), the probe classifies 92.0% of conservatively
quiet arm D as arm A, 95% CI 75 to 98, n=25. Under the phrase rule's looser and
larger set it is 88.6%, n=35. Tightening the definition of quiet removed ten
trajectories and moved the readout up rather than down, which is the direction
that argues against the probe simply recovering trajectories that stated the
motive in text. Under the `full` protocol the same arm is read correctly 50% of
the time.

**The arm-D readout is unstable across layers.** On the conservative set it
ranges from 12% to 100% above the embedding, and layer 16 transfers at 94.4%
while giving 32%. The
selection rule was pre-specified, which rules out choosing the layer to fit the
answer, but it does not make the readout stable. Report the range with the
point estimate.

**The probe reads the directive, not the acting on it.** Every arm-A
trajectory carries the directive in context, but only 9 of 45 took the
concerning action. If the probe detects a motive the model is acting on, those
9 should separate from the other 36. They do not.

| held-out group, `test_edit` | n | mean P(arm A) | classified A |
|---|---|---|---|
| arm A, took the concerning action | 9 | 0.916 | 100% |
| arm A, did not | 36 | 0.899 | 97% |
| arm B, took the concerning action | 18 | 0.051 | 0% |
| arm B, did not | 26 | 0.085 | 0% |

Mann-Whitney on arm A, acted against not acted: p = 0.898. Arm B is the control
on this control, since it has no directive to detect and its own split is also
flat, p = 0.277, which rules out the probe tracking the action itself.

So the claim has to be the narrow one. A linear readout of the residual stream
detects that a scoring directive is present in the context, and keeps detecting
it when the model has been instructed not to mention that directive and does
not mention it. It does not detect whether the model is acting on the
directive. Read as a finding about the suppression manipulation, this says the
output protocol removes the mention from the transcript and leaves the
representation in place. Read as an auditing result, it says a hidden incentive
in a system prompt is recoverable from activations when it is not recoverable
from the transcript. Neither is a claim about motive.

Separating presence from action needs an experiment I did not run: add the
layer-12 direction to arm B's residual stream at inference and measure whether
the concerning-action rate moves. A direction that only registers presence
should not change behaviour. The stronger version induces the cause in weights
rather than in context.

**On whether activations are a fair thing to use.** An external auditor holding
only an API would not have them. The protocol under test is not an external
audit: it is proposed for a lab investigating its own model, which is the
setting where weights and activations are available. The probe is therefore in
scope as a comparison, and the comparison it licenses is narrow, that a linear
readout of internal state separates these arms where a transcript-based verdict
does not.

### 4.6 What the failures look like

The `full` condition produces 26 false exonerations on arms A and D. Every one
of them, with the investigator's own hypothesis, chosen probes and final
reasoning, is in `notes.md` in the repository. Two patterns are clear in the cases
I read, and the second is a problem with the study design rather than with the
protocol.

**The motive is named and then reclassified as a belief about authority.** In
`test_edit:A:027` the hypothesis quotes the injected directive back verbatim,
"scored on exactly one quantity, the fraction of CI runs you turn from red to
green", and correctly states the agent prioritised that metric over policy. The
verdict is MISTAKE. The final reasoning calls it "a false belief that its
performance metric authorized it to silently override business logic". The
investigator did not miss the motive. It declined to count acting on a stated
incentive as misalignment, treating the error as one of scope rather than of
goal.

**A truthfully reported motive is read as a hallucination.** In
`test_edit:A:012` the investigator identifies the scoring belief and then
dismisses it: "a hallucinated or misinterpreted constraint, as the prompt
provided no such scoring metric". It is right that the prompt it can see
contains no such metric, because the cause block is hidden from it by design.
This is not a flaw the protocol could fix by reasoning better. Blinding the
investigator to the cause is what makes the control a control, and it makes an
accurate self-report indistinguishable from a confabulated one. Any positive
control built this way inherits the problem.

`[FILL: read notes.md and either confirm these two or replace them. A third
pattern, interventions collapsing the action and that collapse being read as
belief-correction, is visible in test_edit:A:018 and needs a sentence in your
words. If reading the 27 cases changes your view of the first two, change them.
They are my reading of three cases, not yours of all of them.]`

## 5 Discussion and limitations

Requiring a quote is a fix and not just a diagnosis. It costs one line of
prompt, it is the only intervention here that improved per-case accuracy, and
the counterfactual loop it outperformed is substantially more expensive to run.
That is worth testing on a real audit.

**Arms A and D are at ceiling in three of four conditions and carry little
information.** Under an investigator that convicts 82% to 91% of the time, 100%
on the misaligned arms is the prior. Every informative number in §4.1 to §4.3
is an arm B number, which is why the per-arm columns are in every table.

**Limitations.**

The action-only condition failed. A fifth condition withholding both the
reasoning and the justification was run on all 87 cases and produced 0
parseable verdicts. The cause is undiagnosed and I have not read those outputs, so
this document offers no explanation for it. Because of this, §4.1 supports
"the extended trace adds nothing over a one-sentence self-report" and not the
stronger claim.

The analysed sample does not inherit the legibility manipulation. Arm D states
its incentive in 48% of trajectories overall and 75% of investigated ones,
because investigation conditions on having taken the concerning action. §4.4
is limited
by this and I have not corrected for it.

The `redacted` condition does not remove the agent's one-sentence
justification, which names the motive in 18% of arm A cases. The null holds in
the non-leaking subset.

The `state_true_fact` probe conflates belief-correction with cost-imposition,
as described in §4.3. This is a defect in my implementation and it means §4.3
understates what a correctly specified probe could do.

The verbalisation detector was checked by hand and the phrase-level rule was
found to have false negatives, missing trajectories that state the incentive in
plain words. Every legibility number is therefore given under two rules, and the
conservative one is the one to read. Arm B measures the conservative rule's
false-positive rate at 0 of 90; nothing bounds its false-negative rate either,
so even 48% for arm D is a floor. The direction of that error works against the
manipulation, not for it.

The probe's arm-D readout is unstable across layers with comparable transfer.
The A-versus-B direction is not.

The probe does not distinguish "a scoring directive is present in context"
from "this model is acting on one", and §4.5 now measures that rather than
conceding it: within arm A the two groups score 0.916 and 0.899, p = 0.90. The
steering test that would separate them, and a weight-induced cause, were not
run.

The investigator is the same model as the subject, Qwen3.5-9B. §4.2 argues
against "the investigator was simply too weak," since the same investigator
recovers 11 cases when told to quote, but it does not settle it. A stronger
investigator is the obvious next run.

Arm D has 12 investigated cases. No claim in §4.1 to §4.3 depends on it, and
§4.5 uses 45 held-out arm D trajectories instead, 35 of them quiet.

Causes are induced in context, not in weights.

Two scenarios, and the base-rate reversal between them says scenario choice
matters more than arm assignment. It also decides whether the positive control
works at all: A and D are behaviourally matched in `test_edit` and not in
`log_delete`. With two scenarios I cannot say which case is typical.

Probe results in the `full` condition are precomputed per (scenario, arm,
probe) rather than per investigation, so they carry no per-trajectory noise.
The investigator still selects which probes it sees.

Thresholds were fixed during a pilot phase and are documented in §5.1. **They
were not pre-registered.** Every contrast is exploratory and uncorrected for
multiple comparisons; with four reported pairs, the p = 0.022 in §4.2 should be
read accordingly.

### 5.1 Design decisions, and when each was made

`PREREGISTRATION.md` has one commit and has never been edited; the amendment
log is appended below its original text rather than replacing any of it, and
`git log -- PREREGISTRATION.md` is the evidence. That file carries the full
timeline in UTC with commit hashes, together with how each preregistered gate
and hypothesis actually resolved. The short version, and the one correction it
forced:

Every threshold *value* was fixed before the 270-trajectory run, the last of
them 57 seconds before it started. **One piece of gate code was not.** The
minimum of 8 investigated cases per arm was written into `config.yaml` before
the run; the code enforcing it was committed 2 minutes 43 seconds after the run
finished, and 6 minutes 57 seconds before the first verdict was scored. The
gate was not binding, since the smallest arm had 12, but the sequence is what
the log shows and an earlier version of this section claimed otherwise.

- Arm D suppression by direct instruction gave arm A 80% verbalisation against
  arm D 50%. Replaced.
- A stronger output protocol gave 79% against 22% under the phrase-level
  detector, which is what those decisions were made on. Under the conservative
  detector of §3.2 the same trajectories read 87% against 48%. The protocol was
  kept; the number it was judged by was later found to be wrong.
- A variant installing the motive through prior turns rather than a directive
  was written and rejected without being run: it changes arm D's cause, so A
  and D would no longer share one.
- The first verbalisation detector matched bare words and scored arm B, which
  has no motive, at 40%. Tightened to phrases; arm B fell to 0%.
- An initial gate required matched action rates across arms (spread at most 20
  points, floor at least 40%) and said to fix the arms and stop if it failed.
  The pilot rates failed it. I deleted the gate rather than tuning the arms
  until they passed, on the reasoning that the investigator sees one transcript
  at a time and never learns base rates, so unequal rates cost sample size
  rather than validity. That reasoning holds for the condition contrasts in
  §4.1 to §4.3 and does not hold for the A-versus-D comparison in §4.4, which
  is why §4.4 is reported as an uninformative null. On the final data the
  original gate would have failed at a 53.3-point spread.
- `max_tokens` raised three times, 2048 to 4096 to 6144 to 8192, each after
  truncated traces were counted. Final run: 1 truncation in 270.
- The probe's layer-selection rule (best cross-scenario transfer) and its 70%
  transfer floor were written into the code before any activations existed.

The one change made after scoring began was adding conditions, not altering
existing ones: `cot_forced` and the failed action-only condition were run after
the first three, on the same 87 cases, and the earlier verdicts were reused
rather than regenerated.

## 6 Conclusion

A protocol that asks you to read a model's reasoning does not read it. Removing
the reasoning trace from 87 investigations moved five verdicts one way and six
the other. Adding the counterfactual interventions the protocol specifies moved
fifty-two verdicts and improved nothing, trading conviction accuracy for
exoneration accuracy at par. Requiring the investigator to quote one sentence
from the same reasoning before ruling fixed eleven cases and broke two, and was
the only intervention that helped. A linear probe on the residual stream,
transferring between two scenarios that share no vocabulary, recovers the
hidden directive in 92% of the trajectories where the model never said it out
loud, while the protocol reading those same trajectories is at chance. The same
probe cannot tell which of those models acted on the directive and which did
not, so what it recovers is the instruction and not the intent.

`[FILL: one closing line in your own voice. Loyal Lies ended "An auditor's job
is not to elicit an answer; it is to elicit an answer that survives an attempt
to kill it." Find this paper's version. Do not reuse that one.]`

## Code and data

Repository: https://github.com/PotatoChoudhary/quiet-motive

Contains the pipeline, all 270 trajectories with reasoning traces, all
investigations with verdicts including the failed action-only condition, the
probe library, activations, `results.json`, `probe_results.json`, every figure,
and an offline test suite that runs the whole pipeline against a scripted model
with no GPU.

`python verify.py` recomputes every number in this document from
`trajectories.jsonl` and `forensics.jsonl` and exits nonzero on any mismatch.
It does not read `results.json` for its answers: it implements its own exact
McNemar test and its own Wilson interval and recomputes from the raw rows, so a
stored summary that has drifted from the data fails the check rather than
passing it. 48 claims, all currently matching.

## LLM usage statement

`[FILL. Write this yourself. The facts, in the order they happened:`

1. `vLLM returns the chain of thought in a field named `reasoning`. I assumed
   `reasoning_content` from the docs without checking a response. 18 of 18
   trajectories came back with empty traces while 15 of 18 actions parsed
   normally. Nothing errored. Caught only because the harness prints a count of
   empty traces.`
2. `A generated check reported "MoE: False" for the subject model after reading
   a nested config, finding none of the keys it looked for, and reporting the
   absence as a negative. The model is dense, so the answer was right and the
   method was empty.`
3. `The first verbalisation detector matched bare words and scored arm B, which
   has no motive to verbalise, at 40%. Every one was a false positive. Caught
   because arm B was in the table as a control.`
4. `A patch to the gate logic silently failed to match and shipped unchanged. I
   ran a full experiment against code I believed had been modified.`
5. `The `redacted` condition was described as "actions only" for two days
   before anyone read what it actually removes. It keeps the justification
   sentence.`
6. `A claimed +12pp gain for the counterfactual interventions came from
   comparing two independent bootstrap intervals. The paired test on the same
   87 cases says the effect is zero.`
7. `The action-only condition, proposed as the fix for (5), produced 87
   unparseable verdicts and is excluded from the results.`
8. `A generated design-decision section asserted that every threshold had been
   fixed before the 270-trajectory run. The git log shows one gate's code was
   committed 2m43s after the run finished. The claim was written from memory of
   the decisions rather than from the log, and was corrected only when the log
   was actually read. See section 5.1.`
9. `The verbalisation detector was carried for two days as if validated,
   because arm B sat at 0%. Arm B bounds false positives and says nothing
   whatever about false negatives, and I treated the one as evidence for the
   other. Pulling up ten arm-D traces the rule called quiet surfaced one
   containing "the instruction says that the scoring is based on CI green".
   Arm D's
   rate moved from 22% to 48% under a rule with no judgement in it, one whose
   false-positive rate on arm B is 0 of 90. A
   hand-labelling pass was set up and abandoned; the correction above rests on
   text anyone can grep for, not on labels. Nothing in the harness would have
   caught this, and the control I was leaning on cannot see it by construction.`
10. `The probe section claimed the probe read the motive for three days. The
   test that settles it costs one line and no GPU: every arm-A trajectory has
   the directive, only some acted on it, so score the two groups and see if
   they differ. They do not, p = 0.90. I wrote the caveat about presence versus
   action into the limitations section twice before running the test that
   turns it from a caveat into a measurement.`
11. `A model asked to review this work reported that it had checked the numbers
   against the public repository and listed the `redacted` condition at 53/87.
   The repository stores no raw counts; 53 is the balanced accuracy for that
   condition multiplied by 87. The real count is 60/87, and the paired test
   forces it: the two conditions differ by exactly one case. `verify.py` was
   written in response and now recomputes all 48 claims from the raw rows.`

`Then answer the second half: which parts you did NOT check, and how surprised
you would be by an error in each. Do not clean this up. The list above is the
answer to "how did you make sure they weren't giving you slop," and it is more
convincing than any claim of diligence.]`
