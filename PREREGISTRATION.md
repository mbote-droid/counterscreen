# PREREGISTRATION.md

**Spec version 0.5** · 2 November 2026 · part of a five-file set: `CLAUDE.md`, `DESIGN.md`, `METHODS.md`, `PREREGISTRATION.md`, `REFERENCES.md`

**Commit this file before scoring any of your own designs. Do not edit it afterwards.** Corrections go in an appended amendments section with their own timestamps, never by rewriting what was registered.

Committed: `[DATE]` · SHA: `[filled by git]`

---

## 1. Hypotheses

**H1.** Co-folding confidence metrics can resolve the single-residue difference between KRAS G12D and wild-type peptide presented on HLA-A\*11:01, as measured by a positive specificity margin for known discriminating binders.

**H2.** Ranking designs by specificity margin rather than by target-only confidence produces designs that discriminate the mutant from the wild type.

**H3** (exploratory, not powered). The three discrimination mechanisms M1, M2 and M3 differ in success rate.

---

## 2. Stage −1 pass/fail rule — written before running

`[FILL BEFORE RUNNING. A worked template follows; replace with committed numbers.]`

**Pass** requires all of:
- Positive panel median `M_mut` exceeds `[N]` × the measured within-design seed SD
- At least `[N]` of the `[N]` positive controls show `M_mut > 0`
- Negative panel median `M_mut` does not differ from zero at `[criterion]`
- The invariant-surface control shows `|M_mut| < [threshold]` and `|M_pep| < [threshold]`

**On fail:** abandon neural-primary scoring, switch to physics-primary, and validate that fallback on the same panel before proceeding.

---

## 3. Gate thresholds — fixed before scoring own designs

> **Circularity hazard, and how it is handled.** G2 and G3 are derived from the control panel, so they cannot be registered as numbers today. Registering them as `[FILL]` would mean they are chosen after seeing data — which is exactly where a pre-registration most needs to bind.
>
> **Therefore G2 and G3 are registered as derivation rules with no free parameters.** The rule is fixed now; the number it produces is whatever it produces. Any deviation from the stated rule is an amendment, logged below.

| Gate | Registered as | Form |
|---|---|---|
| **G0 geometric validity** | **Chain break > 4.5 Å between consecutive Cα; Ramachandran outliers ≥ 1%; any clash, non-L chirality, or non-proline cis-peptide** | Fixed rule |
| G1 scRMSD monomer | **2.0 Å, Cα only, after Kabsch, best of 8 sequences; and pLDDT ≥ 80 on refold** | Fixed value |
| G2 confidence operating point | **The confidence value maximising F1 on the Stage −1 control panel. If two values tie, take the higher. Computed once, on the full panel, before any campaign design is scored.** | Derivation rule |
| G3 peptide contact fraction | **The 10th percentile of the peptide-contact fraction achieved by the positive control panel.** | Derivation rule |
| G4 margin vs noise | `M > 2 × pooled within-design seed SD`, SD measured per §5 | Fixed rule |
| G6 buried unsatisfied charges | 0 | Fixed value |
| G7 prescreen | verdict `pass` | Fixed value |
| G8 submission constraints | 10–250 aa, single chain, standard residues, no free Cys | Competition rules |
| **G9 structural novelty** | **Max TM-score against the PDB via Foldseek, below 0.8** | Fixed value, registered now |

Values produced by the G2 and G3 rules, recorded after Stage −1 and not editable thereafter:

| Gate | Produced value | Date |
|---|---|---|
| G2 | `[RECORD]` | `[RECORD]` |
| G3 | `[RECORD]` | `[RECORD]` |

**ΔΔG_spec is a ranking feature within the M1 arm. It is not a gate and is not weighted for M2 or M3.**

---

## 4. Ranking rule

> Registered as a rule, not as weights to be chosen later. Weights that are tuned after seeing results are not registered.

**Within each mechanism arm, rank by:**

1. `M_mut` (mutation-specificity margin), descending — primary
2. Ties within `0.5 × pooled SD` of each other are broken by `M_pep`, descending
3. Remaining ties broken by confidence against T+, descending

**ΔΔG_spec enters the M1 ranking only**, as a tiebreak at position 4 for designs still tied after the above. It does **not** enter M2 or M3 ranking at any position, for the reason in `CLAUDE.md` §7.2.

No weighted composite is used. A weighted sum would require choosing weights, and any weight chosen after seeing the score distributions is a post-hoc decision disguised as a formula.

Selection procedure, fixed in advance:
1. Apply gates; log rejections per gate
2. Cluster within each arm by structural similarity, threshold `[FILL]`
3. Take cluster representatives
4. Fill allocation: M1 = 9, M2 = 5, M3 = 4, affinity-only control = 1, reserve = 1
5. Place the affinity-only control at approximately rank 10
6. Prescreen; promote next representative on any flag

---

## 5. Noise floor

Measured on Day 1 by running identical input `[N]` times and recording the spread of each confidence metric. That measured spread defines the `pooled SD` used in G4.

Measured value: `[FILL]`

---

## 6. What would falsify each hypothesis

- **H1 fails** if the positive control panel shows no margin separation from the negative panel. Reported as a finding, not suppressed.
- **H2 fails** if the affinity-only control design performs as well as or better than specificity-ranked designs in the returned experimental data.
- **H3** is not powered and no conclusion will be drawn either way.

---

## 4b. Control outcomes registered in advance

**False-reject rate.** Every positive control must pass every gate. Zero failures in *n* controls gives a 95% upper bound of approximately 3/n, which is reported rather than stated as zero.

Positive controls: `[RECORD n]` · failures: `[RECORD]` · upper bound: `[RECORD]`

**Expected diagnostic per negative control**, registered before running. A negative that fails at a different gate than registered is logged in `FINDINGS.md` and investigated.

| Negative control | Registered to fail at |
|---|---|
| Introduced chain break | G0 |
| Deliberately greasy surface | Hydrophobic patch check |
| Binder docked away from the peptide | G3 |
| Near-copy of a known binder | G7 or G9 |
| Scrambled sequence | G1 |
| Decoy-target-swap design | G4 |

---

## 5b. Evaluation study stop rule

`CLAUDE.md` §12.2 is the headline deliverable, and it currently rests on the unquantified assumption that enough public mutant-versus-wild-type discrimination labels exist. Registered in advance:

| Requirement | Minimum |
|---|---|
| Labelled binder–variant pairs | **40** |
| Distinct targets represented | **4** |
| Minimum per target | **5** |

**If the minimum is not met:** report the shortfall, publish the assembled set as a partial resource with its provenance, and **do not report an AUROC**. Descriptive statistics only. A headline metric computed on an underpowered set is worse than no metric.

Assembled set actually obtained: `[RECORD]`

---

## 6b. Control panel minimum

Stage −1 requires **at least 5 positive controls**. If fewer are obtainable, the go/no-go decision is not meaningful and the shortfall is reported rather than worked around.

Intended panel: 18 published pMHC-I binders [R10] plus the 7OW6 TCR.
Fallback if unobtainable: VDJdb and IEDB TCRs with documented pMHC-I specificity.
Panel actually used: `[FILL]`

---

## 7. Analyses planned in advance

- **Primary estimator:** mixed-effects logistic model, `binds ~ margin + (1 + margin | target)`, target-level random intercept and slope
- AUROC with cluster bootstrap by target, 2,000 replicates, retained as a sensitivity check
- Occupancy and selectivity-index modelling under mass action, reported as a sensitivity surface over a stated copy-number range
- Precision and recall across the full threshold range
- Calibration curve and expected calibration error
- Threshold sensitivity analysis
- Power analysis stating detectable effect size at available n
- Grouped splits by target, asserted in code

Conditional on designs being selected and tested:
- Independent re-fitting of returned sensorgrams; comparison against reported K_D values
- Test of the 1:1 Langmuir assumption by residual inspection; alternative models where it fits poorly
- Separate characterisation of designs classified as binding by the 300% association-shift rule rather than a fitted K_D
- Propagation of fit uncertainty into specificity ratios
- Filter precision and recall against both reported and independently derived labels

Any analysis not listed here and performed later is labelled **post hoc** in all outputs.

---

## Amendments

`[Append only. Each entry dated, with reason. Never edit the sections above.]`
