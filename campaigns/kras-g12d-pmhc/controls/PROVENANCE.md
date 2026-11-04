# Control sequence provenance

`SETUP.md` §3.5 requires every control sequence recorded with its source,
accession, allele, on-target peptide, off-target peptides, residue-difference
count and expected outcome. `PROTOCOL.md` §5.0 makes this a blocking Day-1
task: Stage −1 cannot run without it.

**Status: the panel cannot yet be folded.** The targets and peptides below are
read from the published table. The **binder sequences are not published in the
preprint** — Supplementary Table 2 names the designs and gives their interface
SASA, but no amino-acid sequences appear anywhere in it (`FINDINGS.md` F-3).
Until they are obtained, the positive panel has zero foldable members.

---

## Positive panel — published pMHC-I binders

Source: Liu, Greenwood, Bonzanini et al., *Design of high specificity binders
for peptide-MHC-I complexes*, bioRxiv 2024.11.28.625793, Supplementary
Table 1 [R10]. Difficulty is the residue difference to the **nearest**
off-target, computed from the sequences rather than taken from a description.

| Design | Allele | On-target | Nearest off-target | Δ | Sequence |
|---|---|---|---|---|---|
| CTNNb1_15 | A\*03:01 | `TTAPFLSGK` | `TTAPSLSGK` (CNTTB1) | **1** | not published |
| SARS_137 | A\*02:01 | `GLMWLSYFV` | `GLAWLSLFV` (KCNK5) | 2 | not published |
| HIV_10 | A\*02:01 | `KLTPLCVTL` | `KLIPLCHQL` (CTNNAL1) | 3 | not published |
| WT1_8 | A\*02:01 | `RMFPNAPYL` | `RLFPNLPEL` (ARHGEF11) | 3 | not published |
| PAP_116 | A\*02:01 | `TLMSAMTNL` | `TLFSALTGL` (ZMPSTE24) | 3 | not published |
| MAGE_513 | A\*01:01 | `EVDPIGHLY` | `ESDPIVAQY` (TTN) | 4 | not published |
| YFV_148 | A\*02:01 | `LLWNGPIAV` | `IVWNGPVGV` (PGK2) | 4 | not published |
| gp100_T3 | A\*02:01 | `YLEPGPVTA` | `YLQPWPVDV` (ASB6) | 4 | not published |
| Mart1_5_5 | A\*02:01 | `ELAGIGILTV` | `GLMGAGIAQV` (HADHA) | 5 | not published |
| PRAME_A9 | A\*02:01 | `ALYVDSLFFL` | `ILYVDPLPMI` (ATP2A1) | 5 | not published |

**One of ten is a single-residue discrimination.** CTNNb1 S5F is a point-mutant
neoantigen against its wild-type counterpart — structurally the same problem as
this campaign's `VVVGADGVGK` against `VVVGAGGVGK`, which also differs at one
mid-peptide position. It is therefore the single most informative positive
control and **its result is reported separately from the panel aggregate**.

The other nine test multi-residue discrimination, which is an easier task than
this campaign's. Stated as a limitation in `METHODS.md` §6 and §9.

**None targets A\*11:01.** The panel establishes that a metric can resolve
peptide identity; it does not establish that it resolves one residue on this
allele.

### Against the registered floor

`PREREGISTRATION.md` §6b requires **at least 5 positive controls**, and the
go/no-go is not meaningful below that.

| | Count |
|---|---|
| Positive controls listed | 10 |
| At single-residue difficulty | **1** |
| With a foldable sequence | **0** |

**The published panel does not reach the floor at the difficulty that
matters.** Supplementary single-residue controls from `SETUP.md` §4.2 are
therefore required rather than optional — a conclusion reached by counting,
not by assumption.

## Additional positive control — the receptor from the campaign's own template

| Control | Source | Chains | Specificity | Seed provenance |
|---|---|---|---|---|
| 7OW6 TCR | Poole et al., *Nat Commun* 2022 [R12] | D (203 aa), E (246 aa) | HLA-A\*11:01 + `VVVGADGVGK` | **must be `designed`, never `crystal`** |

The same receptor appears in 7OW5 bound to the wild-type peptide, so it binds
both complexes (`FINDINGS.md` F-6). It is a positive control for *engagement*
of this pMHC, and weaker evidence for discrimination.

> **It must not be seeded from its crystal pose.** `PROTOCOL.md` §5.2 rule 1:
> initial-guess methods are seeded with the design model, so handing a control
> its deposited structure leaks the answer and makes calibration meaningless.
> `counterscreen.evaluate.panel.validate_panel` refuses a panel containing any
> control marked `crystal`.

## Supplementary single-residue controls — to acquire

Required, per the floor arithmetic above. Sources listed in `SETUP.md` §4.2:
VDJdb, IEDB, TCR3d, STCRDab, Proteinbase. What to extract: binder–pMHC or
TCR–pMHC pairs where the **same** binder was tested against peptides differing
by **one residue**, with a recorded outcome for each.

> **Prefer PDB-derived TCRs over database CDR3 records.** VDJdb and IEDB
> largely supply CDR3 loops plus V/J gene names; reconstructing full chains
> from IMGT germlines is error-prone, and the panel needs sequences that can be
> folded. Structures of TCRs bound to pMHC-I give complete chains *and*
> documented specificity in one download.

| Control | Source | Accession | Allele | On-target | Off-target | Δ | Outcome |
|---|---|---|---|---|---|---|---|
| `TO RECORD` | | | | | | | |

## Negative panel

Built per `SETUP.md` §3.3 and registered in `PREREGISTRATION.md` §4b. Each
negative carries the gate it is **registered to fail at**: a flawed design
failing for the wrong reason is a gate working by accident and will not
generalise (`PROTOCOL.md` §5.4).

| Negative control | Derivation | Registered to fail at |
|---|---|---|
| Scrambled positives | seeded shuffle, composition preserved | G1 |
| Reversed positives | sequence reversed | G1 |
| Introduced chain break | backbone cut | G0 |
| Deliberately greasy surface | apolar substitution | G5 |
| Binder docked away from the peptide | α1/α2 helices, distal | G3 |
| Near-copy of a known binder | sequence from the prescreen set | G7 or G9 |
| Decoy-target-swap design | generated against an unrelated target | G4 |

Scrambling is seeded and deterministic
(`counterscreen.evaluate.panel.scramble`): a negative control that differs
between runs is not a control. The derivation records its parent, kind and
seed.

A negative that fails at a gate other than its registered one is logged in
`FINDINGS.md` and investigated, not quietly counted as a pass.
