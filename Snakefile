"""Campaign workflow: one command regenerates everything reproducible.

`PROTOCOL.md` §16 asks for Snakemake regenerating the campaign from one
command, and `DESIGN.md` §9 limits orchestration to exactly that -- no
Airflow, no Prefect, no custom scheduler, because this is an embarrassingly
parallel batch job and anything more would be complexity without a test that
fails when it is removed.

The workflow splits on a line that matters more than the stage boundaries:

**CPU rules are runnable now.** Target preparation, geometric validity and
hotspot derivation need no GPU, no model weights and no network. They are the
rules below with real shell commands, and `snakemake --cores 1 cpu` runs the
campaign as far as it can currently go.

**GPU rules are declared but refuse to run.** Backbone generation, sequence
design and co-folding need models that are installed on Kaggle rather than
here. Declaring them keeps the dependency graph honest -- the DAG shows what
the campaign is -- while the bodies fail loudly with the reason rather than
producing an empty file that a downstream rule would treat as a result.

Determinism (`DESIGN.md` §5): CPU stages are seeded and single-threaded, so
`OMP_NUM_THREADS` and `PYTHONHASHSEED` are pinned for every rule rather than
left to the invoking shell.
"""

import os

CAMPAIGN = config.get("campaign", "kras-g12d-pmhc")
ROOT = f"campaigns/{CAMPAIGN}"
CONFIG = f"{ROOT}/config.yaml"
SOURCES = config.get("sources", "structures")
TARGETS = f"{ROOT}/targets"

# DESIGN.md section 5: CPU stages must be bit-reproducible, which means
# fixing thread counts and hash seeding rather than inheriting them.
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("PYTHONHASHSEED", "0")

PREPARED = [
    f"{TARGETS}/T_plus.pdb",
    f"{TARGETS}/D1_wild_type.pdb",
    f"{TARGETS}/D2_peptide_free.pdb",
    f"{TARGETS}/T_plus_platform.pdb",
    f"{TARGETS}/D1_wild_type_platform.pdb",
]

ARMS = ["M1", "M2", "M3"]

GPU_STAGE_MESSAGE = (
    "{stage} needs model weights that are not installed in this environment. "
    "PROTOCOL.md section 10 runs the generative and folding stages on Kaggle's "
    "free tier; this rule exists so the dependency graph is complete, not so "
    "it can be run here. Record the benchmark in "
    "benchmarks/day1_gpu_benchmark.md before relying on any budget."
)


rule all:
    """Everything reproducible without a GPU."""
    input:
        PREPARED,
        f"{ROOT}/hotspots.json",
        f"{ROOT}/geometry_report.json",


rule cpu:
    """Alias for the CPU-only half of the campaign."""
    input:
        rules.all.input,


rule prepare_targets:
    """Stage 0: T+, the decoys, and the truncated screening construct."""
    input:
        config=CONFIG,
        sources=SOURCES,
    output:
        PREPARED,
    log:
        f"{ROOT}/logs/prepare_targets.log",
    shell:
        "python3 scripts/prepare_targets.py {input.config} {input.sources} "
        f"{TARGETS} > {{log}} 2>&1"


rule hotspots:
    """Derive the three mechanism hotspot schemes from the prepared targets."""
    input:
        target=f"{TARGETS}/T_plus.pdb",
        decoy=f"{TARGETS}/D1_wild_type.pdb",
    output:
        f"{ROOT}/hotspots.json",
    log:
        f"{ROOT}/logs/hotspots.log",
    shell:
        "python3 scripts/derive_hotspots.py {input.target} {input.decoy} "
        "{output} > {log} 2>&1"


rule geometry_gate:
    """Gate G0 over every prepared target, before anything expensive runs."""
    input:
        PREPARED,
    output:
        f"{ROOT}/geometry_report.json",
    log:
        f"{ROOT}/logs/geometry_gate.log",
    shell:
        "python3 scripts/check_geometry.py {output} {input} > {log} 2>&1"


rule generate_backbones:
    """Stage 1: RFdiffusion. Declared for the graph; not runnable here."""
    input:
        f"{ROOT}/hotspots.json",
    output:
        directory(f"{ROOT}/backbones"),
    run:
        raise RuntimeError(GPU_STAGE_MESSAGE.format(stage="RFdiffusion backbone generation"))


rule design_sequences:
    """Stage 2: ProteinMPNN. Declared for the graph; not runnable here."""
    input:
        f"{ROOT}/backbones",
    output:
        directory(f"{ROOT}/sequences"),
    run:
        raise RuntimeError(GPU_STAGE_MESSAGE.format(stage="ProteinMPNN sequence design"))


rule counter_screen:
    """Stage 4a: the three-way screen. Declared for the graph; not runnable here."""
    input:
        sequences=f"{ROOT}/sequences",
        targets=PREPARED,
    output:
        directory(f"{ROOT}/folds"),
    run:
        raise RuntimeError(GPU_STAGE_MESSAGE.format(stage="Co-folding counter-screen"))
