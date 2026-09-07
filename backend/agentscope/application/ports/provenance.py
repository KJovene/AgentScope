"""Port de lecture de la provenance (issue I1.7).

Depuis l'identité naturelle d'une entité normalisée, remonte à son enregistrement
source. Renvoie ``None`` quand le lien est rompu (ligne ``raw_record`` purgée par
une rétention agressive). Sous rétention ``minimal``, la ligne existe encore mais
son ``RawRecord.payload`` revient vide.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from agentscope.domain import RawRecord


@runtime_checkable
class ProvenanceRepository(Protocol):
    def raw_record_for_session(
        self, source_name: str, external_id: str
    ) -> RawRecord | None: ...

    def raw_record_for_model_call(
        self, source_name: str, session_external_id: str, sequence: int
    ) -> RawRecord | None: ...

    def raw_record_for_tool_call(
        self, source_name: str, session_external_id: str, sequence: int
    ) -> RawRecord | None: ...
