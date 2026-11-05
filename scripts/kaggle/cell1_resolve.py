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
    print("\nexit code", result.returncode)
    if result.returncode != 0:
        print(f"pip exited {result.returncode}. If the lines above name a version")
        print(f"conflict, {PACKAGE} does not resolve for this interpreter; if they")
        print("name a network or index error, that is a different problem.")
        print("Record which, in benchmarks/day1_gpu_benchmark.md, before cell 2.")
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
