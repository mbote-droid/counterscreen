"""Numeric provenance: no number is typed by hand into a generated document.

`DESIGN.md` section 9b states this as a constraint rather than a preference,
and gives the reason: hand-copying results from a terminal into prose is how
stale numbers reach a manuscript, and a number that no longer matches the run
that produced it is indistinguishable from one that was never computed.

Every numeric claim is written as a key:

    The measured false-accept rate was [[far.point]] (95% CI
    [[far.ci_lo]]-[[far.ci_hi]]).

:func:`resolve` fills those in from the result metrics, and :func:`check`
implements the three conditions section 9b requires CI to fail on: a key with
no matching entry, a bare numeral outside a key, and a result file newer than
the document it supposedly produced.

The payoff is a sentence the methods can carry honestly -- *every number in
this report resolves mechanically to a result file* -- which any reader can
verify rather than take on trust.

**Exclusions beyond what section 9b specifies.** The registered rule names
one exception, a literature value carrying a reference marker. A checker with
only that exception rejects its own document: headings, numbered lists,
section cross-references, table rules, ratios such as 1:1, anything inside
backticks, and a stated confidence level like "95% CI" are all bare numerals
by the letter of the rule. Each is document structure or a registered design
choice rather than a measured claim, so each is masked before the scan, named
as a pattern at the top of this module, and covered by its own test. They are
additions to the registered rule and are listed here so they can be argued
with rather than discovered.

**The honest limit, stated here as `build_rules.pdf` section VIII states it
for its own checker.** This verifies that a number equals the metric it cites.
It cannot verify that the metric is the one the sentence is about. A correct
value attached to the wrong concept passes, and only a reader catches that.
The residual error is real and should be reported as such rather than implied
away.
"""

import dataclasses
import enum
import math
import re
from collections.abc import Mapping, Sequence
from pathlib import Path

#: Significant digits every metric is rounded to, so byte-identical output
#: survives platform float noise (`build_rules.pdf` section 2.6).
SIG_DIGITS = 6

KEY = re.compile(r"\[\[([a-z0-9_]+(?:\.[a-z0-9_]+)*)\]\]")
REFERENCE = re.compile(r"\[R\d+[a-z]?\]")
INLINE_CODE = re.compile(r"`[^`]*`")
SECTION_REFERENCE = re.compile(r"(?:§|[Ss]ection\s+)\d+(?:\.\d+)*[a-z]?")
HEADING = re.compile(r"^#{1,6}\s+\d+(?:\.\d+)*[a-z]?")
LIST_MARKER = re.compile(r"^\s*\d+[.)]\s")
TABLE_RULE = re.compile(r"^\|[\s|:-]+\|$")
RATIO = re.compile(r"\b\d+:\d+\b")
#: A stated confidence level is a registered design choice, not a measured
#: result, and `METHODS.md` section 8.5 already writes it bare beside the
#: keys it qualifies. See the note on exclusions in the module docstring.
CONFIDENCE_LEVEL = re.compile(r"\b\d{2}(?:\.\d+)?\s*%\s*(?:CI\b|confidence)", re.IGNORECASE)
NUMERAL = re.compile(r"\d")


class ViolationKind(enum.StrEnum):
    """The three conditions `DESIGN.md` section 9b fails the build on."""

    UNKNOWN_KEY = "unknown_key"
    UNCITED_NUMERAL = "uncited_numeral"
    STALE_DOCUMENT = "stale_document"


@dataclasses.dataclass(frozen=True, slots=True)
class Violation:
    """One claim-checking failure, with enough detail to fix it."""

    kind: ViolationKind
    detail: str
    line: int = 0


def round_significant(value: float, digits: int = SIG_DIGITS) -> float:
    """Round to a number of significant digits, not decimal places."""
    if value == 0.0 or not math.isfinite(value):
        return value
    exponent = math.floor(math.log10(abs(value)))
    return round(value, -(exponent - digits + 1))


def flatten(metrics: Mapping[str, object], prefix: str = "") -> dict[str, object]:
    """Flatten nested metrics into dotted keys.

    `build_rules.pdf` section 2.6: one nested dictionary is the entire contract
    between computation and prose. Everything downstream -- the report, the
    checker, the figures -- reads only this.
    """
    flat: dict[str, object] = {}
    for name, value in metrics.items():
        dotted = f"{prefix}{name}"
        if isinstance(value, Mapping):
            flat.update(flatten(value, prefix=f"{dotted}."))
        elif isinstance(value, float):
            flat[dotted] = round_significant(value)
        else:
            flat[dotted] = value
    return flat


def _format(value: object) -> str:
    if isinstance(value, float):
        return f"{round_significant(value):g}"
    return str(value)


def resolve(template: str, metrics: Mapping[str, object]) -> str:
    """Replace every key with its value, leaving unknown keys in place.

    Unknown keys are deliberately not substituted with a placeholder: they stay
    visible in the output and :func:`check` reports them, so a missing metric
    cannot be mistaken for a rendered one.
    """
    flat = flatten(metrics)

    def substitute(match: re.Match[str]) -> str:
        key = match.group(1)
        if key not in flat:
            return match.group(0)
        return _format(flat[key])

    return KEY.sub(substitute, template)


def _mask(line: str) -> str:
    """Blank out everything a bare numeral is allowed to live inside."""
    masked = KEY.sub(" ", line)
    masked = INLINE_CODE.sub(" ", masked)
    masked = SECTION_REFERENCE.sub(" ", masked)
    masked = HEADING.sub(" ", masked)
    masked = LIST_MARKER.sub(" ", masked)
    masked = CONFIDENCE_LEVEL.sub(" ", masked)
    return RATIO.sub(" ", masked)


def find_unknown_keys(template: str, metrics: Mapping[str, object]) -> list[Violation]:
    """Find keys with no matching entry in the metrics."""
    flat = flatten(metrics)
    found: list[Violation] = []
    for number, line in enumerate(template.splitlines(), start=1):
        for match in KEY.finditer(line):
            key = match.group(1)
            if key not in flat:
                found.append(
                    Violation(
                        kind=ViolationKind.UNKNOWN_KEY,
                        detail=f"{key!r} has no entry in the result metrics",
                        line=number,
                    )
                )
    return found


def find_uncited_numerals(template: str) -> list[Violation]:
    """Find numerals written into prose rather than cited through a key.

    Literature values are the one exception section 9b allows, and they carry a
    reference marker tying them to `REFERENCES.md`, so a line containing one is
    skipped. Section references, headings, list markers, table rules, ratios
    such as 1:1, and anything inside backticks are structure rather than
    claims, and are masked before the scan.
    """
    found: list[Violation] = []
    for number, line in enumerate(template.splitlines(), start=1):
        stripped = line.strip()
        if not stripped or TABLE_RULE.match(stripped) or REFERENCE.search(line):
            continue
        masked = _mask(line)
        if NUMERAL.search(masked):
            found.append(
                Violation(
                    kind=ViolationKind.UNCITED_NUMERAL,
                    detail=f"bare numeral outside a key: {stripped!r}",
                    line=number,
                )
            )
    return found


def find_stale_document(document: Path, results: Sequence[Path]) -> list[Violation]:
    """Report any result file newer than the document generated from it."""
    if not document.exists():
        return [
            Violation(
                kind=ViolationKind.STALE_DOCUMENT,
                detail=f"{document} has not been generated",
            )
        ]
    generated = document.stat().st_mtime
    return [
        Violation(
            kind=ViolationKind.STALE_DOCUMENT,
            detail=f"{result} is newer than {document}; regenerate the document",
        )
        for result in results
        if result.exists() and result.stat().st_mtime > generated
    ]


def check(
    template: str,
    metrics: Mapping[str, object],
    document: Path | None = None,
    results: Sequence[Path] = (),
) -> list[Violation]:
    """Run every claim check `DESIGN.md` section 9b requires of CI."""
    found = find_unknown_keys(template, metrics) + find_uncited_numerals(template)
    if document is not None:
        found.extend(find_stale_document(document, results))
    return found
