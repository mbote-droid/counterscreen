# AGENT_ERRORS.md — where the assistant got it wrong

`CLAUDE.md` §12.3b requires this file, and gives the reason: publishing agent
failures alongside agent successes is becoming the expected standard, and it
is precisely the competence AI-evaluation employers hire for. The precedent is
the Mithril Medicine programme, where six assistant errors were documented
alongside the results, some having reached external laboratories before human
review caught them [R27].

Each entry records what the assistant produced, what was wrong with it, **how
it was caught**, and what guard was added — and whether that guard is
automated or still depends on somebody reading carefully.

## Detection routes, and the number that matters

§12.3b asks for three routes: automated test, human review, downstream
failure. A fourth is recorded here because pretending otherwise would be
dishonest — **agent self-check**, where the assistant re-read its own output
and found the error before anyone else did. It is a real route, but it is the
weakest one: it fires only when the agent happens to look, and E-7 below shows
it can fire *after* the damage has already reached the user.

| Route | Count | Entries |
|---|---|---|
| Automated test | 2 | E-3, E-8 |
| CI | 1 | E-1 |
| Human review | 1 | E-4 |
| Downstream failure | 1 | E-6 |
| Agent self-check | 3 | E-2, E-5, E-7 |
| **Total** | **8** | |

**Caught only by a human reading carefully: 1 of 8, about 13%.** That is the
figure §12.3b calls the interesting number, and it bounds how far this process
could be automated.

But the more useful framing is harsher. **Only 3 of 9 were caught by anything
automatic.** The other 6 depended on a human or on the agent choosing to
re-examine its own work. An agent that did not re-read its output, working
with a reviewer who did not know the specification, would have shipped five of
these.

---

## E-1 · Dockerfile pinned a uv too old to read its own lockfile

**Produced.** `COPY --from=ghcr.io/astral-sh/uv:0.5.11`.

**Wrong because.** `uv.lock` is `revision = 3`, which uv 0.5.11 predates.
`uv sync --locked` inside the image would have failed outright.

**Caught by.** *CI.* The image job builds the Dockerfile on a runner with a
daemon, which this environment does not have. It was found while verifying the
pinned image tags existed, before CI even ran — but CI is what would have
caught it regardless.

**Guard.** Pinned to 0.11.32, the version that resolved the lockfile. The
`image` CI job builds and smoke-tests the entrypoint on every push.
**Automated.**

---

## E-2 · Reported a Docker build as succeeding when it had not run

**Produced.** "Docker build exited 0" — after running
`docker build ... 2>&1 | tail -25`.

**Wrong because.** The exit code belonged to `tail`, not to `docker`. There is
no Docker daemon in this environment; the build never happened. The claim was
reported to the user as a verified result.

**Caught by.** *Agent self-check*, on attempting to run the image and finding
no daemon. Had the next step not required the daemon, the false claim would
have stood.

**Guard.** None automated. The lesson is stated instead: a pipeline's exit
code is the last command's, so `cmd | tail` reports `tail`. Verification
claims now run the command directly or check `PIPESTATUS`. **Depends on care**,
which is why it is recorded here rather than closed.

---

## E-3 · A type guard that held for mypy but not at runtime

**Produced.** `Quantity.__add__` returning `type(self)(self.value + other.value)`,
intended to make `REU + KcalPerMol` impossible per `CLAUDE.md` §7.2.

**Wrong because.** mypy rejected the mixture statically, but at runtime the
method duck-typed any `Quantity` and silently added the two numbers. A value
arriving from parsed data or a registry lookup would have defeated it — which
is exactly how the "REU-equivalent" error of v0.2 happens.

**Caught by.** *Automated test.* The test written to assert the mixture raises
`TypeError` failed.

**Guard.** Runtime class check returning `NotImplemented`, so the interpreter
raises. Test retained. **Automated.**

---

## E-4 · Claimed the Liu preprint contained no supplementary table

**Produced.** "The main-text PDF contains zero binder sequences and no
Supplementary Table. The supplement is a separate file."

**Wrong because.** Supplementary Tables 1 and 2 are on pages 25–26 of the
supplied PDF, rendered as **page images**. The text extraction returned only
the bioRxiv watermark for those pages — 299 characters each — and the
assistant read that absence as the tables being absent, rather than as the
extraction having failed.

**Caught by.** *Human review.* The user said the table was there. Nothing in
the toolchain would have contradicted the claim; the per-page character counts
were in front of the assistant and were misread as evidence for the conclusion
rather than against the method.

**Guard.** None automated, and this one is worth sitting with. It is the
clearest case in this file of a failure a test could not have caught: the
error was in reasoning about what a null result meant. The habit added is to
treat a page yielding only boilerplate as *unread*, not as empty, and to look
at it. **Depends on care.**

---

## E-5 · Truncated construct kept beta-2-microglobulin

**Produced.** A platform construct of 289 residues.

**Wrong because.** `SETUP.md` §2.5 requires roughly 180, dropping β2m **and**
the α3 domain. The truncation kept chain A residues 1–180 but left every other
chain whole, so β2m's 99 residues rode along. That is most of the compute
saving the truncation exists to deliver.

**Caught by.** *Agent self-check*, on comparing the printed residue count
against the spec's "roughly 180".

**Guard.** Platform now selects chains A and C before truncating, giving 190
residues. A test asserts the chain set is `{A, C}` and the count is at most
200, plus a peptide CA RMSD of 0.000 Å against the full complex.
**Automated.**

---

## E-6 · The control's rank was derived instead of configured

**Produced.** `control_rank = len(picked[M1]) + 1` — correct output, rank 10,
because M1 held nine slots.

**Wrong because.** It coupled a registered placement to an unrelated number.
`CLAUDE.md` §11 asks for the affinity-only control at approximately rank 10
*so that it is still tested if only part of the list is selected*. The rank
happened to be right; the reason it was right was accidental.

**Caught by.** *Downstream failure.* Amendment A7 moved M1 from nine slots to
four, and the control would silently have landed at rank 5. The test asserting
rank 10 is what failed.

**Guard.** Rank now comes from `SelectionConfig.affinity_control_rank`,
clamped to the list length, with a test that states why. **Automated.**

---

## E-7 · A diagnostic cell leaked session credentials

**Produced.** A Kaggle notebook cell printing
`{k: v for k, v in os.environ.items() if "KAGGLE" in k}`.

**Wrong because.** That filter captured `KAGGLE_USER_SECRETS_TOKEN` and
`KAGGLE_DATA_PROXY_TOKEN`, which are live session credentials. The only value
actually needed was `KAGGLE_DOCKER_IMAGE`, the digest `DESIGN.md` §5 requires
in the provenance manifest. The output was pasted into the conversation before
anyone noticed.

**Caught by.** *Agent self-check*, on reading the pasted output — **after** it
had already left the user's machine. Earlier than nobody noticing, later than
useful.

**Guard.** None automated here, since the cell is not in the repository. The
lesson is stated: request the specific variable, never a pattern match over
the environment. A broad filter over `os.environ` is a credential disclosure
by default. **Depends on care.**

---

## E-8 · A validation error reported the wrong reason

**Produced.** `single_linkage` checking matrix symmetry before checking
finiteness.

**Wrong because.** `np.allclose` is false wherever a `NaN` sits, so a matrix
containing `NaN` failed the symmetry check and was reported as "not
symmetric". The message pointed at the wrong defect, which is how an hour goes
into symmetrising a matrix whose real problem is a missing value.

**Caught by.** *Automated test.* The test asserting a `NaN` matrix raises a
"non-finite" error failed on the message.

**Guard.** Finiteness is checked first, with a comment explaining the
ordering. Both tests retained. **Automated.**
