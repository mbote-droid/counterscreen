"""Cell 3 — the check that decides the project.

`benchmarks/day1_gpu_benchmark.md` calls this the pass condition:
**ipSAE emitted directly, or a PAE matrix plus chain assignments** so ipSAE
can be computed. If neither holds for any model in the stack, `PROTOCOL.md`
§7.1 has no input and the plan changes before Day 2 — that is a result, not an
obstacle to work around.

Record what the model *emits*, not whether it "has confidence". Accelerator on
from here.
"""

import importlib
import pkgutil
import sys

WANTED = ("ipsae", "pae", "ptm", "iptm", "plddt", "chain")


def main() -> int:
    try:
        import boltz  # noqa: PLC0415 - the import failing is the measurement
    except ImportError as exc:
        print("boltz did not import:", exc)
        print("That is the Day-1 answer for this model. Record it and try Protenix.")
        return 1

    print("boltz", getattr(boltz, "__version__", "unknown"))
    print("modules:", sorted(m.name for m in pkgutil.iter_modules(boltz.__path__)))

    for name in ("boltz.main", "boltz.model.model", "boltz.data.types"):
        try:
            module = importlib.import_module(name)
        except Exception as exc:  # noqa: BLE001 - any import failure is the datum
            print(f"{name}: {type(exc).__name__}: {exc}")
            continue
        hits = sorted(
            attribute
            for attribute in dir(module)
            if any(word in attribute.lower() for word in WANTED)
        )
        print(f"{name}: {hits or 'nothing confidence-shaped'}")

    print("\nRecord in benchmarks/day1_gpu_benchmark.md, per model:")
    print("  metrics emitted | PAE matrix available | chain assignments available")
    return 0


if __name__ == "__main__":
    # A notebook renders `raise SystemExit` as a red traceback, which makes a
    # verdict look like a crash. Pasted into a cell this prints and stops; run
    # as a script it still exits with the status.
    _status = main()
    if _status and "IPython" not in sys.modules:
        raise SystemExit(_status)
