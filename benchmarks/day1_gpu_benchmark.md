# Day-1 GPU benchmark

**Status: not yet run.** Every compute decision in this project derives from
this file. `PROTOCOL.md` §10 is explicit that the earlier budget was wrong
because it was estimated: it assumed ~32 s per co-folding prediction where
60–120 s is realistic for a ~240-residue complex on a T4, turning an 8-hour
stage into 15–30 hours. **Do not plan from estimates.**

Fill each row with the measured value and a pass or fail. A blank row is not a
pass.

---

## Environment

Recorded because the execution environment cannot be pinned by us.
`DESIGN.md` §5: Kaggle notebooks run Kaggle's container, so the base image
digest is recorded at run time into the provenance manifest instead.

| Item | Value |
|---|---|
| GPU, memory, driver | `2 × Tesla T4, 15360 MiB each, driver 580.178.04` |
| Container image digest | `gcr.io/kaggle-gpu-images/python@sha256:de153e6d3038…eea01` |
| Python | `3.13.16` |
| CPU cores | `4` |
| Date run | `TO RECORD` |

> Jobs do not span both T4s. Budget against **one 15 GB card**.
>
> The image runs Python 3.13 while this project pins 3.12 (`uv.lock` resolves
> for `==3.12.*`). Unresolved: widen the pin, run a 3.12 environment on
> Kaggle, or keep the package off Kaggle and drive the models standalone.
> Recorded as `BUILD_JOURNAL.md` ISSUE-013.

## Install verification

A failure here is a result, not an obstacle to work around. Record the fallback
taken.

| Check | Pass condition | Result |
|---|---|---|
| RFdiffusion runs | one backbone produced end to end | `TO RECORD` |
| ProteinMPNN runs | sequences produced for that backbone | `TO RECORD` |
| ESMFold runs | monomer prediction produced | `TO RECORD` |
| Protenix installs and runs | complex prediction produced | `TO RECORD` |
| Boltz installs and runs | complex prediction produced | `TO RECORD` |
| PyRosetta installs and licenses | interface score produced, or fallback selected per §7.3 | `TO RECORD` |
| Foldseek installs, PDB database downloads | TM-score returned against a known structure | `TO RECORD` |
| `binder-prescreen` installs | `--skip-prior-art` runs clean on a test FASTA | `TO RECORD` |

**`ESMFold2` may not exist as a distinct release.** The name entered this
specification from a secondary source and was never verified. Check whether it
is a real separate package; if not, use ESMFold and amend `PROTOCOL.md` §6.
Record which is the case: `TO RECORD`.

## The check that decides the project

| Check | Pass condition | Result |
|---|---|---|
| Interface confidence metric available | **ipSAE emitted directly**, or **a PAE matrix plus chain assignments** so ipSAE can be computed | `TO RECORD` |

**If neither holds for any model in the stack, `PROTOCOL.md` §7.1 has no
input and the plan must change before Day 2.** Stop and report rather than
substituting a metric that was not registered.

Record exactly what each model emits, not whether it "has confidence":

| Model | Metrics emitted | PAE matrix available | Chain assignments available |
|---|---|---|---|
| Protenix | `TO RECORD` | `TO RECORD` | `TO RECORD` |
| Boltz | `TO RECORD` | `TO RECORD` | `TO RECORD` |
| ESMFold | `TO RECORD` | `TO RECORD` | `TO RECORD` |

`counterscreen.fold.adapter.objective_has_an_input` applies this rule to an
adapter's declaration, so the decision is made by code against a declaration
rather than by recollection.

## Throughput

| Measurement | Seconds | Notes |
|---|---|---|
| Co-folding, truncated construct (~190 residues) | `TO RECORD` | the screening tier |
| Co-folding, full complex (~390 residues) | `TO RECORD` | finalists only |
| RFdiffusion, one backbone | `TO RECORD` | |
| ESMFold, one monomer | `TO RECORD` | |

### Derived budget

`PROTOCOL.md` §10:

```
N_designs = (available_hours × 3600) / (n_targets × n_seeds × s_per_prediction)
```

At 3 targets × 2 seeds, with the measured seconds per prediction:

| Available hours | s/prediction | Designs screenable |
|---|---|---|
| `TO RECORD` | `TO RECORD` | `TO RECORD` |

Contingency ladder if over budget, in order: reduce tier-4a seeds to 2;
truncate further; cut backbone count; drop optional decoys D3–D5; drop the AF2
orthogonal check on finalists. **Never cut the control panel or the
counter-screen.**

## Noise floor

Run the **same input five times** and record the spread of every confidence
metric. That spread is both the `pooled SD` used in gate G4 and the tolerance
band for CI assertions on GPU stages (`PREREGISTRATION.md` §5, amendment A6).

| Metric | Mean | SD | n |
|---|---|---|---|
| `TO RECORD` | | | 5 |

> **Unresolved before this can be used.** The specification defines `pooled SD`
> twice and the definitions are not equivalent: per design across that design's
> seeds (`PROTOCOL.md` §7.1, `DESIGN.md` §4), or campaign-level from these five
> runs (`PROTOCOL.md` §10, `PREREGISTRATION.md` §5). The same symbol sets G4's
> denominator *and* the ranking tie tolerance, so the two readings give
> different gate verdicts and different rankings. It must be settled by
> amendment before any design is scored. See `DECISIONS.md` D-5.

## Training-data contamination

`PROTOCOL.md` §5.2 rule 3: 7OW3–7OW6 are from Poole et al. 2022. Past
AlphaFold2's 2018 cutoff but plausibly inside more recent models' training
sets. A structure that is in-distribution for a model makes that model's
control result optimistically biased, and it must be reported as such.

| Model | Stated training cutoff | 7OW structures in-distribution? |
|---|---|---|
| Protenix | `TO RECORD` | `TO RECORD` |
| Boltz | `TO RECORD` | `TO RECORD` |
| ESMFold | `TO RECORD` | `TO RECORD` |

## Report back

- Which tools installed, which failed, which fallbacks were selected
- Whether a usable interface-confidence metric exists
- Measured seconds per prediction and the derived design budget
- Noise floor per metric
- Training-cutoff findings

Anything that failed is recorded in `FINDINGS.md`, not worked around silently.
