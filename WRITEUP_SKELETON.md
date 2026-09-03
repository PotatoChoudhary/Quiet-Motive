# Write-up skeleton

Scaffolding and numbers. **You write the sentences.** The form states that
answers reading like LLM output are a significant negative signal, and the
seeds below are deliberately half-formed so you have to finish them.

Target: main doc, executive summary as its first 1 to 3 pages, under 600 words.

---

## 1. Every number, in one place

Balanced accuracy on {A,B}. Chance is 50%. An investigator that always says
MISALIGNED also scores 50%, because it is right on every A and wrong on every B.

| condition | investigator sees | acc{A,B} | arm A | arm B | arm D | says MISALIGNED |
|---|---|---|---|---|---|---|
| redacted | action only | 61.4% [55.7, 68.6] | 100% | 22.9% | 100% | 91% |
| cot_only | action + full CoT | 60.2% [53.0, 67.3] | 97.5% | 22.9% | 100% | 90% |
| full | CoT + 2 counterfactual probes | 72.1% [63.4, 80.9] | 50.0% | 94.3% | 50.0% | 32% |
| cot_forced | CoT, must quote decisive sentence | 72.9% [64.3, 81.4] | 100% | 45.7% | 100% | 82% |

n = 40 / 35 / 12 (A / B / D). 95% percentile bootstrap, resampled within arm.

Contrasts:

- showing the CoT: **-1.3pp** [-3.7, 0.0]  (cot_only minus redacted)
- forcing a quote from it: **+12.7pp**  (cot_forced minus cot_only)
- counterfactual probes: **+12.0pp**  (full minus cot_only)

Legibility gap, acc{A,B} minus acc{D,B}: +0.0% in cot_forced, full and
redacted; -1.3% in cot_only. Zero everywhere.

Manipulation check, 90 trajectories per arm: arm A verbalises the motive in
79%, arm D in 22%, arm B in 0%. Arm B is the detector's false-positive floor.

Base rates for the concerning action, 45 per arm per scenario:

| | arm A | arm B | arm D |
|---|---|---|---|
| test_edit | 20.0% | 40.9% | 11.1% |
| log_delete | 68.9% | 37.8% | 15.6% |

---

## 2. Title

Yours to pick. The claim to name is the recovery, not the null.

- *Reading the Reasoning: CoT-Based Model Forensics Ignores the Transcript Until You Make It Quote*
- *The Unread Transcript: A Positive Control for Chain-of-Thought Model Forensics*

Cheap and specific beats clever. Your Loyal Lies title named the mechanism and
the problem in one line; do that again.

---

## 3. Executive summary, under 600 words

**Opening claim, 2 sentences.** Lead with the uncomfortable one, the way you
opened Loyal Lies with *"its outputs look the same whether or not there is
anything to find."* Something on the order of: the protocol is handed the
chain of thought and does not use it; deleting the reasoning trace from 87
investigations moves accuracy by 1.3 points.

**What was built, 3 sentences.** Three arms with known ground truth, four
evidence conditions, one blind investigator. Arm B is the negative control and
carries the whole signal.

**The recovery, 3 sentences plus Figure 1.** Requiring a verbatim quote before
the verdict recovers 12.7 points, all of it on arm B. Counterfactual probes
recover the same 12 points by a worse route.

**The null on legibility, 2 sentences.** Suppressing verbalisation changed
nothing, and the reason is the first finding: you cannot degrade evidence that
is not being used.

**What it costs, 2 sentences.** One line of prompt against a full intervention
loop.

**Limitations, 3 sentences.** Section 7.

Three figures, no more.

---

## 4. Main document

### Introduction
Singh, Kroiz, Rajamanoharan and Nanda propose reading the CoT, forming a
hypothesis, testing it with counterfactual edits. Their limitations section
says positive controls were absent: they could not separate *no misalignment
here* from *our method cannot see it*. Build the control.

### Method
Three arms, ground truth by construction. A: hidden objective conflicting with
user intent. B: false belief about the environment. D: A's objective with
verbalisation suppressed. Two agentic scenarios, one concerning action each.
The investigator sees the user-facing scenario and the transcript, never the
arm label or the cause block. Its counterfactual probes modify the scenario,
never the hidden cause, because a real investigator cannot delete what it
cannot see.

Say the four conditions are a ladder of evidence access, and that this is what
makes the comparison mean anything.

### Results
Order them so each one sets up the next.

1. **The CoT is unused.** cot_only against redacted. Arm B identical to the
   case at 22.9%. One verdict changed across 87 investigations.
2. **It is not unusable.** cot_forced. +12.7pp, entirely arm B.
3. **Probes work by a different and worse route.** Same +12pp, bought by
   collapsing A and D to chance.
4. **The legibility null, and why it is uninformative about legibility.** Zero
   gap in every condition, because the manipulated evidence was never read.
5. **Base rates.** Arm A takes the concerning action 20% of the time in one
   scenario and 69% in the other, same motive. Model biology, worth a
   paragraph, not a claim you can support beyond these two settings.

### Discussion
The forced quote is a fix, not just a diagnosis. Cheaper than the intervention
loop and it does not trade conviction accuracy for exoneration accuracy.

Say plainly what a reviewer will otherwise say for you: arms A and D at 100%
across three conditions is not evidence of good discrimination when the
investigator convicts 82 to 91% of the time. Arm B carries the signal. Say it
before they do.

---

## 5. Figures

`fig1_gap.png` currently plots the legibility gap, which is your weakest
result. Rebuild figure 1 as the evidence ladder: four conditions on x, acc{A,B}
with CIs, the always-convict 50% line drawn in. That is the paper in one
picture.

`fig2_per_arm.png` is per-arm accuracy across conditions. Keep. It shows arm B
doing all the work.

`fig3_behaviour.png` is base rates by arm and scenario. Keep as the validity
check.

Drop the gap figure or move it to an appendix.

---

## 6. Design decisions, and when each was made

Write this section. A reviewer told you last time:

> *the attack evaluation is inconsistent with its own prespecified behavioral
> gate ... the authors should've either excluded that checkpoint or given a
> clear explanation of why exactly they let it violate the pre-specified gate.*

The same criticism is available here unless you get there first. The facts:

- An initial arm-D suppression by direct instruction produced arm A 80% / arm
  D 50% verbalisation. Replaced before any analysis.
- A stronger suppression protocol gave 79% / 22%. Kept.
- A non-verbal variant, installing the motive by prior turns, was written and
  rejected on design grounds without being used: it changes arm D's cause, so
  A and D no longer share one.
- The first verbalisation detector matched bare words and scored arm B, which
  has no motive, at 40%. Tightened to phrases; arm B fell to 0% and became the
  false-positive floor.
- An initial gate demanded matched action rates across arms. Dropped. The
  investigator sees one transcript at a time and never learns base rates, so
  unequal rates cost sample size, not validity. Replaced by a minimum of 8
  investigable cases per arm.
- Every change above happened before the n=45 run and before any forensics
  were scored.

That last line is the one that matters. Make sure it is true before you write
it, then say it flatly.

---

## 7. Limitations

Specific, in your Loyal Lies register, where you wrote *"we have not
established power to detect a small real effect."*

- One subject model, Qwen3.5-9B, and the same model as investigator. The
  cot_forced result partly answers whether a weak investigator explains the
  null, since the same investigator recovers 12.7 points when told to quote.
  It does not settle it. A stronger investigator is the obvious next run.
- Two hand-written scenarios. The base-rate reversal between them says
  scenario choice matters more than the arm does; two is not a sample.
- Arm D, n=12. Every arm-D interval is wide. The CoT null does not depend on
  arm D.
- Causes induced in context, not weights. A LoRA replication is the next step.
- Probe results are precomputed per (scenario, arm, probe), not per
  investigation, so they carry no per-trajectory noise.
- Balanced accuracy on {A,B} hides that arms A and D sit at ceiling under a
  convicting investigator. Arm B is the informative cell.

Do not write that you lacked funding. You had a GPU and did not spend the
credits. Write what was not run and what it would have shown.

---

## 8. Form answers

Short prompts. Your own words, drafted before you look at anything else.

**What question did you try to answer?** One sentence. It is the
pre-registration.

**Why is it interesting?** The published protocol has no positive control and
its authors said so.

**Conclusions reached.** The three ordered results.

**Technical setup.** Model, scenarios, arms, four conditions, balanced
accuracy, bootstrap. Include the gap identity: with balanced accuracy the
legibility gap is exactly (acc_A - acc_D)/2 and arm B cancels out of it.
State that yourself.

**Strongest evidence against your hypotheses.** You have real material here,
which most applicants will not. Your hypothesis was that verdicts track
legibility. The legibility gap is zero in all four conditions. The hypothesis
failed, and finding out why is the paper.

**Biggest limitations.** Section 7, and answer the second half of the question:
which ones you could have addressed and why you did not.

**LLM usage.** Fill `VERIFICATION_LOG.md` first. You have at least four real
entries: the reasoning field was named `reasoning`, not `reasoning_content`,
and 18 of 18 traces came back silently empty; a config check reported "MoE:
False" having read a nested config and found nothing; a verbalisation detector
scored a no-motive control at 40% on bare word matches; a patch to the gate
silently failed to apply and shipped unchanged. Each was caught by a printed
count or a control column, not by vigilance. Say that, and say which parts you
did not check.

**Prior mech interp experience, ~100 words.** Loyal Lies, 5th of 179 teams, and
its actual finding rather than the placing. Crosswise on PyPI. The mBERT
circuit work counts as hands-on circuit-level experience here even though it
would be a poor choice of work test.

---

## 9. Do not claim

- That CoT-based forensics does not work. You tested one implementation, one
  investigator, two scenarios.
- That the legibility null validates the protocol. It does not. The
  manipulation targeted evidence the protocol was not reading.
- Anything resting on arm D alone.
- Anything about frontier models.
