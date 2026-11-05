"""The Day-1 notebook cells are real Python, checkable like everything else.

They were first written as `CELL_n = r\"\"\"...\"\"\"` string constants inside a
module. That made them uncopyable -- pasting a cell into Kaggle assigned a
string and ran nothing -- and invisible to ruff, mypy and the compiler, which
is how one of them shipped as invalid Python (`BUILD_JOURNAL.md` ISSUE-029).

Each cell is now a file that compiles, imports nothing that is missing, and
uses no notebook-only syntax, so pasting it into a cell runs it.
"""

import ast
import pathlib

import pytest

KAGGLE = pathlib.Path(__file__).resolve().parents[2] / "scripts" / "kaggle"
CELLS = sorted(KAGGLE.glob("cell*.py"))

#: Jupyter line and cell magics. Valid in a notebook, a syntax error anywhere
#: else, which is exactly the trap: a cell carrying one cannot be checked.
MAGIC_PREFIXES = ("!", "%", "%%")


def test_there_are_cells_to_check() -> None:
    assert len(CELLS) >= 4, [path.name for path in CELLS]


@pytest.mark.parametrize("path", CELLS, ids=lambda p: p.name)
def test_each_cell_is_valid_python(path: pathlib.Path) -> None:
    """The failure that shipped: a cell that was never compiled by anything."""
    ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


@pytest.mark.parametrize("path", CELLS, ids=lambda p: p.name)
def test_no_cell_uses_notebook_only_syntax(path: pathlib.Path) -> None:
    """`!pip install` runs in Kaggle and nowhere else, so it cannot be tested."""
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = line.strip()
        if stripped.startswith(MAGIC_PREFIXES):
            pytest.fail(f"{path.name}:{number} uses notebook-only syntax: {stripped!r}")


@pytest.mark.parametrize("path", CELLS, ids=lambda p: p.name)
def test_each_cell_runs_as_a_script_and_as_a_paste(path: pathlib.Path) -> None:
    """Both entry points must exist: `main()` and the `__main__` guard.

    Pasting the file into a cell executes the module body, so without the
    guard the cell would define a function and do nothing -- the same silent
    no-op as the string-constant form.
    """
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    functions = {node.name for node in tree.body if isinstance(node, ast.FunctionDef)}
    assert "main" in functions, f"{path.name} has no main()"

    guarded = [
        node
        for node in tree.body
        if isinstance(node, ast.If) and ast.unparse(node.test) == "__name__ == '__main__'"
    ]
    assert guarded, f"{path.name} has no `if __name__ == '__main__'` guard"


@pytest.mark.parametrize("path", CELLS, ids=lambda p: p.name)
def test_each_cell_says_what_it_answers(path: pathlib.Path) -> None:
    """An operator-facing cell with no docstring is a cell nobody can order."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    docstring = ast.get_docstring(tree)
    assert docstring, f"{path.name} has no module docstring"
    assert len(docstring.splitlines()) > 1, f"{path.name} documents only a title"
