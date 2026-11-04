"""Claim checker contract (DESIGN.md section 9b): no number typed by hand."""

import statistics
import time
from collections.abc import Sequence
from pathlib import Path

import pytest

from counterscreen.core.intervals import CONFIDENCE_LEVEL, Z_TWO_SIDED, level_label
from counterscreen.report.claims import (
    SIG_DIGITS,
    Violation,
    ViolationKind,
    check,
    find_stale_document,
    find_uncited_numerals,
    find_unknown_keys,
    flatten,
    resolve,
    round_significant,
)

METRICS = {
    "far": {"point": 0.025, "ci_lo": 0.003, "ci_hi": 0.13},
    "funnel": {"generated": 412, "g0": 390},
}


def kinds(violations: Sequence[Violation]) -> set[ViolationKind]:
    return {v.kind for v in violations}


# --- The metrics dictionary is the contract ---------------------------------


def test_nested_metrics_flatten_to_dotted_keys() -> None:
    flat = flatten(METRICS)
    assert flat["far.point"] == pytest.approx(0.025)
    assert flat["funnel.generated"] == 412


def test_floats_are_rounded_to_a_fixed_significance() -> None:
    """build_rules section 2.6: byte-identical output across platforms."""
    assert round_significant(1 / 3) == pytest.approx(0.333333)
    assert round_significant(123456789.0) == pytest.approx(123457000.0)
    assert round_significant(0.000123456789) == pytest.approx(0.000123457)
    assert len(str(round_significant(1 / 3)).rstrip("0").replace("0.", "")) <= SIG_DIGITS


def test_zero_and_non_finite_survive_rounding() -> None:
    assert round_significant(0.0) == 0.0
    assert round_significant(float("inf")) == float("inf")


# --- Resolution -------------------------------------------------------------


def test_keys_resolve_to_their_metric() -> None:
    rendered = resolve("The rate was [[far.point]].", METRICS)
    assert rendered == "The rate was 0.025."


def test_an_unknown_key_is_left_visible_rather_than_blanked() -> None:
    """A missing metric must not be mistakable for a rendered one."""
    rendered = resolve("Value [[far.nonexistent]].", METRICS)
    assert "[[far.nonexistent]]" in rendered


# --- Condition 1: a key with no matching entry ------------------------------


def test_an_unknown_key_is_reported_with_its_line() -> None:
    template = "First line.\nThe rate was [[far.missing]].\n"
    (violation,) = find_unknown_keys(template, METRICS)
    assert violation.kind is ViolationKind.UNKNOWN_KEY
    assert violation.line == 2
    assert "far.missing" in violation.detail


def test_known_keys_raise_nothing() -> None:
    assert find_unknown_keys("[[far.point]] and [[funnel.g0]]", METRICS) == []


# --- Condition 2: a bare numeral outside a key ------------------------------


def test_a_hand_typed_number_is_caught() -> None:
    (violation,) = find_uncited_numerals("The measured false-accept rate was 2.5%.")
    assert violation.kind is ViolationKind.UNCITED_NUMERAL


def test_a_number_written_as_a_key_is_not_a_violation() -> None:
    assert find_uncited_numerals("The rate was [[far.point]].") == []


def test_a_literature_value_with_a_reference_marker_is_allowed() -> None:
    """Section 9b's one exception, tied to REFERENCES.md."""
    assert find_uncited_numerals("Binder rate was 26.8% across 1,320 designs [R14].") == []


@pytest.mark.parametrize(
    "line",
    [
        "See PROTOCOL.md section 12.6 for the argument.",
        "As §8.7 sets out.",
        "## 8.7 The funnel",
        "1. Apply gates; log rejections per gate",
        "Use `uv lock --check` in CI.",
        "The standard fit assumes a 1:1 interaction.",
        "| --- | --- |",
    ],
)
def test_structure_and_references_are_not_claims(line: str) -> None:
    assert find_uncited_numerals(line) == []


def test_a_numeral_inside_prose_on_a_structural_line_is_still_caught() -> None:
    violations = find_uncited_numerals("## Results\nWe measured 37 passing designs.")
    assert len(violations) == 1
    assert violations[0].line == 2


# --- Condition 3: a result newer than the document --------------------------


def test_a_result_newer_than_the_document_is_caught(tmp_path: Path) -> None:
    document = tmp_path / "METHODS.md"
    document.write_text("generated", encoding="utf-8")
    time.sleep(0.01)
    result = tmp_path / "metrics.json"
    result.write_text("{}", encoding="utf-8")

    (violation,) = find_stale_document(document, [result])
    assert violation.kind is ViolationKind.STALE_DOCUMENT
    assert "regenerate" in violation.detail


def test_a_document_newer_than_its_results_is_fine(tmp_path: Path) -> None:
    result = tmp_path / "metrics.json"
    result.write_text("{}", encoding="utf-8")
    time.sleep(0.01)
    document = tmp_path / "METHODS.md"
    document.write_text("generated", encoding="utf-8")

    assert find_stale_document(document, [result]) == []


def test_an_ungenerated_document_is_reported(tmp_path: Path) -> None:
    (violation,) = find_stale_document(tmp_path / "missing.md", [])
    assert violation.kind is ViolationKind.STALE_DOCUMENT
    assert "not been generated" in violation.detail


# --- All three together -----------------------------------------------------


def test_a_clean_document_passes_every_check(tmp_path: Path) -> None:
    result = tmp_path / "metrics.json"
    result.write_text("{}", encoding="utf-8")
    time.sleep(0.01)
    document = tmp_path / "METHODS.md"
    document.write_text("x", encoding="utf-8")

    template = (
        "## Results\n"
        "The measured false-accept rate was [[far.point]] "
        "([[ci.level]] CI [[far.ci_lo]]-[[far.ci_hi]]).\n"
        "Base rate was 26.8% [R14].\n"
    )
    assert check(template, METRICS, document=document, results=[result]) == []


def test_every_failure_mode_is_reported_together(tmp_path: Path) -> None:
    document = tmp_path / "METHODS.md"
    document.write_text("x", encoding="utf-8")
    time.sleep(0.01)
    result = tmp_path / "metrics.json"
    result.write_text("{}", encoding="utf-8")

    template = "Rate was [[far.missing]] and also 0.42 by hand.\n"
    found = check(template, METRICS, document=document, results=[result])
    assert kinds(found) == {
        ViolationKind.UNKNOWN_KEY,
        ViolationKind.UNCITED_NUMERAL,
        ViolationKind.STALE_DOCUMENT,
    }


# --- The confidence level is cited, not exempted (BUILD_JOURNAL ISSUE-011) ---


def test_a_hand_typed_confidence_level_is_a_bare_numeral() -> None:
    """The decision recorded against ISSUE-011: no exclusion for "95% CI".

    It is the one number in that sentence that can disagree with the code
    computing the interval, so exempting it would have defeated the rule at
    exactly the point the rule is for.
    """
    assert len(find_uncited_numerals("Measured at 95% CI by the Wilson method.")) == 1
    assert len(find_uncited_numerals("Reported with a 95 % confidence interval.")) == 1


def test_the_registered_level_resolves_without_a_result_file() -> None:
    assert resolve("([[ci.level]] CI)", {}) == f"({level_label()} CI)"
    assert find_unknown_keys("[[ci.level]]", {}) == []


def test_a_result_file_cannot_redefine_the_registered_level() -> None:
    """Otherwise a run could state a level its interval was not computed at."""
    assert resolve("[[ci.level]]", {"ci": {"level": "80%"}}) == level_label()


def test_the_level_and_its_quantile_cannot_disagree() -> None:
    """The quantile is derived from the level, so there is nothing to sync."""
    coverage = 2.0 * statistics.NormalDist().cdf(Z_TWO_SIDED) - 1.0
    assert coverage == pytest.approx(CONFIDENCE_LEVEL)
    assert pytest.approx(1.959963984540054, abs=1e-12) == Z_TWO_SIDED
