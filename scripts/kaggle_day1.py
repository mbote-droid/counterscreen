"""Day-1 benchmark cells, written to be diagnosable rather than terse.

Paste each block into its own Kaggle cell. They are ordered so that the
cheapest question is answered first and no cell can hang without saying so.

**Run cells 0-2 with the accelerator OFF.** Installing and importing needs no
GPU, and a GPU session burns the 30 h/week quota at wall-clock rate whether or
not the GPU is used. Switch the accelerator on for cell 3 and after.

`BUILD_JOURNAL.md` ISSUE-027 is why these look the way they do: the earlier
install cell ended in `| tail -5`, which buffers every line until the command
finishes, so an install that stalled for 79 minutes showed exactly what a
healthy one would have.
"""

# --- Cell 0: what are we on? Seconds, and it decides the rest. -------------
CELL_0 = r"""
import sys, platform, subprocess
print("python", sys.version)
print("platform", platform.platform())
print(subprocess.run(["nvidia-smi", "--query-gpu=name,driver_version,memory.total",
                      "--format=csv,noheader"], capture_output=True, text=True).stdout or "no GPU")
import importlib.metadata as md
for pkg in ("torch", "numpy", "scipy"):
    try:
        print(pkg, md.version(pkg))
    except md.PackageNotFoundError:
        print(pkg, "absent")
"""

# --- Cell 1: can boltz even be resolved for this Python? -------------------
# `--dry-run` resolves without downloading wheels. If this cannot find a
# version, the install in cell 2 would have backtracked through the index
# forever: that is the Python 3.13 case of ISSUE-013, and the answer is to
# pin the notebook to the original environment rather than to wait.
CELL_1 = r"""
!timeout 180 python -m pip install --dry-run --no-cache-dir boltz 2>&1 | tail -20 \
    || echo "TIMED OUT: no resolvable version for this Python (ISSUE-013)"
"""

# --- Cell 2: install, with the output visible while it runs ----------------
# No pipe, so lines appear as they are produced. A hard timeout, so a stall
# ends by itself. A log file, so the evidence survives a lost connection.
CELL_2 = r"""
import subprocess, sys, time
start = time.time()
log = open("/kaggle/working/boltz_install.log", "w")
proc = subprocess.Popen(
    [sys.executable, "-m", "pip", "install", "--no-cache-dir", "--progress-bar", "off", "boltz"],
    stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1,
)
for line in proc.stdout:
    elapsed = time.time() - start
    print(f"[{elapsed:6.0f}s] {line}", end="", flush=True)
    log.write(line); log.flush()
    if elapsed > 1800:
        proc.kill()
        print("\nKILLED at 30 min. Record the last line above in the benchmark sheet.")
        break
proc.wait()
log.close()
print("exit code", proc.returncode, "after", f"{time.time()-start:.0f}s")
"""

# --- Cell 3: the check that decides the project ----------------------------
# `benchmarks/day1_gpu_benchmark.md` calls this the pass condition: ipSAE
# emitted directly, or a PAE matrix plus chain assignments so it can be
# computed. Record exactly what each model emits, not whether it "has
# confidence". Needs the GPU.
CELL_3 = r"""
import boltz, pkgutil, inspect
print("boltz", getattr(boltz, "__version__", "?"))
print(sorted(m.name for m in pkgutil.iter_modules(boltz.__path__)))

# What the output object actually carries is the question. Name every field.
import importlib
for module in ("boltz.main", "boltz.model.model"):
    try:
        mod = importlib.import_module(module)
        print(module, [n for n in dir(mod) if "pae" in n.lower() or "sae" in n.lower()])
    except Exception as exc:  # noqa: BLE001
        print(module, "->", type(exc).__name__, exc)
"""

CELLS = (CELL_0, CELL_1, CELL_2, CELL_3)

if __name__ == "__main__":
    for index, cell in enumerate(CELLS):
        print(f"\n{'=' * 70}\n# Cell {index}\n{'=' * 70}{cell}")
