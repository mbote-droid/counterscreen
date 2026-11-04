# REFERENCES.md

**Spec version 0.5** · 2 November 2026 · part of a five-file set: `PROTOCOL.md`, `DESIGN.md`, `METHODS.md`, `PREREGISTRATION.md`, `REFERENCES.md`

Every quantitative claim in `PROTOCOL.md`, `DESIGN.md` and `METHODS.md` traces to an entry here.

**Confidence labels.** `verified` — primary source read directly. `secondary` — reported by a reliable intermediary, primary not yet read. `unverified` — encountered in search results, needs checking before any public use.

> **Action required before publication:** every `secondary` and `unverified` entry must be upgraded to `verified` or the claim removed. Do not publish a number you have not read in its primary source.

---

## Prior art — direct

**[R9]** `verified` — Wang, Y. & Kollasch, A. W. *LLM-Assisted versus Agentic Approaches to De Novo Minibinder Design for a KRAS G12D Neoantigen.* GenBio Workshop, ICML 2026. Also presented at NECB 2026.
Target: 9-mer VVGADGVGK on HLA-A\*11:01, PDB 9UV8. Compared human-directed, minimally supervised agent, and human-supervised agent design. Calibrated metrics on 18 published binders from Liu et al. 2025. Key finding: specificity, not affinity, was the discriminating filter; the human-led and supervised-agent approaches succeeded by targeting the mutant aspartate via a salt bridge.
**Our delta:** 10-mer on 7OW6, three-way counter-screen, specificity-margin objective, wet-lab measurement.

**[R10]** `secondary` — Liu, Greenwood, Bonzanini et al. (2025). De novo pMHC-I binders via RFdiffusion, making extensive contacts with outward-facing peptide residues in the MHC groove; binders incorporated into CARs gave specific Jurkat activation. 18 sequences used as a calibration set in [R9].
**Use:** positive control panel for Stage −1. **Obtain the sequences and read the primary paper before relying on it.**

**[R11]** `verified` — Zhu, J. et al. *Structure guided analysis of KRAS G12 mutants in HLA-A\*11:01 reveals a length encoded immunogenic advantage in G12D.* Communications Biology 9, 26 (2026).
Crystal structures of HLA-A\*11:01 with G12C, G12R, G12V, G12D, G12A, G12S peptides; MD and NMR chemical shift perturbation; PDB 7OW3. Reports ~50-fold higher binding for the 10-mer G12D peptide over the 9-mer.
**Use:** additional decoys D3–D5; evidence on peptide conformational landscape; justification for designing against the 10-mer.

**[R12]** `secondary` — Poole et al. *Nat Commun* (2022). Source of PDB 7OW4 (G12D, no TCR), 7OW5 (wild type with TCR), 7OW6 (G12D with TCR). Cited by the challenge page.

---

## Competition

**[R18]** `verified` — Anthropic × Adaptyv Protein Design Competition, Challenge 05: KRAS G12D pMHC. proteinbase.com/competitions/anthropic-adaptyv-2026/challenges/pmhc
Target sequences, three objectives, ranking rules, submission requirements, 8 November 2026 deadline, structural note on Arg114/Gln70 and missing density in 7OW4.

**[R19]** `verified` — Selection prompt, same competition. proteinbase.com/competitions/anthropic-adaptyv-2026/selection
Model builds a rubric before reading submissions; inputs include participant method descriptions; recommendation approved by humans at both organisers.

**[R15]** `verified` — adaptyvbio/binder-prescreen v0.5 (27 October 2026). `kras-pmhc` known-binder set: 51 TCRs from IEDB, VDJdb, PDB and patent sequence listings (US11458191, US11382954, WO2016085904). Searches PDB, SwissProt, PLAbDab, THPdb, Proteinbase, USPTO. Framework reuse is reported as context and never disqualifies.

**[R13]** `secondary` — Claude Science / Shanehsazzadeh, A. *Autonomous de novo protein binder design with Claude* (18 August 2026). 1,320 designs across 16 targets, 354 binders, 26.8% hit rate; 49% among designs ranked first per target. Reports that ensembling ESMFold2 and Protenix v2 scores produces state-of-the-art filtering for de novo binder designs.

---

## Metrics and calibration

**[R2]** `secondary` — *Predicting Experimental Success in De Novo Binder Design: A Meta-Analysis of 3,766 Experimentally Characterised Binders.* bioRxiv 2025.08.14.670059.
436 confirmed binders, 3,330 non-binders, 15 targets. **AF3 ipSAE_min** was the best single predictor, outperforming ipTM, ipAE and pDockQ; 1.4-fold increase in average precision over AF2 initial-guess ipAE. F1-optimal cutoff **0.61**.
> **Caveats that matter.** The cutoff is for **AF3 ipSAE_min**, not AF2 initial-guess, and is reported as average precision, not AUROC. Authors note possible bias from designs pre-selected by AF2 ipAE. **This cutoff must not be imported into a different model or metric.** It motivated the v0.3 removal of the hard-coded G2 threshold.

**[R14]** `secondary` — binderkit retrospective study (github.com/Dar-kSun/binderkit). Retrospective analysis of 1,320 published de novo binders, 15 targets.
- `ipsae_mean` within-target AUROC **0.761**; best single predictor 0.733; leave-one-target-out model over 27 columns 0.726; trivial hydrophobic-fraction baseline **0.589**. Paired bootstrap, 2,000 replicates; confidence beats baseline by +0.172 (CI +0.077 to +0.273).
- Averaging ten predictors not measurably better than one: **+0.028 (CI −0.031 to +0.081)**.
- Trained model over all scores worse than their plain average: −0.034 (CI −0.063 to −0.004).
- Reliability curve inverts above 0.6: designs predicted at **70–80% bound only 28%** of the time.
- Thirteen geometry metrics added to a confidence model: none improved it, two hurt, all thirteen together **−0.049** (CI −0.091 to −0.006). Authors note this used a linear term and therefore does not test the product-form claim of Overath et al.
- Per-target uncertainty: EGFR AUROC **0.669**, CI **0.466–0.857**, includes chance; 4 of 14 targets in that state.
- **Two wet-lab assays on the same designs agree only 89% of the time.**
- Measured binder rates 0% (MBP) to 80% (TREM2).
> `secondary` because this is a public repository, not peer-reviewed. The statistics appear carefully done and corrections are documented, but **read the code before citing the numbers publicly.**

---

## Field state

**[R1]** `secondary` — Baker Lab, *Nat Commun* 2026. "Recent advances in de novo protein design have greatly outpaced standard protein biochemistry workflows, making experimental validation a bottleneck."

**[R2b]** `secondary` — *Code to complex: AI-driven de novo binder design.* Structure (Cell Press), S0969-2126(25)00311-9. "Metrics like pLDDT, pAE_interaction, RMSD, and Rosetta ΔΔG have improved in silico filtering… they remain imperfect predictors of experimental success." Notes no reliable metric correlates well with binder affinity.

**[R3]** `verified` — Pacesa, M. et al. *One-shot design of functional protein binders with BindCraft.* Nature (2025). Open-source automated pipeline, experimental success 10–100%, leverages AlphaFold2 weights without training a new model, no high-throughput screening required. 212 designs across 12–13 targets, 65 binders, 30.7% overall; 10% (HER2) to 60% (SpCas9).

**[R4]** `verified` — Proteinbase (Adaptyv Bio). proteinbase.com. Over 1,000 novel proteins with computational predictions, experimental validation and design method. Standardised protocols, **includes negative data**. ODC-ODbL licence. Weekly collection drops. Off-target HSA binding and expression quantification added for the Nipah competition.

**[R5]** `secondary` — *ProtDBench: A Unified Benchmark of Protein Binder Design and Evaluation.* arXiv 2605.04118. University of Amsterdam and ByteDance Seed. Throughput-aware, fixed 24-hour budget, cluster-level success criteria, verifier reliability.

**[R6]** `secondary` — Adaptyv Bio, *BenchBB*. Curated set of 7 standardised binder design targets (PD-L1, EGFR, IL7Rα and others).

**[R7]** `secondary` — *Benchmarking and behavioral characterization of LLM agents for protein design* (BioDesignBench). Romero Lab. 76 expert-curated tasks. MIT licence.

**[R8]** `secondary` — *ProteinBench* (arXiv 2409.06744); *PDFBench* (arXiv 2505.20346).

**[R16]** `secondary` — *Design of linear and cyclic peptide binders from protein sequence information.* Commun Chem (2025). "No in silico metric separates true from false binders." Describes adversarial designs: high pLDDT, no binding.

**[R17]** `unverified` — Ding et al. (21 January 2026), via emergentmind summary. Overrepresentation of helical motifs with scarce β-strand-rich architectures; static-receptor modelling neglects induced fit and conformational selection.
> **Primary source not read. Verify before citing.**

**[R20]** `secondary` — Crowdsourced Protein Design: Lessons From the Adaptyv EGFR Binder Competition. bioRxiv 2025.04.17.648362. 1,800+ submissions, 601 characterised by BLI. Notes the lack of standardised benchmarks and of computational metrics with predictive power for affinity; proposes BenchBB.

---

## Thermodynamics

**[R21]** `verified` — Standard relation ΔG = RT·ln(K_D/C°), C° = 1 M. At 298.15 K, RT = 0.5925 kcal/mol; RT·ln10 = **1.3642 kcal/mol per decade of affinity**. Computed directly, not recalled.

| K_D | ΔG_bind |
|---|---|
| 1 µM | −8.19 kcal/mol |
| 100 nM | −9.55 |
| 1 nM | −12.28 |
| 1 pM | −16.37 |

---

## Competitions

**[R22]** `verified` — Poreva Open 2026 (MegaRobo / Megalaxy Lab). porevaopen.megalaxylab.com. Five challenges in two rounds; round 1 submissions 19 Oct–18 Nov 2026; round 2 9 Nov–8 Dec. Cash prizes ¥1,000,000 / ¥500,000 / ¥200,000. Validation to March 2027, results April 2027.
**[R22b]** `unverified` — Secondary reporting (for9a.com) states teams must have **at least 3 members**, individual and anonymous entries are not accepted, and registration requires an institutional email. **Verify on the official rules page before relying on this.**

**[R23]** `secondary` — Changjiang Cup 2026 Global AI Protein Design Challenge. Nanobodies and minibinders; 5,000+ sequences for free wet-lab testing including expression, purification and binding assays. Sponsored in part by Biointron.

**[R24]** `verified` — GEM × Adaptyv RBX-1 Binder Design Competition. gembio.ai/gemadaptyv2026. **Closed: submissions 15 Feb – 26 March 2026, results 26 April 2026 at the GEM workshop, ICLR.** Listed only to record that it is closed. Rules of record: ≤100 sequences per team, ≤250 aa, de novo only, ≤75% identity to any known protein on full sequence and every ≥30-residue window.

---

## Experimental data handling

**[R26]** `secondary` — Adaptyv Bio, public statements accompanying the Nipah Protein Design Competition data release (January 2026). Added off-target human serum albumin binding measurements, quantified expression for all proteins in their E. coli cell-free system, and noted that the standard model for fitting protein binding data assumes a 1:1 interaction, with further fitting models added.
**Use:** motivates independent re-fitting of returned sensorgrams (`PROTOCOL.md` §12.5, `METHODS.md` §8.2). **Verify the current fitting methodology directly with Adaptyv documentation before relying on this.**

**[R27]** `secondary` — Anthropic, acquisition of Mithril Medicine, announced 27 October 2026 (completed July 2026). One-person biotech, founder Cody Tranbarger, programmes in LAMA2-related congenital muscular dystrophy and alpha-dystroglycanopathy. Claude used to organise contracts, logistics and experiments across 11 external laboratories, alongside eight paid part-time consultants. Concept to mouse data in under 18 months; treated mice roughly doubled grip strength. Anthropic calls the model "Pipeline-in-a-Person". Technical report not peer reviewed. **Anthropic documented six errors Claude made during the programme, some of which reached external laboratories in emails before human review caught them.**
**Use:** precedent only, for the practice of publishing agent errors alongside agent results (`PROTOCOL.md` §12.3b, `METHODS.md` §8.3). **Not a scientific reference for any claim in this project.**
> Context worth recording, since the "solo founder" framing is widely repeated in a simplified form: the founder held a Harvard MS/MBA, had worked at Goldman Sachs, Casdin Capital and Prime Medicine, was entrepreneur-in-residence at Atlas Venture which seeded the company, and retained eight paid consultants. One full-time employee, not one person working unaided.

---

## Statistics

**[R28]** `secondary` — Smyth, G. K. *Linear models and empirical Bayes methods for assessing differential expression in microarray experiments.* Statistical Applications in Genetics and Molecular Biology 3(1), Article 3 (2004). The moderated t-statistic: a per-feature variance estimated from a handful of replicates, used as the denominator of a t-like statistic across many features, promotes the features whose variance was underestimated; the fix is to shrink each estimate toward a pooled prior. Primary not read in this build.
**Use:** the argument for amendment A9 only — G4 is the same ratio test with the design as the feature and the seed as the replicate, so a within-design pooled SD alone would select designs the model happened to be quiet about. **No quantitative claim in this project rests on this entry;** the registered resolution is a hard floor rather than a shrinkage estimator, because a shrinkage weight would be a new free parameter under a registered gate.

---

## Reagents

**[R25]** `verified` — Commercial HLA-A\*11:01 / β2m / KRAS G12D monomers and tetramers exist in both 9-mer (VVGADGVGK) and 10-mer (VVVGADGVGK) forms (e.g. Kactus Bio MHC-HM455B, MHC-HM420T). Confirms both presentations are experimentally tractable and that the 9-mer/10-mer distinction is real and consequential.
