# DESIGN.md — Architecture and Engineering Decisions

**Spec version 0.5** · 2 November 2026 · part of a five-file set: `CLAUDE.md`, `DESIGN.md`, `METHODS.md`, `PREREGISTRATION.md`, `REFERENCES.md`

Companion to `CLAUDE.md`. That file says *what* to build and *why it matters scientifically*. This file says *how it works* and records the engineering decisions, including the ones forced by constraints rather than chosen freely.

---

## 1. Shape of the system

A staged filter cascade. Each stage is cheaper than the one after it and removes candidates that the next stage would waste time on.

```
targets ──► generate ──► sequence ──► cheap filter ──► counter-screen ──► physics ──► rank ──► prescreen ──► package
                                            │                 │
                                      (ESMFold2)      (Protenix / Boltz,
                                                       3 targets × n seeds)
```

The only unusual thing about the topology is that the counter-screen stage runs **the same design against three or more targets** and scores the *difference*. Most published pipelines score one target. That difference is the project.

### Package boundaries

| Package | Owns | Must not know about |
|---|---|---|
| `targets/` | Structure prep, truncation, decoy construction | Anything downstream |
| `generate/` | RFdiffusion invocation, hotspot schemes | Scoring |
| `sequence/` | ProteinMPNN invocation | Folding, scoring |
| `fold/` | ESMFold2, Protenix, Boltz, AF2-IG adapters behind one interface | Gates, ranking |
| `geometry/` | Chain breaks, clashes, Ramachandran, bond geometry, chirality, cis-peptides, disulfide presence | Folding models, scoring. Pure structural arithmetic |
| `score/` | Margins, interface energetics, contact analysis, Foldseek novelty | How candidates were made |
| `rank/` | Gates, composite score, clustering, selection | Model internals |
| `evaluate/` | Control panel, calibration, AUROC, bootstraps | The campaign's own designs |
| `analyze/` | Sensorgram re-fitting, fit diagnostics, uncertainty propagation | Design generation; runs only on returned experimental data |
| `biophys/` | Mass-action occupancy, selectivity index, sensitivity surfaces | Folding models; takes K_D values as input from any source |
| `report/` | Document generation and claim checking | Everything else, read-only |

One-way dependencies. `evaluate/` must be runnable against the control panel with no campaign data present — that is what makes the evaluation study independent of whether the campaign succeeds.

`analyze/` is the post-results package and is absent from the critical path. It reads sensorgrams from `results/raw/`, never mutates them, and writes independent fits to `results/refit/`. Raw data is append-only: a returned measurement is evidence and is never edited in place.

### Folding adapter

All folding models sit behind a single interface so the stack can be reordered without touching scoring:

```
fold(sequence, target_spec, seed, model) -> FoldResult
    FoldResult: coordinates, per-metric confidence dict, wall time, model id, weights checksum
```

This matters because the model stack is not settled (see §3) and because the Day-1 benchmark may force a substitution.

---

## 2. Target preparation

| Target | Construction | Notes |
|---|---|---|
| T+ | 7OW6, chains A/B/C, TCR chains deleted | Receptor-bound, ordered conformation |
| D1 | 7OW5, same treatment | **Real crystal coordinates, not a mutated T+.** Mutating in silico would bias the comparison toward our own repacking |
| D2 | 7OW6 with chain C deleted | Empty groove. Note the groove may collapse in reality; we model it as-is and say so |
| D3–D5 (optional) | Zhu et al. G12V / G12C / G12R structures [R11] | Stronger specificity claim if budget allows |

### Truncation

Full complex ≈ 390 residues (281 heavy chain + 99 β2m + 10 peptide). The α1/α2 platform plus peptide ≈ 180 residues and is the surface a TCR reads.

- **Screening stages** run on the truncated construct.
- **Finalists** are re-run on the complete complex.

This is the single decision that makes the compute budget feasible. It is also defensible on modelling grounds: β2m and the α3 domain are structurally remote from the epitope and identical across all targets, so they contribute nothing to discrimination while costing most of the compute.

**Record the truncation boundaries explicitly** in `config.yaml`, and verify after truncation that the peptide and groove geometry are unchanged relative to the full structure.

---

## 3. Model stack and why it is tiered

See `CLAUDE.md` §6 for the scientific rationale. Engineering notes:

| Tier | Model | Engineering risk |
|---|---|---|
| Cheap | ESMFold2 | Low. Well packaged |
| Discrimination | Protenix v2 primary, Boltz-2 fallback | **Install on Kaggle unverified.** Day-1 check |
| Orthogonal | AF2 initial-guess | Needs the design model as the seed; requires care in the control panel (below) |

### The initial-guess trap

AlphaFold2 initial-guess is seeded with the designed complex pose. This is what makes it discriminative for designed binders, and it is also a hazard:

> **Controls must be run exactly as designs will be run.** Seeding a control with its crystal pose leaks the answer and makes calibration meaningless.

For the Stage −1 control panel, the control binders must be folded from sequence with the same seeding procedure the campaign designs will receive. If the campaign seeds from an RFdiffusion backbone, the controls must be seeded from an equivalently derived model, not from 7OW6.

Encode this as a test, not a comment. `evaluate/` should refuse to run a control whose seed provenance is `crystal`.

### Ensemble as a measured question

The stack combines models that fail differently. Whether that actually helps is tested, not assumed — see `CLAUDE.md` §6 and [R14]. Implement single-model and ensemble scoring as two selectable ranking functions and report both on the control panel.

---

## 4. Scoring

### Margins

```
M_mut = C(T+) − C(D1)
M_pep = C(T+) − C(D2)
M_var = C(T+) − max(C(D3..D5))     optional
```

for confidence metric `C`, computed per seed. Report mean and SD. Gate on `M > 2 × pooled SD`.

**Implementation note:** pooled SD must be computed across seeds *within a design*, not across designs. Across-design variance is signal, not noise. Getting this backwards would invert the gate.

### Contact analysis

For each design, partition binder–target contacts by target chain and residue:

```
peptide_fraction = contacts_to_peptide / total_contacts
```

Threshold is calibrated from the control panel, not guessed. Also record contacts to Arg114 and Gln70 specifically, since the Asp6 environment is the discriminating feature.

### Interface energetics and the Rosetta contingency

Preferred: Rosetta `InterfaceAnalyzer` for `dG_separated`, `dSASA`, shape complementarity, buried unsatisfied polars.

**PyRosetta requires a licence and may not be available** — the author operates under a company name, which can affect free-licence eligibility. Verify Day 1.

Rosetta-free fallback, all open:

| Quantity | Tool |
|---|---|
| Buried surface area | FreeSASA, Biotite |
| Contacts, H-bonds, salt bridges | Biotite, MDAnalysis |
| Shape complementarity | Geometric approximation over the interface |
| Local minimisation, interaction energy | OpenMM |
| Binding affinity proxy | PRODIGY |

Whichever path is taken, record it and the reason in `METHODS.md`. The fallback is not inferior for our purposes — we rank, we do not predict affinities.

### ΔΔG_spec is a ranking feature, not a gate

See `CLAUDE.md` §7.2. Implementation consequence: `rank/` must accept per-arm scoring configuration. The M1 arm uses ΔΔG_spec in its composite; M2 and M3 record it but do not weight it. Hard-coding one composite across all arms would reintroduce the bug v0.3 removed.

---

## 5. Reproducibility — the honest position

> v0.2 claimed a Docker image pinned by digest as the execution environment. **Kaggle notebooks run Kaggle's container. You cannot run your own image there.** This section states what is actually achievable.

| Concern | Reality | What we do |
|---|---|---|
| Environment | Kaggle's base image, not ours | Record the base image name and digest at run time into the provenance manifest. Pin every package with `uv`. Ship a `Dockerfile` for independent reproduction off-Kaggle |
| Determinism, CPU | Achievable | Fixed seeds, single-threaded BLAS, fixed `PYTHONHASHSEED` |
| Determinism, GPU | **Not achievable bit-exactly.** cuDNN algorithm selection, TF32, non-deterministic atomics | Do not claim it. Assert numerical tolerance bands instead |
| CI | Cannot run GPU stages | CPU-only fixtures run bit-exactly in CI. GPU stages have recorded reference outputs and tolerance assertions, run manually and logged |
| Seeds | Logged | Every seed into the manifest |
| Weights | Versioned | Checksum every model weight file |

### Provenance manifest

Written by every stage, appended, never overwritten:

```yaml
stage: fold_counterscreen
git_commit: <sha>
kaggle_image: <name>@<digest>
packages: <uv.lock hash>
model: protenix-v2
model_weights_sha256: <...>
seeds: [...]
inputs_sha256: {...}
outputs_sha256: {...}
wall_time_s: <...>
gpu: <device name>
```

### Tolerance bands

For GPU stages, CI asserts that confidence metrics reproduce within a stated tolerance, established empirically by running the same input five times on Day 1 and recording the observed spread. **That spread is also the noise floor used in the `2 × pooled SD` gate**, so it must be measured regardless.

---

## 6. Compute strategy

See `CLAUDE.md` §10. Engineering requirements:

- **Benchmark before planning.** The Day-1 benchmark writes `benchmarks/day1_gpu_benchmark.md` with measured seconds per prediction for each model and construct size. All budgets derive from that file, not from estimates.
- **Checkpoint everything.** Kaggle sessions drop. Every stage writes its outputs to disk and is restartable from the last completed unit of work, not from the start of the stage.
- **Idempotent stages.** Re-running a stage with the same inputs and seeds must not duplicate work; check for existing outputs by content hash.
- **Queue discipline.** Order work so that the most informative candidates are scored first. If the session dies at 70%, you want the top candidates done, not a random 70%.

### Contingency ladder, in order

1. Reduce seeds at the screening tier to 2
2. Truncate the target further
3. Cut backbone count
4. Drop optional decoys D3–D5
5. Drop the AF2 orthogonal check on finalists

**Never cut:** the control panel, or the counter-screen itself. Those are the project.

---

## 7. Selection

1. Apply hard gates (`CLAUDE.md` §8). Log every rejection with its failing gate — rejection counts per gate are a reportable result.
2. Within each mechanism arm, cluster by structural similarity.
3. Take cluster representatives, not top-N by score.
4. Fill the allocation in `CLAUDE.md` §11.
5. Insert the affinity-only control at approximately rank 10.
6. Run `binder-prescreen`; any flag other than `pass` removes the design and the next cluster representative is promoted.

**Gate rejection counts belong in the report.** If one gate removes 95% of candidates, that is either the gate working or the gate being wrong, and the reader should be able to tell which.

---

## 8. Testing

| Kind | Scope |
|---|---|
| Unit | Pure functions in `score/` and `rank/` — margins, contact fractions, clustering |
| Contract | Schema of `FoldResult`, config files, provenance manifest |
| Property | Margin calculation is antisymmetric: `M(A,B) == −M(B,A)`. Gates are monotone in their inputs |
| Fixture | Known small complexes with recorded expected outputs, CPU-only, bit-exact |
| Tolerance | GPU stages against recorded references within measured bands |
| Leakage | **Assert no target appears in both train and test splits** in `evaluate/`. This is a test, not a convention |
| **Mutation, code** | Deliberate one-line defects must each kill a test. Report the mutation score. Mutant set in `CLAUDE.md` §12.4b |
| **Mutation, designs** | Scrambled, alanine-mutated and decoy-swapped designs pushed through the full ranking; measured false-accept rate with interval |
| Provenance | Assert `evaluate/` refuses controls seeded from crystal poses |
| Immutability | Assert `analyze/` never writes to `results/raw/` |
| Fit quality | Assert re-fitted K_D values carry uncertainty estimates, not bare point values |
| Occupancy | Assert `biophys/` refuses a single copy-number value and requires a range |
| **Geometry** | Assert G0 runs before any GPU stage, on a fixture with a known chain break, a known clash and a known Ramachandran outlier |
| **Target integrity** | Assert prepared targets retain the HLA α2 and β2m disulfide bonds |
| **Funnel** | Assert the reported funnel counts sum consistently stage to stage |
| Pooling | Assert the hierarchical model is fitted before the bootstrap is reported |

The last two are the ones that protect the scientific claims. Treat them as load-bearing.

---

## 9. What this architecture deliberately does not do

Cross-referenced with `CLAUDE.md` §14. Engineering-specific exclusions:

- **No service layer, no API, no web UI.** This is a batch pipeline. Adding a server adds failure modes and demonstrates nothing.
- **No database.** Files on disk with content-addressed names. The dataset is small and files are inspectable.
- **No orchestration framework beyond Snakemake.** No Airflow, no Prefect, no custom scheduler.
- **No GPU cluster abstraction.** One GPU at a time. Claiming distributed computing for an embarrassingly parallel batch job is a red flag to any reviewer who reads the code.
- **No model training.** We evaluate and combine existing models. Training a predictor on 20 designs would be meaningless.

---

## 8b. Gate ordering is an engineering constraint

G0 costs seconds; co-folding costs minutes to hours. The pipeline must enforce the ordering, not merely document it.

```
generate ──► G0 geometry ──► G1 self-consistency ──► G2-G4 co-folding ──► G6-G9 ──► rank
             (CPU, seconds)   (cheap fold)            (expensive)
```

`fold/` should refuse a candidate that has not been stamped as G0-passed. A structure that is geometrically invalid is not a cheap mistake to fold, it is a wasted GPU-hour and a number in the results that means nothing.

---

## 9b. No number is ever typed into prose

**Constraint, not a preference.** `METHODS.md` is a scored input to the competition. A stale or mistyped number there costs directly, and hand-copying results from a terminal into prose is how stale numbers happen.

**Every numeric claim in a generated document is written as a key, not a value:**

```
The measured false-accept rate was [[far.point]] (95% CI [[far.ci_lo]]–[[far.ci_hi]]).
```

`report/` resolves keys against the result files and emits the final document. A **claim checker** runs in CI and fails if:

- any key has no matching entry in the result files
- any bare numeral appears in a generated section outside a key, excluding cited literature values which carry a reference marker
- any result file is newer than the last generated document

The payoff is a sentence you can put in the methods: *every number in this report resolves mechanically to a result file.* For a document that judges read, that is a cheap and strong signal, and it is checkable by them.

Literature values are the one exception, and they carry a `[Rn]` marker tying them to `REFERENCES.md` rather than to a result file.

---

## 10. Logs that are deliverables, not debugging aids

Three append-only records are outputs of this project, not scaffolding. They must be written as they happen, because reconstructing them afterwards produces a tidy narrative instead of a record.

| File | Captures | Why it is a deliverable |
|---|---|---|
| `ADVERSARIAL_LOG.md` | Pipeline producing impossible or implausible output | Candidate findings; the basis for any edge-case contribution |
| `AGENT_ERRORS.md` | AI assistant mistakes, detection route, guard added | Directly demonstrates the evaluation competence this project is meant to evidence |
| `benchmarks/day1_gpu_benchmark.md` | Measured throughput per model and construct | Every compute decision derives from it; also the noise floor for the margin gate |
| `FINDINGS.md` | What validation changed about the design | **The document outsiders actually read.** One entry per occasion where a check altered a decision: what was believed, what the check showed, what changed |

For `AGENT_ERRORS.md`, classify each entry by detection route: automated test, human review, or downstream failure. **The proportion caught only by human review is the interesting number** — it bounds how far this process could be automated, and an honest answer there is worth more than a low count.
