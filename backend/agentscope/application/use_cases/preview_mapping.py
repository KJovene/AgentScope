"""Cas d'utilisation ``PreviewMapping`` (issue I3.9) : dry-run de normalisation.

Applique un mapping à un échantillon d'un fichier, **sans rien persister**
(aucune ``UnitOfWork``) — sert à prévisualiser un mapping avant de le
sauvegarder ou de lancer un import réel (contrat §5.3,
``POST /mappings/{id}/preview``).
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from io import BytesIO

from agentscope.application.mapping.contract import MappingDefinition
from agentscope.application.mapping.normalizer import NormalizationResult, Normalizer
from agentscope.application.ports import SourceReader
from agentscope.domain import DomainError, FileFormat


class PreviewFailedError(DomainError):
    """Le dry-run ne peut pas aboutir : aucun lecteur pour le format demandé."""


@dataclass(frozen=True, slots=True)
class PreviewReport:
    """Bilan d'une prévisualisation."""

    sampled_count: int  # nombre d'enregistrements réellement lus (peut être < sample_size)
    result: NormalizationResult


class PreviewMapping:
    """Dry-run de ``Normalizer`` sur un échantillon d'un fichier, sans écriture DB."""

    def __init__(
        self,
        readers: Sequence[SourceReader],
        normalizer: Normalizer | None = None,
    ) -> None:
        self._readers = tuple(readers)
        self._normalizer = normalizer or Normalizer()

    def execute(
        self,
        *,
        content: bytes,
        file_format: FileFormat,
        mapping: MappingDefinition,
        sample_size: int = 50,
    ) -> PreviewReport:
        reader = self._reader_for(file_format)
        records = []
        for record in reader.read(BytesIO(content)):
            records.append(record)
            if len(records) >= sample_size:
                break

        result = self._normalizer.normalize(records, mapping)
        return PreviewReport(sampled_count=len(records), result=result)

    def _reader_for(self, file_format: FileFormat) -> SourceReader:
        for reader in self._readers:
            if reader.supports(file_format.value):
                return reader
        raise PreviewFailedError(f"aucun lecteur pour le format `{file_format.value}`")
