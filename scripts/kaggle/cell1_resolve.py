"""Cell 1 — whether Boltz can be resolved for this interpreter at all.

`pip --dry-run` resolves without downloading wheels, so this answers in
seconds to minutes what a full install takes an hour to fail at. A timeout
rather than a hang: if the resolver is still working after three minutes it is
backtracking through the index, which means no compatible version exists and
waiting longer will not change that.

Accelerator still off.
"""

import importlib.util
import subprocess
import sys

TIMEOUT_SECONDS = 180
PACKAGE = "boltz"

#: Lines that mean "no wheel for this interpreter, so pip is compiling".
#: Measured on Python 3.13: boltz pins numpy<2.0, numpy has no 3.13 wheel
#: below 2.1, and scipy follows it down. `BUILD_JOURNAL.md` ISSUE-013.
SOURCE_BUILD_MARKERS = (".tar.gz", "Preparing metadata", "meson", "Building wheel")


def main() -> int:
    # "Could not run the resolver" and "the resolver said no" are different
    # answers, and a diagnostic cell that reports the second for the first is
    # worse than one that says nothing.
    if importlib.util.find_spec("pip") is None:
        print(f"pip is not installed for {sys.executable}.")
        print("This says nothing about whether boltz resolves. On Kaggle pip is")
        print("present; if you see this there, the interpreter is not the one")
        print("you think it is.")
        return 3

    command = [sys.executable, "-m", "pip", "install", "--dry-run", "--no-cache-dir", PACKAGE]
    print(" ".join(command), f"(timeout {TIMEOUT_SECONDS}s)\n", flush=True)
    try:
        result = subprocess.run(
            command, capture_output=True, text=True, timeout=TIMEOUT_SECONDS, check=False
        )
    except subprocess.TimeoutExpired:
        print(f"\nTIMED OUT after {TIMEOUT_SECONDS}s.")
        print(
            f"No resolvable {PACKAGE} version for Python {sys.version_info.major}."
            f"{sys.version_info.minor}; the resolver is backtracking."
        )
        print("Pin the notebook to the original environment. BUILD_JOURNAL.md ISSUE-013.")
        return 2

    output = (result.stdout + result.stderr).strip().splitlines()
    for line in output[-25:]:
        print(line)

    compiling = sorted(
        {
            line.strip()
            for line in output
            if any(marker in line for marker in SOURCE_BUILD_MARKERS)
        }
    )
    if compiling:
        print("\nSOURCE BUILDS — pip has no wheel for this interpreter:")
        for line in compiling[:8]:
            print(" ", line)
        print("On Python 3.13 this is numpy and scipy, pulled below their 3.13")
        print("wheels by boltz's numpy<2.0 pin. Pin the notebook to Python 3.12")
        print("or earlier rather than waiting. BUILD_JOURNAL.md ISSUE-013.")
    print("\nexit code", result.returncode)
    if result.returncode != 0:
        print(f"pip exited {result.returncode}. If the lines above name a version")
        print(f"conflict, {PACKAGE} does not resolve for this interpreter; if they")
        print("name a network or index error, that is a different problem.")
        print("Record which, in benchmarks/day1_gpu_benchmark.md, before cell 2.")
    return result.returncode


if __name__ == "__main__":
    # A notebook renders `raise SystemExit` as a red traceback, which makes a
    # verdict look like a crash. Pasted into a cell this prints and stops; run
    # as a script it still exits with the status.
    _status = main()
    if _status and "IPython" not in sys.modules:
        raise SystemExit(_status)
