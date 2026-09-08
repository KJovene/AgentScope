"""Détection du format d'un fichier source à partir de son nom.

Logique pure (nom → ``FileFormat``), partagée par le service d'import et le
plan de travail des mappings. Ne lit aucun contenu.
"""

from __future__ import annotations

from pathlib import PurePosixPath

from agentscope.domain import DomainError, FileFormat

_SUFFIX_TO_FORMAT: dict[str, FileFormat] = {
    ".jsonl": FileFormat.JSONL,
    ".ndjson": FileFormat.JSONL,
    ".csv": FileFormat.CSV,
    ".parquet": FileFormat.PARQUET,
}


class UnsupportedFileFormatError(DomainError):
    """Extension de fichier non reconnue pour l'ingestion."""


def detect_format(filename: str) -> FileFormat:
    suffix = PurePosixPath(filename).suffix.lower()
    fmt = _SUFFIX_TO_FORMAT.get(suffix)
    if fmt is None:
        accepted = ", ".join(sorted(_SUFFIX_TO_FORMAT))
        raise UnsupportedFileFormatError(
            f"Format non reconnu pour « {filename} » (extensions acceptées : {accepted})."
        )
    return fmt
