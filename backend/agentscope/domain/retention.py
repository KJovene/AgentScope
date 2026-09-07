"""Politique de rétention des enregistrements bruts (issue I1.7).

Règle métier pure : sous forte volumétrie, on peut ne conserver que l'index et le
hash d'un enregistrement source (assez pour tracer et détecter les doublons), en
gardant le payload complet uniquement pour les enregistrements rejetés.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import StrEnum

from agentscope.domain.entities import RawRecord


class RetentionMode(StrEnum):
    FULL = "full"
    """Le payload d'origine est conservé pour chaque enregistrement (défaut)."""

    MINIMAL = "minimal"
    """Seuls index + sha256 sont conservés ; payload gardé uniquement pour les rejets."""


@dataclass(frozen=True, slots=True)
class RetentionPolicy:
    mode: RetentionMode = RetentionMode.FULL

    def keep_payload(self, *, rejected: bool) -> bool:
        return self.mode is RetentionMode.FULL or rejected

    def apply(self, record: RawRecord, *, rejected: bool = False) -> RawRecord:
        """Renvoie l'enregistrement, payload vidé si la politique l'exige.

        La ligne ``raw_record`` reste écrite (index + sha256) : la clé étrangère
        ``raw_record_id`` des entités normalisées est donc toujours renseignée,
        seul le payload devient ``NULL``.
        """
        if self.keep_payload(rejected=rejected):
            return record
        return replace(record, payload={})
