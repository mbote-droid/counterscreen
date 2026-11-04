# METHODS.md — Scientific Write-Up

**Spec version 0.5** · 2 November 2026 · part of a five-file set: `PROTOCOL.md`, `DESIGN.md`, `METHODS.md`, `PREREGISTRATION.md`, `REFERENCES.md`

**Status: template.** Sections marked `[FILL]` are completed as the campaign runs. This file is both the submission methods document and the basis for later publication.

> This document is a **scored input** to the competition's selection process [R19]. It is not paperwork.

---

## AI assistance disclosure

`[FILL — one line, factual]` State which AI tools were used and for what: e.g. pipeline implementation, analysis scripting, literature search, draft review.

Rationale for including this: the competition scores method descriptions, the toolchain is part of the method, and honest provenance matters. This is separate from repository commit attribution, which carries the author's account only.

---

## 1. Objective

Design a protein binder that binds the KRAS G12D peptide `VVVGADGVGK` presented by HLA-A\*11:01, and does **not** bind either the wild-type complex (`VVVGAGGVGK`, differing at peptide position 6 only) or the peptide-free HLA-A\*11:01 / β2-microglobulin complex. [R18]

Specificity is the primary objective; affinity is a constraint. This follows the challenge's lexicographic ranking, in which mutation specificity and peptide-dependence are resolved before affinity. [R18]

## 2. Targeted surface

`[FILL — residue-level specification, with evidence links]`

We target the peptide and the groove immediately surrounding it, the surface read by a T-cell receptor. Design templates: PDB 7OW6 (G12D with TCR, TCR deleted) and 7OW5 (wild type with TCR, TCR deleted) [R12].

**Structural rationale.** Two features of this target constrain design:

1. In the receptor-bound structure the mutant aspartate is tucked against HLA Arg114 and Gln70 [R18]. The discriminating carboxylate is partly engaged by the HLA itself and is not a freely accessible handle.
2. In 7OW4, the G12D structure without a receptor, peptide positions 5 and 6 have **no coordinates** [R18]. The residue carrying the entire discrimination signal is disordered in the unbound state.

**Assumption stated explicitly:** designs were generated against a receptor-stabilised conformation that may not be populated before binding. Any successful binder must pay the entropic cost of ordering that loop. We did not model this cost.

## 3. Discrimination mechanisms

Designs were allocated across three mechanisms rather than ranked from a single pool.

| Arm | Mechanism | n |
|---|---|---|
| M1 | Direct electrostatic readout of the Asp6 carboxylate | `[FILL]` |
| M2 | Composite readout of the Asp6–Arg114–Gln70 surface | `[FILL]` |
| M3 | Conformational selection exploiting wild-type glycine backbone freedom | `[FILL]` |
| Control | Affinity-only ranking, specificity ignored | 1 |

M1 is motivated by the finding of Wang & Kollasch that successful discrimination on this neoantigen proceeded through a salt bridge to the mutant aspartate [R9].

> **This comparison is exploratory.** At n = 20 and an expected base rate near 27% [R14], each arm yields two or three hits at best. The allocation makes the campaign interpretable; it does not support a statistical comparison between mechanisms, and none is claimed.

## 4. Pipeline

`[FILL — versions, parameters, seeds for every stage]`

| Stage | Tool and version | Parameters |
|---|---|---|
| Backbone generation | RFdiffusion `[FILL]` | `[FILL]` |
| Sequence design | ProteinMPNN `[FILL]` | `[FILL]` |
| Monomer filter | ESMFold2 `[FILL]` | `[FILL]` |
| Counter-screen | `[FILL]` | 3 targets × `[FILL]` seeds |
| Interface scoring | `[FILL]` | `[FILL]` |

Screening was performed on a truncated construct comprising the α1/α2 platform domain and peptide (~180 residues); finalists were re-scored against the complete three-chain complex. Truncation boundaries: `[FILL]`.

## 5. Scoring and calibration

### Specificity margins

For confidence metric `C` and each design, over `n` seeds:

```
M_mut = C(T+) − C(D1)
M_pep = C(T+) − C(D2)
```

Designs were required to show `M > 2 × pooled within-design seed SD`. Margins below this were treated as indistinguishable from prediction noise.

### Operating point

`[FILL — the calibrated threshold and how it was derived]`

> **We did not import a literature threshold.** The frequently cited ipSAE cutoff of 0.61 derives from a meta-analysis in which the best metric was AF3 ipSAE_min, reported as average precision, with the authors noting possible bias from designs pre-selected by AF2 ipAE [R2]. It does not transfer across models or metrics. Our operating point was derived from the control panel described in §6.

### Interface energetics

`[FILL — Rosetta or the open fallback, with the reason for the choice]`

ΔΔG_spec, computed by in-place Asp6→Gly substitution with local repacking, was used as a **ranking feature within the M1 arm only**. It was recorded but not weighted for M2 and M3, because in-place mutation with static repacking measures loss of direct side-chain contact and is insensitive to backbone-entropy (M3) and rotamer-rearrangement (M2) mechanisms. Using it as a filter would have systematically removed those arms.

**Units.** Rosetta reports Rosetta Energy Units, not kcal/mol, with no explicit solvent or conformational entropy sampling. Values are used for ranking only and are not interpretable as predicted affinities. For reference, ΔG = RT·ln(K_D/C°) and one order of magnitude in affinity corresponds to 1.36 kcal/mol at 298 K [R21].

## 6. Control panel and metric validation

Before scoring any design, we tested whether the chosen metrics can resolve a single-residue epitope change at all.

**Positive panel:** the T-cell receptor from 7OW6, plus 18 published de novo pMHC-I binders [R10].
**Negative panel:** `[FILL]` — binders specific for unrelated pMHC complexes, and scrambled sequences.
**Invariant-surface control:** a binder deliberately targeting the α1/α2 helices distal to the peptide, expected to show no margin against any decoy.

**Procedural controls applied:**
- Controls were folded by the identical procedure applied to designs. Crystal poses were **not** supplied as structural seeds, since the initial-guess procedure would otherwise leak the answer.
- Training-data contamination was assessed by comparing each model's stated training cutoff against the deposition dates of 7OW3/4/5/6 and 9UV8. `[FILL — result]` Where a structure falls inside a model's training set, that model's control performance is optimistically biased and is reported as such.
- The numeric pass/fail rule was committed to `PREREGISTRATION.md` before the panel was run.

**Result:** `[FILL]`

**Consequence for the campaign:** `[FILL — proceeded with neural scoring / fell back to physics-primary]`

## 7. Selection of submitted designs

`[FILL]`

Hard gates applied, with rejection counts per gate: `[FILL]`

Within each mechanism arm, surviving designs were clustered by structural similarity and cluster representatives were selected rather than top-N by score, to avoid submitting twenty variations of a single fold.

Prior-art clearance: all submitted sequences passed `binder-prescreen --target kras-pmhc` [R15]. `[FILL — any flags and their resolution]`

## 8. Evaluation study

### 8.1 Specificity-margin calibration

`[FILL]`

Separately from the campaign, we asked whether co-folding specificity margins separate known mutant-versus-wild-type discriminators from non-discriminators, using public TCR and TCR-mimic structures with variant peptides [R10, R11].

Reported with: AUROC and cluster-bootstrapped confidence intervals, precision and recall across the threshold range, calibration curve and expected calibration error, threshold sensitivity, and a power analysis stating the detectable effect size at the available n. Splits were grouped by target; a test asserts no target appears in both partitions.

Reference baselines: mean co-folding confidence AUROC ≈ 0.761 against a hydrophobic-fraction baseline ≈ 0.589 [R14].

Control sequence provenance, including any substitution of the intended panel: `[FILL]`

**Primary estimator.** Because observations are clustered by target with few per target, a mixed-effects logistic model (`binds ~ margin + (1 + margin | target)`) was fitted as the primary analysis, with target-level random intercept and slope. Partial pooling shrinks unstable per-target estimates toward the population mean. The cluster bootstrap is retained as a sensitivity check rather than the headline; material disagreement between the two is reported. `[FILL]`

Because the registered minimum is four targets, the full random-slope model is frequently not identifiable at the available n. The estimator is therefore a pre-registered ladder, descended only on a stated failure and never on taste: rung 1 `binds ~ margin + (1 + margin | target)`; rung 2 `binds ~ margin + (1 | target)`; rung 3 `binds ~ margin` with target-clustered robust standard errors. Rung used: `[FILL]`. Descending a rung is itself reported, since it says the data could not support the model the analysis wanted.

### 8.2 Raw experimental data re-analysis

`[FILL — conditional on designs being selected and tested]`

Where experimental results were returned, we did not treat the reported binary binder / non-binder calls as the terminal output.

- Sensorgrams were re-fitted independently and the resulting K_D values compared against those reported. `[FILL]`
- The 1:1 Langmuir assumption was tested by inspection of fit residuals; heterogeneous-ligand and two-state models were applied where the 1:1 fit was poor. The provider has noted that the standard fit assumes a 1:1 interaction and has been extending its fitting models [R26]. `[FILL]`
- Designs classified as binding by the 300% association-shift rule rather than by a fitted K_D [R18] were examined separately as an ambiguous class. `[FILL]`
- Uncertainty in individual fits was propagated into the specificity ratios, rather than reporting ratios of point estimates. `[FILL]`
- Filter precision and recall were computed against both the reported labels and our independently derived labels, and both are reported. `[FILL]`

### 8.2b Occupancy and competition modelling

Dissociation constants, measured or predicted, were translated into fractional occupancy under mass action and into a selectivity index expressed in bound complexes per cell rather than K_D ratio alone.

```
θ = [B] / ([B] + K_D)

selectivity_index = (θ_G12D × copies_G12D,tumour) / (θ_WT × copies_WT,healthy)
```

**Rationale.** K_D(WT)/K_D(G12D) is not the selectivity a cell experiences. Wild-type KRAS is expressed across healthy tissue while G12D is restricted to tumour cells, so the ratio of presented complexes modifies effective selectivity. A design with a favourable K_D ratio may have a selectivity index near unity once presentation density is accounted for.

Reported as a sensitivity surface over a stated copy-number range, not as a point prediction. `[FILL — ranges used, sources, and which parameter dominates]`

Comparison against affinity-enhanced T-cell receptors in development against this target, where published: `[FILL]`

### 8.3 AI assistant error log

This pipeline was implemented with an AI coding assistant. Errors the assistant made during construction, how each was detected, and the guard subsequently added are recorded in `AGENT_ERRORS.md` and summarised here. `[FILL]`

Errors are classified by detection route — caught by automated test, caught by human review, or caught only by downstream failure. The proportion caught only by human review is reported, since it bounds how far the process could be automated.

This follows the precedent set by the published Mithril Medicine program, in which six assistant errors were documented alongside the results [R27].

## 8.4b Filter false-reject rate

Every positive control was required to pass every gate. Failures: `[[frr.failures]]` of `[[frr.n]]`. Upper bound on the false-reject rate, by the rule of three where no failures were observed: `[[frr.upper]]`. `[FILL]`

A positive control failing a gate indicates the gate is wrong, not the control. Gate changes made in response, with dates: `[FILL]`

Each negative control was additionally required to fail **at its registered gate**. Negatives failing at an unregistered gate: `[FILL]` — investigated and recorded in `FINDINGS.md`.

## 8.5 Filter false-accept rate

Deliberately invalid designs were pushed through the complete ranking pipeline and the resulting false-accept rate measured: scrambled sequences, designs with the key contact residue mutated to alanine, designs generated against an unrelated target, and reversed sequences.

Sample size was registered before running: **10 adversarial designs per class, 40 in total** (`PREREGISTRATION.md` §7b). Registering n matters because the width of this interval is the result; choosing n after seeing how many were accepted would let the interval be tuned.

Measured false-accept rate: `[[far.point]]` (95% CI `[[far.ci_lo]]`–`[[far.ci_hi]]`), by the Wilson method, or by the rule of three where zero adversarial designs were accepted. `[FILL]`

Code-level mutation score, fraction of deliberate one-line defects killed by the test suite: `[[mutation.score]]`. Surviving mutants and the tests added in response: `[FILL]`

> A filter with no measured false-accept rate is an assertion. To our knowledge no published de novo binder design pipeline reports one for its own in-silico filter.

## 8.6 Theory-versus-measurement check

The energetic scale of the interactions the scorer claims to resolve was checked against first-principles thermodynamics. Using ΔG = RT·ln(K_D/C°) and 1.36 kcal/mol per decade of affinity at 298 K [R21], the expected ΔΔG for removal of the Asp6 salt bridge was predicted and compared against the value reported by the scoring function for the same in-place substitution. `[FILL]`

A second interaction class of known energetic scale was checked the same way: `[FILL]`

Agreement indicates the scoring function behaves physically on this interaction class. A substantial shortfall indicates it is not resolving the interaction, in which case ΔΔG_spec carries correspondingly less weight even within the M1 arm. A substantial excess suggests a repacking artifact. Result and consequence: `[FILL]`

## 8.7 The funnel

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
| Submitted | 20 |

All quality metrics are reported as distributions rather than point values: median, interquartile range, and the count passing. Per-residue confidence profiles and their minima are reported alongside means, since a mean conceals a locally disordered region.

## 9. Limitations

Stated here rather than in an appendix.

1. **Apo-state conformation.** Designs target a receptor-stabilised conformation. The discriminating residue is disordered without a bound receptor [R18]. The entropic cost of ordering it was not modelled.
2. **Decoy construction.** D2 models the peptide-free complex using the peptide-bound groove geometry. The real empty groove may differ.
3. **Metric sensitivity.** `[FILL]` Co-folding confidence metrics were developed and validated for binary binding discrimination, not for single-residue specificity.
4. **Training-data contamination.** `[FILL]`
5. **Mechanism comparison is exploratory.** n = 20 cannot support it.
6. **Reproducibility is partial.** GPU stages are not bit-reproducible; tolerance bands are reported in place of exact reproduction. The execution environment is Kaggle's container, recorded by digest rather than controlled by us.
7. **Interface energetics are ranking statistics.** Not predicted affinities.
8. **Assay ceiling.** Independent wet-lab assays on identical designs have been reported to agree only 89% of the time [R14], which bounds the correlation any in-silico metric can achieve against experimental labels.
8c. **Occupancy parameters.** pMHC copy numbers for this epitope on tumour and healthy tissue are not well established. §8.2b is a sensitivity analysis over an assumed range, not a prediction. Conclusions depend most strongly on `[FILL]`.
8b. **Control panel composition.** `[FILL]` If the intended 18-binder panel [R10] could not be obtained and a VDJdb/IEDB substitute was used, the calibration is correspondingly weaker and the operating point less well determined.
10. **Folding is assumed, not modelled.** Every structure predictor in this
stack presupposes Anfinsen's thermodynamic hypothesis: that the native state
is determined by the sequence and is the free-energy minimum under
physiological conditions. Nothing here tests that assumption, models a folding
pathway, or estimates a folding rate. The assumption is load-bearing in a
specific way worth naming: a designed binder that is kinetically trapped, or
that populates an alternative state, would be scored by this pipeline as
though its predicted structure were its native one. The refolding filter at
G1 (scRMSD, best of 8 ProteinMPNN sequences) is the only check in that
direction, and it tests self-consistency of prediction, not foldability in
reality. Expression failure in the returned data is the first point at which
this assumption is tested at all, and §12.3 records that such failure censors
binding labels informatively rather than at random.

11. **Scope — what this pipeline does not model.** Stated explicitly because
the omissions are deliberate rather than pending. It does not model folding
kinetics, transition states, folding times, chaperone-assisted folding, or
conformational dynamics beyond the single static pose each predictor returns.
Molecular dynamics appears only as an optional local-minimisation fallback for
interface energetics (§5), never in the design loop. The pipeline predicts no
structure of its own: it orchestrates ESMFold, Protenix and Boltz and scores
*differences* between their outputs, so its structural accuracy is theirs,
inherited along with their failure modes — over-confidence on designed
backbones, high pLDDT on non-binders [R16], and a reliability curve that
inverts above 0.6 [R14]. Calibration is against a single target class: one
HLA allele, one peptide length, one substitution. No claim of generalisation
to other folds, to unusual kinetics, or to rare structural classes is made or
supported, and the counter-screen objective is the only component offered as
transferable.

9. **Base rate.** Most de novo designs do not bind; a measured rate of 26.8% across an expert campaign spans 0% to 80% by target [R14]. pMHC is at the difficult end.

## 10. Claim discipline

- Computational results in this document are predictions. Where a quantity is predicted, it is labelled predicted.
- No claim is made that any design binds its target. That claim requires experimental measurement.
- Should experimental results become available, the defensible statement without an orthogonal method and an interface-mutant control is that a design shows target-dependent signal in a named assay, not that it binds. Without a structure, the claim is that it binds the target, not that it binds via the designed interface.

## 10b. Numerical provenance

Every number in this document is written as a key resolved against a result file by the reporting pipeline, and a claim checker in CI fails the build on any key without a matching entry, any bare numeral outside a key, or any result file newer than this document. Literature values are the sole exception and carry a `[Rn]` marker tying them to `REFERENCES.md`.

**No number in this document was typed by hand.**

## 11. Data and code availability

Repository: `[FILL]`
Pre-registration: `PREREGISTRATION.md`, committed `[FILL — date and SHA]`
Adversarial log: `campaigns/kras-g12d-pmhc/ADVERSARIAL_LOG.md`
AI assistant error log: `AGENT_ERRORS.md`
Control sequence provenance: `campaigns/kras-g12d-pmhc/controls/PROVENANCE.md`
Raw and re-fitted experimental data: `campaigns/kras-g12d-pmhc/results/raw/` and `results/refit/`
Findings log, what validation changed about the design: `FINDINGS.md`
Superseded specification, retained as provenance only: `docs/history/PROJECT_BRIEF_v0.2.md`
All references: `REFERENCES.md`
