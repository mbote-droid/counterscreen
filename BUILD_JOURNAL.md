# BUILD_JOURNAL.md — dated issues

Symptom, diagnosis, fix, regression test. `build_rules.pdf` Part V keeps this
separate from `AGENT_ERRORS.md`: that file records where the *assistant's
reasoning* went wrong, this one records what the *build* did. Several entries
appear in both, from the two angles.

Open issues are marked. Nothing here is worked around silently.

---

### ISSUE-001 · Specification absent from the container · 2 Nov

**Symptom.** Session resumed in a fresh cloud container with none of the seven
specification files.
**Diagnosis.** They existed only on the desktop and had never been committed.
Only tracked files survive a container move.
**Fix.** Re-supplied by the user and committed verbatim before any amendment.
Architecture had survived in the commit-1 package docstrings, which carried
the `DESIGN.md` §1 dependency table almost intact.
**Regression test.** `tests/contract/test_architecture_contracts.py` fails if a
package exists without a boundary statement or an import contract — so the
table can be reconstructed from the code if it is ever lost again.

### ISSUE-002 · mypy refused an empty test tree · 2 Nov

**Symptom.** `mypy` errored: "There are no .py[i] files in directory 'tests'".
**Diagnosis.** `files = ["src", "tests", "scripts"]` with only `.gitkeep` in
those directories.
**Fix.** Real tests written; `scripts` re-added once it held modules.
**Regression test.** Self-correcting — the condition cannot recur while tests
exist.

### ISSUE-003 · Typer ran `version` instead of showing help · 2 Nov

**Symptom.** `counterscreen` with no arguments printed `0.0.0`.
**Diagnosis.** Typer promotes a lone command to the root callback, so
`no_args_is_help` never applied.
**Fix.** Explicit `@app.callback()` declaring the group up front, since
subcommands arrive per package.
**Regression test.** `test_bare_invocation_shows_help_rather_than_failing_silently`.

### ISSUE-004 · Image pinned a uv too old for its lockfile · 2 Nov

**Symptom.** Dockerfile pinned `uv:0.5.11`; `uv.lock` is `revision = 3`.
**Diagnosis.** Revision 3 postdates that uv. `uv sync --locked` would have
failed inside the build.
**Fix.** Pinned 0.11.32, the version that resolved the lockfile.
**Regression test.** CI `image` job builds and smoke-tests the entrypoint;
`tests/contract/test_python_pin_is_consistent.py` holds the four places that
name the interpreter in agreement.

### ISSUE-005 · Dependabot proposed Python 3.12 → 3.15 · 2 Nov

**Symptom.** PR #1 bumped the base image; CI failed with "No interpreter found
for Python ==3.12.*".
**Diagnosis.** The pin is load-bearing — `uv.lock` is resolved for `==3.12.*` —
and the docker ecosystem does not know that.
**Fix.** Dependabot now ignores major and minor bumps of the python image;
moving Python is a lockfile decision made by hand across four files.
**Regression test.** `test_python_pin_is_consistent.py`, verified by applying
the 3.15 bump and confirming it fails with a named error rather than a Docker
build dying three layers in.

### ISSUE-006 · Shared test builders were not importable · 2 Nov

**Symptom.** `ModuleNotFoundError: No module named 'conftest'`.
**Diagnosis.** Under `--import-mode=importlib`, `conftest.py` is loaded by
pytest but is not importable as a module.
**Fix.** Builders moved to `tests/_helpers/structures.py`, added to pytest's
`pythonpath`.
**Regression test.** The geometry suite imports them; a regression breaks
collection immediately.

### ISSUE-007 · hypothesis conflicts with `disallow_any_decorated` · 2 Nov

**Symptom.** Every property test failed mypy with "Type of decorated function
contains Any".
**Diagnosis.** hypothesis types `@given` as `Callable[..., None]`.
**Fix.** Per-file `# mypy: disallow_any_decorated=false` at the top of each
property module, stating the reason. A `[[tool.mypy.overrides]]` pattern was
tried first and did not match the module names.
**Regression test.** Strict mode still applies to every other flag in those
files.

### ISSUE-008 · `pytest.approx` inside a tuple comparison · 2 Nov

**Symptom.** mypy reported a non-overlapping equality check and the following
assertion as unreachable.
**Diagnosis.** Comparing `tuple[tuple[int, float], ...]` against a tuple
holding `Approx` objects. It works at runtime through `Approx.__eq__`, but the
types do not overlap, so mypy concluded the assertion could never run.
**Fix.** Compare seeds and values separately.
**Regression test.** mypy strict in CI; the pattern cannot return silently.

### ISSUE-009 · A `NaN` matrix was reported as asymmetric · 2 Nov

**Symptom.** Clustering rejected a `NaN`-containing matrix with "similarity
must be symmetric".
**Diagnosis.** `np.allclose` is false wherever a `NaN` sits, so the symmetry
check fired before the finiteness check and named the wrong defect.
**Fix.** Finiteness checked first, with the ordering explained in a comment.
**Regression test.** `test_non_finite_similarity_is_refused` asserts on the
message, not just the exception.

### ISSUE-010 · Truncated construct was 289 residues, not 180 · 2 Nov

**Symptom.** Platform construct came out at 289 residues.
**Diagnosis.** Truncation kept chain A residues 1–180 but left every other
chain whole, so β2m's 99 residues survived. `SETUP.md` §2.5 drops β2m and the
α3 domain both.
**Fix.** Select chains A and C before truncating. Now 190 residues.
**Regression test.** `test_the_platform_construct_drops_b2m_and_the_alpha3_domain`,
plus a peptide CA RMSD of 0.000 Å against the full complex.

### ISSUE-011 · The claim checker rejects its own document · 2 Nov

**Symptom.** Written to the letter of `DESIGN.md` §9b, the checker flagged
`95% CI` in `METHODS.md` §8.5.
**Diagnosis.** §9b allows one exception, a literature value with `[Rn]`.
Headings, numbered lists, section cross-references, table rules, ratios like
`1:1` and stated confidence levels are all bare numerals under that rule.
**Fix.** Each masked before the scan, named as a pattern, and listed in the
module docstring as an addition to the registered rule.
**Regression test.** One test per exclusion.
**Decided, 4 Nov.** The confidence-level exclusion is removed. It is the one
number in that sentence that can disagree with the code computing the
interval, so it is cited through a key like any other. Registered constants
are available as keys without a result file (`REGISTERED` in
`report/claims.py`), the level lives in `core/intervals.py`, and the normal
quantile is derived from it rather than typed beside it. See FINDINGS F-4.

### ISSUE-012 · Control rank was coupled to M1's allocation · 3 Nov

**Symptom.** Amendment A7 moved M1 from nine slots to four; the rank-10 test
failed.
**Diagnosis.** The rank was computed as `len(picked[M1]) + 1`. It had been
right by arithmetic, not by intent.
**Fix.** Taken from `SelectionConfig.affinity_control_rank`, clamped.
**Regression test.** `test_the_affinity_control_lands_at_rank_ten`, whose
docstring now records why a derived rank was wrong.

### ISSUE-013 · Kaggle runs Python 3.13; the project pins 3.12 · 3 Nov · **DIAGNOSED 5 Nov**

**Symptom.** Kaggle's GPU image reports Python 3.13.16.
**Diagnosis.** `requires-python = ">=3.12,<3.13"` means `counterscreen` will
not install there as-is. Separately, Boltz and Protenix may lack 3.13 wheels.

**Measured, 5 Nov.** The speculation was right in effect and wrong in
mechanism, and the mechanism matters because it names the fix. A full
`pip install --dry-run boltz` on Python 3.13.18:

| Step | What happens |
|---|---|
| `boltz 2.0.3` | resolves fine — it is a pure-Python `py3-none-any` wheel |
| `torch>=2.2` | `cp313` wheel exists; fine |
| `rdkit>=2024.3.2` | `cp313` wheel exists; fine |
| **`numpy<2.0,>=1.26`** | **no `cp313` wheel exists.** numpy added 3.13 wheels in 2.1, and boltz pins below 2.0, so pip downloads `numpy-1.26.4.tar.gz` (15.8 MB) to build from source |
| **`scipy`** | pinned below 2.0 by the same constraint, so it resolves to **1.13.1**, which also predates 3.13 wheels and builds from source via meson |
| build | `ERROR: Unknown compiler(s): gfortran, flang, ifort, ...` → `metadata-generation-failed` |

**So Boltz itself is not the problem: its `numpy<2.0` pin is.** On Python 3.13
that one constraint forces source builds of numpy *and* scipy. Where a Fortran
compiler is missing the install fails outright; where one is present it
succeeds only after tens of minutes of compilation. Either way the cell looks
like the one in ISSUE-027: long, silent, and not obviously progressing.

**Confirmed on Kaggle, 5 Nov.** Cell 0 reports Python 3.13.18 with
**numpy 2.1.3** and **scipy 1.16.3** already installed — both *above* boltz's
`numpy<2.0` pin. So the install does not merely fail to find a wheel: it
first has to **downgrade** a working numpy to 1.26.4, for which no 3.13 wheel
exists, and build it from source. The image is further from boltz's
constraints than a bare interpreter would be.

**Fix.** Pin the notebook to an environment with **Python 3.12 or earlier**,
where numpy 1.26.4 and scipy 1.13.x both have binary wheels and nothing
compiles. That also removes the `requires-python` conflict for
`counterscreen` itself, so the choice that looked like three options is one.
Widening the project pin to 3.13 would *not* have helped: the obstruction is
in Boltz's dependency range, not in ours.
**Regression test.** `test_python_pin_is_consistent.py` will fail the moment
the pin is widened inconsistently.

### ISSUE-014 · No outbound access to any scientific host · 2 Nov · **OPEN**

**Symptom.** 403 at the egress gateway for `files.rcsb.org`, `www.ebi.ac.uk`,
`rest.uniprot.org`, `iedb.org`, `vdjdb.cdr3.net`, `creativecommons.org`.
WebFetch cannot resolve them either.
**Diagnosis.** Environment network policy allows package registries and
GitHub only.
**Fix.** Structures supplied by hand. `docs/LICENSE` references the CC-BY-4.0
legal code rather than vendoring it, with a maintainer note.
**Regression test.** None possible. Recorded so the gap in provenance —
nothing was fetched and checksummed directly from source — is visible.

### ISSUE-015 · Repository settings cannot be written · 3 Nov · **OPEN**

**Symptom.** `gh api -X PATCH repos/...` returns "Repository settings writes
are not permitted through this proxy" (HTTP 403).
**Diagnosis.** Proxy policy.
**Fix.** Description and topics supplied to the user to paste by hand.
**Regression test.** None.

### ISSUE-016 · G0 rejected deposited crystal structures · 4 Nov

**Symptom.** Running the workflow's geometry rule over the prepared targets,
three of five failed G0 on Ramachandran outliers at 1.1-1.6%.
**Diagnosis.** Three of the four flagged residues were implementation
artefacts: two sat in a ten-degree dead band between adjacent allowed-region
rectangles, and one at phi = 178 was mishandled because the regions did not
wrap. See FINDINGS F-9.
**Fix.** Adjacent basins made contiguous; phi and psi folded into
[-180, 180) and boxes added past the wrap. Threshold unchanged at 1%.
**Regression test.** `test_deposited_structures_pass_the_geometry_gate`
asserts every prepared target passes, plus one test each for the wrap, the
former dead zone, and that a disallowed conformation is still rejected.

### ISSUE-017 · G9's cost was declared as local structural work · 4 Nov

**Symptom.** Writing a general cheap-first invariant over the gate ordering
for amendment A10, rather than the pair of assertions that existed before, the
new test failed on the pipeline as it stood.
**Diagnosis.** Two separate causes behind one failure. `GATE_COST` declared G9
as `STRUCTURE`, the tier meaning local structural arithmetic costing seconds,
when G9 is a Foldseek search against the whole PDB: a multi-gigabyte download
and minutes per query, which is what `EXTERNAL` is for. Classified that way it
would have been legal to move G9 in among G0, G5 and G6 and pay for the
database before any co-folding. Separately, the invariant as first written was
wrong: it treated G6 as mis-ordered, when G6 is cheap but asks its question in
the T+ complex and so cannot run before co-folding at any price.
**Fix.** G9 reclassified as `EXTERNAL`. `GateInput` added so each gate also
declares what it has to be given, and `effective_tier` takes the more
expensive of a gate's cost and its input; the cost enum now says it classifies
by expense rather than by the kind of input read.
**Regression test.** `test_the_order_is_cheap_first_with_no_exceptions_left`
asserts the order is non-decreasing in `effective_tier` over every pair,
`test_every_gate_declares_both_a_cost_and_an_input` refuses an undeclared
gate, and `test_a_cheap_gate_that_needs_the_complex_cannot_run_early` pins why
G6 sits where it does.

### ISSUE-018 · Two funnel tables, two orders, neither the pipeline's · 4 Nov

**Symptom.** Found while moving G8 for A10. `METHODS.md` §8.7 listed the
funnel as G0, G1, G2-G4, G5, G6, G7/G9, G8; the campaign report listed G0, G1,
G5, G2-G4, G6, G7/G9, G8. The second matched the pipeline before A10; the
first matched no ordering the code ever ran.
**Diagnosis.** `DESIGN.md` §9b forbids typing numbers into prose and the claim
checker enforces it, so each count resolves from a result file and cannot go
stale. The *order of the rows* was still typed by hand, and a per-stage count
means nothing except relative to the stages before it, so a correct number in
the wrong row describes a pipeline nobody ran.
**Fix.** Both tables reordered to `PIPELINE_ORDER`.
**Regression test.** `tests/contract/test_funnel_documents.py` parses the
`[[funnel.*]]` keys out of both documents in written order and asserts they
match the pipeline order, cover every gate once, and agree with each other.

### ISSUE-019 · `REQUIREMENTS.md` miscounted itself, and reused an ID · 4 Nov

**Symptom.** The coverage table claimed 43 verified of 49 while the document
carried 57 rows, 53 of them verified. A new row was then added as G-08, which
already existed.
**Diagnosis.** The same class as ISSUE-018 one level up: the counts and the
identifiers were typed by hand into a document nothing read. The claim checker
guards generated documents, not this one.
**Fix.** Counts corrected to 54 verified, 4 pending, 58 total. The new row
renumbered G-11.
**Regression test.** `tests/contract/test_requirements_document.py` recounts
the rows and compares them with the coverage table, asserts each row is
verified or pending and not both, asserts every verified row names a
verification method, and asserts identifiers are unique. The duplicate ID was
caught by that last assertion on its first run.

### ISSUE-020 · The evidence-class table stopped two findings short · 5 Nov

**Symptom.** Found while writing FINDINGS F-10, which is the finding these
four issues add up to. The evidence-class table at the head of `FINDINGS.md`
carried rows for F-1 to F-7 while the file held entries through F-9.
**Diagnosis.** The same class as ISSUE-018 and ISSUE-019, and the fourth
instance of it: a table about the document, maintained by hand, that nothing
read. It matters more here than in the other two, because the file's own
preamble says the evidence class governs what may be written from a finding
and that a reader cannot infer it from the finding alone. A finding with no
row is a finding with no stated licence, and F-8 is the one most likely to be
cited outside this project.
**Fix.** Rows added for F-8, F-9 and F-10. The ranking paragraph above the
table, which also listed only part of the file, now accounts for all ten.
**Regression test.** `tests/contract/test_findings_document.py` asserts every
`F-n` entry has an evidence-class row, that the table names no finding that
does not exist, that numbering is unique and ordered, and that no row leaves
the "does not license" column empty.

### ISSUE-021 · The cheapest gate was the most memory-hungry step · 5 Nov

**Symptom.** Measured while auditing G0 for the premortem. `check_geometry`
on a 390-residue complex peaked at **632 MB** and took 4.1 s; on the
four-copy asymmetric unit of 7OW4 it peaked at **10.1 GB** and took 61 s.
**Diagnosis.** `_clashes` built the full pairwise distance matrix via
`coords[:, None, :] - coords[None, :, :]`, an (n, n, 3) float64 array: 230 MB
of intermediate at 3,100 atoms and 3.8 GB at 12,500. G0 is the gate
`PROTOCOL.md` §8 puts first *because it is cheap*, and it would have been the
step most likely to exhaust a 16 GB Kaggle box. At campaign scale the time
mattered too: 4 s × a few hundred designs × three targets × two seeds is hours
of CPU attributed to the cheap gate.
**Fix.** `scipy.spatial.cKDTree.query_pairs`, which is linear in memory.
T+ went 632 MB → **16.4 MB** and 7OW4 10,089 MB → **3.0 MB**, 61 s → 3.7 s.
**Regression test.** `test_the_neighbour_search_finds_the_same_clashes_as_comparing_every_pair`
cross-checks the KD-tree result against brute force over every pair on a
random 60-atom fixture that genuinely contains clashes, so the optimisation
cannot have changed the answer.

### ISSUE-022 · An alignment range bound was silently discarded · 5 Nov

**Symptom.** `superpose_on(mobile, reference, "A", first=10)` on a 12-residue
chain fitted all 12 CA atoms instead of 3.
**Diagnosis.** `not (first <= n <= last if last else True)` parses as
`not (… if last else True)`, so with `last` unset the conditional returns
`True`, the negation is `False`, and every residue is kept — the `first` bound
had no effect. `last=0` was also treated as absent, being falsy.
**Fix.** Each bound applied independently against `None`.
**Not a wrong result anywhere.** The only call site passes both bounds, so no
recorded number changes. The hotspot schemes re-derive identical.
**Regression test.** `test_each_alignment_bound_applies_on_its_own`.

### ISSUE-023 · An untested Ramachandran check reported as a pass · 5 Nov

**Symptom.** A two-residue structure, which has no computable φ/ψ at all,
passed G0's Ramachandran criterion.
**Diagnosis.** `ramachandran_outlier_fraction` returns 0.0 when
`ramachandran_evaluated == 0`, and `passed` compares that to the 1% threshold.
Zero outliers out of zero residues is absence of evidence, and `FINDINGS.md`
F-10 is about what happens when that is read as evidence of absence — the same
shape as `one_to_one_adequate` returning `True` when the runs test could not
run.
**Fix.** `ramachandran_untested` is a separate property, it fails the gate,
and `reasons()` says so rather than reporting an outlier percentage.
**Regression test.** `test_an_untested_ramachandran_check_does_not_pass`.

### ISSUE-024 · TM-score symmetrisation was an unregistered free parameter · 5 Nov

**Symptom.** `single_linkage` refuses an asymmetric matrix with the message
"TM-score is not, so symmetrise before clustering", and nothing in the
codebase symmetrised one.
**Diagnosis.** TM-score normalises by the length of one of the two structures,
so A-against-B and B-against-A differ. Which direction is used changes how
many clusters survive and therefore which designs are submitted. Amendment A2
registered the threshold and the linkage and left this open, which left a free
parameter underneath a pre-registered selection procedure — the exact gap A2
was created to close. A test now demonstrates it: one pair at 0.62 and 0.38
either merges into one fold family or submits both, on the choice alone.
**Fix.** Amendment A11 registers `symmetrise`, the larger of the two
directions, for the same reason single linkage was chosen: it merges more
readily, so it under-reports diversity rather than over-reporting it.
`single_linkage` still refuses an asymmetric matrix, so symmetrising stays a
visible step rather than a hidden one.
**Regression test.** `test_symmetrise_takes_the_larger_direction`,
`test_the_choice_of_direction_changes_the_clustering`, and
`test_an_asymmetric_matrix_is_still_refused_by_the_clusterer`.

### ISSUE-025 · A CIF handed to the PDB reader failed deep inside biotite · 5 Nov

**Symptom.** `check_geometry.py <out.json> structures/7OW4.cif` ended in
`biotite.InvalidFileError: '1   ? 26' cannot be parsed into a float`.
**Diagnosis.** The script's usage line says `<structure.pdb>...` and it calls
`read_pdb` on every argument. The project holds its sources as mmCIF and its
prepared targets as PDB, so mixing them in one invocation is the natural thing
for an operator to try, and the error names neither the file format nor the
script. On Day 1 that is time spent on the wrong question.
**Fix.** A reader table keyed by extension, and a `SystemExit` naming what is
accepted. Running the gate over all ten structures in one command is what
found F-21, so the fix paid for itself immediately.
**Regression test.** `test_the_geometry_script_names_the_formats_it_accepts`.
The report also now carries `chain_gaps`.

### ISSUE-026 · The patch pass percolated, then mis-ordered itself · 5 Nov

**Symptom.** Three defects in one implementation, each caught by its own test
rather than by review. (a) Adjacency over atom centres put 100% of a protein's
exposed apolar area in one patch. (b) The ordering tie-break used each patch's
lowest atom row, and two patches can share one: patches partition *dots*, so a
side chain exposed on both sides of a polar ridge is in two of them. (c)
Single-dot regions in crevices were being reported as patches.
**Diagnosis.** (a) Exposed carbons are everywhere on a protein surface, so a
distance graph over them is connected; contiguity of a surface is not a
distance between atoms. (b) A property of the decomposition I had asserted
without checking. (c) One dot on a carbon is 0.47 Å² at 256 dots, below the
resolution the surface is sampled at.
**Fix.** Connected components of accessible surface dots; `first_dot` as the
tie-break, which is unique by construction; a four-dot floor, with the gated
quantity shown to be invariant to it.
**Also caught.** The F-13 duplicate-atom guard rejected my own test fixture —
three atoms named `CB` in one residue — on its first run. The guard was right.
**Regression test.** `tests/geometry/test_apolar_patches.py`, fifteen tests,
including the percolation bound, the invariance of the gated quantity, that an
atom may belong to two patches, and the differential test against `biotite`.

### ISSUE-027 · The install cell hid its own progress for 79 minutes · 5 Nov

**Symptom.** Cell 2 of the Day-1 notebook ran for 1 h 19 m with no output.
The session panel read CPU 0.00%, GPU memory 0 bytes, RAM 678 MiB, disk
2.5 GiB, and the page reported "Failed to save draft".
**Diagnosis.** Two things, and only one of them is Kaggle's. The cell was
`!pip install -q boltz 2>&1 | tail -5`: `tail` cannot emit a line until the
command it is piped from exits, so a stalled install and a healthy one look
identical for as long as they run, and `-q` removed the progress that would
have distinguished them. A cell that cannot be observed cannot be diagnosed,
and the operator had no way to tell a slow install from a dead one. The
underlying stall is ISSUE-013's open question: 0.00% CPU with a live session
is a process waiting on the network, which is what pip does when it backtracks
through an index looking for a version that exists for this interpreter.
**Fix.** `scripts/kaggle_day1.py` carries replacement cells: a version probe
that answers in seconds, a `--dry-run` resolve with a 180 s timeout that
distinguishes "no resolvable version" from "slow download", and an install
that streams each line with an elapsed-time prefix to both the cell and a log
file, with a hard 30-minute kill. Cells 0-2 are marked to run with the
accelerator **off**, because installing needs no GPU and a GPU session spends
the 30 h/week quota at wall-clock rate regardless of use -- 1 h 19 m of the
3 h 03 m consumed so far bought nothing.
**No regression test.** This is an operator-facing notebook cell, outside the
test suite. The guard is that the replacement cannot run silently: every path
prints within seconds or exits on a timeout.

### ISSUE-028 · chain_sequence spliced a chain across its unmodelled gaps · 5 Nov

**Symptom.** Extracting the 7OW6 TCR's alpha chain for the control panel
returned a continuous 181-mer. The deposition says the construct is 203
residues.
**Diagnosis.** `chain_sequence` collects modelled residues, sorts by residue
number and concatenates. Chain D has three internal gaps -- 152 to 157, 167 to
175, 185 to 189 -- so the result joins residues that are not adjacent and
reads as a protein that does not exist. The same root cause as F-12, in a
different function: F-12 taught the geometry gate about numbering gaps and
nobody checked the sequence extractor. Existing uses were unaffected, because
the prepared targets have no gaps, which is also why it had never shown.
**Fix.** `chain_sequence` refuses a gapped chain unless the caller passes
`allow_gaps`, and `construct_sequences` reads
`entity_poly.pdbx_seq_one_letter_code_can` -- what was crystallised, including
what the model does not resolve -- which is the sequence to fold from.
**Regression test.** `test_a_chain_with_unmodelled_residues_refuses_to_give_a_sequence`
pins both the refusal and the 203/246 construct lengths, and
`test_an_ungapped_chain_still_gives_its_sequence` pins that the peptide chains
the campaign uses are unaffected.

### ISSUE-029 · The notebook cells were strings, so nothing could check them · 5 Nov

**Symptom.** The user pasted cell 0 into Kaggle and asked why it began
`CELL_0 = r"""`. Pasted as written it assigns a string and runs nothing.
**Diagnosis.** `scripts/kaggle_day1.py` held each cell as a module-level
string constant. Two consequences, and the second is worse. The cells could
not be copied -- the thing an operator-facing file exists to allow -- and the
code inside the quotes was invisible to ruff, mypy and the compiler, so the
project's whole toolchain ran over the file and checked none of it. Compiling
the four strings by hand showed `CELL_1` was **not valid Python**: it carried
`!timeout ...`, a notebook magic. A cell that could only have failed in front
of the user shipped because the only thing that would have caught it was
turned off by the quoting.
**Fix.** `scripts/kaggle/cell0_environment.py` through `cell3_metrics.py`:
one runnable file per cell, plain Python with no magics, so each runs
unchanged in a Kaggle cell, in a terminal, and under `make check`. Cell 0 and
cell 1 were then run here, which found a third defect: cell 1 reported
"boltz does not resolve here" when the real cause was that this virtual
environment has no pip. A diagnostic cell that reports the resolver's verdict
when it could not run the resolver is worse than one that says nothing, so it
now distinguishes the two.
**Regression test.** `tests/contract/test_kaggle_cells.py` parses every cell,
and asserts each compiles, uses no notebook-only syntax, has a `main()` and a
`__main__` guard -- without the guard, pasting the file defines a function and
does nothing, the same silent no-op as the string form -- and carries a
docstring saying what it answers.

### ISSUE-030 · A cell's verdict rendered as a crash · 5 Nov

**Symptom.** Cell 0 printed its diagnosis correctly and then showed a red
`SystemExit: 1` traceback box, with IPython adding "To exit: use 'exit',
'quit', or Ctrl-D."
**Diagnosis.** The cells end in `raise SystemExit(main())`, which is right for
a script and wrong in a notebook: a non-zero status is how the cell *reports a
verdict*, and rendering it as an exception makes a working cell look broken.
The operator cannot tell a refusal from a failure, which is the same confusion
ISSUE-027 and the cell-1 pip message were both about.
**Fix.** The guard raises only when IPython is absent, so a paste prints its
verdict and stops while a script keeps its exit code.
**Regression test.** Covered by the existing guard assertion in
`tests/contract/test_kaggle_cells.py`; the notebook path is exercised by
running a cell with `IPython` injected into `sys.modules`.
