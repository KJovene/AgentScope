"""Masquage des valeurs sensibles avant exposition dans les profils."""

from __future__ import annotations

import re
from collections.abc import Mapping

_REDACTED = "[REDACTED]"


class DefaultSensitiveFilter:
    """Masque les emails, secrets courants et chemins de dossiers personnels."""

    _PATTERNS = (
        re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
        re.compile(r"(?i)\b(?:bearer\s+)?(?:sk-[A-Za-z0-9_-]{12,}|gh[pousr]_[A-Za-z0-9_]{12,})\b"),
        re.compile(r"(?i)\b(?:api[_ -]?key|access[_ -]?token|secret|password)\s*[:=]\s*[^\s,;]+"),
        re.compile(r"(?:[A-Za-z]:\\Users\\[^\\\s]+|/home/[^/\s]+|/Users/[^/\s]+)"),
    )

    def scrub(self, value: object) -> object:
        """Retourne une copie récursive dont les chaînes sensibles sont masquées."""
        if isinstance(value, str):
            return self._scrub_string(value)
        if isinstance(value, Mapping):
            return {key: self.scrub(item) for key, item in value.items()}
        if isinstance(value, list):
            return [self.scrub(item) for item in value]
        if isinstance(value, tuple):
            return tuple(self.scrub(item) for item in value)
        if isinstance(value, set):
            return {self.scrub(item) for item in value}
        return value

    @classmethod
    def _scrub_string(cls, value: str) -> str:
        scrubbed = value
        for pattern in cls._PATTERNS:
            scrubbed = pattern.sub(_REDACTED, scrubbed)
        return scrubbed
