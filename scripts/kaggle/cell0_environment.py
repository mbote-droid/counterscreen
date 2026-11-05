"""Cell 0 — what this notebook is running on, in seconds.

Paste the whole file into a Kaggle cell and run it. Run this one with the
**accelerator off**: it needs no GPU, and a GPU session spends the 30 h/week
quota at wall-clock rate whether or not the GPU is touched.

If the Python version is 3.13, stop here and pin the notebook to the original
environment before going on (`BUILD_JOURNAL.md` ISSUE-013): Boltz and Protenix
may have no 3.13 wheels, and pip answers that by backtracking through the
index for as long as you let it.
"""

import importlib.metadata as md
import platform
import subprocess
import sys


def main() -> int:
    print("python  ", sys.version.replace("\n", " "))
    print("platform", platform.platform())

    try:
        gpu = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,driver_version,memory.total", "--format=csv,noheader"],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        ).stdout.strip()
    except (OSError, subprocess.SubprocessError) as exc:
        gpu = f"no GPU ({type(exc).__name__})"
    print("gpu     ", gpu or "no GPU attached")

    for package in ("torch", "numpy", "scipy", "biotite"):
        try:
            print(f"{package:9s}", md.version(package))
        except md.PackageNotFoundError:
            print(f"{package:9s}", "absent")

    if sys.version_info[:2] >= (3, 13):
        print("\nSTOP: Python 3.13. Pin the notebook to the original environment")
        print("before installing anything. BUILD_JOURNAL.md ISSUE-013.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
