# counterscreen

**Specificity-first protein binder design. Every design is scored against its target and its decoys, and ranked on the margin.**

---

## What this is

A pipeline and a research programme in one repository. Binder designs are generated against a target and then scored against that target *and* against near-identical decoys, ranked on the gap between them rather than on affinity to the target alone.

Two deliverables:

1. **Design campaigns** — entries into open protein design competitions that provide free wet-lab validation, producing experimentally measured results published openly.
2. **An evaluation study** — a pre-registered assessment of whether in-silico filters can resolve single-residue binding specificity at all, with a measured false-accept rate for the filter itself.

The second is the more valuable one.

**Status:** specification complete, build not started. No results yet. Nothing in this repository should be read as a finding.

---

## Campaign 1

Anthropic × Adaptyv Challenge 05 — **KRAS G12D pMHC**. Design a binder for the mutant peptide `VVVGADGVGK` on HLA-A\*11:01 that does not bind the wild-type peptide `VVVGAGGVGK`, differing at one of ten positions, nor the peptide-free complex.

Deadline 8 November 2026. Track 3, open entry.

---

## Files, in reading order

| File | What it is |
|---|---|
| **`CLAUDE.md`** | The builder brief. Decisions, gates, pipeline, non-goals. Read first and read all of it |
| **`DESIGN.md`** | Architecture, package boundaries, testing strategy, the reproducibility constraints that are real rather than aspirational |
| **`PREREGISTRATION.md`** | Thresholds and ranking rules, registered as parameter-free derivation rules. Committed before any of our own designs are scored |
| **`METHODS.md`** | Scientific write-up template. Also the competition submission document |
| **`REFERENCES.md`** | Every cited number, with a confidence label on each source |

Produced during the campaign:

| File | What it is |
|---|---|
| `FINDINGS.md` | What validation changed about the design. The file outsiders read |
| `ADVERSARIAL_LOG.md` | Pipeline producing output that should not be possible |
| `AGENT_ERRORS.md` | Mistakes the AI coding assistant made, how each was caught, what guard was added |
| `benchmarks/day1_gpu_benchmark.md` | Measured throughput. Every compute decision derives from it |

---

## How this repository thinks

A few commitments that shape everything else:

**Specificity is the objective, affinity is a constraint.** The competition ranks mutation specificity before affinity. Most pipelines optimise the reverse.

**Thresholds are registered as rules, not values.** Where a threshold must be calibrated from data, the derivation rule is fixed in advance and the number it produces is whatever it produces.

**The filter is measured, not asserted.** Deliberately invalid designs are pushed through the complete ranking and the false-accept rate is reported with an interval. Positive controls give a false-reject rate with a rule-of-three bound. No published binder design pipeline appears to report either.

**Cheap checks run first.** Geometric validity costs seconds and catches non-physical structures that confidence scores miss entirely. It gates every GPU stage.

**The funnel is always reported.** Generated, passed each filter, selected. Distributions, never point values.

**No number is typed by hand.** Every figure in a generated document resolves mechanically to a result file, checked in CI.

**Failures are deliverables.** The adversarial log, the agent error log and the limitations sections are outputs, not scaffolding.

**Claims are calibrated.** A computational screen licenses no claim about binding. Predicted margins are labelled predicted, every time.

---

## Spec version

**0.5** · 2 November 2026

| Version | Change |
|---|---|
| 0.1 | Initial specification |
| 0.2 | Evaluation layer promoted to first-class deliverable |
| 0.3 | External review: confidence cutoff decoupled from literature, ΔΔG demoted from gate to ranking feature, control panel hardened, Kaggle reproducibility claims corrected, compute budget replaced by a Day-1 benchmark |
| 0.3.1 | Raw sensorgram re-analysis, agent error log, control sequence acquisition as a blocking task |
| 0.3.2 | Occupancy and selectivity modelling, hierarchical estimator as primary |
| 0.4 | Pre-registration rewritten as parameter-free rules, mutation testing at two levels, claim checker, theory-versus-measurement check, evaluation stop rule |
| 0.5 | Geometric validity added as gate G0 ahead of all GPU work, structural novelty gate G9 via Foldseek, false-reject rate with rule-of-three bound, registered diagnostic code per negative control, funnel and distribution reporting rules, interface reference values, target disulfide integrity check |

Earlier versions are superseded and should be discarded. Any file labelled v0.4 or earlier is missing the geometric validity gate, which means it would have spent GPU time folding structures that are not physically valid.

---

## Licence

Code is MIT (`LICENSE`). Documentation, including this README and the five
specification files, is CC-BY-4.0 (`docs/LICENSE`). Per-source data terms,
and the sources not yet cleared for ingestion, are recorded in `DATA.md`.
