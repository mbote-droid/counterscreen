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

---

## F-5 · The M1 handle is 6.4 square angstrom of one oxygen, already bidentate to Arg114

**Believed.** `CLAUDE.md` §4 defines M1, the direct electrostatic readout, as
placing an Arg, Lys or His against "the carboxylate oxygens of Asp6 **not
taken by Arg114**", calls it the highest expected value of the three
mechanisms, and allocates it **9 of the 20 submissions** — the largest arm.
§3.3 cautions that the carboxylate "is **not** a free solvent-exposed handle,
and a naive 'place an Arg to salt-bridge it' strategy may have nowhere to
reach", and §18 lists "the designable surface may be too small" as a risk.
None of this was quantified.

**Checked.** Measured directly on the prepared T+ target, 7OW6 with the TCR
removed.

Contacts to the Asp6 carboxylate, polar atoms within 3.6 Å:

| Oxygen | Partners |
|---|---|
| OD1 | Arg114 NH1 (3.04 Å), Arg114 NH2 (3.34 Å) |
| OD2 | Arg114 NH2 (2.95 Å), Gln70 NE2 (3.08 Å), Gln70 OE1 (3.58 Å) |

Arg114 makes a **bidentate** salt bridge spanning both oxygens, and Gln70 caps
OD2 in addition. **There is no carboxylate oxygen not taken by Arg114.**

Solvent accessibility of the same atoms (Shrake-Rupley, 1.4 Å probe):

| Atom | SASA |
|---|---|
| OD1 | **6.4 Å²** |
| OD2 | **0.0 Å²** |
| Asp6 whole residue | 19.0 Å² |

A fully exposed aspartate side chain runs to roughly 100–120 Å², so Asp6 is
about 85% buried. Across the whole peptide:

| Position | 1 V | 2 V | 3 V | 4 G | 5 A | **6 D** | 7 G | 8 V | 9 G | 10 K |
|---|---|---|---|---|---|---|---|---|---|---|
| SASA (Å²) | 2.1 | 3.6 | 7.8 | 35.2 | 29.9 | **19.0** | 73.3 | 45.1 | 17.1 | 6.8 |

Total peptide SASA is 239.8 Å².

**Changed.** Three things follow, and the third is a decision rather than a
record.

1. **§3.3's caution is vindicated and sharpened.** The strategy it warned
   against is not merely awkward; the target it names does not exist. M1 as
   literally specified — contacting an oxygen not taken by Arg114 — cannot be
   built. What remains available is 6.4 Å² of OD1, which is already accepting
   a bidentate pair from Arg114, or competition with Gln70, whose contacts
   (3.08 and 3.58 Å) are the weaker of the two.
2. **The discriminating residue is among the least accessible on the
   peptide.** Positions 7, 8, 4 and 5 are two to four times more exposed than
   position 6. Any binder reading position 6 directly is reaching for the
   hardest point on the surface, while the signal-free positions are the easy
   ones — which is precisely the failure mode the counter-screen exists to
   detect, since a binder that grips the accessible positions binds wild type
   equally well.
3. **The 9/5/4 allocation rests on an assumption the structure does not
   support.** §4 calls M1 "where the hits probably are" and gives it nearly
   half the submissions; §11's allocation is registered in
   `PREREGISTRATION.md` §4 step 4. The measurement says M1 is the *hardest*
   arm, not the most promising, and that M2 (composite readout of the
   Asp6–Arg114–Gln70 surface, which is exactly the network measured above) and
   M3 (conformational selection, which needs no contact with the carboxylate
   at all) are better matched to what the surface offers.

   This is registered, so it is not changed here. It is raised as a proposed
   amendment. Note that the measurement does not make M1 impossible: 6.4 Å² is
   small but not zero, and a binder may read the Asp6 environment without
   touching the carboxylate. It makes M1 expensive per hit, which is an
   argument about allocation, not about feasibility.

**Caveats.** SASA is computed on the receptor-stabilised conformation with the
TCR removed; the apo surface may differ, and `FINDINGS.md` F-1 shows the apo
state has no coordinates there at all. Absolute SASA values depend on the
radius set and probe size, so the comparison between positions is the robust
part, not the individual numbers.

---

## F-6 · The only known discriminator never touches the carboxylate

**Believed.** `CLAUDE.md` §4 motivates M1 from [R9]'s finding that
discrimination on this neoantigen "proceeded through a salt bridge to the
mutant aspartate", and §5.2 rule 5 says to calibrate the G3 peptide-contact
threshold on the real TCR rather than guess it. How the 7OW6 TCR achieves
discrimination had not been measured here.

**Checked.** 7OW6 and 7OW5 carry the **same** engineered TCR — identical
203-residue alpha and 246-residue beta sequences; the differing modelled
lengths are disorder, not different constructs — bound to G12D and wild-type
peptide respectively. That makes them a controlled pair.

*What the TCR touches*, heavy atoms within 4.0 Å:

| | Contacts |
|---|---|
| TCR → peptide | 29 |
| TCR → HLA | 107 |
| **Peptide-contact fraction** | **0.213** |

Distributed across the peptide as:

| Position | 1 V | 2 V | 3 V | 4 G | 5 A | **6 D** | 7 G | 8 V | 9 G | 10 K |
|---|---|---|---|---|---|---|---|---|---|---|
| TCR contacts | 0 | 0 | 0 | 1 | 2 | **1** | **18** | 4 | 3 | 0 |

**The closest TCR atom to an Asp6 carboxylate oxygen is 7.51 Å.** The TCR does
not engage the discriminating group at all. Its HLA contacts concentrate on
the alpha-1 helix — Arg65 (23), Gln62 (16), Gln155 (12), Glu58, Thr73, Ala69 —
and not on the Arg114/Gln70 pair that coordinates the aspartate.

*What the substitution does to the peptide.* Superposing the two structures on
the HLA alpha-1/alpha-2 platform (179 CA, RMSD 0.276 Å) and comparing peptide
CA positions:

| Position | 1 | 2 | 3 | 4 | 5 | **6** | 7 | 8 | 9 | 10 |
|---|---|---|---|---|---|---|---|---|---|---|
| CA shift (Å) | 0.12 | 0.13 | 0.11 | 0.04 | 0.26 | **0.96** | 0.78 | 0.51 | 0.64 | 0.33 |

Positions 1–5 are static. The substitution displaces position 6 by about 1 Å
and that displacement **propagates forward to positions 7–9**.

**Changed.** The three observations compose into a mechanism, and it is not
the one M1 describes.

Position 6 carries the chemistry but is 85% buried with no free carboxylate
oxygen (F-5). Positions 7–9 carry no sequence difference at all — they are
identical between mutant and wild type — but they are the accessible ones
(73.3, 45.1, 17.1 Å²) **and they move when position 6 changes**. The TCR reads
exactly there: 18 of its 29 peptide contacts land on position 7, which shifts
0.78 Å between the two complexes.

So discrimination is available *indirectly*: read the geometry of the
accessible positions, not the chemistry of the buried one. That is
conformational selection, which is **M3**, read out at residues that are
sequence-identical between the two targets. It is close to M2 in spirit but
distinct in detail: the surface that differs is not the
Asp6–Arg114–Gln70 network the TCR ignores, but the downstream backbone.

**This strengthens the case for amending the 9/5/4 allocation** raised in F-5.
The only worked solution to this exact discrimination problem uses the
mechanism currently allocated four designs, and avoids the one allocated nine.

**Caveats, which matter here.**
- The same TCR binds **both** complexes. Poole et al. solved the pair to study
  specificity; this is a high-affinity engineered receptor, not a clean
  discriminator, so "how it binds" is better evidenced than "how it
  discriminates".
- A 0.96 Å CA shift is modest. At typical coordinate error it is perhaps three
  to four times the noise, and the two structures are different crystals.
- The G3 reference of 0.213 is from **one** TCR. §5.2 rule 5 asks for the
  distribution across the TCR *and* the Liu binders; the latter have no
  published sequences (F-3), so the threshold currently rests on a single
  observation and should be reported as such.
- [R9] reported salt-bridge discrimination on the **9-mer** on 9UV8, a
  different peptide length and a different structure. These results do not
  contradict it; they say it does not transfer to the 10-mer complex.


---

## F-7 · Deriving the hotspots narrowed M1 further than A8 allowed for

**Believed.** Amendment A8 redefined M1, after F-5, as targeting either the
solvent-accessible face of OD1 **or** displacement of the weaker Gln70
contacts to OD2 at 3.08 Å and 3.58 Å. Two routes were thought to remain.

**Checked.** Deriving the M1 hotspot scheme from the prepared target rather
than writing residue numbers by hand. The rule selects carboxylate oxygens a
probe can reach, then the HLA residues hydrogen-bonding *those* oxygens,
excluding arginine. It returned a single hotspot: the aspartate itself, on
OD1.

Gln70 did not appear, and the reason is that the two conditions do not
intersect. Gln70 coordinates **OD2**, whose SASA is **0.0 Å²**. A binder
approaching from solvent cannot reach OD2 to compete for it. The only
reachable oxygen, OD1, is coordinated solely by Arg114, which is not
displaceable.

**Changed.** The second of A8's two routes is closed. **M1 reduces to one
thing: contact the 6.4 Å² accessible face of OD1.** A8 is not wrong, but it
offered an option the geometry does not support, and that would not have
surfaced if the hotspots had been typed from a figure instead of derived. The
arm is still not retired — 6.4 Å² is reachable — but it is now a single
narrow target rather than a choice of two.

For contrast, the same derivation applied to the other arms produced:

| Arm | Hotspots | Rule |
|---|---|---|
| M1 | `C6` | reachable carboxylate oxygens plus displaceable partners |
| M2 | `A70, A73, A77, A97, A114, A147, A155, A156` | HLA within 5 Å of the aspartate side chain |
| M3 | `C6, C7, C8, C9` | CA displacement ≥ 0.4 Å between complexes **and** SASA ≥ 10 Å² |

M2 recovers the Asp6-Arg114-Gln70 network §4 names and adds Thr73, Asp77,
Ile97, Trp147, Gln155 and Gln156, which the specification did not list. M3
recovers exactly the propagating displacement of F-6.
