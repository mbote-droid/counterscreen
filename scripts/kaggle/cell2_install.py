"""Cell 2 — install Boltz, with the output visible while it runs.

No pipe, so each line appears as pip produces it; an elapsed-time prefix, so a
stall is obvious; a log file, so the evidence survives a lost browser
connection; and a hard kill, so it cannot run for an hour saying nothing.

`BUILD_JOURNAL.md` ISSUE-027 is why. The cell this replaces ended in
`| tail -5`, and `tail` cannot emit a line until the command it is piped from
exits, so a stalled install and a healthy one looked identical for 79 minutes.

Accelerator still off: installing needs no GPU.
"""

import subprocess
import sys
import time
from pathlib import Path

KILL_AFTER_SECONDS = 1800
LOG = Path("/kaggle/working/boltz_install.log")
PACKAGE = "boltz"


def main() -> int:
    command = [
        sys.executable,
        "-m",
        "pip",
        "install",
        "--no-cache-dir",
        "--progress-bar",
        "off",
        PACKAGE,
    ]
    print(" ".join(command), f"(kill after {KILL_AFTER_SECONDS}s)\n", flush=True)

    log_path = LOG if LOG.parent.is_dir() else Path("boltz_install.log")
    start = time.monotonic()
    killed = False
    with (
        log_path.open("w", encoding="utf-8") as log,
        subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        ) as proc,
    ):
        for line in proc.stdout or ():
            elapsed = time.monotonic() - start
            print(f"[{elapsed:6.0f}s] {line}", end="", flush=True)
            log.write(line)
            log.flush()
            if elapsed > KILL_AFTER_SECONDS:
                proc.kill()
                killed = True
                break
        proc.wait()

    total = time.monotonic() - start
    if killed:
        print(f"\nKILLED after {total:.0f}s. The last line above is where it stopped;")
        print(f"record it in benchmarks/day1_gpu_benchmark.md. Full log: {log_path}")
        return 2
    print(f"\nexit code {proc.returncode} after {total:.0f}s. Log: {log_path}")
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
