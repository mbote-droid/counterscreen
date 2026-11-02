"""Content-addressed identifiers.

`DESIGN.md` section 4.3 requires stable identifiers and content-addressed
inputs: a design id derived from the sequence itself, and a checksum for every
structure file and model-weight file. Identity therefore comes from content,
never from the order something happened to be generated in or the filename it
happened to be given. Two runs that produce the same sequence produce the same
id, which is what lets an idempotent stage skip work it has already done
(`DESIGN.md` section 6).

Python's built-in ``hash()`` is salted per process and must never be used for
anything that is recorded or compared across runs. Everything here is SHA-256.
"""

import hashlib
from pathlib import Path

#: Hex characters kept from a sequence digest. 16 hex characters is 64 bits,
#: which is ample for the thousands of designs a campaign produces and short
#: enough to read in a filename or a results table.
SEQUENCE_ID_CHARS = 16

_READ_CHUNK_BYTES = 1 << 20


def bytes_sha256(data: bytes) -> str:
    """Return the full hex SHA-256 of a byte string."""
    return hashlib.sha256(data).hexdigest()


def text_sha256(text: str) -> str:
    """Return the full hex SHA-256 of text, encoded as UTF-8."""
    return bytes_sha256(text.encode("utf-8"))


def file_sha256(path: Path) -> str:
    """Return the full hex SHA-256 of a file, read in chunks.

    Chunked because model-weight files run to gigabytes and must not be loaded
    into memory to be checksummed.
    """
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(_READ_CHUNK_BYTES):
            digest.update(chunk)
    return digest.hexdigest()


def normalise_sequence(sequence: str) -> str:
    """Strip all whitespace from an amino-acid sequence and upper-case it.

    FASTA in the wild arrives wrapped at 60 or 80 columns, sometimes lower-case,
    sometimes with trailing spaces. Normalising before hashing means the same
    protein read from two sources gets one id rather than two.
    """
    stripped = "".join(sequence.split()).upper()
    if not stripped:
        msg = "sequence is empty"
        raise ValueError(msg)
    if not stripped.isalpha():
        offenders = sorted({c for c in stripped if not c.isalpha()})
        msg = f"sequence contains non-letter characters: {offenders}"
        raise ValueError(msg)
    return stripped


def sequence_id(sequence: str) -> str:
    """Return the stable design id for an amino-acid sequence.

    The sequence is normalised first, so whitespace and case cannot produce two
    ids for one protein.
    """
    return text_sha256(normalise_sequence(sequence))[:SEQUENCE_ID_CHARS]
