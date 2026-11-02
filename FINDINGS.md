# FINDINGS.md — what validation changed about the design

One entry per occasion where a check altered a decision: what was believed,
what the check showed, what changed. Written as it happens, because
reconstructing this afterwards produces a tidy narrative instead of a record.

Nothing here is a result about a design. These are findings about the
*inputs* and the *specification*.

---

## F-1 · 7OW4 has no density at the discriminating residue, in all four copies

**Believed.** The challenge page states that peptide positions 5 and 6 have no
coordinates in 7OW4, the receptor-free G12D structure (`CLAUDE.md` §3.3).
`SETUP.md` §3.4 says to confirm this rather than trust it.

**Checked.** Parsed 7OW4 directly and listed which peptide residues carry
atoms, per chain. The asymmetric unit holds four crystallographically
independent copies of the peptide, chains C, F, I and L.

| Copy | Peptide residues present |
|---|---|
| C | `VVVG__GVGK` |
| F | `VVVG__GVGK` |
| I | `VVVG__GVGK` |
| L | `VVVG__GVGK` |

Positions 5 (Ala) and 6 (Asp) are absent in **every** copy. By contrast, 7OW5
and 7OW6 — both receptor-bound — carry complete 10-mers.

**Changed.** The claim is confirmed and is stronger than stated. It is not one
modelling choice in one copy; it is systematic disorder reproduced four times
independently, and the receptor demonstrably orders the loop. This strengthens
the candidate finding in `CLAUDE.md` §12.3: the residue carrying the entire
discrimination signal is experimentally undetermined in the unbound state, and
how a structure predictor behaves when the discriminating atoms are
undetermined is a specific, genuine, under-characterised question. The
assumption stated in `METHODS.md` §2 — that designs target a receptor-stabilised
conformation that may not be populated before binding — is now evidenced rather
than asserted.

---

## F-2 · REFERENCES [R11] attributes the wrong PDB accession

**Believed.** `REFERENCES.md` [R11], labelled `verified`, cites Zhu et al.,
*Commun Biol* 9:26 (2026) for crystal structures of HLA-A\*11:01 with six G12
mutant peptides, and gives PDB **7OW3**. `DESIGN.md` §2 builds the optional
decoys D3–D5 from those structures.

**Checked.** Read the primary citation recorded inside 7OW3 itself:

> *Therapeutic high affinity T cell receptor targeting a KRAS G12D cancer
> neoantigen* — Poole, Karuppiah, Hartt, Haidar, Moureau et al.,
> *Nat Commun* (2022), DOI 10.1038/s41467-022-32811-1

7OW3 belongs to the Poole et al. 2022 deposition group, the same as
7OW4/7OW5/7OW6 ([R12]). Its contents are HLA-A\*11:01 with the **wild-type**
10-mer `VVVGAGGVGK` and no TCR — not a G12 mutant series. A single accession
could not have carried six structures in any case.

**Changed.** [R11]'s accession is wrong despite its `verified` label, and the
Zhu G12V/G12C/G12R codes remain unknown. **D3–D5 cannot be built** until they
are resolved from the paper's data-availability statement. Entry [R11] should
be corrected and its confidence label revisited. Separately, 7OW3 is useful in
its own right as a wild-type 10-mer apo structure, but it must **not** be
substituted for 7OW5 as D1: T+ comes from a receptor-bound structure, so an apo
D1 would differ in conformational state as well as in sequence, and the margin
would partly measure that instead of the substitution.

---

## F-3 · The Liu main text carries no binder sequences

**Believed.** `SETUP.md` §1 lists the Liu et al. supplement and paper as on
disk, and §3.1 says to extract binder name, sequence, allele, on-target and
off-target peptides from Supplementary Table 1.

**Checked.** Extracted the full text of the supplied PDF
(bioRxiv 2024.11.28.625793, *Design of high specificity binders for
peptide-MHC-I complexes*). It contains **no amino-acid string longer than 24
residues** and no supplementary table. It is the main text only; the
designed-binder sequences are in a separate supplementary file.

The residue-difference analysis of §3.2 was verified for the pairs the main
text does name:

| Case | On-target | Off-target | Differences |
|---|---|---|---|
| CTNNB1 S5F, A\*03:01 | `TTAPFLSGK` | `TTAPSLSGK` | **1**, at position 5 |
| SARS-CoV1, A\*02:01 | `GLMWLSYFV` | `GLAWLSLFV` | 2 |
| MAGE-A3 vs Titin, A\*01:01 | `EVDPIGHLY` | `ESDPIVAQY` | 4 |
| *Our campaign* | `VVVGADGVGK` | `VVVGAGGVGK` | **1**, at position 6 |

**Changed.** §3.2's table and its conclusion are confirmed: CTNNB1 S5F is the
only true single-residue discrimination in the panel, and it is structurally
the same problem as ours — one substitution, mid-peptide. Stage −1 remains
blocked on the supplement, and the registered floor of five single-residue
positive controls (`PREREGISTRATION.md` §6b) still requires the supplementary
controls of `SETUP.md` §4.2.

---

## F-4 · The claim checker, written to the letter, rejects its own document

**Believed.** `DESIGN.md` §9b registers one exception to the no-bare-numerals
rule: a literature value carrying a reference marker.

**Checked.** Implemented the checker to that letter and ran it on text in the
shape of `METHODS.md`. It rejects headings, numbered lists, section
cross-references, table rules, ratios such as `1:1`, and — the one that
matters — the stated confidence level in `(95% CI [[far.ci_lo]]-[[far.ci_hi]])`,
which §8.5 already writes bare beside the keys it qualifies.

**Changed.** Each of these is document structure or a registered design choice
rather than a measured claim, so each is masked before the scan, named as a
pattern, and covered by a test. They are additions to the registered rule and
are listed in the module docstring so they can be argued with. The alternative
is to make the confidence level a key as well, at the cost of clumsier prose.
Open for decision.
