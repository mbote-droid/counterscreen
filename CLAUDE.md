# CLAUDE.md — Builder Brief

**Project:** Specificity-first protein binder design and evaluation
**Author:** Dr. Samuel Mbote · GitHub `mbote-droid`
**Version:** 0.5 — supersedes all earlier versions. Discard any file labelled v0.1 through v0.4.
**Written:** 1 November 2026 · last revised 2 November 2026
**Campaign 1 deadline:** 8 November 2026, 23:59 AoE

> Read this entire file before writing code. Section 14 (Non-Goals) is binding.
> Companion files: `DESIGN.md` (how it works), `METHODS.md` (scientific write-up), `REFERENCES.md` (citations), `PREREGISTRATION.md` (commit before scoring own designs).

---

## 1. Purpose

Two deliverables from one body of work:

1. **A design campaign** — competitive entries into open protein-binder competitions offering free wet-lab validation, producing experimentally measured results on the author's own designs, published openly.
2. **An evaluation study** — a pre-registered, calibrated assessment of whether in-silico filters can resolve single-residue binding specificity.

**The second is the more valuable deliverable and must not be treated as a byproduct.**

### Why

The author is a medical doctor (MBChB, MCS COSECSA) who moved into computational biology, holds no PhD, is based in rural Kenya, and is applying for remote contractor roles in computational biology, protein engineering, scientific computing and AI evaluation. Job descriptions in this space consistently require: designing rigorous evaluation tasks, developing objective scoring rubrics, identifying model limitations and failure cases, and distinguishing computational predictions from experimentally validated results.

A design campaign proves you can *use* the tools. An evaluation study proves you can *judge* them. Employers want the second. Experimental ground truth makes the claims independently verifiable, which outweighs any CV assertion.

### Field context

- The bottleneck has moved from design to validation; design throughput has outpaced standard biochemistry workflows. [R1]
- In-silico metrics remain imperfect predictors of experimental success; no metric correlates reliably with affinity. [R2]
- The largest recent hit-rate jump came from pipeline engineering, not new models — BindCraft trained nothing, reused AlphaFold2 weights, inserted a refolding filter. [R3]
- Open experimental datasets including negative results are appearing for the first time (Proteinbase, ODC-ODbL). [R4]
- Evaluation frameworks are being formalised right now (ProtDBench, BenchBB, BioDesignBench, ProteinBench, PDFBench). [R5–R8] The field is mid-way through deciding how it measures itself.

---

## 2. Prior art — read before designing anything

**This project is not a reproduction of any of the following. It uses their outputs as inputs and asks a question they left open.**

| Work | What it did | How we use it |
|---|---|---|
| **Wang & Kollasch, GenBio Workshop @ ICML 2026** [R9] | Compared LLM-assisted vs agentic vs human-directed minibinder design for KRAS G12D. **9-mer** VVGADGVGK, PDB **9UV8**. Found specificity, not affinity, was the real filter, and that the discriminating interaction was a salt bridge to the mutant aspartate | Direct prior art. Must cite. Their finding motivates our M1 mechanism. Different peptide length, different structure, different question |
| **Liu et al. 2025** [R10] | Published de novo pMHC-I binders via RFdiffusion targeting outward-facing peptide residues; 18 sequences used by Wang & Kollasch to calibrate metrics | **Positive control panel for Stage −1.** Replaces the single-TCR control, which was underpowered. **⚠ DAY-1 BLOCKER — see §5.0** |
| **Zhu et al., Commun Biol 9:26 (2026)** [R11] | Crystal structures of HLA-A\*11:01 with six G12 mutant peptides (G12C, G12R, G12V, G12D, G12A, G12S), plus MD and NMR on the conformational landscape. Reports ~50-fold higher affinity for the 10-mer G12D over the 9-mer | **Additional decoys beyond wild type.** A binder discriminating G12D from G12V and G12C is a substantially stronger result |
| **Poole et al., Nat Commun 2022** [R12] | Source of 7OW4, 7OW5, 7OW6 | Design templates |

### Delta statement (state this in METHODS.md)

> No published work has calibrated whether co-folding specificity margins can resolve single-residue pMHC discrimination, nor tested a three-way counter-screen objective against experimental measurement on the 10-mer KRAS G12D / HLA-A\*11:01 target.

That claim is narrow, checkable and defensible. Do not inflate it.

---

## 3. Campaign 1 — Anthropic × Adaptyv Challenge 05

### 3.1 Task

| Label | Composition | Requirement |
|---|---|---|
| **T+** | HLA-A\*11:01 + β2m + `VVVGADGVGK` | **Must bind** |
| **D1** | HLA-A\*11:01 + β2m + `VVVGAGGVGK` (wild type) | **Must not bind** |
| **D2** | HLA-A\*11:01 + β2m, empty groove | **Must not bind** |
| **D3–D5** (optional, our addition) | HLA-A\*11:01 + β2m + G12V / G12C / G12R peptides [R11] | Should not bind — strengthens the result |

> **Check the target's disulfides survive preparation.** Both the HLA-A\*11:01 α2 domain and β2-microglobulin carry structural disulfide bonds. If stripping the TCR, truncating, or re-protonating drops them, every downstream number is computed on a subtly wrong target. Assert their presence after preparation and record the assertion.

T+ and D1 differ at peptide position 6 only: aspartate versus glycine. This is KRAS residue 12.

### 3.2 Sequences

**HLA-A\*11:01 heavy chain** (Q5S3G3, 25–305, 281 aa):
```
GSHSMRYFYTSVSRPGRGEPRFIAVGYVDDTQFVRFDSDAASQRMEPRAPWIEQEGPEYWDQETRNVKAQSQTDRVDLGTLRGYYNQSEDGSHTIQIMYGCDVGPDGRFLRGYRQDAYDGKDYIALNEDLRSWTAADMAAQITKRKWEAAHAAEQQRAYLEGRCVEWLRRYLENGKETLQRTDPPKTHMTHHPISDHEATLRCWALGFYPAEITLTWQRDGEDQTQDTELVETRPAGDGTFQKWAAVVVPSGEEQRYTCHVQHEGLPKPLTLRWELSSQPT
```

**β2-microglobulin** (P61769, 21–119, 99 aa):
```
IQRTPKIQVYSRHPAENGKSNFLNCYVSGFHPSDIEVDLLKNGERIEKVEHSDLSFSKDWSFYLLYYTEFTPTEKDEYACRVNHVTLSQPKIVKWDRDM
```

**G12D peptide:** `VVVGADGVGK` (P01116, 7–16)
**Wild type:** `VVVGAGGVGK`
**Allele:** A\*11:01:01:01 (IPD-IMGT/HLA HLA00043)

### 3.3 Structural basis — drives every decision

| PDB | Contents | Use |
|---|---|---|
| **7OW6** | G12D pMHC **with TCR** | Primary template. Chains A–C, TCR deleted |
| **7OW5** | Wild-type pMHC with TCR | Real D1 coordinates |
| **7OW4** | G12D, **no TCR** | **No coordinates for peptide positions 5 and 6** |
| 7OW3, 9UV8 | Related HLA-A\*11:01 complexes [R9, R11] | Cross-reference |

Two facts that constrain everything:

1. **In 7OW6 the Asp is tucked against Arg114 and Gln70** of the HLA (PDB numbering). The discriminating carboxylate is already partly engaged by the HLA's own arginine. It is **not** a free solvent-exposed handle, and a naive "place an Arg to salt-bridge it" strategy may have nowhere to reach.
2. **7OW4 has no density at positions 5 and 6.** In the receptor-free state the residue carrying the entire discrimination signal is disordered.

Consequences:
- You design against a **receptor-stabilised conformation that may not exist until your binder arrives.** The binder must pay the entropic cost of ordering that loop. State this assumption explicitly.
- Wild type has **glycine** there — no side chain, wider Ramachandran range, so the wild-type peptide middle is *more* flexible. Exploitable as an entropic discrimination mechanism.

### 3.4 Epitope

The peptide and the groove immediately around it — the surface a TCR reads. The rest is identical across all targets.

**Off limits:** target His and Avi tags; your design's C-terminal Twin-Strep capture tag. Binding to a tag does not count.

### 3.5 Ranking (lexicographic, not weighted)

All designs measured against all three targets under identical conditions, design immobilised, target in solution. Binding counts when the sensorgram gives a fittable curve and a K_D, or where unfittable, when the association shift clears 300% over negative control.

1. **Mutation specificity** — measurable K_D vs T+, no detectable binding to D1. Designs binding both rank after, by K_D(D1)/K_D(T+) descending.
2. **Peptide-dependent binding** — measurable K_D vs T+, no detectable binding to D2. Designs binding it rank after, by K_D(D2)/K_D(T+) descending.
3. **Affinity** — lowest K_D vs T+.

Winner must clear all three, ties settled in that order. Each step also awards an honourable mention.

> **Central strategic fact.** A micromolar binder that discriminates beats a nanomolar binder that does not. Nearly every default pipeline ranks on confidence or predicted affinity against the target alone — optimising criterion 3 while criteria 1 and 2 decide the outcome. **Our objective optimises the specificity margin and treats affinity as a constraint.**

### 3.6 Submission

| Item | Value |
|---|---|
| Length | 10–250 aa |
| Format | Single chain protein, nanobody, scFv, or Fab |
| Designs | **20** (Track 3) |
| Type | De novo only |
| Deadline | 8 Nov 2026, 23:59 AoE |

**Track 3** (open, self-supported). No Claude or Modal credits — that window closed 24 Sep. Designs are considered for testing **without guaranteed allocation**.

**Selection:** a Claude-based workflow builds a scoring rubric before reading submissions. Inputs are ranked sequences **plus any metrics, structures and method descriptions the participant chooses to share.** Does not rely on a single in-silico metric.

> **The methods document is a scored input.** The challenge page states: tell us which surface you target and link your evidence; if you don't, we take it from a predicted complex. Most entrants submit sequences and a paragraph. Submit a campaign report.

**The 20-design cap means compute is not the bottleneck.** A funded lab submits the same twenty. This challenge is unusually winnable from a free tier.

---

## 4. Three discrimination mechanisms

Allocate designs deliberately across three hypotheses rather than ranking one pool. Makes the campaign an experiment.

**M1 — Direct electrostatic readout.** *Redefined by amendment A8; the original wording named a target that does not exist.* A hydrogen-bond donor placed against the **solvent-accessible face of OD1** — the only carboxylate oxygen with non-zero SASA, at 6.4 Å² — or displacing the **Gln70** contacts to OD2 (3.08 Å and 3.58 Å), which are the weaker of the two coordinating interactions. The Arg114 pair is **not** a target: it is bidentate across both oxygens at 2.95 Å and 3.04 Å and leaves none free (`FINDINGS.md` F-5). Against wild type a successful design still loses the contact *and* buries an unsatisfied positive charge, so the double penalty stands. Expected value is now the **lowest** of the three, not the highest: the handle is 6.4 Å² on an 85%-buried residue, and the only worked discriminator avoids it entirely (F-6). Motivated by [R9], which reported salt-bridge discrimination on the **9-mer** on 9UV8 — a different length and structure, and a finding that does not transfer to this complex.

**M2 — Composite surface readout.** Target the altered local surface created by the Asp6–Arg114–Gln70 network rather than the aspartate itself. In wild type Arg114 is unpaired and likely adopts a different rotamer, changing local shape and electrostatics.

**M3 — Conformational selection.** Require a tightly defined peptide backbone conformation. Glycine's wider backbone freedom means wild type pays a larger entropic ordering penalty. Specificity from differential ordering cost, not from a contact.

M3 is where the hits probably are, on the evidence of `FINDINGS.md` F-6: the substitution displaces peptide position 6 by about 1 Å and that displacement propagates to positions 7–9, which carry no sequence difference but are the accessible ones, and which is exactly where the 7OW6 TCR reads. M2 remains a differentiator. M1 is the hardest, for the reason above.

> **Critical:** the scoring must not be blind to M2 and M3. See §7.2.

---

## 5. Stage −1 — falsification check, run before anything else

**Purpose:** determine whether the chosen metrics can resolve a single-residue epitope change at all. If they cannot, the neural arm is blind and the pipeline must fall back to physics.

### 5.0 Obtain the control sequences — blocking task, Day 1

**Stage −1 cannot run without these. Do this before the GPU benchmark.**

1. Locate Liu, Greenwood, Bonzanini et al. 2025 [R10] and extract the 18 binder sequences from supplementary data.
2. If the sequences are not published in usable form, fall back to: TCRs from **VDJdb** and **IEDB** with documented pMHC-I specificity, plus the 7OW6 TCR. Record that the panel is degraded and why.
3. Build the negative panel: binders or TCRs specific for unrelated pMHC complexes, plus scrambled sequences of the positives.
4. Record provenance for every control sequence — source database, accession, publication — in `campaigns/kras-g12d-pmhc/controls/PROVENANCE.md`.

**Do not proceed to §5.1 with fewer than 5 positive controls.** Below that the panel cannot distinguish a working metric from luck, and the go/no-go decision is not meaningful.

### 5.1 Controls (hardened from v0.2 — a single TCR is underpowered)

| Set | Content | Expected |
|---|---|---|
| **Positive panel** | The 7OW6 TCR **plus the 18 published pMHC minibinders from Liu et al.** [R10] | Positive margin, T+ over D1 |
| **Negative panel** | TCRs or binders specific for unrelated pMHC; scrambled sequences | No margin |
| **Invariant-surface control** | A binder deliberately targeting the α1/α2 helices away from the peptide | No margin on any comparison |

### 5.2 Protocol rules — all mandatory

1. **Do not feed the crystal pose in as the initial guess.** Initial-guess methods are seeded with the design model; seeding controls with the crystal pose leaks the answer and makes calibration meaningless. **Controls must run exactly as designs will run.**
2. **Write the numeric pass/fail rule before running.** Commit it to `PREREGISTRATION.md` first.
3. **Check training-data contamination.** 7OW4/5/6 are from Poole et al. 2022 [R12]. Past AlphaFold2's 2018 PDB cutoff, but plausibly inside the training sets of Protenix, Boltz and other recent models. Record each model's stated cutoff. If a structure is in-distribution for a model, that model's control result is optimistically biased and must be reported as such.
4. **Validate the fallback too.** If the physics arm becomes primary, it needs its own control panel result. An unvalidated fallback is not a fallback.
5. **Calibrate G3 empirically** — measure the peptide-contact fraction achieved by the real TCR and the Liu binders, and use that distribution as the threshold reference rather than a guessed number.
6. **Calibrate the confidence cutoff empirically** — see §7.1. Do not import a literature threshold.

### 5.3 Outcomes

| Result | Action |
|---|---|
| Positive panel shows margins exceeding seed noise; negatives do not | Metrics are sensitive. Proceed |
| Any positive control **fails a gate** | That is a **false reject**, and it means the gate is wrong, not the control. Fix the gate, log the change, re-run |
| No separation | Co-folding confidence cannot resolve one-residue discrimination. **This is itself a reportable finding.** Switch to physics-primary, validate it, and report |

### 5.4 False-reject rate and diagnostic codes

**Report a false-reject rate with an interval.** Every positive control must pass every gate. With zero failures in *n* controls, the 95% upper bound on the false-reject rate is approximately **3/n** (rule of three). With the intended panel of 19, that is an upper bound near 16% — report the number, do not imply it is zero.

**Every negative control must fail, and fail with the expected diagnostic code.** A flawed design that fails for the wrong reason is a gate working by accident, and it will not generalise. Register the expected failure mode for each negative control in advance:

| Negative control | Must fail at |
|---|---|
| Backbone with an introduced chain break | G0 |
| Design with a deliberately greasy surface | G5 |
| Binder docked away from the peptide | G3 |
| Near-copy of a known binder | G7 or G9 |
| Scrambled sequence | G1 |
| Decoy-target-swap design | G4 |

A negative control that fails at the wrong gate is logged in `FINDINGS.md` and investigated, not quietly counted as a pass.

Cost: a few hours. It can invalidate the approach on day one. That property is the point.

---

## 6. Model stack (revised in v0.3)

Tiered and complementary, not a large ensemble average.

| Tier | Model | Role |
|---|---|---|
| Cheap screen | **ESMFold2** | Monomer self-consistency; first pass over many designs |
| Discrimination | **Protenix v2** primary, **Boltz-2** fallback | Three-way counter-screen on survivors |
| Orthogonal check | **AlphaFold2 initial-guess** | Finalists only |

**Rationale.** Anthropic reported that ensembling ESMFold2 with Protenix v2 produces state-of-the-art filtering for de novo binder designs [R13]. Counter-evidence: averaging ten co-folding predictors was **not** measurably better than one (+0.028, CI −0.031 to +0.081) [R14]. These reconcile if what matters is ensembling models that **fail differently** — a protein-language-model folder and an AF3-class diffusion folder are different machinery; ten co-folding models are one method run ten times. AF2 initial-guess is retained because the initial-guess trick is purpose-built for designed binders and fails differently again.

> **Treat the ensemble as a testable question, not an assumption.** On the Stage −1 control panel, measure whether the ensemble beats the single best model. Given [R14] it may not. Either result is reportable.

**Install feasibility on Kaggle for Protenix v2 and Boltz-2 is unverified. Benchmark both on Day 1** before committing (see §10).

---

## 7. Objective function

### 7.1 Neural arm — specificity margins

Per design, over *n* seeds, for the chosen confidence metric *C* (ipSAE or the model's equivalent):

```
M_mut = C(T+) − C(D1)      mutation-specificity margin
M_pep = C(T+) − C(D2)      peptide-dependence margin
M_var = C(T+) − max C(D3..D5)   variant-discrimination margin (optional)
```

**Margins must exceed prediction noise.** Report mean ± SD across seeds; require `M > 2 × pooled SD`. A one-side-chain difference produces small margins; without this guard the ranking is noise. Non-negotiable.

**Confidence cutoff must be calibrated locally, not imported.** The frequently quoted 0.61 ipSAE cutoff comes from a meta-analysis of 3,766 binders where the best metric was **AF3 ipSAE_min**, reported as average precision, with the authors noting possible bias from designs pre-selected by AF2 ipAE [R2]. It does **not** transfer to a different model or metric. Derive the operating point from the Stage −1 control panel.

### 7.2 Physics arm — ranking feature, NOT a gate

```
ΔΔG_spec = ΔG_bind(binder·WT) − ΔG_bind(binder·G12D)
```

computed by in-place Asp6→Gly mutation, local repack, rescore.

> **Why this is not a gate.** In-place mutation with local repack measures **loss of direct side-chain contact**. M3 operates through backbone entropy, which a static repack cannot see at all. M2 operates partly through Arg114 rotamer rearrangement, which it sees unreliably. **Used as a hard gate it would systematically delete the two differentiated arms.** Use it as a ranking feature, calibrated on the control panel, applied within M1 and reported but not enforced for M2 and M3.

**Terminology discipline (enforce in all outputs):**
- ΔG is the free energy change of one process. ΔG = RT·ln K_D; RT ≈ 0.59 kcal/mol at 298 K; **every tenfold in affinity is 1.36 kcal/mol**. Strictly ΔG = RT·ln(K_D/C°) with a 1 M standard state.
- ΔΔG is a difference between two ΔG values and always needs a stated reference.
- Rosetta's interface filter is historically named `ddg` but reports a ΔG_bind (complex minus separated). It reports **REU, not kcal/mol**, with no explicit solvent or conformational entropy sampling. Rank with it. Never quote it as an affinity. **Never write "REU-equivalent" — that phrase was an error in v0.2.**

### 7.3 PyRosetta contingency

PyRosetta requires a licence and non-trivial install. The author operates under a company name (Daktari Genomed Labs), which may affect eligibility for the free academic licence. **Verify on Day 1.** If blocked, the Rosetta-free fallback is:

- Buried surface area — FreeSASA or Biotite
- Contact maps, H-bond and salt-bridge geometry — Biotite or MDAnalysis
- Shape complementarity — geometric approximation
- Local minimisation and interaction energy — OpenMM
- Binding affinity proxy — PRODIGY (open)

Document whichever path is taken and why.

---

## 8. Hard gates

> **Gate order matters.** G0 runs first and costs seconds. Never spend GPU time co-folding a structure that is not physically valid.

| | Gate | Justification |
|---|---|---|
| **G0** | **Geometric validity — all of:** chain breaks (consecutive Cα distance 3.8 Å nominal; **> 4.5 Å is a break**), clash score, **Ramachandran outliers < 1%**, bond lengths and angles within standard tolerance, Cα chirality all L, no *cis* peptide bonds outside proline | Generative backbones do emit non-physical geometry, and **confidence scores miss it entirely**. Costs seconds; runs before anything else |
| G1 | scRMSD(monomer) ≤ 2.0 Å, **Cα atoms only, after Kabsch superposition**, best of 8 ProteinMPNN sequences; **and pLDDT ≥ 80 on the refolded prediction** | Standard designability criterion. The unit and superposition method are part of the specification, not decoration |
| G2 | Confidence ≥ **locally calibrated** operating point | Derived in Stage −1. Do **not** import 0.61 — wrong model, wrong metric [R2] |
| G3 | Peptide contact fraction ≥ control-panel reference | Calibrated in Stage −1 on the TCR and Liu binders, not guessed |
| G4 | M_mut and M_pep > 2 × pooled SD | Margin must beat prediction noise |
| **G5** | **Hydrophobic patch: largest contiguous solvent-exposed apolar patch on the refolded monomer, at or below the 90th percentile of the positive control panel** | §5.4 registers a negative control that must fail at a hydrophobic patch check, and v0.5 had no such gate, so that control had no failure point. Also a real expression and aggregation liability. Derivation rule, no free parameter, mirroring G3. CPU, seconds: runs after G1, before any co-folding. ΔΔG_spec remains a ranking feature and is still not a gate (§7.2) |
| G6 | No buried unsatisfied charges in the T+ complex | Expression and folding liability |
| G7 | `binder-prescreen --target kras-pmhc` = pass | 51 known TCRs from IEDB, VDJdb, PDB, patents; v0.5 released 27 Oct 2026 for this challenge [R15] |
| G8 | 10–250 aa, single chain, standard residues, no free Cys | Submission rules plus expression |
| **G9** | **Structural novelty: max TM-score against the PDB, via Foldseek, below a registered threshold** | G7 checks *sequence* prior art. A design can be a structural copy of a known fold carrying a novel sequence. Report the maximum TM-score found; do not assume novelty |

### Interface reference values — sanity benchmarks, not gates

Computed values that fall far outside these ranges indicate an error upstream rather than an interesting design:

| Quantity | Typical for a real interface |
|---|---|
| Buried surface area (ΔSASA) | 1,500–2,000 Å² total for a stable complex |
| Shape complementarity (Sc) | 0.65–0.75 |
| Buried unsatisfied polar atoms | As near zero as possible; each is a real energetic penalty |
| Rosetta total score, normalised | −2 to −3 REU per residue for well-packed designs, energy-function dependent |

Use these to catch mistakes, not to filter. Report where your designs sit relative to them.

Targeted surface must exclude all tag regions.

---

## 9. Pipeline

| Stage | Tool | Output |
|---|---|---|
| 0 | Target prep | T+ (7OW6 TCR-stripped), D1 (7OW5 TCR-stripped), D2 (7OW6 minus peptide), optional D3–D5 [R11], truncated screening construct |
| **−1** | **Control panel** | **Go/no-go; G2 and G3 calibration; ensemble test** |
| 1 | **RFdiffusion** | Backbones, 55–75 aa, three hotspot schemes for M1/M2/M3 |
| 2 | **ProteinMPNN** | 8 sequences per backbone, T = 0.1 |
| 2b | **Geometry validation** (G0) | Chain breaks, clashes, Ramachandran, bond geometry, chirality, cis-peptides. Seconds. Runs before any GPU spend on folding |
| 3 | **ESMFold2** | Monomer scRMSD filter — cheap, discards most failures |
| 4a | **Protenix v2 / Boltz-2**, truncated target | Three-way screen, 2 seeds |
| 4b | Protenix + **AF2 initial-guess**, full complex | Finalists only, 5 seeds |
| 5 | Rosetta or fallback (§7.3) | Interface energetics, ΔΔG_spec, contact analysis |
| 6 | Cluster and select | Final 20 |
| 7 | `binder-prescreen` | Prior-art clearance |
| 8 | Package | Ranked CSV, methods document, structures |

### Critical optimisation: truncation

Full complex ≈ 390 residues (281 + 99 + 10). The **α1/α2 platform plus peptide ≈ 180 residues** and is the surface a receptor reads. Screen truncated, validate finalists on the complete complex. This is what makes the budget fit. Document the reasoning — it shows understanding of what the model needs rather than feeding it everything.

---

## 10. Compute — Kaggle free tier, benchmark first

**No paid tier.** Kaggle primary (30 GPU-h/week, P100 or dual T4). Colab free as spillover. Checkpoint every stage; assume sessions drop.

> **The v0.2 budget was wrong.** It assumed ~900 co-folding predictions in 8 hours, implying ~32 s each. Realistic for a ~240-residue complex on a T4 is 60–120 s, making that stage 15–30 hours. **Do not plan from estimates. Benchmark on Day 1 and derive the budget.**

### Day-1 benchmark (mandatory before Stage 1)

Measure and record, on the actual Kaggle GPU:
- seconds per co-folding prediction, truncated construct
- seconds per co-folding prediction, full complex
- seconds per RFdiffusion backbone
- ESMFold2 throughput
- whether Protenix v2 and Boltz-2 install at all
- whether PyRosetta installs and licenses
- **which confidence metrics each model actually emits.** §7.1 says "ipSAE or the model's equivalent", which is not yet resolved. ipSAE is a derived quantity; Protenix and Boltz may emit PAE, pTM and ipTM but not ipSAE itself. Confirm either a reference implementation or that ipSAE is computable from the emitted PAE matrix plus chain assignments. **If no model in the stack yields a usable interface-confidence metric, the objective function in §7.1 has no input and the plan must change before Day 2.**
- numerical spread across 5 identical repeat runs — this is the noise floor for G4 and the tolerance band for CI

### Budget formula

```
N_designs_tier2 = (available_hours × 3600) / (n_targets × n_seeds × s_per_prediction)
```

Worked examples, 3 targets × 2 seeds, 12 hours available:

| s/prediction | Designs screenable |
|---|---|
| 30 s | 240 |
| 60 s | 120 |
| 120 s | 60 |

**Contingency ladder if over budget**, in order: reduce seeds at tier 4a to 2; truncate the target further; cut backbone count; drop optional decoys D3–D5; drop the AF2 orthogonal check on finalists. **Never cut the control panel or the counter-screen** — those are the project.

---

## 11. Selecting the final 20

| Arm | Count |
|---|---|
| M1 direct electrostatic | 4 |
| M2 composite surface | 5 |
| M3 conformational selection | 9 |
| Affinity-only control | 1 |
| Reserve (highest composite, any mechanism) | 1 |

**Diversity-cluster within each arm** by structural similarity; take cluster representatives, not top-N by score. Twenty variants of one fold is one experiment, not twenty.

**Affinity-only control:** the design that would win if ranked by confidence against T+ alone, ignoring specificity. If it binds all three targets while specificity-ranked designs do not, that is direct evidence the objective was right. **Place around rank 10** so it is still tested if only part of the list is selected.

> **n = 20 cannot support an M1/M2/M3 comparison.** At a ~27% base rate split 4/5/9 you get two or three hits per arm. **Label the comparison exploratory in every output.** Do not report it as a result.

---

## 12. Evaluation layer — first-class deliverable

### 12.1 Pre-registration

**Before seeing any of your own designs' scores**, commit `PREREGISTRATION.md`: all gate thresholds, the ranking rule, the mechanism allocation, the Stage −1 numeric pass/fail rule, and the hypotheses. Timestamped git commit. This separates the work from essentially every competition entrant and most published design papers.

### 12.2 The evaluation question — revised in v0.3

> **v0.2 had this wrong.** It proposed a Proteinbase reference panel. Proteinbase carries binder/non-binder labels against single targets and **no decoys**, so it validates an affinity filter and cannot evaluate specificity margins — the novel component. It also overclaimed: binary binding prediction has already been measured [R2, R14].

**The right question, answerable offline, independent of whether your designs get selected:**

> Do co-folding specificity margins separate known mutant-versus-wild-type discriminators from non-discriminators?

**Test set:** public TCR and TCR-mimic structures with variant peptides — IEDB, VDJdb, PDB, the Liu et al. binders [R10], the Zhu et al. G12-mutant series [R11]. Many TCRs have published cross-reactivity data giving positive and negative labels.

**Primary estimator: a hierarchical (partial-pooling) model, not per-target bootstrap.**

The data are clustered by target with few observations each, and per-target estimates are correspondingly unstable — in the published retrospective, 4 of 14 per-target AUROC intervals include chance, EGFR being 0.669 with CI 0.466–0.857 [R14]. Treating each target as an independent estimate discards the information that targets are draws from a population.

Fit a mixed-effects logistic model:

```
binds ~ margin + (1 + margin | target)
```

with target-level random intercept and slope. Partial pooling shrinks noisy per-target estimates toward the population mean, yields a population-level effect with honest uncertainty, and gives per-target estimates that do not swing wildly at small n. Tools: `statsmodels` MixedLM, or `bambi` / `numpyro` for the Bayesian version with explicit priors.

> **This model is not identifiable at the registered floor.** §12.2's stop rule admits as few as **4 targets**, and `(1 + margin | target)` must estimate a 2×2 random-effects covariance — two variances and a correlation — from that many clusters. It will typically return a singular fit or fail to converge, and a singular fit silently reported as the primary analysis is worse than a simpler model honestly chosen. **The fallback is therefore registered in advance as a ladder with a switch rule** (`PREREGISTRATION.md` §7), not decided at the keyboard once the fit misbehaves. The rung actually used is reported in every output.

**Keep the cluster bootstrap as a sensitivity check, not as the headline.** Material disagreement between the hierarchical and bootstrap estimates is itself reportable.

**Also report:** AUROC with cluster-bootstrapped confidence intervals, precision and recall across the threshold range, a calibration curve, expected calibration error, and threshold sensitivity analysis. **Use grouped splits by target** — random splits leak target base rates. Assert in code that no target appears in both train and test.

**Known baselines:** mean co-folding confidence AUROC ≈ 0.761 vs a hydrophobic-fraction baseline ≈ 0.589 [R14].

> **Stop rule, registered in `PREREGISTRATION.md` §5b.** This deliverable rests on the assumption that enough public mutant-versus-wild-type labels exist, which is unquantified. Minimum: **40 labelled pairs across at least 4 distinct targets, 5 per target.** Below that, report the shortfall, publish the partial set with provenance, and **report no AUROC** — descriptive statistics only. Stage −1 has a floor; the more valuable deliverable needs one too.

**Power analysis before running.** State the detectable effect size for the available n.

### 12.3 Adversarial log

From day one, record every instance where the pipeline produces something that should not be possible: inputs, seeds, package versions, full output. At the end, test whether each reproduces systematically.

> **Discovered-by-accident is an anecdote. Discovered-by-protocol is a finding.** "I noticed X sometimes happens" is a blog post. "X occurs in n of N cases under condition C, here is the mechanism, here is a test that detects it, here is the confidence interval" is research.

**Known edge cases for orientation** — there is no existing catalogue, and assembling one would itself be a contribution:
- Structure predictors are systematically over-confident on designed backbones, which are out of distribution relative to the experimentally solved natural structures they trained on. The bias has direction; it is not noise.
- Adversarial designs achieve high pLDDT and do not bind. [R16]
- The reliability curve inverts above 0.6: designs predicted at 70–80% bound only 28% of the time. [R14]
- Two wet-lab assays on the same designs agree only **89%** of the time — a hard ceiling on what any in-silico metric can achieve, rarely acknowledged. [R14]
- Expression failure censors binding labels informatively; designs that never express never get a label, and treating that as missing-at-random biases every reported hit rate. [R4]
- Generators overrepresent helical folds; β-strand-rich architectures are scarce. [R17]
- Most generative methods treat the receptor as rigid, neglecting induced fit. [R17]
- Per-target AUROC confidence intervals frequently include chance — 4 of 14 targets in one study; EGFR 0.669, CI 0.466–0.857. [R14]

**This project's strongest candidate finding:** 7OW4 has no coordinates for the two peptide positions carrying the entire discrimination signal. **How a structure predictor behaves when the discriminating atoms are experimentally undetermined is a specific, genuine, under-characterised question.** That alone could be the paper.

### 12.3a Reporting rules — the funnel and the distribution

Two rules that apply to every number this project reports.

**Report the funnel, always.** Cherry-picking is reporting the best of a thousand designs without reporting the thousand. State at every stage: generated → passed G0 → passed G1 → passed each subsequent gate → clustered → selected. The drop at each step is a result in itself, and a gate that removes 95% of candidates is either doing real work or is wrong, which the reader should be able to judge.

**Report distributions, never point values.** "Median scRMSD 1.4 Å, interquartile range 1.0–2.6, 37 of 100 designs passing all filters" says something. "The model achieved 1.4 Å" says nothing and invites the reader to assume it is typical.

This extends to confidence metrics: **report the per-residue profile and its minimum, not only the mean.** A mean pLDDT of 85 can conceal a disordered twenty-residue stretch at 40. The same reasoning that makes minimum interface PAE a bad summary statistic (§12.2, §7.1) makes a bare mean pLDDT one.

### 12.3b Agent error log — `AGENT_ERRORS.md`

This pipeline is built with an AI coding assistant. **Record where the assistant got things wrong**, in a file separate from the pipeline adversarial log.

Precedent: when Anthropic published the Mithril Medicine program, it documented **six errors Claude made**, some of which reached external labs in emails before humans caught them [R27]. Publishing agent failures alongside agent successes is becoming the expected standard, and it is precisely the competence that AI-evaluation employers hire for.

For each entry record: what the assistant produced, what was wrong with it, how it was caught (test, review, downstream failure), what guard was added, and whether the guard is automated or relies on a human reading carefully.

Entries worth capturing by default:
- Silently wrong scientific reasoning that looked plausible
- Imported literature thresholds without checking provenance (the v0.2 G2 error was exactly this)
- Units or sign errors in scoring
- Scope creep back toward anything in §14
- Fabricated or misattributed citations
- Statistical mistakes, such as computing pooled SD across designs instead of within

**Distinguish caught-by-automation from caught-by-review.** A failure mode that only a careful human catches is a different risk class from one a test catches, and the ratio between them is itself a result.

### 12.4b Mutation testing — two levels, both required

This is the method the author's published benchmark work rests on, and it transfers directly. Its absence from v0.3 was an omission.

**Level 1 — mutate the code, verify the tests catch it.**

Introduce deliberate one-line defects and confirm a test fails. Minimum mutant set:

| Mutant | Must be caught by |
|---|---|
| Invert the sign of `M_mut` | Margin unit test |
| Compute pooled SD across designs instead of within | Statistics unit test |
| Skip gate G3 entirely | Gate contract test |
| Swap D1 and D2 in the counter-screen | Target wiring test |
| Return the crystal pose as a control seed | Provenance assertion (§DESIGN 3) |
| Write to `results/raw/` from `analyze/` | Immutability assertion |
| Report bootstrap before fitting the hierarchical model | Pooling assertion |

Report the **mutation score**: fraction of mutants killed. A surviving mutant is a missing test, and the pooled-SD mutant in particular proves the bug anticipated in §12.3b is actually caught rather than merely noted.

**Level 2 — mutate the designs, measure the filter's false-accept rate.**

Push deliberately bad designs through the **complete ranking pipeline**, not just Stage −1:

- Scrambled sequences of passing designs
- Passing designs with the key contact residue point-mutated to alanine
- Decoy-target swap: designs generated against an unrelated target, scored against T+
- Reversed sequences

**Report the measured false-accept rate with a confidence interval**, by the Wilson or rule-of-three method as appropriate. This is the number that converts the ranking function from an assertion into a calibrated instrument.

> Essentially no published design pipeline reports a false-accept rate for its own filter. It is cheap, it is the central claim of the project, and it is the direct analogue of the grader-validity argument in the author's prior work.

### 12.5 Raw experimental data re-analysis — conditional, high value

**If designs are selected and tested**, Adaptyv returns sensorgrams, not just binary labels. Our evaluation must not stop at consuming the labels.

Adaptyv has noted that the standard fit assumes a **1:1 interaction** and that they have been adding further fitting models [R26]. The challenge also defines binding as either a fittable curve with a K_D, **or**, where the curve cannot be fitted, an association shift clearing 300% over the negative control [R18]. That second category is where the interesting failures live.

Planned analysis:
1. **Re-fit the sensorgrams independently.** Compare your K_D values against the reported ones.
2. **Test the 1:1 assumption.** Check residual structure; try heterogeneous-ligand and two-state models where 1:1 fits badly.
3. **Examine every unfittable curve.** Designs scored by the 300% rule are the ambiguous class. Characterise them rather than accepting the binary call.
4. **Propagate fit uncertainty** into the specificity ratios. A K_D ratio built from two poorly determined fits carries more uncertainty than the point estimate suggests.
5. **Re-derive the filter's precision and recall** using your own labels as well as the reported ones, and report both.

Almost no competition entrant will re-analyse the raw data. It converts you from a consumer of someone else's measurement into someone who can interrogate it, which is the distinction that matters for the roles being targeted.

### 12.5b Theory-versus-measurement check

The scoring function makes claims that first-principles thermodynamics can check independently. Where they disagree, that is a finding about the scorer.

**The check.** A buried salt bridge contributes on the order of a few kcal/mol; a solvent-exposed one, less. Using R21 (ΔG = RT·ln(K_D/C°), 1.36 kcal/mol per decade of affinity), predict the ΔΔG that removing the Asp6 salt bridge *should* produce, then compare against what the scorer reports for the same in-place mutation.

**Interpretation:**

| Outcome | Meaning |
|---|---|
| Scorer lands in the predicted range | Scoring function behaves physically on this interaction class |
| Scorer reports far less | It is not resolving the interaction; ΔΔG_spec is uninformative here and should carry less weight even within M1 |
| Scorer reports far more | Likely a repacking artifact rather than a real energetic difference |

Run the same comparison for a second interaction class with a known energetic scale — a buried hydrogen bond, or a hydrophobic burial of known surface area.

Cheap, uses only material already in the project, and a disagreement is more interesting than agreement.

### 12.6 Occupancy and competition modelling — what the numbers mean biologically

The challenge ranks on K_D and K_D ratios. Neither answers whether a binder would be *useful*. A mass-action occupancy model does, it is cheap, and it connects measured constants to biological meaning.

**Single-site occupancy** at free binder concentration `[B]`:

```
θ = [B] / ([B] + K_D)
```

**Competition with an endogenous partner** for the same complex:

```
θ_binder = ([B]/K_D,B) / (1 + [B]/K_D,B + [T]/K_D,T)
```

**The analysis that matters: selectivity in bound complexes, not in K_D.**

The ratio `K_D(WT) / K_D(G12D)` is not the selectivity a cell experiences. Wild-type KRAS is expressed ubiquitously across healthy tissue; G12D is confined to tumour cells. If the wild-type complex is presented at higher copy number than the mutant, a given K_D ratio translates into a **substantially worse** ratio of bound complexes per cell.

```
selectivity_index = (θ_G12D × copies_G12D,tumour) / (θ_WT × copies_WT,healthy)
```

Compute across a plausible range of copy numbers and report as a surface, not a single value. Neoantigen pMHC presentation is typically low — often tens to low hundreds of copies per cell — while wild-type presentation on healthy tissue may be higher. **A design with a 100-fold K_D ratio can have a selectivity index near or below 1 once presentation density is accounted for.** That is a real therapeutic constraint the competition ranking does not capture.

Report:
1. Fractional occupancy versus concentration for each measured or predicted K_D
2. The K_D required for meaningful occupancy at plausible neoantigen copy numbers
3. The selectivity-index surface over the copy-number ratio
4. Comparison against affinity-enhanced TCRs in development for this target, where published

**State parameter uncertainty honestly.** Copy numbers for this specific pMHC may not be well established. Present it as a sensitivity analysis over a stated range, never as a point prediction, and say which parameters dominate the result.

Standard mass-action modelling, an afternoon's work, and essentially no competition entrant will do it. It is also the section that shows a clinician's instinct for whether a number means anything in a patient.

### 12.4 Post-hoc validation — conditional

If and only if designs are selected and tested, measure the filter's precision and recall against the returned ground truth. **This is conditional on Track 3 selection, which is not guaranteed.** Do not build the project's value on it.

---

## 13. Scope — must / should / could

Seven days is tight, and §10 makes it tighter.

| Priority | Work |
|---|---|
| **Must** | §5.0 control sequence acquisition · Day-1 benchmark · **G0 geometric validity** · Stage −1 control panel with **false-reject rate (§5.4)** · pipeline through to 20 designs · `PREREGISTRATION.md` with parameter-free rules · **mutation testing level 1 (§12.4b)** · **funnel and distribution reporting (§12.3a)** · `METHODS.md` · `FINDINGS.md` · prescreen · submission |
| **Should** | §12.2 offline evaluation study · **mutation testing level 2, false-accept rate (§12.4b)** · **G9 Foldseek structural novelty** · §12.6 occupancy · adversarial log · `AGENT_ERRORS.md` · §12.5b theory-vs-measurement · REFERENCES.md |
| **Could** | `REQUIREMENTS.md` with traceability matrix · full Snakemake CI · optional decoys D3–D5 · ensemble-versus-single comparison · power analysis · replication playbook (§13b) |

> **Honest time cost.** `REQUIREMENTS.md` with an EARS-style traceability matrix is three to four hours. It is the author's established standard from prior work, but in a seven-day sprint with Day 1 already overloaded it competes directly with the false-accept-rate measurement. **If forced to choose, measure the false-accept rate.** A traceability matrix documents the build; the false-accept rate is a result.
| **After submission** | §12.5 raw sensorgram re-analysis, if designs are tested · §12.4 post-hoc precision and recall |

§12.6 occupancy modelling sits in **Should** — it needs no GPU, runs on predicted K_D values before any experimental result exists, and can be written while folding jobs occupy the GPU.

### 13b. Replication playbook — optional artifact

A short standalone document: **how to run a solo de novo binder design campaign on a free GPU tier.** Derived from what actually happened, including the benchmark numbers, the contingency decisions taken, what broke, and what it cost in hours.

This is cheap because it is a byproduct of work already done, and it is the kind of artifact that gets cited and shared by people who are not otherwise interested in KRAS. Write it only after submission, from the real record — a playbook written in advance is a guess.

If the schedule slips, cut from Could, then Should. **Never cut from Must.**

---

## 14. Non-Goals — explicitly rejected, do not reintroduce

- Quantum-to-molecular-to-systems multi-scale pipelines
- Systems biology networks and circuits (different field; forced integration)
- Neuroscience concepts (unrelated)
- Distributed or embedded systems (this is an embarrassingly parallel batch job at most; claiming distributed systems is a red flag)
- Streaming ingestion with standby fetch triggers (the PDB releases weekly; a cron job is the honest answer)
- Agentic or multi-agent orchestration (adds nothing here)
- Knowledge bases and data mining as goals rather than means
- Explainable AI bolted on with no trained model to explain
- Building another general evaluation framework — ProtDBench, BenchBB, BioDesignBench, ProteinBench, PDFBench already exist and are funded [R5–R8]

> **Seniority is demonstrated by what is left out and whether you can say why.** A system touching twenty areas and going deep in none signals inability to scope.

---

## 15. Repository structure

One repository, one pipeline, multiple campaigns.

```
counterscreen/
  README.md
  CLAUDE.md                  # this file
  DESIGN.md                  # architecture and engineering decisions
  METHODS.md                 # scientific write-up
  REFERENCES.md              # citations
  PREREGISTRATION.md         # committed before scoring own designs
  pyproject.toml / uv.lock
  Dockerfile                 # for independent reproduction, NOT for Kaggle
  Snakefile
  src/
    targets/                 # prep, truncation, decoy construction
    generate/                # RFdiffusion wrappers
    sequence/                # ProteinMPNN wrappers
    fold/                    # ESMFold2, Protenix, Boltz, AF2-IG
    score/                   # margins, interface energetics, contact analysis
    rank/                    # gates, composite, clustering, selection
    evaluate/                # control panel, calibration, AUROC + CIs
    report/                  # methods generation
  AGENT_ERRORS.md            # AI assistant failures, caught and guarded
  FINDINGS.md                # what validation changed about the design — the file outsiders read
  REQUIREMENTS.md            # numbered requirements, verification method each, traceability matrix
  PLAYBOOK.md                # optional, written after submission
  docs/history/
    PROJECT_BRIEF_v0.2.md    # SUPERSEDED — kept as provenance, never as guidance
  campaigns/
    kras-g12d-pmhc/
      config.yaml
      PREREGISTRATION.md
      controls/
        PROVENANCE.md        # every control sequence, with source
      results/
        raw/                 # sensorgrams as returned, unmodified
        refit/               # our independent fits
      ADVERSARIAL_LOG.md
      METHODS.md
      REPORT.md
  benchmarks/
    day1_gpu_benchmark.md
  tests/
  docs/
```

### Commit convention

**Commits show only `mbote-droid`. No AI co-author trailers, no "Generated with" lines, no AI attribution of any kind in commit messages or PR descriptions.**

Separately and not in conflict: **`METHODS.md` carries a one-line AI-assistance disclosure.** A methods description is scored in this competition, the toolchain is part of the method, and honest provenance matters to employers. Commit attribution and scientific methods disclosure are different things.

---

## 16. Reproducibility — honest about the Kaggle constraint

> **v0.2 claimed a pinned Docker image. Kaggle notebooks run Kaggle's container and cannot run your own image.** State the real position rather than the ideal one.

| Concern | Approach |
|---|---|
| Environment | Record the Kaggle base image and its digest. Pin every package with `uv`. Ship a `Dockerfile` for independent reproduction off-Kaggle |
| Determinism | GPU stages are **not** bit-reproducible — cuDNN nondeterminism, TF32, atomic ordering. Do not claim they are |
| CI | Run CPU-only fixtures bit-exactly. For GPU stages, assert **numerical tolerance bands**, not byte equality |
| Seeds | Log every seed. Record them in the provenance manifest |
| Provenance | Git commit, package versions, model weight checksums, Kaggle image digest, input and output checksums |
| Workflow | Snakemake regenerating the campaign from one command |
| Quality | `ruff`, `mypy`, complexity limits, shellcheck-verified strict Bash |

Commit continuously. Repo history is part of the artifact.

---

## 17. Schedule

| Day | Work |
|---|---|
| 1 | **§5.0 control sequence acquisition (blocking)** · target prep · **Day-1 GPU benchmark** · install checks (Protenix, Boltz, PyRosetta) · Stage −1 control panel · go/no-go · G2 and G3 calibration · `PREREGISTRATION.md` committed |
| 2 | RFdiffusion, three hotspot schemes |
| 3 | ProteinMPNN · ESMFold2 monomer filter |
| 4–5 | Three-way counter-screen |
| 6 | Interface scoring · ranking · clustering · prescreen |
| 7 | `METHODS.md` · package · submit |
| **After** | §12.5 raw sensorgram re-analysis when results return · §12.4 post-hoc calibration · §13b playbook |

Offline evaluation study (§12.2) runs in parallel where GPU jobs leave CPU idle, and continues after submission.
`AGENT_ERRORS.md` (§12.3b) is appended to throughout, from Day 1.

---

## 18. Risks

- **Metrics may be blind to one-residue changes.** Stage −1 catches it. Fallback is physics-primary, itself requiring validation.
- **The designable surface may be too small.** A 10-residue peptide mostly in the groove may not offer enough area for a 60 aa binder to read peptide-dominantly.
- **Apo-state uncertainty.** Designing against a receptor-stabilised conformation that may not exist until the binder arrives.
- **Training-data contamination.** 7OW structures may be in recent models' training sets, inflating control performance.
- **Install failure** for Protenix, Boltz or PyRosetta on Kaggle. Day-1 check; fallbacks in §6 and §7.3.
- **Kaggle session loss.** Checkpoint everything.
- **Testing not guaranteed** in Track 3. §12.5 and §12.4 are conditional on selection; the project's value must not depend on them.
- **Control sequences may be unobtainable** (§5.0). Fallback is a VDJdb/IEDB panel, recorded as degraded.
- **Occupancy parameters are uncertain.** pMHC copy numbers for this epitope may not be well established. §12.6 must be a sensitivity analysis over a stated range, never a point prediction.
- **Base rates are unforgiving.** Measured binder rate across an expert campaign was 26.8% of 1,320 designs, ranging 0% (MBP) to 80% (TREM2) [R14]. pMHC is at the frontier end. **Most designs will not bind. That is the expected outcome, not failure.**

---

## 19. Subsequent campaigns

| Competition | Status | Notes |
|---|---|---|
| Anthropic × Adaptyv Ch. 06+ | New challenge each Monday | Same mechanics, maximal reuse. Prefer a conventional binder target for a higher chance of a first experimental hit |
| Poreva Open (MegaRobo) | Round 1 to 18 Nov; round 2 9 Nov–8 Dec | Cash prizes ¥1M / ¥500k / ¥200k. **Reportedly requires a team of ≥3 with institutional email; individual entries not accepted — verify directly** |
| Changjiang Cup 2026 | Registration open | Nanobodies and minibinders, 5,000+ free wet-lab tests. Details unverified |
| GEM × Adaptyv RBX-1 | **Closed 26 March 2026** | Do not pursue |

---

## 20. Claim discipline — enforce in every output

- Without an orthogonal method and an interface-mutant control: "shows target-dependent signal in [assay]", not "binds".
- Without a structure: "binds the target", not "binds via the designed interface".
- A computational screen licenses neither.
- Predicted margins are predicted. Say so every time.
- Report limitations in the same document as the results, not in an appendix.
- Exploratory comparisons are labelled exploratory, every time.
