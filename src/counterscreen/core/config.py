"""Campaign configuration: frozen, validated, and intolerant of typos.

`build_rules.pdf` section 2.5 is the rule this file implements. Every tunable
number lives in one validated place, defaults carry the section that justifies
them, a file may override any field, and **an unknown key is an error** so a
typo cannot silently leave a default in force.

That last rule does a second job here that is worth stating, because it was
not the reason it was written. The confidence operating point of G2 has no
field in this file at all: `CLAUDE.md` section 8 and `PREREGISTRATION.md`
section 3 register it as a derivation rule computed on the Stage -1 control
panel, so it is a *result*, not a setting. Adding ``g2_confidence: 0.61`` to a
config file therefore fails as an unknown key -- and 0.61 is precisely the
imported literature threshold that `CLAUDE.md` section 12.3b lists as the
canonical v0.2 error, an AF3 ipSAE_min cutoff reported as average precision
that does not transfer across models or metrics [R2]. The rule that protects
against typos also makes re-importing that number structurally impossible.

The same applies to G3 and G5: what is configurable is the *percentile* their
registered rules take, never the value those rules produce.
"""

import dataclasses
from pathlib import Path

import yaml

#: CLAUDE.md section 3.6: Track 3 submits exactly this many designs.
SUBMITTED_DESIGNS = 20

_PERCENT_MAX = 100.0
_TM_SCORE_MAX = 1.0


class ConfigError(ValueError):
    """Raised when a configuration file is unusable.

    A distinct type because a bad config is an operator error with a fix, not a
    bug, and the pipeline should say so plainly rather than raise from deep
    inside a stage.
    """


@dataclasses.dataclass(frozen=True, slots=True)
class GateConfig:
    """Parameters of the hard gates in `CLAUDE.md` section 8.

    G2 is deliberately absent; see the module docstring.
    """

    # CLAUDE.md section 8, G0: consecutive Ca distance is 3.8 A nominal and
    # anything beyond this is a chain break.
    g0_chain_break_angstrom: float = 4.5
    # CLAUDE.md section 8, G0: Ramachandran outliers < 1%.
    g0_max_ramachandran_outlier_fraction: float = 0.01
    # PREREGISTRATION.md section 3 registers G0 as "any clash", which is the
    # rule; these fix what counts as one, and are implementation detail made
    # explicit rather than buried in geometry/.
    g0_clash_distance_angstrom: float = 2.0
    # CLAUDE.md section 8, G0: "bond lengths and angles within standard
    # tolerance", against ideal peptide geometry.
    g0_bond_length_tolerance_angstrom: float = 0.1
    g0_bond_angle_tolerance_degrees: float = 10.0
    # A peptide bond is cis when omega is near zero; trans is near 180.
    g0_cis_peptide_tolerance_degrees: float = 30.0
    # S-S is about 2.05 A; this is the distance below which two cysteine SG
    # atoms are treated as bonded. Used for the CLAUDE.md section 3.1 target
    # disulfide assertion, not as a design filter.
    g0_disulfide_max_angstrom: float = 2.5
    # CLAUDE.md section 8, G1: 2.0 A, Ca only, after Kabsch superposition.
    g1_max_scrmsd_angstrom: float = 2.0
    # CLAUDE.md section 8, G1: pLDDT >= 80 on the refolded prediction.
    g1_min_plddt: float = 80.0
    # CLAUDE.md section 9, stage 2: best of 8 ProteinMPNN sequences.
    g1_mpnn_sequences: int = 8
    # PREREGISTRATION.md section 3, G3: the 10th percentile of the contact
    # fraction achieved by the positive control panel.
    g3_control_percentile: float = 10.0
    # CLAUDE.md section 7.1 and G4: margins must beat 2 x pooled seed SD.
    g4_sd_multiple: float = 2.0
    # PREREGISTRATION.md section 3, G5 (amendment A1): at or below the 90th
    # percentile of the panel's largest apolar patch.
    g5_control_percentile: float = 90.0
    # CLAUDE.md section 8, G6.
    g6_max_buried_unsatisfied_charges: int = 0
    # CLAUDE.md section 3.6 and G8: submission length bounds.
    g8_min_length_aa: int = 10
    g8_max_length_aa: int = 250
    # PREREGISTRATION.md section 3, G9: max TM-score against the PDB.
    g9_max_tm_score: float = 0.8


@dataclasses.dataclass(frozen=True, slots=True)
class SamplingConfig:
    """How much is generated and with how many seeds."""

    # CLAUDE.md section 9, stage 1.
    backbone_min_length_aa: int = 55
    backbone_max_length_aa: int = 75
    # CLAUDE.md section 9, stage 2.
    mpnn_temperature: float = 0.1
    # CLAUDE.md section 9, stage 4a / 4b.
    screening_seeds: int = 2
    finalist_seeds: int = 5
    # PREREGISTRATION.md section 5 (amendment A6), CLAUDE.md section 10,
    # DESIGN.md section 5: the noise floor and the CI tolerance band come from
    # the spread over this many identical runs.
    noise_floor_repeats: int = 5


@dataclasses.dataclass(frozen=True, slots=True)
class SelectionConfig:
    """Clustering and the arm allocation of `CLAUDE.md` section 11."""

    # PREREGISTRATION.md section 4 step 2 (amendment A2): single-linkage at the
    # conventional same-fold boundary.
    cluster_tm_score: float = 0.5
    m1: int = 9
    m2: int = 5
    m3: int = 4
    affinity_control: int = 1
    reserve: int = 1
    # CLAUDE.md section 11: placed here so it is still tested if only part of
    # the list is selected.
    affinity_control_rank: int = 10

    @property
    def total(self) -> int:
        """Total designs allocated across all arms."""
        return self.m1 + self.m2 + self.m3 + self.affinity_control + self.reserve


@dataclasses.dataclass(frozen=True, slots=True)
class EvaluationConfig:
    """Floors registered in `PREREGISTRATION.md` before any data was seen."""

    # PREREGISTRATION.md section 6b: below this the go/no-go is not meaningful.
    min_positive_controls: int = 5
    # PREREGISTRATION.md section 5b: the evaluation-study stop rule.
    min_labelled_pairs: int = 40
    min_targets: int = 4
    min_pairs_per_target: int = 5
    # PREREGISTRATION.md section 7b (amendment A4): per adversarial class.
    adversarial_per_class: int = 10


@dataclasses.dataclass(frozen=True, slots=True)
class TruncationConfig:
    """Screening-construct boundaries.

    No defaults, deliberately. `DESIGN.md` section 2 requires the truncation
    boundaries to be recorded explicitly, and a default here would let a
    campaign run on boundaries nobody chose.
    """

    first_residue: int
    last_residue: int


@dataclasses.dataclass(frozen=True, slots=True)
class CampaignConfig:
    """Everything a campaign run needs that is not a result."""

    campaign: str
    truncation: TruncationConfig
    gates: GateConfig = dataclasses.field(default_factory=GateConfig)
    sampling: SamplingConfig = dataclasses.field(default_factory=SamplingConfig)
    selection: SelectionConfig = dataclasses.field(default_factory=SelectionConfig)
    evaluation: EvaluationConfig = dataclasses.field(default_factory=EvaluationConfig)

    def __post_init__(self) -> None:
        """Reject a configuration that is internally inconsistent."""
        if not self.campaign.strip():
            msg = "campaign name is empty"
            raise ConfigError(msg)
        if self.truncation.first_residue >= self.truncation.last_residue:
            msg = (
                f"truncation first_residue ({self.truncation.first_residue}) must be "
                f"below last_residue ({self.truncation.last_residue})"
            )
            raise ConfigError(msg)
        if self.selection.total != SUBMITTED_DESIGNS:
            msg = (
                f"arm allocation sums to {self.selection.total}, but CLAUDE.md "
                f"section 11 allocates exactly {SUBMITTED_DESIGNS} designs"
            )
            raise ConfigError(msg)
        if self.gates.g8_min_length_aa >= self.gates.g8_max_length_aa:
            msg = "g8_min_length_aa must be below g8_max_length_aa"
            raise ConfigError(msg)
        for name, value in (
            ("g3_control_percentile", self.gates.g3_control_percentile),
            ("g5_control_percentile", self.gates.g5_control_percentile),
        ):
            if not 0.0 <= value <= _PERCENT_MAX:
                msg = f"{name} must lie in [0, 100], got {value}"
                raise ConfigError(msg)
        for name, value in (
            ("g9_max_tm_score", self.gates.g9_max_tm_score),
            ("cluster_tm_score", self.selection.cluster_tm_score),
        ):
            if not 0.0 <= value <= _TM_SCORE_MAX:
                msg = f"{name} must lie in [0, 1], got {value}"
                raise ConfigError(msg)
        if self.sampling.noise_floor_repeats < 2:  # noqa: PLR2004
            msg = "noise_floor_repeats must be at least 2 to measure a spread"
            raise ConfigError(msg)


def _section[T](cls: type[T], raw: object, name: str) -> T:
    """Build one configuration section, refusing any key the section lacks."""
    if raw is None:
        raw = {}
    if not isinstance(raw, dict):
        msg = f"section '{name}' must be a mapping, got {type(raw).__name__}"
        raise ConfigError(msg)
    allowed = {field.name for field in dataclasses.fields(cls)}  # type: ignore[arg-type]
    unknown = sorted(str(key) for key in raw if str(key) not in allowed)
    if unknown:
        msg = f"unknown key(s) in section '{name}': {unknown}. Valid keys are: {sorted(allowed)}"
        raise ConfigError(msg)
    try:
        return cls(**{str(key): value for key, value in raw.items()})
    except TypeError as exc:
        msg = f"section '{name}': {exc}"
        raise ConfigError(msg) from exc


def load_config(path: Path) -> CampaignConfig:
    """Read and validate a campaign ``config.yaml``."""
    with path.open("rb") as handle:
        document = yaml.safe_load(handle)
    if document is None:
        msg = f"{path} is empty"
        raise ConfigError(msg)
    if not isinstance(document, dict):
        msg = f"{path} must contain a mapping, got {type(document).__name__}"
        raise ConfigError(msg)

    top_level = {"campaign", "truncation", "gates", "sampling", "selection", "evaluation"}
    unknown = sorted(str(key) for key in document if str(key) not in top_level)
    if unknown:
        msg = f"unknown top-level key(s): {unknown}. Valid keys are: {sorted(top_level)}"
        raise ConfigError(msg)

    campaign = document.get("campaign")
    if not isinstance(campaign, str):
        msg = "'campaign' must be a string naming the campaign directory"
        raise ConfigError(msg)
    if "truncation" not in document:
        msg = (
            "'truncation' is required: DESIGN.md section 2 requires the screening "
            "construct boundaries to be recorded explicitly"
        )
        raise ConfigError(msg)

    return CampaignConfig(
        campaign=campaign,
        truncation=_section(TruncationConfig, document["truncation"], "truncation"),
        gates=_section(GateConfig, document.get("gates"), "gates"),
        sampling=_section(SamplingConfig, document.get("sampling"), "sampling"),
        selection=_section(SelectionConfig, document.get("selection"), "selection"),
        evaluation=_section(EvaluationConfig, document.get("evaluation"), "evaluation"),
    )
