# Campaign report — KRAS G12D / HLA-A*11:01

**Status: template.** Generated from the result files by `report/`; not
hand-edited. Every number below is written as a key and resolved mechanically,
and the claim checker fails the build on any key without a matching entry, any
bare numeral outside a key, or any result file newer than this document.

Literature values are the one exception and carry an `[Rn]` marker tying them
to `REFERENCES.md`.

---

## Objective

Design a binder for the KRAS G12D 10-mer `VVVGADGVGK` presented by
HLA-A\*11:01 that does **not** bind the wild-type complex `VVVGAGGVGK`,
differing at position 6 alone, nor the peptide-free complex. Specificity is
the objective; affinity is a constraint.

## Funnel

`PROTOCOL.md` §12.3a: the drop at each stage is a result in itself.

| Stage | Designs remaining |
|---|---|
| Generated | `[[funnel.generated]]` |
| Passed G8, submission constraints | `[[funnel.g8]]` |
| Passed G0, geometric validity | `[[funnel.g0]]` |
| Passed G1, self-consistency | `[[funnel.g1]]` |
| Passed G5, hydrophobic patch | `[[funnel.g5]]` |
| Passed G2, confidence | `[[funnel.g2]]` |
| Passed G3, peptide contact | `[[funnel.g3]]` |
| Passed G4, margin above noise | `[[funnel.g4]]` |
| Passed G6, no buried unsatisfied charges | `[[funnel.g6]]` |
| Passed G7 and G9, sequence and structural novelty | `[[funnel.g79]]` |
| After diversity clustering | `[[funnel.clustered]]` |
| Submitted | `[[funnel.submitted]]` |

## Specificity margins

Reported as distributions, never point values.

| Margin | Median | IQR | Passing G4 |
|---|---|---|---|
| M_mut | `[[margins.m_mut.median]]` | `[[margins.m_mut.q1]]`–`[[margins.m_mut.q3]]` | `[[margins.m_mut.passing]]` |
| M_pep | `[[margins.m_pep.median]]` | `[[margins.m_pep.q1]]`–`[[margins.m_pep.q3]]` | `[[margins.m_pep.passing]]` |

Per amendment A9, G4 divided each margin by the larger of the campaign noise
floor and that design's own pooled seed SD.

| Quantity | Value |
|---|---|
| Campaign noise floor, from the Day-1 repeats | `[[noise.campaign_sd]]` |
| Repeats it was measured from | `[[noise.repeats]]` |
| Designs whose own seed SD exceeded the floor | `[[noise.above_floor]]` |
| Ranking tie tolerance, `0.5 ×` the floor | `[[noise.tie_tolerance]]` |

## Mechanism allocation

Amendment A7 inverted the registered allocation on structural evidence
(`FINDINGS.md` F-5, F-6) before any design was generated.

| Arm | Allocated | Submitted |
|---|---|---|
| M1 direct electrostatic | 4 | `[[allocation.m1]]` |
| M2 composite surface | 5 | `[[allocation.m2]]` |
| M3 conformational selection | 9 | `[[allocation.m3]]` |
| Affinity-only control | 1 | `[[allocation.control]]` |
| Reserve | 1 | `[[allocation.reserve]]` |

The comparison between arms is **exploratory** and is not reported as a
result: at n = 20 and a base rate near 27% [R14] each arm yields two or three
hits at best.

## Filter validation

| Quantity | Value |
|---|---|
| False-reject rate, positive controls | `[[frr.failures]]` of `[[frr.n]]`, upper bound `[[frr.upper]]` |
| False-accept rate, adversarial designs | `[[far.point]]` (`[[ci.level]]` CI `[[far.ci_lo]]`–`[[far.ci_hi]]`) |
| Code mutation score | `[[mutation.score]]` |

Adversarial sample size was registered before running: 10 per class, 40 total
(`PREREGISTRATION.md` §7b).

## Claim discipline

Computational results in this document are predictions and are labelled as
such. No claim is made that any design binds its target; that claim requires
experimental measurement. Where results are returned, the defensible statement
without an orthogonal method and an interface-mutant control is that a design
shows target-dependent signal in a named assay, not that it binds.
