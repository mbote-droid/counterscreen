# Adversarial log

`PROTOCOL.md` §12.3: from day one, record every instance where the pipeline
produces something that should not be possible — inputs, seeds, package
versions, full output. At the end, test whether each reproduces
systematically.

> **Discovered-by-accident is an anecdote. Discovered-by-protocol is a
> finding.** "I noticed X sometimes happens" is a blog post. "X occurs in n of
> N cases under condition C, here is the mechanism, here is a test that detects
> it, here is the confidence interval" is research.

**Status: no entries.** Nothing has been run that could produce an impossible
output. The pipeline has generated no designs and called no model. This file
exists so that the first such observation is recorded when it happens rather
than reconstructed afterwards, which produces a tidy narrative instead of a
record.

Geometric and arithmetic defects found while building the pipeline itself are
not adversarial outputs and live in `BUILD_JOURNAL.md`; errors in reasoning
live in `AGENT_ERRORS.md`; measurements that changed a decision live in
`FINDINGS.md`.

---

## Entry template

```
### ADV-00n · one-line symptom · date

**Observed.**      what the pipeline produced that should not be possible
**Inputs.**        design id, target, seed, model and weights checksum
**Environment.**   image digest, package versions, GPU
**Output.**        the full artefact, or its path under results/
**Reproduces.**    n of N attempts under condition C
**Mechanism.**     why it happens, or 'not established'
**Detection.**     the test that now catches it, or 'none yet'
```

## Candidates to watch for

`PROTOCOL.md` §12.3 lists these for orientation. There is no existing
catalogue of them, and assembling one would itself be a contribution. Each is
a hypothesis about this pipeline until observed in it.

| Candidate | What would count as an observation here |
|---|---|
| Predictors are systematically over-confident on designed backbones, with direction rather than noise | Control panel confidence on designs exceeding that on experimentally solved binders of comparable quality |
| Adversarial designs reach high pLDDT and do not bind [R16] | A scrambled or reversed negative passing G1 and G2 |
| The reliability curve inverts above 0.6: designs predicted at 70–80% bound only 28% of the time [R14] | Calibration curve from the Stage −1 panel showing the same inversion |
| Expression failure censors binding labels informatively [R4] | Returned data where non-expressers differ systematically from binders |
| Generators overrepresent helical folds; β-rich architectures are scarce [R17] | Secondary-structure distribution across generated backbones |
| Per-target AUROC intervals frequently include chance [R14] | Any per-target interval in the evaluation study spanning 0.5 |

## The strongest candidate for this project

`PROTOCOL.md` §12.3: 7OW4 has no coordinates for peptide positions 5 and 6 —
the two carrying the entire discrimination signal — and `FINDINGS.md` F-1
confirms this across **all four** crystallographically independent copies, so
the disorder is systematic rather than one modelling choice.

**How a structure predictor behaves when the discriminating atoms are
experimentally undetermined is a specific, genuine and under-characterised
question.** The experiment is available without any design: fold the apo
complex and compare what each model places at positions 5–6 against the
receptor-bound coordinates in 7OW6, across seeds. A model that confidently
places a side chain the experiment could not resolve is making something up,
and the confidence it attaches to that is measurable.

Not yet run; it needs the model stack.
