"""Cell 1b — is boltz's `numpy<2.0` a hard requirement or a defensive pin.

Run this only if cell 0 still reports Python 3.13 after pinning the
environment, which happens when the notebook was created recently enough that
its "original" image is already 3.13 (`BUILD_JOURNAL.md` ISSUE-013).

The pin is what forces numpy 1.26.4 and scipy 1.13.1 to build from source on
3.13. This installs every *other* dependency normally, installs boltz itself
without dependencies, leaves the image's numpy 2.x in place, and tries to
import it. Nothing compiles, so it answers in a minute or two.

An import that works is not proof the pin was unnecessary -- boltz may use a
removed numpy 1.x API only on some code path -- so treat a pass as "worth
carrying on with" and record it as such, not as "the pin was wrong". The
authoritative check is still a real prediction in cell 3.

Accelerator off.
"""

import importlib.metadata as md
import subprocess
import sys

PACKAGE = "boltz"
#: Left at whatever the image already has, which is what the probe is about.
HELD = {"numpy", "scipy"}


def requirements() -> list[str]:
    """Boltz's declared dependencies, minus the ones being held back."""
    wanted: list[str] = []
    for raw in md.distribution(PACKAGE).requires or ():
        if ";" in raw:  # an extra or an environment marker; skip optional ones
            requirement, marker = raw.split(";", 1)
            if "extra" in marker:
                continue
        else:
            requirement = raw
        name = requirement.strip().split("[")[0].split("=")[0].split("<")[0].split(">")[0]
        if name.strip().lower() in HELD:
            print(f"holding back {requirement.strip()} — the image's version stays")
            continue
        wanted.append(requirement.strip())
    return wanted


def pip(*arguments: str) -> int:
    command = [sys.executable, "-m", "pip", "install", "--no-cache-dir", *arguments]
    print("\n$", " ".join(command), flush=True)
    return subprocess.run(command, check=False).returncode


def main() -> int:
    for package in sorted(HELD):
        try:
            print(f"{package} already installed:", md.version(package))
        except md.PackageNotFoundError:
            print(f"{package} absent — this probe assumes the image supplies it")
            return 2

    if pip("--no-deps", PACKAGE) != 0:
        print(f"\n{PACKAGE} would not install even without dependencies.")
        return 1

    pending = requirements()
    print(f"\n{len(pending)} dependencies to install normally")
    if pending and pip(*pending) != 0:
        print("\nA dependency failed. The line above names it; record it and stop.")
        return 1

    try:
        import boltz  # noqa: PLC0415 - the import is the measurement
    except Exception as exc:  # noqa: BLE001 - any failure is the answer
        print(f"\nimport boltz -> {type(exc).__name__}: {exc}")
        print("The pin is real on this numpy. Go to a 3.12 interpreter.")
        return 1

    print(f"\nimport boltz OK, version {getattr(boltz, '__version__', 'unknown')}")
    print(f"numpy still {md.version('numpy')}, scipy still {md.version('scipy')}")
    print("Worth carrying on with. Not proof the pin was unnecessary — record it")
    print("as 'imports under numpy 2.x' and let cell 3 decide.")
    return 0


if __name__ == "__main__":
    # A notebook renders `raise SystemExit` as a red traceback, which makes a
    # verdict look like a crash. Pasted into a cell this prints and stops; run
    # as a script it still exits with the status.
    _status = main()
    if _status and "IPython" not in sys.modules:
        raise SystemExit(_status)
