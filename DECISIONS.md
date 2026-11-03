# DECISIONS.md — how each method was chosen, and what was discarded

A companion to `FINDINGS.md`, which records what measurement changed, and
`AGENT_ERRORS.md`, which records what went wrong. This file records **why one
method was chosen over the alternatives that were available**, with the
evidence that narrowed the field at each step.

## How to read this file

Method selection here behaves like a folding funnel, and the analogy is
load-bearing rather than decorative.

A wide ensemble of candidate approaches enters at the top. Cheap, coarse
constraints — competition rules, published failure rates, arithmetic — remove
most of them for a few pence of effort, exactly as local secondary-structure
propensity collapses most of an unfolded chain's conformational space before
any tertiary contact forms. Only then is it worth spending expensive,
specialised measurement on the survivors, because those techniques cost
structures, GPU hours or days of reading, and applying them to the full
initial ensemble would exhaust the budget on candidates a one-line argument
could have killed.

The order is therefore not arbitrary and not laziness. It is the same reason
gate G0 runs before co-folding (`DESIGN.md` §8b): the cheap filter is cheap
*and* it removes the most candidates, so running it first is strictly
dominant. Reversing the order does not merely waste effort, it changes what
you can afford to evaluate at all.

Three failure modes of that process are tracked explicitly, because they are
the ones that actually occurred:

| Funnel pathology | What it is here | Example |
|---|---|---|
| **Kinetic trap** | A choice that looks correct, and is correct, for the wrong reason — so it breaks silently when a neighbouring assumption moves | D-2 · the control's rank |
| **Degenerate native states** | Two defensible methods that the specification supports equally, where picking by taste would be unregistered researcher freedom | D-5 · which pooled SD |
| **Chaperone** | An external check that prevents a trap rather than detecting it afterwards | D-6 · types, tests, CI, and the reader |

Each decision below states: the question, the candidate set, the coarse
filter, the specialised narrowing, the iterations it took, and how the choice
is validated. Numbers are given with their source.

---

## D-1 · The objective function: rank on the margin, not on confidence

**Question.** What quantity should the pipeline optimise?

**Candidate set (4).** (a) Confidence against the target alone; (b) predicted
affinity; (c) a weighted composite of confidence, affinity and interface
terms; (d) the specificity margin, `M = C(T+) − C(decoy)`.

**Coarse filter — competition arithmetic, minutes.** The challenge ranks
lexicographically: mutation specificity, then peptide dependence, then
affinity (`CLAUDE.md` §3.5). Criteria 1 and 2 decide the outcome; criterion 3
only breaks ties among designs that already cleared them. Options (a) and (b)
optimise criterion 3 directly and criteria 1–2 only incidentally. **A
micromolar binder that discriminates beats a nanomolar binder that does not.**
Two of four eliminated on reading the rules.

**Coarse filter — published predictor performance, one afternoon.** Option (c)
needs weights. [R14] reports that averaging ten co-folding predictors was not
measurably better than one (+0.028, CI −0.031 to +0.081), and that a trained
model over all scores was *worse* than their plain average (−0.034, CI −0.063
to −0.004). A composite therefore buys nothing measurable while introducing
free parameters. Any weight chosen after seeing the score distributions is a
post-hoc decision wearing a formula.

**Specialised narrowing.** Option (d) survived, but the margin needs a noise
floor or it ranks prediction variance. Three refinements, each from a specific
source:

1. `M > 2 × pooled SD`, with pooled SD measured **across seeds within one
   design**. `DESIGN.md` §4 warns that pooling across designs inverts the
   gate, because between-design variance is the signal being ranked. The
   implementation makes the wrong quantity inexpressible: a `CounterScreen`
   holds one design.
2. Margins pair by **seed identity**, not list position. The same seed runs
   against every target, so subtracting matched seeds removes the
   seed-to-seed component the gate measures against.
3. No weighted composite exists in the code, and there is no argument through
   which one could be supplied — a test asserts the signature carries nothing
   weight-shaped.

**Iterations: 4.** v0.2 ranked on confidence with a hard imported threshold;
v0.3 removed the threshold; v0.4 rewrote the rule as parameter-free
derivations; the current implementation added seed pairing.

**Validation.** Antisymmetry `M(A,B) = −M(B,A)` and gate monotonicity are
property-tested over generated inputs. Three of the seven level-1 mutants
registered in `CLAUDE.md` §12.4b attack this decision — sign inversion,
pooled-SD scope, D1/D2 swap — and each has a test that kills it.

**Residual risk.** The margin is only as good as the metric `C`. If no model
emits a usable interface-confidence metric, this objective has no input at all
(`SETUP.md` §5), and the fallback is physics-primary, itself requiring its own
control-panel validation.

---

## D-2 · Which discrimination mechanism to spend designs on

This is the decision the structural measurements overturned, and it is the
clearest funnel in the project.

**Question.** A 10-residue peptide differs from its wild type at one position.
Through what physical mechanism should a binder read that difference?

**Candidate set (3), from `CLAUDE.md` §4.** M1 direct electrostatic readout of
the Asp6 carboxylate; M2 composite readout of the altered local surface; M3
conformational selection on the peptide backbone.

**Coarse filter — do not pick one.** With n = 20 submissions and a base rate
near 27% [R14], no arm yields enough hits to compare. Rather than choose, the
campaign allocates across all three and labels the comparison exploratory in
every output. The coarse filter here *widened* the funnel deliberately, which
is the correct move when the prior is weak and the measurement is cheap.

**Initial allocation and its basis.** M1 = 9, M2 = 5, M3 = 4. M1 took nearly
half on the strength of [R9], which reported that discrimination on this
neoantigen proceeded through a salt bridge to the mutant aspartate.

**Specialised narrowing — three measurements on the deposited structures.**
These were not run first, because each requires prepared targets, and target
preparation requires the structures, the chain assignments and the disulfide
assertions to be correct. Measuring before that would have measured
preparation errors.

*Measurement 1 — is the handle there?* (`FINDINGS.md` F-5)

| Oxygen | Coordinating partners (≤3.6 Å) | SASA |
|---|---|---|
| OD1 | Arg114 NH1 3.04 Å, NH2 3.34 Å | 6.4 Å² |
| OD2 | Arg114 NH2 2.95 Å, Gln70 NE2 3.08 Å, OE1 3.58 Å | 0.0 Å² |

Arg114 is **bidentate across both oxygens**. M1 was defined as contacting "the
carboxylate oxygens not taken by Arg114" — an empty set. Asp6 is ~85% buried
against a fully exposed aspartate's ~100–120 Å².

*Measurement 2 — how does the one known discriminator do it?* (F-6) The same
engineered TCR appears in 7OW6 (G12D) and 7OW5 (wild type), making a
controlled pair. Superposing on the HLA α1/α2 platform (179 CA, RMSD 0.276 Å):

- Closest TCR atom to an Asp6 carboxylate oxygen: **7.51 Å**. It never touches
  the discriminating group.
- 18 of its 29 peptide contacts land on position 7; peptide-contact fraction
  **0.213**.
- The substitution displaces peptide CA position 6 by **0.96 Å**, propagating
  0.78, 0.51 and 0.64 Å to positions 7–9, while positions 1–5 stay within
  0.26 Å.

Position 6 carries the chemistry and is buried. Positions 7–9 carry **no
sequence difference at all** but are the accessible ones (73.3, 45.1, 17.1 Å²)
**and they move when position 6 changes**. Discrimination is available
indirectly, by reading geometry at the accessible positions — which is M3.

*Measurement 3 — deriving the hotspots.* (F-7) Computing M1's hotspot scheme
from the structure, rather than writing residue numbers by hand, returned a
single hotspot. The redefinition in A8 had offered two routes, the second
being displacement of Gln70; but Gln70 coordinates OD2, whose SASA is zero, so
that route is unreachable from solvent. **M1 reduces to one target: the 6.4 Å²
face of OD1.**

**Iterations: 3**, each strictly narrowing, each cheap once the previous step
existed.

**Outcome.** Amendment A7 inverted the allocation to M1 = 4, M2 = 5, M3 = 9.
A8 redefined M1. M2 was left at 5 deliberately: the evidence is weaker in
*both* directions, since the TCR ignores the Asp6–Arg114–Gln70 network M2
targets, so neither promotion nor demotion is supported.

**The kinetic trap this decision exposed.** The affinity-only control's
submission rank was computed as `len(picked[M1]) + 1`. With M1 at nine slots
that yields rank 10, which is what `CLAUDE.md` §11 asks for. It was right by
arithmetic, not by intent. When A7 moved M1 to four, the control would
silently have moved to rank 5 — defeating the stated reason for the placement,
that it be tested if only part of the list is selected. A registered test
caught it. The general form: **a value that is correct for an incidental
reason is indistinguishable from one that is correct for the right reason,
until a neighbouring assumption moves.**

**Residual risk, stated.** All three measurements are on the
receptor-stabilised conformation; F-1 shows the apo state has no coordinates
at positions 5–6 at all. A 0.96 Å displacement is perhaps three to four times
coordinate error, across different crystals. And the TCR binds *both*
complexes, so "how it binds" is better evidenced than "how it discriminates".

---

## D-3 · Where the wild-type decoy comes from

**Question.** D1 must be HLA-A\*11:01 + β2m + `VVVGAGGVGK`. Three sources
exist.

**Candidate set (3).** (a) Mutate T+ in silico, Asp6→Gly, and repack; (b) 7OW5,
wild-type pMHC with TCR, TCR stripped; (c) 7OW3, wild-type 10-mer with no TCR.

**Coarse filter.** (a) eliminated by `SETUP.md` §2.2: an in-silico mutation
biases the comparison toward our own repacking rather than toward
crystallographic reality. The margin would partly measure the repacking
algorithm.

**Specialised narrowing.** (c) is superficially the tidiest — it is already
TCR-free, so no stripping is needed. It was rejected on a confound. T+ derives
from a receptor-bound structure; a D1 drawn from an apo structure would differ
in **conformational state as well as in sequence**, and `M_mut` would partly
measure receptor-induced ordering rather than the substitution. Both arms must
be prepared identically.

The HLA platform of 7OW5 superposes onto 7OW6 at **0.276 Å over 179 CA**,
confirming the scaffolds are effectively identical and that the peptide
difference is the signal.

**Validation.** A test asserts D1's backbone differs from T+ across the whole
groove rather than only near position 6 — the signature of independently
solved coordinates, which an in-silico mutant would fail.

---

## D-4 · Thresholds as derivation rules, not values

**Question.** How should a threshold that must be calibrated from data be
registered before that data exists?

**Candidate set (3).** (a) Import a published cutoff; (b) register `[FILL]` and
decide later; (c) register a parameter-free derivation rule.

**Coarse filter — provenance of the published number.** The frequently quoted
ipSAE cutoff of **0.61** comes from a meta-analysis of 3,766 binders [R2] in
which the best metric was **AF3 ipSAE_min**, reported as *average precision*
rather than AUROC, with the authors noting possible bias from designs
pre-selected by AF2 ipAE. It is the right number for a different model, a
different metric and a different selection process. Option (a) eliminated; its
appearance in v0.2 is recorded as the project's canonical specification error.

**Specialised narrowing.** Option (b) fails on its own terms:
`PREREGISTRATION.md` §3 argues that registering a threshold as `[FILL]` means
choosing it after seeing the data, "which is exactly where a pre-registration
most needs to bind". Option (c) selected. G2 is "the confidence value
maximising F1 on the Stage −1 panel"; G3 is "the 10th percentile of the
peptide-contact fraction achieved by the positive panel"; G5 is the 90th
percentile of the panel's largest apolar patch. The rule is fixed now; the
number it produces is whatever it produces.

**The chaperone.** G2 has **no configuration field at all**, because its
operating point is a result rather than a setting. Writing `g2_confidence:
0.61` into a config file therefore fails as an unknown key. The typo guard
required by `build_rules.pdf` §2.5 makes re-importing the v0.2 error
structurally impossible, which is stronger than documenting it.

**Iterations: 2.** v0.2 imported; v0.3 removed the import; v0.4 replaced it
with rules. Amendment A5 then found §2 still carried four free `[N]`
placeholders in the rule that gates the entire neural arm, and made it
parameter-free too.

---

## D-5 · The primary estimator, and a degeneracy still unresolved

**Question.** How to estimate whether specificity margins separate
discriminators from non-discriminators, given data clustered by target with
few observations each?

**Candidate set (3).** (a) Per-target bootstrap; (b) a single pooled logistic
regression ignoring clustering; (c) a hierarchical partial-pooling model.

**Coarse filter — published instability.** [R14] reports that **4 of 14**
per-target AUROC intervals include chance, EGFR being 0.669 with CI
0.466–0.857. Option (a) therefore produces per-target estimates too unstable
to aggregate. Option (b) discards the clustering entirely and overstates
precision.

**Specialised narrowing.** Option (c) selected: `binds ~ margin + (1 + margin
| target)`, with partial pooling shrinking unstable per-target estimates
toward the population mean.

**Then the arithmetic was checked, and the chosen method did not survive
contact with the registered floor.** `PREREGISTRATION.md` §5b admits as few as
**4 targets**. A random intercept *and* slope requires estimating a 2×2
covariance — two variances and a correlation — from four clusters. It will
commonly return a singular fit or fail to converge, and a singular fit
reported as the primary analysis is worse than a simpler model honestly
chosen.

**Resolution (amendment A3): a registered ladder with a switch rule**, so the
descent is fixed in advance rather than at the keyboard once the fit
misbehaves:

| Rung | Model | Descend when |
|---|---|---|
| 1 | `binds ~ margin + (1 + margin \| target)` | — |
| 2 | `binds ~ margin + (1 \| target)` | rung 1 fails to converge, is singular, or puts a random-effect correlation at ±1 |
| 3 | `binds ~ margin`, target-clustered robust SE | rung 2 fails to converge or its intercept variance sits at the zero boundary |

The rung used is reported in every output, and descending is itself a result.

**The degeneracy, still open.** The specification defines `pooled SD` **twice**
and the definitions are not equivalent. `CLAUDE.md` §7.1 and `DESIGN.md` §4
define it per design, across that design's seeds. `CLAUDE.md` §10 and
`PREREGISTRATION.md` §5 describe a campaign-level noise floor measured once
from five identical Day-1 runs. The same symbol sets **G4's denominator** and
**the ranking tie tolerance**, and the two readings give different gate
verdicts and different rankings.

This is a genuine degenerate state: two conformations the specification
supports equally well. Resolving it by preference would be unregistered
researcher freedom, so the implementation takes the tolerance as an **explicit
argument** and imposes no answer. It must be settled by amendment before any
design is scored.

---

## D-6 · Chaperones: what prevents traps rather than detecting them

**Question.** Given that most errors in this build were *not* caught by tests,
what class of guard actually works?

**The evidence.** `AGENT_ERRORS.md` classifies nine errors by detection route.
**Only 3 of 9 were caught by anything automatic.** Two were caught only by a
person reading carefully; three by the assistant re-reading its own output,
which is the weakest route because it fires only when the agent happens to
look — and in one case fired *after* the output had already reached the user.

**What that implies.** Adding tests after the fact detects errors. Making
errors inexpressible prevents them. Four guards in this build are of the
second kind:

| Guard | Error class made impossible |
|---|---|
| `REU` and `KcalPerMol` as distinct types with **no conversion** | Quoting a Rosetta score as an affinity — the v0.2 "REU-equivalent" error |
| G2 has **no config field** | Re-importing a literature threshold (D-4) |
| `CounterScreen` holds **one design** | Pooling SD across designs (D-1) |
| `fold()` refuses a design not stamped G0-passed | Spending a GPU-hour on an invalid structure |

Each converts a documented rule into one the code cannot break. That is the
distinction `CLAUDE.md` §12.3b asks for between caught-by-automation and
caught-by-review, applied forward rather than backward.

**A caveat against over-reading the type guard.** It did not work on the first
attempt. mypy rejected `REU + KcalPerMol` statically while the runtime method
duck-typed the mixture and added the numbers silently. The guard became real
only when a test exercised it. **A constraint that holds only in the type
checker is not a constraint on the running program** — recorded as E-4.

---

## What this file deliberately does not claim

Every decision above is a **method-selection** decision, supported by
published failure rates, competition rules, or measurements on deposited
structures. None is supported by results from this pipeline, because the
pipeline has produced none: no design has been generated, no model has been
run, Stage −1 has not executed.

The structural measurements (F-5, F-6, F-7) are observations on crystal
structures solved by others, reproduced here with stated methods and caveats.
They constrain which mechanism is worth spending designs on. They do **not**
show that any binder will work, and `CLAUDE.md` §20 governs every statement
made from them: a computational screen licenses no claim about binding.
