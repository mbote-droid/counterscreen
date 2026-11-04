"""Every funnel table in prose lists the gates in the order they are run.

`DESIGN.md` section 8b makes the cascade order an engineering constraint, and
section 9b forbids typing numbers into prose. A funnel table typed in a
different order than the pipeline runs is the same class of error one step
removed: the numbers resolve correctly and still describe a pipeline nobody
ran, because a per-stage count only means anything relative to the stages
before it.

Amendment A10 is what made this worth pinning. Moving G8 to the front changed
every per-stage count in the funnel without changing a single survivor, and
two documents carried the table by hand -- in two different orders, neither of
them the pipeline's.
"""

import pathlib
import re

import pytest

from counterscreen.core.design import Gate
from counterscreen.rank.gates import PIPELINE_ORDER

ROOT = pathlib.Path(__file__).resolve().parents[2]
DOCUMENTS = (
    ROOT / "METHODS.md",
    ROOT / "campaigns" / "kras-g12d-pmhc" / "REPORT.md",
)
KEY = re.compile(r"\[\[funnel\.g([0-9]+)\]\]")


def gates_named(key: str) -> list[Gate]:
    """Split a funnel key into the gates it reports, in the order written.

    ``g79`` is one row for G7 and G9 because both are prior-art checks and the
    report gives them together; the digits are read one at a time.
    """
    return [Gate(f"G{digit}") for digit in key]


def funnel_gates(document: pathlib.Path) -> list[Gate]:
    found: list[Gate] = []
    for match in KEY.finditer(document.read_text()):
        found.extend(gates_named(match.group(1)))
    return found


@pytest.mark.parametrize("document", DOCUMENTS, ids=lambda p: p.name)
def test_the_funnel_table_follows_the_pipeline_order(document: pathlib.Path) -> None:
    assert funnel_gates(document) == list(PIPELINE_ORDER), (
        f"{document.name} lists the funnel out of pipeline order"
    )


@pytest.mark.parametrize("document", DOCUMENTS, ids=lambda p: p.name)
def test_the_funnel_table_covers_every_gate_exactly_once(document: pathlib.Path) -> None:
    found = funnel_gates(document)
    assert len(set(found)) == len(found)
    assert set(found) == set(Gate)


def test_the_documents_agree_with_each_other() -> None:
    first, *rest = [funnel_gates(document) for document in DOCUMENTS]
    for other in rest:
        assert other == first
