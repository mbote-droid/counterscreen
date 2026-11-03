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
**Status.** The confidence-level exclusion is **open for decision** — the
alternative is a `[[far.ci_level]]` key so nothing is exempted.

### ISSUE-012 · Control rank was coupled to M1's allocation · 3 Nov

**Symptom.** Amendment A7 moved M1 from nine slots to four; the rank-10 test
failed.
**Diagnosis.** The rank was computed as `len(picked[M1]) + 1`. It had been
right by arithmetic, not by intent.
**Fix.** Taken from `SelectionConfig.affinity_control_rank`, clamped.
**Regression test.** `test_the_affinity_control_lands_at_rank_ten`, whose
docstring now records why a derived rank was wrong.

### ISSUE-013 · Kaggle runs Python 3.13; the project pins 3.12 · 3 Nov · **OPEN**

**Symptom.** Kaggle's GPU image reports Python 3.13.16.
**Diagnosis.** `requires-python = ">=3.12,<3.13"` means `counterscreen` will
not install there as-is. Separately, Boltz and Protenix may lack 3.13 wheels.
**Fix.** Undecided — widen the pin, run a 3.12 environment on Kaggle, or keep
the package off Kaggle and run models standalone. Deliberately not decided
speculatively: the install attempt is still running.
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
