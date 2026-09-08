"""Implémentation de ``MappingWorkbenchService`` (issue I4.3).

Câble ``AnalyzeUnknownFile`` (I3.7) et ``PreviewMapping`` (I3.9) aux routes
``POST /analyze`` et ``POST /mappings/{id}/preview``. Choisit le lecteur d'après
le nom du fichier ; ne persiste rien.
"""

from __future__ import annotations

from collections.abc import Sequence
from io import BytesIO

from agentscope.application.mapping.file_format import detect_format
from agentscope.application.mapping.validator import parse_and_validate
from agentscope.application.ports.llm_provider import LLMProvider
from agentscope.application.ports.profiler import FieldProfiler
from agentscope.application.ports.source_reader import SourceReader
from agentscope.application.use_cases.analyze_unknown_file import (
    AnalysisResult,
    AnalyzeUnknownFile,
)
from agentscope.application.use_cases.preview_mapping import (
    PreviewFailedError,
    PreviewMapping,
    PreviewReport,
)
from agentscope.domain import RawRecord


class MappingWorkbenchAdapter:
    def __init__(
        self,
        readers: Sequence[SourceReader],
        profiler: FieldProfiler,
        llm_provider: LLMProvider,
        sample_size: int = 20,
    ) -> None:
        self._readers = tuple(readers)
        self._analyze = AnalyzeUnknownFile(
            profiler=profiler, llm_provider=llm_provider, sample_size=sample_size
        )
        self._preview = PreviewMapping(readers=self._readers)

    def analyze(self, filename: str, content: bytes) -> AnalysisResult:
        fmt = detect_format(filename)
        reader = self._reader_for(fmt.value)
        records: list[RawRecord] = list(reader.read(BytesIO(content)))
        return self._analyze.execute(records)

    def preview(
        self,
        filename: str,
        content: bytes,
        definition: dict,
        sample_size: int = 50,
    ) -> PreviewReport:
        fmt = detect_format(filename)
        mapping = parse_and_validate(definition)  # InvalidMappingError -> 400
        return self._preview.execute(
            content=content,
            file_format=fmt,
            mapping=mapping,
            sample_size=sample_size,
        )

    def _reader_for(self, fmt_value: str) -> SourceReader:
        for reader in self._readers:
            if reader.supports(fmt_value):
                return reader
        raise PreviewFailedError(f"aucun lecteur pour le format `{fmt_value}`")
