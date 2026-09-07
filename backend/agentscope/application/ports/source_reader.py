"""Port de lecture des fichiers source."""

from __future__ import annotations

from collections.abc import Iterator
from io import BufferedIOBase
from typing import Protocol

from agentscope.domain import RawRecord


class SourceReader(Protocol):
    """Lit un fichier source en flux d'enregistrements bruts."""

    def supports(self, file_format: str) -> bool:
        """Indique si le lecteur prend en charge le format demandé."""

    def read(self, source: BufferedIOBase) -> Iterator[RawRecord]:
        """Produit les enregistrements sans charger tout le fichier en mémoire."""