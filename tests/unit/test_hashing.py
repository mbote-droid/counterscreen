"""Identity comes from content, and is stable across processes."""

import hashlib
import subprocess
import sys
from pathlib import Path

import pytest

from counterscreen.core.hashing import (
    SEQUENCE_ID_CHARS,
    bytes_sha256,
    file_sha256,
    normalise_sequence,
    sequence_id,
    text_sha256,
)

# The canonical SHA-256 test vector for "abc".
ABC_SHA256 = "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"

PEPTIDE = "VVVGADGVGK"


def test_known_digest_vector() -> None:
    assert bytes_sha256(b"abc") == ABC_SHA256
    assert text_sha256("abc") == ABC_SHA256


def test_sequence_id_is_deterministic_within_a_process() -> None:
    assert sequence_id(PEPTIDE) == sequence_id(PEPTIDE)


def test_sequence_id_is_stable_across_processes() -> None:
    """Not merely deterministic: Python's own hash() is salted per process."""
    code = f"from counterscreen.core.hashing import sequence_id;print(sequence_id({PEPTIDE!r}))"
    out = subprocess.run(  # noqa: S603
        [sys.executable, "-c", code], capture_output=True, text=True, check=True
    )
    assert out.stdout.strip() == sequence_id(PEPTIDE)


def test_wrapping_and_case_do_not_change_the_id() -> None:
    wrapped = "vvvga\n  dgvgk\t"
    assert sequence_id(wrapped) == sequence_id(PEPTIDE)


def test_the_single_residue_difference_changes_the_id() -> None:
    """T+ and D1 differ at position 6 alone and must not collide."""
    assert sequence_id("VVVGADGVGK") != sequence_id("VVVGAGGVGK")


def test_sequence_id_length() -> None:
    assert len(sequence_id(PEPTIDE)) == SEQUENCE_ID_CHARS


def test_normalise_rejects_empty() -> None:
    with pytest.raises(ValueError, match="empty"):
        normalise_sequence("   \n ")


def test_normalise_rejects_non_letters() -> None:
    with pytest.raises(ValueError, match="non-letter"):
        normalise_sequence("VVVGA*GVGK")


def test_file_sha256_matches_hashlib(tmp_path: Path) -> None:
    payload = b"ATOM      1  N   MET A   1\n" * 5000
    target = tmp_path / "structure.pdb"
    target.write_bytes(payload)
    assert file_sha256(target) == hashlib.sha256(payload).hexdigest()


def test_file_sha256_handles_a_file_larger_than_one_chunk(tmp_path: Path) -> None:
    payload = b"x" * ((1 << 20) + 17)
    target = tmp_path / "weights.bin"
    target.write_bytes(payload)
    assert file_sha256(target) == hashlib.sha256(payload).hexdigest()
