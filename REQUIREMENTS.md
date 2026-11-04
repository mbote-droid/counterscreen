# REQUIREMENTS.md — numbered requirements and how each is verified

`PROTOCOL.md` §13 places this in **Could**, below the false-accept-rate
measurement, and is explicit that if forced to choose, measure the
false-accept rate. It is written here because most requirements were already
verified by construction while the packages were built, so the cost is
recording what exists rather than creating new work.

Each requirement is a testable statement with a verification method and its
current status. **Verified** means a test asserts it and that test passes.
**Pending** means the requirement is real and the verification does not exist
yet, usually because it needs a GPU, returned data, or a source this
environment cannot reach.

A requirement with no verification method is not a requirement; it is a wish.

---

## G · Gating and geometric validity

| ID | Requirement | Verification | Status |
|---|---|---|---|
| G-01 | G0 shall reject a structure with consecutive Cα beyond 4.5 Å | fixture with a known chain break | **verified** |
| G-02 | G0 shall reject clashing heavy atoms that are not bonded neighbours | two chains overlapped by 0.4 Å | **verified** |
| G-03 | G0 shall reject Ramachandran outliers at or above 1% | fixture at φ = ψ = 0 | **verified** |
| G-04 | G0 shall **not** reject experimentally determined coordinates | every prepared target passes | **verified** (see F-9) |
| G-05 | G0 shall reject non-L chirality | mirrored structure; improper dihedrals negate | **verified** |
| G-06 | G0 shall reject cis-peptides except before proline | ω = 0 chains with and without proline | **verified** |
| G-07 | Gates shall run cheapest-first, geometry before any fold | ordering asserted to be non-decreasing in `effective_tier` over every pair of gates | **verified** — amendment A10; the last departure, G8 after co-folding, was removed |
| G-08 | A gate without an evaluator shall refuse to run, never skip | parametrised over all ten gates | **verified** |
| G-09 | A design shall not be folded unless G0 passed it | adapter never reached for unstamped design | **verified** |
| G-10 | G2's operating point shall not be settable from configuration | unknown-key error on `g2_confidence` | **verified** |
| G-11 | Every funnel table in prose shall list the gates in the order they run | `tests/contract/test_funnel_documents.py` | **verified** — both tables were out of order before A10 (`BUILD_JOURNAL.md` ISSUE-018) |

## T · Targets

| ID | Requirement | Verification | Status |
|---|---|---|---|
| T-01 | T+ shall be 7OW6 chains A/B/C with the TCR removed | chain composition; no TCR chains | **verified** |
| T-02 | D1 shall use real 7OW5 coordinates, not a mutated T+ | backbones differ across the whole groove | **verified** |
| T-03 | T+ and D1 peptides shall differ at position 6 alone | computed from the prepared targets | **verified** |
| T-04 | Disulfides shall survive preparation | ≥2 found in each prepared target | **verified** |
| T-05 | Truncation boundaries shall be recorded in configuration | script takes config; no constants | **verified** |
| T-06 | Truncation shall not move the peptide | CA RMSD 0.000 Å against the full complex | **verified** |
| T-07 | The platform construct shall drop β2m and the α3 domain | chains {A, C}, ≤200 residues | **verified** |

## S · Scoring and ranking

| ID | Requirement | Verification | Status |
|---|---|---|---|
| S-01 | Margins shall be target minus decoy, never the reverse | per-seed and mean asserted | **verified** |
| S-02 | Pooled SD shall be computed within a design, never across | structural; plus level-shift invariance | **verified** |
| S-03 | M_mut shall read the wild-type decoy and M_pep the peptide-free one | roles addressed by name | **verified** |
| S-04 | Margins shall pair by seed identity, not list position | mismatched seed sets refused | **verified** |
| S-05 | The G4 gate shall be one-sided | large negative margin fails | **verified** |
| S-06 | Margins shall be antisymmetric | property test over generated inputs | **verified** |
| S-07 | Gates shall be monotone in their inputs | property test | **verified** |
| S-08 | No weighted composite shall be constructible | signature carries nothing weight-shaped | **verified** |
| S-09 | ΔΔG_spec shall not affect ranking outside M1 | varied on M2/M3; order unchanged | **verified** |
| S-10 | REU shall not be combinable with kcal/mol | type error and runtime `TypeError` | **verified** |
| S-11 | The pooled SD used by G4 and the tie tolerance shall be one defined quantity | `tests/unit/test_noise.py`, `tests/property/test_margin_properties.py` | **verified** — amendment A9; `NoiseFloor` is required by `exceeds_noise` and by `rank_arm`, so neither reading can be selected by omission |

## E · Evaluation and controls

| ID | Requirement | Verification | Status |
|---|---|---|---|
| E-01 | A control seeded from a crystal pose shall be refused | panel validation names the offenders | **verified** |
| E-02 | Control difficulty shall be computed from sequences | all nine panel entries asserted | **verified** |
| E-03 | A negative control shall carry its registered failure gate | construction refuses without one | **verified** |
| E-04 | Negative derivation shall be deterministic under a seed | same seed, same sequence | **verified** |
| E-05 | The panel shall be measured against the floor of 5 | floor report; panel supplies 1 | **verified** |
| E-06 | Stage −1 shall produce a false-reject rate with an interval | — | **pending** — needs the panel folded |
| E-07 | The filter shall have a measured false-accept rate with an interval | — | **pending** — needs the full pipeline |
| E-08 | No target shall appear in both train and test splits | — | **pending** — needs the evaluation set |

## P · Provenance and reproducibility

| ID | Requirement | Verification | Status |
|---|---|---|---|
| P-01 | Design identity shall derive from sequence content | stable across processes | **verified** |
| P-02 | The provenance manifest shall be appended, never overwritten | first entry's bytes survive the second | **verified** |
| P-03 | Manifest output shall not depend on dict order | two orderings, byte-identical files | **verified** |
| P-04 | An uncommitted tree shall be recorded, not hidden | dirty flag round-trips | **verified** |
| P-05 | `analyze/` shall never write into `results/raw/` | direct, traversal and subdirectory writes refused | **verified** |
| P-06 | Returned measurements shall not be rewritten in git | append-only gate; negative test tampers and fails | **verified** |
| P-07 | A re-fitted K_D shall carry an uncertainty | non-finite standard error refused | **verified** |
| P-08 | Specificity ratios shall propagate uncertainty, not divide points | multiplicative interval; log-symmetric | **verified** |
| P-09 | The execution image digest shall be recorded at run time | — | **pending** — needs a GPU run |

## R · Reporting

| ID | Requirement | Verification | Status |
|---|---|---|---|
| R-01 | Every number in a generated document shall resolve to a result file | unknown key reported with its line | **verified** |
| R-02 | A bare numeral outside a key shall fail the build | one test per allowed exclusion | **verified** |
| R-08 | A hand-typed confidence level shall fail the build | `95% CI` in prose is reported as a bare numeral | **verified** — the exclusion was removed (`FINDINGS.md` F-4) |
| R-09 | A registered constant shall be citable without a result file, and a result file shall not redefine one | `[[ci.level]]` resolves against `{}` and is not shadowed | **verified** |
| R-10 | The interval's confidence level and its normal quantile shall not be able to disagree | quantile derived from the level; coverage recomputed in a test | **verified** |
| R-03 | A result newer than the document shall fail the build | mtime comparison | **verified** |
| R-04 | Metrics shall round to a fixed significance | 6 significant digits | **verified** |
| R-05 | The funnel shall balance stage to stage | unbalanced funnel refused at construction | **verified** |
| R-06 | Funnel counts shall never increase down the cascade | asserted | **verified** |
| R-07 | Quality metrics shall be reported as distributions | median, quartiles, range, count passing | **verified** |

## A · Architecture

| ID | Requirement | Verification | Status |
|---|---|---|---|
| A-01 | Package boundaries shall be enforced, not documented | 12 import-linter contracts | **verified** |
| A-02 | Every package shall be named by a contract | contract coverage test | **verified** |
| A-03 | No package shall exist outside the dependency table | set equality against `DESIGN.md` §1 | **verified** |
| A-04 | The Python pin shall agree in all four places that state it | consistency test | **verified** |
| A-05 | The image shall build and its entrypoint run | CI job | **verified** |

---

## Coverage

| | Count |
|---|---|
| Verified | 57 |
| Pending | 4 |
| **Total** | **61** |

Every pending requirement is blocked on something this environment cannot
supply: a GPU, returned experimental data, or an unreachable source. None is
pending for want of effort. S-11, the one specification ambiguity on the list,
was settled by amendment A9 on 4 November 2026 rather than left for the
campaign to resolve at the keyboard.
