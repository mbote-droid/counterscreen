# counterscreen

**Specificity-first protein binder design. Every design is scored against its
target *and* its near-identical decoys, and ranked on the gap between them.**

---

## The problem

A binder that grips its target tightly, and grips a near-identical decoy just
as tightly, has not solved the problem it was posed. For a point-mutant
neoantigen that distinction is the whole therapeutic question: the mutant is
confined to tumour cells while the wild-type complex is presented across
healthy tissue, so a binder that cannot tell them apart is not a candidate
drug, whatever its affinity.

Nearly every published design pipeline ranks on confidence or predicted
affinity **against the target alone**. This one ranks on the margin between
target and decoy, and treats affinity as a constraint.

## Two deliverables

**1 · A design campaign.** Entries into open protein-design competitions that
provide free wet-lab validation, producing experimentally measured results
published openly. Campaign 1 targets the KRAS G12D neoantigen `VVVGADGVGK` on
HLA-A\*11:01, against the wild-type peptide differing at a single position and
against the peptide-free complex.

**2 · A pre-registered evaluation study**, and the more valuable of the two:

> Can in-silico filters resolve single-residue binding specificity at all?

Answered with a measured **false-accept rate for the filter itself**, with a
confidence interval. To our knowledge no published de novo binder design
pipeline reports one.

## Status

**Scaffolding and analysis complete; no designs generated, no models run, no
results.** Nothing in this repository should be read as a finding about a
binder.

What exists and is verified: twelve packages, 407 tests, `mypy --strict`, and
twelve architecture contracts that make the dependency rules executable rather
than aspirational. What does not: anything requiring a GPU.

## What has been found so far

These are observations on crystal structures solved by others, reproduced here
with stated methods and caveats. They are recorded in full, with evidence
class, in [`FINDINGS.md`](FINDINGS.md).

**The discriminating residue is largely unreachable.** The mutant aspartate's
carboxylate is coordinated bidentately by HLA Arg114 (2.95 Å, 3.04 Å) with
Gln70 capping the second oxygen. Solvent accessibility is **6.4 Å² on OD1 and
0.0 Å² on OD2** — the residue is roughly 85% buried.

**The only known discriminator never touches it.** The engineered TCR in 7OW6
comes no closer than **7.51 Å** to that carboxylate. Instead the substitution
displaces peptide position 6 by 0.96 Å, propagating 0.78, 0.51 and 0.64 Å to
positions 7–9, which carry *no sequence difference* but are the solvent-exposed
ones — and 18 of the TCR's 29 peptide contacts land on position 7.

Discrimination is therefore available **indirectly**: read the geometry of the
accessible positions, not the chemistry of the buried one. That measurement
inverted the design allocation before any compute was spent on it.

## How this repository thinks

**Specificity is the objective, affinity is a constraint.**

**Thresholds are registered as rules, not values.** Where a threshold must be
calibrated from data, the derivation rule is fixed in advance and the number
it produces is whatever it produces. The confidence operating point has no
configuration field at all, so importing a literature cutoff is not a
discouraged practice but an unknown-key error.

**The filter is measured, not asserted.** Deliberately invalid designs are
pushed through the complete ranking and the false-accept rate reported with an
interval. Positive controls give a false-reject rate with a rule-of-three
bound.

**Cheap checks run first.** Geometric validity costs seconds and catches
non-physical structures that confidence scores miss entirely. It gates every
GPU stage, and the code refuses to fold a candidate that has not passed it.

**The funnel is always reported.** Generated, passed each filter, selected.
Distributions, never point values.

**No number is typed by hand.** Every figure in a generated document resolves
mechanically to a result file, checked in CI.

**Failures are deliverables.** The findings log, the decision record and the
limitations sections are outputs, not scaffolding.

**Claims are calibrated.** A computational screen licenses no claim about
binding. Predicted margins are labelled predicted, every time.

## Reading order

| File | What it is |
|---|---|
| [`FINDINGS.md`](FINDINGS.md) | What measurement changed about the design, with evidence class per finding |
| [`DECISIONS.md`](DECISIONS.md) | Why each method was chosen, and what was discarded on the way |
| [`PROTOCOL.md`](PROTOCOL.md) | The scientific specification: targets, gates, mechanisms, objective function |
| [`DESIGN.md`](DESIGN.md) | Architecture, package boundaries, reproducibility constraints that are real rather than aspirational |
| [`PREREGISTRATION.md`](PREREGISTRATION.md) | Thresholds and ranking rules as parameter-free derivation rules, with every amendment dated and reasoned |
| [`METHODS.md`](METHODS.md) | Scientific write-up |
| [`REFERENCES.md`](REFERENCES.md) | Every cited number, with a confidence label on each source |
| [`AGENT_ERRORS.md`](AGENT_ERRORS.md) | Errors made during the build, classified by how each was caught |
| [`BUILD_JOURNAL.md`](BUILD_JOURNAL.md) | Dated issues: symptom, diagnosis, fix, regression test |

## Running it

```bash
make setup     # locked environment, Python 3.12
make check     # lint, types, architecture contracts, tests
```

Everything above runs on CPU with no network and no model weights. The
generative and folding stages are driven as external processes behind
adapters, so the package stays installable and fully testable without a GPU.

## Licence

Code is MIT ([`LICENSE`](LICENSE)). Documentation is CC-BY-4.0
([`docs/LICENSE`](docs/LICENSE)). Per-source data terms, and the sources not
yet cleared for ingestion, are recorded in [`DATA.md`](DATA.md).
