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

## F-3 · The Liu panel holds one single-residue control, not five

**Believed.** `SETUP.md` §3.1 says to extract the panel from Supplementary
Table 1, and §3.2 states that only CTNNB1 S5F is a true single-residue
discrimination, with others at 3 to 7 differences. `CLAUDE.md` §5.1 and §5.4
describe an intended panel of **18 published binders** plus the 7OW6 TCR,
giving n = 19 and a rule-of-three false-reject bound "near 16%".

**Checked.** Supplementary Tables 1 and 2 are present in the preprint as
page images, which is why a text search of the PDF finds nothing. Read
directly, Table 1 gives every allele, target, on-target peptide and
off-target peptides; Table 2 gives the design names and interface SASA.
Counting differences between each on-target peptide and its *nearest*
off-target:

| Target | On-target | Nearest off-target | Differences |
|---|---|---|---|
| CTNNB1 (S5F), A\*03:01 | `TTAPFLSGK` | `TTAPSLSGK` (CNTTB1) | **1** |
| SARS-CoV M, A\*02:01 | `GLMWLSYFV` | `GLAWLSLFV` (KCNK5) | 2 |
| HIV-Env, A\*02:01 | `KLTPLCVTL` | `KLIPLCHQL` (CTNNAL1) | 3 |
| WT1, A\*02:01 | `RMFPNAPYL` | `RLFPNLPEL` (ARHGEF11) | 3 |
| PAP, A\*02:01 | `TLMSAMTNL` | `TLFSALTGL` (ZMPSTE24) | 3 |
| MAGE-A3, A\*01:01 | `EVDPIGHLY` | `ESDPIVAQY` (TTN) | 4 |
| YFV NS4b, A\*02:01 | `LLWNGPIAV` | `IVWNGPVGV` (PGK2) | 4 |
| gp100, A\*02:01 | `YLEPGPVTA` | `YLQPWPVDV` (ASB6) | 4 |
| MART-1, A\*02:01 | `ELAGIGILTV` | `GLMGAGIAQV` (HADHA) | 5 |
| PRAME, A\*02:01 | `ALYVDSLFFL` | `ILYVDPLPMI` (ATP2A1) | 5 |
| *Our campaign* | `VVVGADGVGK` | `VVVGAGGVGK` | **1**, at position 6 |

**Changed.** Three corrections, each affecting a registered number.

1. §3.2's conclusion is confirmed and is exact: **one** target in ten is a
   single-residue discrimination, and it is structurally our problem — one
   mid-peptide substitution. Its range is 1 to 5 differences, not the 3 to 7
   §3.2 estimates for the remainder.
2. **The panel is ten designs, not eighteen.** Table 1 lists ten targets and
   Table 2 thirteen rows, of which three are reference TCRs. The figure of 18
   in `CLAUDE.md` §5.1 does not match the source. This changes §5.4's
   arithmetic: with the TCR the panel is about 11, so the rule-of-three upper
   bound on the false-reject rate is near **27%**, not the 16% stated for
   n = 19.
3. **The binder sequences are still absent.** Table 2 names the designs
   (MAGE_513, HIV_10, PRAME_A9, CTNNb1_15 and the rest) and gives their
   interface SASA, but no amino-acid sequences appear anywhere in the
   preprint. Stage -1 needs sequences to fold, so it remains blocked, and the
   §6b floor of five single-residue positive controls still requires the
   supplementary controls of `SETUP.md` §4.2 — now demonstrably, since the
   panel supplies one.

> An earlier note in this file claimed the preprint contained no
> supplementary table. That was wrong: the tables are page images and the
> text extraction missed them. Corrected here rather than edited away.

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
