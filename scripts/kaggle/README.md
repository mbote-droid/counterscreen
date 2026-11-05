# Day-1 Kaggle cells

One file per notebook cell. **Paste the whole file** into a cell and run it —
each is plain Python with no notebook magics, so it runs unchanged in a cell,
in a terminal, and under this project's linter and type checker. The earlier
version wrapped each cell in a `CELL_n = r"""..."""` string, which made the
code uncopyable *and* invisible to `make check`; one of those cells was not
valid Python and nothing caught it (`BUILD_JOURNAL.md` ISSUE-029).

| Cell | File | Accelerator | Answers |
|---|---|---|---|
| 0 | `cell0_environment.py` | **off** | Which Python, which GPU, what is installed |
| 1 | `cell1_resolve.py` | **off** | Does Boltz resolve for this interpreter at all |
| 1b | `cell1b_nodeps_probe.py` | **off** | Only if still on 3.13: is `numpy<2.0` a hard requirement or a defensive pin |
| 2 | `cell2_install.py` | **off** | Install it, visibly, with a hard time limit |
| 3 | `cell3_metrics.py` | on | ipSAE, or PAE plus chain assignments — the check that decides the project |

Cells 0–2 run with the accelerator **off**. Installing and importing need no
GPU, and a GPU session spends the 30 h/week quota at wall-clock rate whether
or not the GPU is touched.

Stop at cell 0 if it reports Python 3.13 and pin the notebook to the original
environment first (`BUILD_JOURNAL.md` ISSUE-013). **Re-run cell 0 after
pinning**: "original" means the image from when the notebook was created, so
for a recent notebook it can also be 3.13. If it is, cell 1b is the next
cheapest question.
