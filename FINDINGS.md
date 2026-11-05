# FINDINGS.md — what validation changed about the design

One entry per occasion where a check altered a decision: what was believed,
what the check showed, what changed. Written as it happens, because
reconstructing this afterwards produces a tidy narrative instead of a record.

Nothing here is a result about a design. These are findings about the
*inputs* and the *specification*.

## When an entry is owed

Named explicitly because the two entries that arrived late were both of kind
(c), which had no name until F-10 gave it one. An entry is owed whenever:

- **(a) a check rejected something it was built to accept** — a positive
  control failing a gate, which `PROTOCOL.md` §5.3 already says means the gate
  is wrong rather than the control. F-9.
- **(b) a belief written into a specification file turned out to be false** —
  a handle that does not exist, an accession that cannot be right, a panel
  that does not reach its own floor. F-2, F-3, F-5, F-8.
- **(c) a guard turned out not to cover the class it was assumed to cover** —
  not a guard that failed, a guard that worked on a narrower class than the
  confidence it created. F-4, F-10.

A fix with a regression test and no change in belief is a build issue, not a
finding, and belongs in `BUILD_JOURNAL.md`. The distinction is whether a
reader of the specification would now read it differently.

---

## How strong is each finding, and what does it license

Added because the distinction was being made in discussion and not on the
record. A finding's evidence class governs what may be written from it, and a
reader of a preprint cannot infer that from the finding alone.

| | Evidence class | What it licenses | What it does **not** license |
|---|---|---|---|
| **F-1** | Direct observation, four independent copies | That the discriminating residue is experimentally undetermined in the apo state | Any claim about *why*, or about what a predictor does with it — that is the open question, not the answer |
| **F-2** | Documentary, decisive | That [R11]'s accession is wrong and D3–D5 are unbuildable | Nothing about the Zhu structures themselves, which remain unread |
| **F-3** | Direct count from published sequences | That the panel supplies one single-residue control against a floor of five, and F-16 that **none of them is runnable** | Nothing about whether the Liu binders work, which is their own paper's result |
| **F-4** | Self-referential | That the registered rule rejects its own document | Nothing scientific |
| **F-5** | Standard measurement, one structure | That M1's specified handle does not exist and Asp6 is largely buried | **Not a discovery.** `PROTOCOL.md` §3.3 predicted this in prose; the contribution is quantifying it and acting before GPU spend. SASA and contact distances on a deposited structure are routine |
| **F-6** | Controlled structural comparison | That the known discriminator reads accessible positions that move rather than the buried one that changes | **The substantive finding.** Still one receptor, one structure pair, and that receptor binds both complexes — so it evidences *how it binds* more strongly than *how it discriminates* |
| **F-7** | Derivation from F-5 | That M1 reduces to a single target | A corollary of F-5, not independent evidence |
| **F-8** | Direct power measurement on a synthetic two-site curve | That the registered 1:1 adequacy test has no power at the series length a real SPR experiment supplies, so it belongs on kinetic residuals | Nothing about whether the returned fits *are* 1:1 adequate — that needs the sensorgrams. The power figures are for one two-site curve, not a general power curve |
| **F-9** | Negative control on five deposited structures | That the gate as first written rejected experimentally determined coordinates, and that two implementation defects caused it | Nothing about the 1% threshold, which never moved. It does not license calling the gate validated: five structures of one complex class is not a validation set |
| **F-10** | Complete audit of the repository's hand-maintained document facts, n = 5 | That numeric provenance covering a document's *values* leaves its claims *about itself* unguarded, and that in this project 4 of 5 such facts were wrong | Nothing about other projects' tooling. Only hand-maintained facts were audited, so it does not license "these were the only unguarded claims" |
| **F-11** | Direct measurement of every disulfide in the prepared targets, n = 13 | That the clash cutoff and the disulfide assertion can contradict each other, and that whether a structure passes depends on refinement rather than geometry | Nothing about how often this fires in deposited structures generally — 13 bonds from two crystals of one complex. It does not license a claim that the 2.0 Å cutoff is otherwise correct |
| **F-12** | Negative control on a sixth deposited structure | That G0 counted an unmodelled region as six defects, and that F-9's calibration was incomplete rather than wrong | Nothing about generated backbones, where numbering is consecutive and the two cases cannot overlap. Six of six structures passing is still six, from one deposition group |
| **F-13** | Complete census of alternate conformers in the five source files | That conformer selection was being made by file order at half occupancy, and that Gln70 — an M1 target under A8 — is one of them | Nothing about which conformer is right; at 0.5/0.5 the data does not say. It is one apo structure, so it does not license a claim that Gln70 is mobile when a receptor is bound |
| **F-14** | Re-measurement with the coercion removed | That F-5's zero is a measured zero, and that the path it came through could not have distinguished one | Nothing further about Asp6. The audit covers this project's SASA path only |
| **F-15** | Direct measurement over 1,409 residues of five experimental structures | That the improper-dihedral sign convention for L-amino acids is as assumed, so the chirality check is correctly oriented | Nothing about the Ramachandran criterion, which remains the coarse approximation F-9 left it. Confirming a sign is not validating the gate |
| **F-16** | Direct test of the go/no-go logic | That the floor could be met by controls that cannot be folded, and that the published panel supplies **zero** runnable single-residue controls rather than one | Nothing about whether the Liu binders work. It sharpens F-3's count; it does not add evidence about the panel itself |
| **F-17** | Direct measurement on a synthetic curve with a known K_D, n = 2 noise levels | That a fit can report a K_D 154× above the highest concentration tested with 0.34 relative error and no flag, and that the existing guards cannot see it | Nothing about the returned data, which does not exist yet. Two noise levels on one curve shape, so the 4-fold spread is an illustration, not a general error model |
| **F-18** | Exact algebraic identity, verified against the mass-action code to machine precision | That realised discrimination is `r(1 − x) + x` in target occupancy, so a K_D ratio is its best case at vanishing dose | **No new biology.** Mass action is textbook, and the identity follows in two lines. It licenses a claim-discipline requirement — a ratio means nothing without a stated occupancy — not a discovery |
| **F-19** | Reasoning from the metric's construction, supported by the chain composition of the prepared decoys | That `M_pep` and `M_var` compare complexes of different composition, so part of each is normalisation rather than discrimination, and that the registered invariant-surface control measures that bias | **Not yet measured.** No model has been run, so the bias's size and sign are argued from how interface metrics are normalised, not observed. It licenses treating the invariant control's `M_pep` as a calibration; it does not license a correction before that number exists |

**Ranked by what a reader should care about: F-6, then F-1, then F-8 and F-18,
then the rest.** F-6 proposes a mechanism with a testable consequence — that a binder
reading positions 7–9 geometry can discriminate without contacting position 6.
F-1 poses a question nobody has answered. F-8 is transferable: anyone testing
1:1 adequacy on an eight-point isotherm is reporting statistical power rather
than a binding model, and that mistake is not specific to this project. F-5
and F-7 are engineering diligence: they corrected a plan before it cost
anything, which is valuable to this project and not a contribution to the
field. F-18 is transferable for the same reason as F-8 and in the same
place — a reported affinity ratio without a stated occupancy is a best case,
not a property — though it is textbook mass action rather than anything new.
F-9 to F-17 are findings about this build's own instruments: a gate that
rejected its positive controls, a guard aimed at the wrong class of fact, a
clash cutoff contradicting a disulfide assertion, a reader choosing
conformers by file order, and a re-fitter reporting a K_D its data could not
determine. They are the premortem's output, and they are engineering rather
than science. F-19 is the one of that group with a claim attached: it says
`M_pep` is partly an artefact of how interface confidence is normalised, and
that the registered invariant-surface control is the instrument that measures
it.

None of them is a result about a design. Nothing in this pipeline has been
run.

---

## F-1 · 7OW4 has no density at the discriminating residue, in all four copies

**Believed.** The challenge page states that peptide positions 5 and 6 have no
coordinates in 7OW4, the receptor-free G12D structure (`PROTOCOL.md` §3.3).
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
the candidate finding in `PROTOCOL.md` §12.3: the residue carrying the entire
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
discrimination, with others at 3 to 7 differences. `PROTOCOL.md` §5.1 and §5.4
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
   in `PROTOCOL.md` §5.1 does not match the source. This changes §5.4's
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

> **Sharpened by F-16, 5 November.** The shortfall is the full five, not four.
> The one qualifying single-residue control is one of these designs, so it has
> no sequence either and cannot be folded. The panel supplies **zero** runnable
> single-residue controls, and the go/no-go has none of its registered input
> rather than a fifth of it.

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

**Changed.** Headings, numbered lists, section cross-references, table rules,
ratios and inline code are document structure rather than measured claims, so
each is masked before the scan, named as a pattern, and covered by a test.
They are additions to the registered rule and are listed in the module
docstring so they can be argued with.

**Decided, 4 November.** The confidence level is *not* masked. It looked like
the clearest case for an exclusion — a registered design choice, not a
measurement — but it is the one number in that sentence that can go stale
against the code: the interval is computed from
`counterscreen.core.intervals.CONFIDENCE_LEVEL`, and prose repeating the level
by hand disagrees with the computation as soon as either moves. Exempting it
would have defeated the rule at the point the rule is for. Registered
constants are instead citable as keys, so `METHODS.md` §8.5 now reads
`` `[[ci.level]]` CI ``; a result file cannot shadow them, and the normal
quantile is derived from the level rather than written beside it, so the two
cannot disagree either. The cost is one more key in the prose, which is the
cheaper of the two mistakes.

---

## F-5 · The M1 handle is 6.4 square angstrom of one oxygen, already bidentate to Arg114

**Believed.** `PROTOCOL.md` §4 defines M1, the direct electrostatic readout, as
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

**Believed.** `PROTOCOL.md` §4 motivates M1 from [R9]'s finding that
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


---

## F-8 · The 1:1 adequacy test has no power on a steady-state isotherm

**Believed.** `PROTOCOL.md` §12.5 item 2 requires testing the 1:1 Langmuir
assumption by inspecting fit residuals, and trying heterogeneous-ligand or
two-state models where 1:1 fits badly. The implicit assumption was that
residual inspection on the fitted isotherm would detect inadequacy.

**Checked.** Implemented the Wald-Wolfowitz runs test on residual signs — it
detects systematic curvature without needing an alternative model fitted —
then measured its power directly. A synthetic two-site curve (60% of R_max at
K_D 2 nM, 40% at 400 nM) was fitted as 1:1 at several series lengths:

| Concentration points | Runs-test z | Flags 1:1 as inadequate |
|---|---|---|
| 8 | −1.44 | **no** |
| 16 | −3.09 | yes |
| 32 | −5.02 | yes |
| 64 | −7.56 | yes |

**Changed.** The diagnostic is sound but **cannot be applied where it was
assumed to apply**. A typical SPR experiment uses five to eight
concentrations, and at eight points a two-site curve differing this markedly
from 1:1 goes undetected at α = 0.05. Reporting "residuals show no structure"
from an eight-point isotherm would be a statement about statistical power, not
about the binding model.

The test therefore belongs on the **kinetic time-course residuals**, where a
single sensorgram contributes hundreds of points, rather than on the
steady-state isotherm. `METHODS.md` §8.2 should say which residuals were
tested, and report the series length alongside any claim that the 1:1 fit was
adequate.

**A second limitation found in the same work.** Specificity ratios propagate
uncertainty by the delta-method identity `sigma_ln(x) ~= sigma_x / x`, which
is first order and degrades as relative error grows — accurate below roughly
30% relative error, unreliable by 100%. Poorly determined fits need a
bootstrap over residuals, or refitting with `ln K_D` as the parameter. The
relative standard error is reported alongside every ratio so the regime is
visible. Recorded here because a ratio interval that is itself unreliable is
exactly the kind of number that reads as rigour without being it.


---

## F-9 · Experimentally determined structures failed the geometric validity gate

**Believed.** Gate G0 exists to reject non-physical generated backbones before
GPU time is spent on them (`PROTOCOL.md` §8). Its Ramachandran criterion was
documented from the start as a coarse region test rather than a reference
contour, with the stated expectation that it "will over-report in the tails".
How badly was unmeasured.

**Checked.** Running G0 over the five prepared targets — all derived from
deposited crystal structures — as part of building the workflow:

| Structure | Outlier fraction | Verdict |
|---|---|---|
| T+ (7OW6, full) | 0.5% | pass |
| D2 (peptide-free) | 0.5% | pass |
| **D1 (7OW5, full)** | **1.1%** | **fail** |
| **T+ platform** | **1.1%** | **fail** |
| **D1 platform** | **1.6%** | **fail** |

`PROTOCOL.md` §5.3 governs this case directly: *a positive control failing a
gate is a false reject, and it means the gate is wrong, not the control.*
Experimentally solved coordinates are the strongest positive control available
for geometric validity.

Diagnosing the four flagged residues in D1 showed that **three were artefacts
of how the regions were drawn, not conformations**:

| Residue | φ, ψ | Cause |
|---|---|---|
| Gly16 | 100, −59 | Fell in a 10° band between two adjacent rectangles |
| Gly162 | −112, −99 | 9° below a box edge, in the same kind of gap |
| His84 | **178**, 138 | φ near +180; the regions did not wrap, so a residue 2° from the beta basin edge was treated as far from it |
| Asp29 | 45, −133 | A genuinely unusual conformation |

**Changed.** Two defects in the implementation, both structural rather than a
matter of threshold:

1. **Adjacent basins now meet.** The right-handed alpha box ended at ψ = 50
   and the beta box began at ψ = 60, so a residue was an outlier purely for
   sitting between two rectangles. They are now contiguous.
2. **φ and ψ are treated as periodic.** Boxes covering φ near +180 were added
   and angles are folded into [−180, 180) before testing.

All five structures now pass, at 0.26% outliers for D1 — the single genuine
one. The gate was **not** loosened in threshold: 1% stands as registered, the
deliberately disallowed conformation φ = ψ = 0 is still rejected for both
alanine and glycine, a wholly disallowed chain still fails at 100%, and the
mirrored-chirality check is untouched. Four regression tests pin this,
including one asserting that every deposited structure passes.

**Why this matters beyond the fix.** Had this not surfaced, G0 would have
rejected roughly 1% of *correct* geometry. Applied to generated backbones it
would have produced a false-reject rate attributable to the gate's
implementation rather than to the designs, and the funnel would have reported
it as designs failing. The project's own false-reject discipline (§5.4) exists
for exactly this, and it was found by running the gate against reality rather
than against synthetic fixtures — which had all passed.

**Still owed.** The criterion remains coarse. The differential test against a
reference implementation (`build_rules.pdf` §2.7) is still outstanding; what
has changed is that it now agrees with five experimental structures rather
than disagreeing with three of them.

---

## F-10 · The numeric guard covered the documents' values, not their claims about themselves

**Believed.** `DESIGN.md` §9b was treated as the answer to stale numbers in
prose: every value in a generated document is written as a key, resolved from
a result file, and CI fails on a bare numeral, an unknown key, or a document
older than its inputs. With that in place the documents were considered
guarded, and the remaining risk was taken to be the one the checker itself
names — a correct value attached to the wrong concept.

**Checked.** Amendment A10 moved G8 to the front of the gate cascade, which
changes every per-stage funnel count while changing no survivor at all. That
made the funnel tables worth re-reading, and the re-read turned into a census:
every fact a document asserts *about itself*, rather than every value *in*
it. Five such facts existed. Four were wrong.

| Hand-maintained document fact | State when audited |
|---|---|
| `METHODS.md` §8.7 funnel row order | Wrong. G5 listed after G4 — an ordering the pipeline never ran, in any version |
| Campaign `REPORT.md` funnel row order | Correct until A10, stale after it, with nothing to notice |
| `REQUIREMENTS.md` coverage counts | Wrong. Claimed 43 verified of 49, against 57 rows of which 53 were verified |
| `REQUIREMENTS.md` identifiers | Wrong. A new row was added as G-08, which already existed |
| `FINDINGS.md` evidence-class table | Wrong. Stopped at F-7 while F-8 and F-9 existed — found while writing this entry |

**What it shows.** The four kinds of fact the checker cannot see are the
**order** of rows, a **count** of rows, an **identifier**, and a table's
**coverage** of its own document. Each of these resolves perfectly under the
claim checker, because each is about the document's structure rather than
about a number in it.

The funnel is the sharpest case. A per-stage count means nothing except
relative to the stages before it, so a correct count in the wrong row is
*worse* than a missing one: it reads as a result, it survives every check, and
the pipeline it describes was never run. The same holds for a results table in
a manuscript — row order is a claim, and nothing in a reference manager or a
figure script checks it.

The ratio is what makes this a finding rather than three incidents. These were
not sampled; the census was complete, and 4 of 5 were wrong after the *values*
in the same documents had been machine-resolved for three days. The guard did
not fail. It was pointed at one class of fact, and its success there is what
made the adjacent class feel covered.

**Changed.** Each of the five is now derived from the code or asserted against
it: `tests/contract/test_funnel_documents.py` parses the funnel keys out of
both documents and compares them with `PIPELINE_ORDER`;
`test_requirements_document.py` recounts the rows against the coverage table,
requires a verification method on every verified row, and requires unique
identifiers — which is what caught the collision on its first run;
`test_findings_document.py` requires every `F-n` here to have an evidence-class
row. `BUILD_JOURNAL.md` ISSUE-017 to ISSUE-020 carry the individual cases.

**The general form, which is the part worth keeping.** `DECISIONS.md` D-6
argues that guards which make an error inexpressible beat guards that detect
it. This finding adds the failure mode of a *successful* guard: it defines a
class of fact as handled, and the facts just outside that class inherit the
confidence without inheriting the guard. Asking what a passing check does
**not** cover is a different question from asking whether it passes, and only
the first one found these.

---

## F-11 · G0's clash cutoff sits 0.02 Å below a real disulfide

**Believed.** G0's clash check and the disulfide assertion of `PROTOCOL.md`
§3.1 were treated as independent: one rejects atoms too close to be physical,
the other confirms the HLA α2 and β2m disulfides survived preparation.

**Checked.** Every disulfide in the five prepared targets, measured:

| Target | SG–SG distances (Å) |
|---|---|
| T+ | 2.066, 2.049, 2.024 |
| D1 | 2.079, 2.020, 2.037 |
| D2 | 2.066, 2.049, 2.024 |

The registered clash cutoff is **2.0 Å**. The closest disulfide in the project
is **2.020 Å**. Raising the cutoff to 2.2 Å — still well inside the range a
clash check is meant to cover — makes G0 report exactly three clashes in T+,
and all three are SG–SG pairs: the structure's own disulfides.

**Why the margin is not reassuring.** A disulfide bond is ~2.05 Å and refined
values below 2.0 Å are ordinary, so whether a structure passes depends on
refinement rather than on geometry. Worse, the two gates **push designs into
this corner**: G8 requires no free cysteine, so any submitted design
containing cysteine carries a disulfide, and G0 — which runs second under
amendment A10 — would then judge a bond at ideal 2.03 Å against a 2.0 Å
cutoff. A design could fail G0 for carrying the feature G8 requires.

**Changed.** `_clashes` takes the bonded pairs it must not judge, and
`check_geometry` passes it the disulfides it has already found. The cutoff is
unchanged at 2.0 Å. A test asserts no clash at a 2.2 Å cutoff, so what is
pinned is the exclusion rather than the cutoff's luck.

**The general point.** The clash rule already excluded same-chain adjacent
residues as "bonded or one-three neighbours", so the *concept* of exempting a
bond was present and one bond type was missed — the only one that is not
backbone-adjacent. A rule stated over a proxy for bonding (sequence
adjacency) silently omits every bond the proxy cannot see.

---

## F-12 · An unmodelled loop was read as a chain break, six times over

**Believed.** F-9 corrected G0's Ramachandran regions, after which all five
prepared targets passed, and the gate was taken to be calibrated against
experimental reality.

**Checked.** 7OW4 — the sixth deposited structure, and the one F-1 is about —
still failed, and for a different reason. All four peptide copies are numbered
**4 then 7**: positions 5 and 6 were never modelled, which is precisely F-1's
missing density at the discriminating residue. G0 measured 7.0–7.7 Å across
each gap and reported four chain breaks. Because φ, ψ and ω were taken from
list-adjacent rather than bonded residues, the ω spanning one gap also came
back as a cis-peptide. **Six false defects in a structure that has none.**

**Changed.** A chain break is now consecutive *numbering* with a non-bonded
distance — the backbone claims to continue and the coordinates say otherwise,
which is the defect `PREREGISTRATION.md` §3 registers. A jump in numbering is
a `ChainGap`: recorded, reported, and not judged, because the chain never
claimed to continue. Dihedrals are computed only between numerically
consecutive residues. 7OW4 now passes with four gaps and no defects, so the
count against experimental reality is **6 of 6**.

**Not a loophole.** Generated backbones are numbered consecutively by
construction, so for a design the two cases cannot overlap: a 7 Å jump with
consecutive numbering is still a break and still fails. A test pins both
directions.

**What this says about F-9.** F-9 fixed the two artefacts it found and
declared the gate calibrated on the evidence then available — five structures,
none with an unmodelled region. The conclusion was sound and incomplete, and
the incompleteness was invisible because the test set did not contain the case.
A gate validated on five structures of one preparation pipeline is validated
against that pipeline, not against crystallography.

---

## F-13 · Alternate conformers were resolved by file order, and one of them is Gln70

**Believed.** The mmCIF reader dropped HETATM records and was otherwise taken
to read what the depositors modelled.

**Checked.** It ignored `label_alt_id`. Residues indexed by (chain, number,
atom name) collided, and the assignment kept whichever row came **last** —
the B conformer. Counting what was there:

| Structure | Residues with alternates | Largest A↔B separation |
|---|---|---|
| 7OW3, 7OW6, 9UV8 | 0 | — |
| 7OW5 | 1 — Arg111 of TCR chain E | 9.70 Å at NH2 |
| 7OW4 | 5 — **Gln70 of HLA chain A**, Glu212, His13 ×2, Val27 | 6.09 Å at Gln70 NE2 |

Each is modelled at **0.5 occupancy**, so neither conformer is the right one
and the file order was deciding.

**Gln70 is the one that matters.** `PROTOCOL.md` §4, as redefined by amendment
A8, names it: M1 now targets the solvent-accessible face of OD1 **or
displacement of the Gln70 contacts to OD2**. The residue one of three
mechanism arms is aimed at is modelled in two half-occupied conformations
6.1 Å apart at the contacting atom, in the apo structure. That bears on M1's
feasibility independently of F-5, and in the same direction: a side chain that
cannot be placed at half occupancy is not a fixed handle to design against. It
also sharpens F-1 — in 7OW4 the discriminating residue has no density *and*
one of its two coordinating partners has two positions.

**Changed, and what it did not change.** The reader keeps one conformer by a
stated rule, `alternate_conformers()` reports what was there, and
`Structure.from_atoms` now **refuses** a duplicate atom name in a residue, so
the silent path is gone rather than merely corrected; insertion codes are
refused for the same reason instead of collapsing two residues into one.

Nothing already recorded moves. T+ comes from 7OW6, which has no alternates,
and 7OW5's single one is in a TCR chain that truncation discards. Verified
rather than argued: the five prepared targets regenerate **byte-identical**,
and the hotspot schemes re-derive identical.

---

## F-14 · The zero that would have looked exactly like a measurement

**Believed.** F-5's headline numbers — OD1 exposing 6.4 Å², OD2 exposing
**zero** — came from the SASA module and were treated as measurements.

**Checked.** `atom_sasa` ended in `np.nan_to_num`. `biotite` returns NaN for
an atom whose element it has no radius for, and the element was inferred from
the **first character of the atom name**, which is wrong for every two-letter
element. So an unparsed element produced NaN, and NaN was converted to
**0.0 Å²** — reported as fully buried, indistinguishable from a real zero.
The one number in F-5 most open to attack is an exposure of exactly zero.

**It was real.** Re-measured with the coercion removed: OD1 6.43 Å², OD2
**0.00 Å²**, Asp6 total 19.0 Å². OD2 is an oxygen, its element parsed
correctly, and a finite zero was returned. F-5 stands — but it stood on a code
path that could not have told the difference.

**Changed.** Elements are parsed after stripping the leading digits of
hydrogen names, checked against the set a protein heavy-atom table may
contain, and anything else raises. A non-finite area for a heavy atom raises
rather than becoming zero; hydrogens, which legitimately have no area under
the single-radius set, are excluded instead of patched.

**The general point, which is F-10 again in a different costume.** A silent
coercion is most dangerous where the coerced value is a *plausible answer*.
`nan_to_num` is harmless on a quantity whose zero is impossible and invisible
on one whose zero is the finding.

---

## F-15 · The chirality convention, confirmed — three days after it could be

**Believed.** `L_CHIRALITY_SIGN = -1.0` was documented as resting on
convention: a test proved the *relative* claim — that mirroring a structure
negates every improper dihedral — while the *absolute* claim, that negative
means L, was recorded as "not yet checked against an experimental structure",
with the check "owed as soon as real coordinates are available".

**Checked.** The coordinates had been available since 2 November. The
N–CA–C–CB improper over every side-chain-bearing residue of the five prepared
targets:

| | Value |
|---|---|
| Residues measured | 1,409 |
| Mean | −122.1° |
| Range | −129.1° to −111.2° |
| Positive (i.e. D) | **0** |

The conventionally quoted value for an L-amino acid is about −122°. The sign
is confirmed, the magnitude matches, and the ±9° spread shows the measurement
is stable across five structures.

**What was actually wrong here.** Not the constant — the record. F-9 ran the
whole gate against these structures and they passed, which *required* the sign
to be right; the check had already happened as a side effect and nobody
noticed, so a verified fact stayed on the books as owed for three days. An
owed verification that is silently discharged by other work is worse than one
still outstanding: it makes the register of what is unverified wrong in the
direction of over-caution, and a register that over-reports doubt gets
discounted.

---

## F-16 · The Stage −1 go/no-go could read "floor met" with nothing runnable

**Believed.** `assess_floor` reported three numbers — positives,
single-residue discriminations, foldable controls — and `met` compared the
single-residue count against the registered floor of five. F-3 used it to
establish that the published panel supplies **one** single-residue control
against a floor of five, a shortfall of four.

**Checked.** Five single-residue positive controls with no binder sequences
reported `met = True` and `foldable = 0`. Stage −1 folds every control through
the procedure a design receives, so a control with no sequence contributes
nothing to the calibration whatever its peptides differ by. The gate that
decides whether the neural arm proceeds at all could have passed on controls
that cannot be run.

**The counts could not express the question.** `single_residue` and
`foldable` were counted independently over the panel, so the report did not
contain the number the floor is about — controls that are **both**. Two
marginal counts cannot recover a joint one.

**F-3 was understated.** With `usable` computed, the published panel supplies
**zero** runnable single-residue controls, not one: the single qualifying
control is one of the Liu binders whose sequences were never obtained. The
shortfall against the registered floor is the full **five**, not four. The
go/no-go was reported as 80% short of its input; it is 100% short.

**Changed.** `FloorReport` carries `usable`, `met` and `shortfall` read from
it, and `__post_init__` refuses counts that cannot describe one panel. A
second guard went in alongside: `negative_from` now refuses a derived negative
control identical to its positive, which a shuffle returning the identity or a
palindromic reversal would produce — a negative control registered to fail a
gate it should pass.

---

## F-17 · The re-fitter reports a K_D the data cannot determine

**Believed.** `PROTOCOL.md` §12.5 makes independent re-fitting of returned
sensorgrams a headline commitment, and `DESIGN.md` §8 guards it by refusing a
K_D without a standard error. A fit that converges and carries a usable
uncertainty was treated as a measurement.

**Checked.** A five-point series at 1–100 nM against a synthetic curve whose
true K_D is 10 µM — a hundredfold above the top concentration, which is the
ordinary case of a weak binder measured on a standard series:

| Noise | Fitted K_D | Relative SE | Above top point | `one_to_one_adequate` |
|---|---|---|---|---|
| 1% | 15.4 µM | 0.34 | **154×** | reported `True` |
| 3% | 3.9 µM | 0.53 | 39× | reported `True` |

The same underlying truth gives answers **4-fold apart** from 1% and 3%
noise, both with respectable-looking error bars and neither flagged.

**Why, and why the existing guards miss it.** Below the K_D the isotherm is
still linear: `R ≈ (R_max/K_D)·C`. Only the **ratio** is determined, so K_D
and R_max trade off against each other almost freely while the residuals stay
small. The uncertainty guard does not catch it because the standard error is
finite and not even large; the delta-method caveat does not catch it because
0.34 sits inside the range the module documents as reliable; and the runs test
does not catch it because the 1:1 model is not *wrong* here — it is
unidentified, which is a different defect.

**Changed.** `SteadyStateFit` now requires the concentration range it was
fitted over — a fit that does not know what was measured cannot say whether it
is determined — and exposes `kd_is_identified` and `kd_range_multiple`, so a
report can say "154× above the highest concentration tested" rather than
"15 µM". `classify` returns a fitted call only for an identified K_D;
otherwise the curve falls through to the association-shift test, which is
exactly what `PROTOCOL.md` §3.5's second class is for — a curve the series
cannot pin a K_D on. `specificity_ratio` **refuses** two fits unless both are
identified, because that is the point where an extrapolation would have become
a headline ratio with an interval around it.

**Two statistics corrections came with it.** The runs-test critical value was
−1.96, the *two-sided* 5% quantile used in a one-sided test, so the
implemented α was 0.025 while F-8 reported its power "at α = 0.05". It is now
derived as the one-sided 5% quantile, −1.645; F-8's conclusion is unchanged
(z = −1.44 at eight points is still undetected) and a test pins that.
And `one_to_one_adequate` returned `True` when the test could not run, with a
docstring telling the caller not to read it that way — prose guarding an API
that invited the error. It is now a three-state `Adequacy`, so `UNTESTED`
cannot be mistaken for a verdict.

---

## F-18 · The objective is dose-free; the discrimination it buys is not

**Believed.** The project ranks on specificity margins and, at the wet-lab
stage, on K_D ratios: `K_D(WT)/K_D(G12D)`. §12.6 already warns that a
hundredfold ratio can give a selectivity index near 1 once presentation
density is folded in, and `biophys/occupancy.py` computes that surface. The
ratio itself was treated as a dose-independent property of a design.

**Checked.** Substituting the concentration that produces target occupancy
`x` into the ratio of occupancies cancels the concentration exactly:

```
theta_mut / theta_wt = (K_wt + [B]) / (K_mut + [B]) = r(1 - x) + x
```

An identity, verified against the mass-action code to machine precision at
seven concentrations. Discrimination interpolates **linearly** between the
full K_D ratio — approached only as the dose goes to zero — and 1 at
saturation:

| Target occupancy | Discrimination from a 100-fold K_D ratio |
|---|---|
| 1% | 99.0× |
| 50% | 50.5× |
| 90% | **10.9×** |
| 99% | 2.0× |

**What it means for the project.** The K_D ratio is the design's *best case*,
realised at a concentration that binds almost nothing. Occupancy and
selectivity cannot both be had: at half occupancy — the dose a therapeutic
would aim for, since that is what `K_D` means — exactly half the ratio is
already gone, and `(r+1)/2` holds for every `r`. To reach 90% occupancy of the
neoantigen, a hundredfold-selective binder is tenfold-selective.

This does not change what to optimise: more ratio is still more
discrimination at every dose, and the linearity means the trade is
proportional rather than cliff-edged. What it changes is **what may be
claimed**. A reported K_D ratio, or a specificity margin standing in for one,
is meaningless without the concentration it would be used at, and
`PROTOCOL.md` §20's claim discipline should cover it the way it covers
computational screens: a ratio licenses a statement about discrimination *at a
stated occupancy*, and nothing about a dose nobody named.

**Changed.** `discrimination_at_occupancy` and
`occupancy_for_discrimination` make the trade-off computable rather than
implicit, with the identity tested against the mass-action path. Recorded
alongside: `fraction_below` averages over a **log-spaced** grid, so it is an
average under an implicit log-uniform prior over copy numbers — a choice, now
stated, and `minimum` is the summary that carries no prior.

---

## F-19 · Only one of the three margins compares like with like

**Believed.** The three margins are the same quantity computed against
different decoys: `M_mut` against the wild-type complex, `M_pep` against the
empty groove, `M_var` against variant peptides. G4 applies one noise rule to
all three.

**Checked.** What each comparison holds constant:

| Margin | Decoy | Differs from T+ by |
|---|---|---|
| `M_mut` | D1, wild-type complex | **one side chain**; same chains, same residue count |
| `M_pep` | D2, empty groove | an entire **10-residue chain** |
| `M_var` | D3–D5, variant peptides | peptide **sequence and, for the 9-mers, length** |

Interface confidence metrics are normalised quantities computed over
inter-chain residue pairs. Removing the peptide removes every binder–peptide
pair from the interface being scored, which changes the metric's
normalisation, not only the biology. So `M_pep` carries an additive bias of
unknown size from the comparison itself, and the bias runs in the **same
direction as the signal**: a smaller, worse-scoring interface at D2 looks like
peptide dependence even for a binder that reads only the HLA platform. The
margin the project ranks on is inflated by the way it is measured.
`M_mut` has no such term — one side chain, everything else identical — which
is a reason to prefer it beyond the ones already registered.

**Changed — the control that measures it already exists.** `PROTOCOL.md` §5.1
registers an **invariant-surface control**: a binder deliberately aimed at the
α1/α2 helices away from the peptide, expected to show "no margin on any
comparison", and `PREREGISTRATION.md` §2 already requires `|M_mut|` and
`|M_pep|` both small for it. That control's `M_pep` **is** the composition
bias: a binder that does not touch the peptide has no biological reason to
score differently against an empty groove, so whatever margin it shows is the
measurement. Nothing in the specification says to read it that way, and the
difference matters: a non-zero value is currently a control failure, when it
should be a calibration to subtract from every `M_pep` and to report beside
it. Recorded as a reading of the registered condition rather than a new
control, so no amendment is needed — but it must be applied when Stage −1
runs, and it is the one number that can tell the difference between a
peptide-dependent binder and a metric that rewards a smaller interface.
