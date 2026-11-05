"""The Stage -1 control panel: what it is made of, and what it may not contain.

`PROTOCOL.md` section 5 makes Stage -1 a falsification check run before anything
else: determine whether the chosen metrics can resolve a single-residue
epitope change *at all*. If they cannot, the neural arm is blind and the
pipeline falls back to physics. Cost is a few hours; it can invalidate the
approach on day one, and that property is the point.

**The initial-guess trap is enforced here, not documented here.** `DESIGN.md`
section 3 and `PROTOCOL.md` section 5.2 both say controls must run exactly as
designs will run, because seeding a control with its crystal pose leaks the
answer and makes calibration meaningless. `DESIGN.md` section 3 is explicit
that this should be encoded as a test rather than a comment, and
`PROTOCOL.md` section 12.4b registers "return the crystal pose as a control
seed" as a mutant a provenance assertion must kill. So a control carrying
:attr:`SeedProvenance.CRYSTAL` is refused by :func:`validate_panel`, and the
panel cannot be assembled around it.

**Difficulty is measured, not assumed.** A control only tests what its
on-target and off-target peptides actually differ by. Counting that difference
is what revealed that the published panel supplies a single genuine
single-residue discrimination rather than the five the registered floor needs
(`FINDINGS.md` F-3), so the count is computed from the sequences here rather
than taken from a description of them.
"""

import dataclasses
import enum
import random
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import yaml

from counterscreen.core.design import Gate

#: PREREGISTRATION.md section 6b: below this the go/no-go is not meaningful.
MIN_POSITIVE_CONTROLS = 5

#: A control is a single-residue discrimination when its on-target peptide
#: differs from its nearest off-target at exactly one position.
SINGLE_RESIDUE = 1


class PanelError(ValueError):
    """Raised when a control panel is not fit to calibrate against."""


class ControlRole(enum.StrEnum):
    """What a control is for, per `PROTOCOL.md` section 5.1."""

    POSITIVE = "positive"
    NEGATIVE = "negative"
    INVARIANT_SURFACE = "invariant_surface"


class SeedProvenance(enum.StrEnum):
    """How a control's structure was seeded.

    ``DESIGNED`` means folded from sequence by the same procedure the campaign
    designs receive. ``CRYSTAL`` means seeded from a deposited pose, which
    leaks the answer: the initial-guess procedure is seeded with the design
    model, so handing it the crystal structure tells it what it was meant to
    predict.
    """

    DESIGNED = "designed"
    CRYSTAL = "crystal"


def residue_differences(left: str, right: str) -> int | None:
    """Count differing positions, or ``None`` if the peptides differ in length.

    Length-mismatched peptides are not a discrimination task of a stated
    difficulty, so they return ``None`` rather than a misleading number.
    """
    if len(left) != len(right):
        return None
    return sum(1 for a, b in zip(left, right, strict=True) if a != b)


@dataclasses.dataclass(frozen=True, slots=True)
class Control:
    """One control, with the provenance `SETUP.md` section 3.5 requires."""

    name: str
    role: ControlRole
    allele: str
    target: str
    on_target_peptide: str
    off_target_peptides: tuple[tuple[str, str], ...] = ()
    source: str = ""
    seed_provenance: SeedProvenance = SeedProvenance.DESIGNED
    binder_sequence: str | None = None
    #: Chains of a multi-chain binder, e.g. a TCR's alpha and beta. Separate
    #: from ``binder_sequence`` because a scrambled or reversed negative is
    #: derived from a single chain and is not meaningful across two.
    binder_chains: tuple[str, ...] = ()
    expected_gate: Gate | None = None

    def __post_init__(self) -> None:
        """Refuse a control that cannot be used as registered."""
        if not self.name.strip():
            msg = "a control must be named"
            raise PanelError(msg)
        if self.role is ControlRole.NEGATIVE and self.expected_gate is None:
            msg = (
                f"negative control {self.name!r} has no registered failure gate. "
                "PROTOCOL.md section 5.4: a flawed design that fails for the wrong "
                "reason is a gate working by accident"
            )
            raise PanelError(msg)

    @property
    def difficulty(self) -> int | None:
        """Residue differences to the *nearest* off-target peptide.

        The nearest one sets the difficulty: a control is only as demanding as
        the closest decoy it has to reject.
        """
        counts = [
            count
            for peptide, _ in self.off_target_peptides
            if (count := residue_differences(self.on_target_peptide, peptide)) is not None
        ]
        return min(counts) if counts else None

    @property
    def is_single_residue(self) -> bool:
        """Whether this control tests a one-residue discrimination."""
        return self.difficulty == SINGLE_RESIDUE

    @property
    def is_foldable(self) -> bool:
        """Whether a sequence is available to fold, of one chain or several."""
        return bool(self.binder_sequence) or bool(self.binder_chains)

    @property
    def chains(self) -> tuple[str, ...]:
        """Every chain to fold, whether the control carries one or several."""
        if self.binder_chains:
            return self.binder_chains
        return (self.binder_sequence,) if self.binder_sequence else ()


@dataclasses.dataclass(frozen=True, slots=True)
class FloorReport:
    """Whether the panel clears the registered floor, and by how much.

    ``single_residue`` and ``foldable`` count the two properties separately
    and ``usable`` counts controls with **both**, which is the only one the
    floor can be judged against. Two independent counts cannot answer the
    question: a panel of five single-residue controls with no published
    binder sequences reported the floor as met while not one control could be
    folded (`FINDINGS.md` F-16).
    """

    positives: int
    single_residue: int
    foldable: int
    usable: int
    required: int = MIN_POSITIVE_CONTROLS

    def __post_init__(self) -> None:
        """Refuse counts that cannot describe one panel."""
        if self.usable > min(self.single_residue, self.foldable):
            msg = (
                f"usable={self.usable} exceeds single_residue={self.single_residue} "
                f"or foldable={self.foldable}; a usable control is both"
            )
            raise PanelError(msg)

    @property
    def met(self) -> bool:
        """Whether enough *runnable* single-residue positive controls exist.

        Stage -1 folds each control through the same procedure a design gets,
        so a control with no binder sequence cannot contribute to the
        calibration whatever its peptides differ by.
        """
        return self.usable >= self.required

    @property
    def shortfall(self) -> int:
        """How many runnable single-residue controls are still needed."""
        return max(0, self.required - self.usable)


def validate_panel(controls: Sequence[Control]) -> None:
    """Refuse a panel that would make calibration meaningless.

    The crystal-seed check is the one `DESIGN.md` section 3 asks to be encoded
    rather than written down, and it runs before anything else here because a
    leaked answer invalidates every number the panel produces.
    """
    leaked = [c.name for c in controls if c.seed_provenance is SeedProvenance.CRYSTAL]
    if leaked:
        msg = (
            f"controls seeded from crystal poses: {sorted(leaked)}. "
            "PROTOCOL.md section 5.2: controls must run exactly as designs will run; "
            "seeding from the deposited pose leaks the answer"
        )
        raise PanelError(msg)

    names = [c.name for c in controls]
    if len(set(names)) != len(names):
        msg = f"panel repeats a control name: {names}"
        raise PanelError(msg)


def assess_floor(controls: Sequence[Control]) -> FloorReport:
    """Measure the panel against the `PREREGISTRATION.md` section 6b floor."""
    validate_panel(controls)
    positives = [c for c in controls if c.role is ControlRole.POSITIVE]
    return FloorReport(
        positives=len(positives),
        single_residue=sum(1 for c in positives if c.is_single_residue),
        foldable=sum(1 for c in positives if c.is_foldable),
        usable=sum(1 for c in positives if c.is_single_residue and c.is_foldable),
    )


#: Sections a control catalogue may carry. ``supplementary`` is separate from
#: ``positives`` so the published panel and what was added to reach the floor
#: stay distinguishable in every report; both are positive controls.
POSITIVE_SECTIONS = ("positives", "supplementary")


def _control_from(entry: Mapping[str, Any], section: str) -> Control:
    """Build one control from a catalogue entry, refusing a malformed one."""
    missing = sorted({"name", "allele", "target", "on_target_peptide"} - set(entry))
    if missing:
        msg = f"control in {section!r} is missing {missing}: {dict(entry)}"
        raise PanelError(msg)

    role = ControlRole(entry.get("role", "positive" if section in POSITIVE_SECTIONS else section))
    off_targets = tuple(
        (str(item["peptide"]), str(item.get("name", "")))
        for item in entry.get("off_target_peptides", ())
    )
    gate = entry.get("expected_gate")
    return Control(
        name=str(entry["name"]),
        role=role,
        allele=str(entry["allele"]),
        target=str(entry["target"]),
        on_target_peptide=str(entry["on_target_peptide"]),
        off_target_peptides=off_targets,
        source=str(entry.get("source", "")),
        seed_provenance=SeedProvenance(entry.get("seed_provenance", "designed")),
        binder_sequence=entry.get("binder_sequence"),
        binder_chains=tuple(str(chain) for chain in entry.get("binder_chains", ())),
        expected_gate=Gate(gate) if gate else None,
    )


def load_catalogue(path: Path) -> tuple[Control, ...]:
    """Read a control catalogue into controls, validated as a panel.

    The panel is data rather than code so that obtaining a control is an edit
    to one file and the go/no-go recomputes from it. `PROTOCOL.md` section 5.0
    makes assembling the panel a blocking Day-1 task, and until this existed
    the real panel lived only in a test fixture, where nothing the campaign
    runs could read it.

    Every control is validated on the way in: :func:`validate_panel` refuses a
    crystal-seeded control and a repeated name, and :class:`Control` itself
    refuses a negative with no registered failure gate.
    """
    document = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(document, dict):
        msg = f"{path} does not contain a control catalogue"
        raise PanelError(msg)

    controls: list[Control] = []
    for section in (*POSITIVE_SECTIONS, "negatives"):
        entries = document.get(section) or []
        if not isinstance(entries, list):
            msg = f"{path}: section {section!r} must be a list, got {type(entries).__name__}"
            raise PanelError(msg)
        controls.extend(_control_from(entry, section) for entry in entries)

    validate_panel(controls)
    return tuple(controls)


def scramble(sequence: str, seed: int) -> str:
    """Shuffle a sequence deterministically, preserving composition.

    Seeded because `build_rules.pdf` section 4.1 requires every random source
    seeded and the seed recorded: a negative control that differs between runs
    is not a control.
    """
    letters = list(sequence)
    random.Random(seed).shuffle(letters)  # noqa: S311 -- reproducibility, not secrecy
    return "".join(letters)


def reverse(sequence: str) -> str:
    """Reverse a sequence, preserving composition and changing the fold."""
    return sequence[::-1]


def negative_from(
    positive: Control,
    kind: str,
    seed: int,
    expected_gate: Gate,
) -> Control:
    """Derive a negative control from a positive one.

    `SETUP.md` section 3.3 builds the negative panel from scrambled and
    reversed positives, and `PREREGISTRATION.md` section 4b requires each to
    carry the gate it is registered to fail at.
    """
    if positive.binder_chains:
        msg = (
            f"cannot derive a negative from {positive.name!r}: it has "
            f"{len(positive.binder_chains)} chains. Scrambling or reversing one chain of "
            "a pair leaves a control whose registered failure gate is not the one it "
            "would fail at"
        )
        raise PanelError(msg)
    if positive.binder_sequence is None:
        msg = f"cannot derive a negative from {positive.name!r}: no binder sequence"
        raise PanelError(msg)
    if kind == "scrambled":
        derived = scramble(positive.binder_sequence, seed)
    elif kind == "reversed":
        derived = reverse(positive.binder_sequence)
    else:
        msg = f"unknown negative kind {kind!r}; expected 'scrambled' or 'reversed'"
        raise PanelError(msg)
    if derived == positive.binder_sequence:
        # A shuffle can return the identity and a palindrome reverses to
        # itself. The complement of the rule above: a negative control
        # identical to its positive is not a control, and it would be
        # registered to fail a gate it should pass.
        msg = (
            f"the {kind} negative derived from {positive.name!r} is identical to it; "
            "pick another seed or another kind"
        )
        raise PanelError(msg)

    return dataclasses.replace(
        positive,
        name=f"{positive.name}_{kind}",
        role=ControlRole.NEGATIVE,
        binder_sequence=derived,
        source=f"derived from {positive.name} ({kind}, seed={seed})",
        expected_gate=expected_gate,
    )
