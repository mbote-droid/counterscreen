# PREREGISTRATION.md

**Spec version 0.5** · 2 November 2026 · part of a five-file set: `PROTOCOL.md`, `DESIGN.md`, `METHODS.md`, `PREREGISTRATION.md`, `REFERENCES.md`

**Commit this file before scoring any of your own designs. Do not edit it afterwards.** Corrections go in an appended amendments section with their own timestamps, never by rewriting what was registered.

Committed: `[DATE]` · SHA: `[filled by git]`

---

## 1. Hypotheses

**H1.** Co-folding confidence metrics can resolve the single-residue difference between KRAS G12D and wild-type peptide presented on HLA-A\*11:01, as measured by a positive specificity margin for known discriminating binders.

**H2.** Ranking designs by specificity margin rather than by target-only confidence produces designs that discriminate the mutant from the wild type.

**H3** (exploratory, not powered). The three discrimination mechanisms M1, M2 and M3 differ in success rate.

---

## 2. Stage −1 pass/fail rule — written before running

> **Registered as parameter-free conditions, for the reason §3 gives.** The v0.5
> text carried four `[N]` placeholders, which is precisely the failure §3 forbids
> three paragraphs later: a rule whose numbers are chosen after seeing the panel
> does not bind, and this is the rule that decides whether the whole neural arm
> proceeds. Every quantity below is either already registered elsewhere in this
> document or a stated statistical convention.

**Pass** requires all of:
- Positive panel median `M_mut` exceeds `2 × pooled within-design seed SD` — the
  G4 rule of §3, reused rather than a second threshold invented here
- A strict majority of positive controls show `M_mut > 0`, against a null of one
  half, by a one-sided exact binomial test at α = 0.05
- Negative panel median `M_mut` does not differ from zero by a two-sided Wilcoxon
  signed-rank test at α = 0.05
- The invariant-surface control shows `|M_mut|` and `|M_pep|` both below
  `2 × pooled within-design seed SD`

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
| **G5 hydrophobic patch** | **Largest contiguous solvent-exposed apolar patch on the refolded monomer, at or below the 90th percentile of that statistic over the positive control panel. Apolar atoms are carbon and sulfur; patches are contiguous by surface adjacency; computed once on the full panel before any campaign design is scored.** | Derivation rule |
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

**ΔΔG_spec enters the M1 ranking only**, as a tiebreak at position 4 for designs still tied after the above. It does **not** enter M2 or M3 ranking at any position, for the reason in `PROTOCOL.md` §7.2.

No weighted composite is used. A weighted sum would require choosing weights, and any weight chosen after seeing the score distributions is a post-hoc decision disguised as a formula.

Selection procedure, fixed in advance:
1. Apply gates; log rejections per gate
2. Cluster within each arm by structural similarity: single-linkage at **TM-score ≥ 0.5**, the conventional same-fold boundary, computed with the same TM-align machinery that serves G9. Registered as a fixed value carrying an external justification, rather than a number tuned on our own designs
3. Take cluster representatives
4. Fill allocation: **M1 = 4, M2 = 5, M3 = 9**, affinity-only control = 1, reserve = 1 (amendment A7)
5. Place the affinity-only control at approximately rank 10
6. Prescreen; promote next representative on any flag

---

## 5. Noise floor

Measured on Day 1 by running identical input **5 times** and recording the spread of each confidence metric. That measured spread defines the `pooled SD` used in G4.

The repeat count is registered here rather than left open because the `2 × pooled SD` rule of G4, and therefore §2's pass condition, is measured against it: a repeat count chosen after seeing how noisy the metric turned out would set the noise floor to suit the result. Five is not a new decision — it is what `PROTOCOL.md` §10 and `DESIGN.md` §5 already specify for the same measurement.

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
| Deliberately greasy surface | G5 |
| Binder docked away from the peptide | G3 |
| Near-copy of a known binder | G7 or G9 |
| Scrambled sequence | G1 |
| Decoy-target-swap design | G4 |

---

## 5b. Evaluation study stop rule

`PROTOCOL.md` §12.2 is the headline deliverable, and it currently rests on the unquantified assumption that enough public mutant-versus-wild-type discrimination labels exist. Registered in advance:

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

- **Primary estimator: a registered ladder.** §5b admits as few as **4 targets**, and `binds ~ margin + (1 + margin | target)` must estimate a 2×2 random-effects covariance — two variances and a correlation — from that many clusters. At the registered floor it will commonly return a singular fit or fail to converge. A singular fit reported as the primary analysis is worse than a simpler model honestly chosen, so the descent is fixed now rather than at the keyboard:
  | Rung | Model | Descend when |
  |---|---|---|
  | 1 | `binds ~ margin + (1 + margin \| target)` | — |
  | 2 | `binds ~ margin + (1 \| target)` | rung 1 fails to converge, returns a singular fit, or puts a random-effect correlation at ±1 |
  | 3 | `binds ~ margin`, target-clustered robust standard errors | rung 2 fails to converge or its intercept variance sits at the zero boundary |

  The rung used is reported in every output, and descending is itself a reported result: it says the data could not support the model the analysis wanted. No rung below 3 is registered; if rung 3 fails, descriptive statistics only.
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

## 7b. Adversarial sample size, registered before running

`PROTOCOL.md` §12.4b level 2 and `METHODS.md` §8.5 require a false-accept rate with an interval but registered no n, which would leave the width of that interval — the result itself — to be settled after seeing how many adversarial designs were accepted.

| Adversarial class | n |
|---|---|
| Scrambled sequences of passing designs | 10 |
| Passing designs, key contact residue mutated to alanine | 10 |
| Decoy-target swap, generated against an unrelated target | 10 |
| Reversed sequences | 10 |
| **Total** | **40** |

Interval by the Wilson method; by the rule of three where zero are accepted, giving a 95% upper bound near 7.5% at n = 40. That bound is reported as the result, never as zero.

**This is a floor, and it is affordable.** Most adversarial designs die at G0, G1 or G5, all of which are CPU and cost seconds, so only survivors reach co-folding and the GPU cost is far below the worst case of 40 × 3 targets × 2 seeds. If the Day-1 benchmark shows room for more, raising n is an amendment logged below; it is never lowered.

---

## Amendments

`[Append only. Each entry dated, with reason. Never edit the sections above.]`

**Amendments A1–A8 were made on 2 November 2026 and A9–A10 on 4 November 2026,
all before any campaign design was scored and before Stage −1 was run.** They are
recorded here rather than folded silently into the text: the specification was
committed verbatim one commit earlier, so every change is visible as a diff
against it.

| # | Section | Change | Reason |
|---|---|---|---|
| A1 | §3, §4b | **G5 registered as a hydrophobic patch gate**, as a derivation rule from the positive control panel | §4b registered a negative control — the deliberately greasy surface — that had to fail at a "hydrophobic patch check", and no such gate existed anywhere in G0–G9. A registered control with no failure point cannot fail as designed, so the diagnostic-code discipline of `PROTOCOL.md` §5.4 was unenforceable for that control. G5 was vacant: it was emptied in v0.3 when ΔΔG_spec was demoted to a ranking feature, so the number is reused and the gate list stays contiguous. Placed after G1 in the ordering because it is CPU and costs seconds |
| A2 | §4 step 2 | **Clustering threshold registered** as single-linkage at TM-score ≥ 0.5 | It was `[FILL]`, inside the registered selection procedure. A threshold left blank in a pre-registration is chosen after seeing the score distributions, which is the thing this document exists to prevent. TM-score 0.5 is the conventional same-fold boundary and reuses the machinery already registered for G9 |
| A3 | §7 | **Primary estimator replaced by a three-rung ladder with a switch rule** | `binds ~ margin + (1 + margin \| target)` estimates a 2×2 random-effects covariance from as few as 4 targets, which §5b explicitly permits. At that n it will commonly return a singular fit or fail to converge. Without a registered descent, the fallback would be chosen after watching the fit misbehave, and a singular fit might be reported as though it were the registered primary analysis |
| A4 | new §7b | **Adversarial sample size registered**: 10 per class, 40 total, Wilson or rule of three | `PROTOCOL.md` §12.4b and `METHODS.md` §8.5 required a false-accept rate with an interval but registered no n. The width of that interval is the headline result, so an unregistered n would let it be tuned after seeing how many designs were accepted |
| A7 | §4 step 4 | **Allocation changed from M1 = 9, M2 = 5, M3 = 4 to M1 = 4, M2 = 5, M3 = 9** | Measured on the prepared targets before any design was generated. `FINDINGS.md` F-5: Arg114 is bidentate across both Asp6 carboxylate oxygens at 2.95 Å and 3.04 Å and Gln70 caps OD2, so the oxygen M1 was defined to reach does not exist; OD1 exposes 6.4 Å² and OD2 zero, with Asp6 about 85% buried. F-6: the same engineered TCR in 7OW6 and 7OW5 comes no closer than 7.51 Å to the carboxylate, places 18 of its 29 peptide contacts on position 7, and the substitution displaces position 6 by 0.96 Å propagating 0.78, 0.51 and 0.64 Å to positions 7–9 while positions 1–5 stay within 0.26 Å. The only worked solution to this discrimination problem is conformational, which is M3. Allocating nine designs to the arm whose handle is 6.4 Å² and four to the arm the evidence supports inverted the expected value. M2 is unchanged at 5, because the evidence for it is weaker in both directions: the TCR ignores the Asp6–Arg114–Gln70 network M2 targets |
| A8 | `PROTOCOL.md` §4 | **M1 redefined** | Its original wording — a donor contacting "the carboxylate oxygens of Asp6 not taken by Arg114" — names an empty set. M1 now targets the 6.4 Å² solvent-accessible face of OD1, or displacement of the weaker Gln70 contacts, and records that Arg114 is not displaceable. The arm is retained rather than deleted because 6.4 Å² is small but not zero and a binder may read the Asp6 environment without contacting the carboxylate; the change is to its definition and its expected value, not its feasibility |
| A6 | §5 | **Noise-floor repeat count set to 5**, matching `PROTOCOL.md` §10 and `DESIGN.md` §5 | §5 left the repeat count as `[N]` while both companion files already specified five identical runs for the same measurement. Left open it would be a free parameter underneath G4 and §2, since the measured spread defines the `pooled SD` both depend on: a repeat count chosen after seeing the noise would set the floor to suit the result. Alignment with the registered value, not a new choice |
| A5 | §2 | **Stage −1 pass/fail rule rewritten parameter-free** | §2 carried four `[N]` placeholders while §3, three paragraphs later, argued that registering a threshold as `[FILL]` means choosing it after seeing data, "which is exactly where a pre-registration most needs to bind". §2 is the rule that decides whether the neural arm proceeds at all, so it needed that discipline most. Now expressed through quantities already registered — the G4 rule — plus stated conventions |
| A9 | §3 (G4), §4 step 1 | **`pooled SD` resolved to one quantity.** G4's denominator is `max(within-design pooled seed SD, campaign noise floor)`. The ranking tie tolerance is half the campaign noise floor alone | The specification defined `pooled SD` twice and the definitions are not equivalent: `PROTOCOL.md` §7.1 and `DESIGN.md` §4 take it per design across that design's seeds, while `PROTOCOL.md` §10 and §5 here take it as a campaign floor measured once from five identical runs. The same symbol sets G4's denominator and the tie tolerance, so the two readings give different gate verdicts and different orderings, and `DECISIONS.md` D-5 recorded the degeneracy rather than resolving it by preference. Each reading fails where the other does not. The within-design estimate rests on four degrees of freedom per arm and sits in the denominator of a ratio test, so across a few hundred designs the ones whose seeds happened to agree pass on a small denominator — the selection effect that motivates moderated variance estimators in differential-expression testing. The campaign floor is estimated once and well, but from one input, so it cannot see that a conformationally loose design is genuinely noisier than a rigid one. The maximum is weaker than neither reading, is parameter-free, and moves error toward false rejects, which cost one design, rather than false accepts, which cost a wet-lab slot. The tie tolerance takes the campaign floor alone because it compares *two different designs*: a per-design SD makes that comparison asymmetric — A inside B's tolerance while B sits outside A's — so the grouping would depend on which design was read first, and a rank that depends on input order is not a registered rank. The fraction stays 0.5 and is not configurable, for the reason G2 carries no configuration field |
| A10 | `DESIGN.md` §8b | **G8 moved to the front of the gate cascade** | §8b states cheap-first as an engineering constraint and then breaks it once: it places G8 after co-folding. G8 is sequence-only — length, chain count, standard residues, free cysteines — costs microseconds and needs no structure, while a design reaching it had already been co-folded against three targets at two seeds, which is 360–720 GPU-seconds at the 60–120 s per prediction `PROTOCOL.md` §10 calls realistic. Reordering cannot change which designs survive: the cascade is a conjunction of predicates, each depending only on the design and on thresholds derived from the control panel rather than from the design set. What it does change is every per-stage funnel count, so counts are comparable only within one ordering, and the funnel tables in `METHODS.md` §8.7 and the campaign report are now asserted against the pipeline order rather than typed by hand. G6 stays after co-folding: it is cheap, but `PROTOCOL.md` §8 asks it for buried unsatisfied charges *in the T+ complex*, so its position is set by its input. That distinction is now declared per gate and the ordering is tested to be non-decreasing in it |

Changes made in the companion files at the same time, recorded here because
they follow from the amendments above:

| Section | Change |
|---|---|
| `PROTOCOL.md` §8 | G5 row replaced; §5.4 diagnostic table now names G5 |
| `PROTOCOL.md` §12.2 | Identifiability of the random-slope model stated, pointing at the §7 ladder |
| `METHODS.md` §8.7 | **G5 and G8 added to the funnel.** G8 was a live gate in `PROTOCOL.md` §8 and §3 here, but had no funnel row, so the stage-to-stage consistency test `DESIGN.md` §8 requires would have been written against an incomplete funnel |
| `METHODS.md` §8.1, §8.5 | Estimator ladder and registered adversarial n reflected in the write-up |
| `DESIGN.md` §8b | Gate ordering diagram now places G5 after G1, before any co-folding |
| `README.md` | Licence resolved: MIT for code, CC-BY-4.0 for documentation |
| `PROTOCOL.md` §7.1, §8 | G4's denominator named explicitly, per A9 |
| `DESIGN.md` §4 | Implementation note separates *which* SD is measured from *what G4 divides by*, per A9 |
| `benchmarks/day1_gpu_benchmark.md` | Noise-floor section now states how the recorded SD is used, replacing the unresolved-ambiguity note |
| `DESIGN.md` §8b | Cascade diagram leads with G8 and names why G6 follows co-folding, per A10 |
| `METHODS.md` §8.7 | Funnel table reordered to the pipeline order; it had also listed G5 after G4, which no ordering ever used |

Still open, and deliberately not amended here because neither can be settled
without reading a primary source:

- **`REFERENCES.md` [R11]** gives a single PDB accession, 7OW3, for six peptide
  complexes, and `DESIGN.md` §2 needs three specific ones for decoys D3–D5. One
  accession cannot carry six structures. 7OW3 also sits in the same block as
  7OW4/5/6, which [R12] attributes to Poole et al. 2022 rather than to Zhu et
  al. 2026. The entry is labelled `verified`. Resolve the accessions before
  building D3–D5.
- **§5.0 control sequences** remain the Day-1 blocker. Nothing here changes that.
