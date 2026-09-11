"""Prétraitement d'un export brut du format de session "pi" (pi-coding-agent).

Le format natif journalise une session comme une chaîne d'événements reliés par
``parentId`` : seul l'événement racine (``type: "session"``) porte l'identifiant
réel de la session — aucun autre événement ne le référence. Le ``Normalizer``
construit une session indépendamment pour chaque ligne (aucune mémoire
inter-lignes, cf. ``application/mapping/normalizer.py``), donc un export brut
n'est jamais directement mappable : il faut d'abord injecter un ``session_id``
explicite sur chaque ligne, comme le fait déjà nativement TraceLab/SWE-chat.

Utilisé automatiquement par ``SqlImportService`` quand le mapping choisi est
``pi-session-jsonl`` (cf. ``docs/data/mappings/pi-session.md``). Miroir de
``scripts/convert_pi_session_jsonl.py`` (CLI autonome pour un usage hors ligne) —
les deux implémentent le même algorithme, volontairement dupliqué : les scripts
de ce dépôt tournent sans dépendre du paquet applicatif.
"""

from __future__ import annotations

import json
from typing import Any

#: Identifiant du mapping qui déclenche ce prétraitement.
PI_SESSION_MAPPING_ID = "pi-session-jsonl"


def _load_records(content: bytes) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line in content.decode("utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict):
            records.append(obj)
    return records


def _resolve_session_ids(records: list[dict[str, Any]]) -> dict[int, str | None]:
    """Associe l'index de chaque enregistrement à l'id de session résolu en
    remontant `parentId` jusqu'à un événement `type == "session"`."""
    by_id = {rec["id"]: rec for rec in records if isinstance(rec.get("id"), str)}
    fallback_session_id = next(
        (
            rec["id"]
            for rec in records
            if rec.get("type") == "session" and isinstance(rec.get("id"), str)
        ),
        None,
    )

    resolved: dict[int, str | None] = {}
    for index, rec in enumerate(records):
        if rec.get("type") == "session" and isinstance(rec.get("id"), str):
            resolved[index] = rec["id"]
            continue

        seen: set[str] = set()
        current = rec
        session_id: str | None = None
        while True:
            parent_id = current.get("parentId")
            if not isinstance(parent_id, str) or parent_id in seen:
                break
            seen.add(parent_id)
            parent = by_id.get(parent_id)
            if parent is None:
                break
            if parent.get("type") == "session":
                session_id = parent.get("id")
                break
            current = parent
        resolved[index] = session_id or fallback_session_id

    return resolved


def is_pi_session_export(content: bytes) -> bool:
    """Détecte un export "pi" brut : au moins une ligne `type == "session"` sans
    `session_id` déjà présent (un fichier déjà converti n'est pas re-converti)."""
    records = _load_records(content)
    has_session_event = any(rec.get("type") == "session" for rec in records)
    already_flat = any("session_id" in rec for rec in records)
    return has_session_event and not already_flat


def convert_pi_session_bytes(content: bytes) -> bytes:
    """Réécrit un export "pi" brut en JSONL plat, un `session_id` ajouté à
    chaque ligne. Les lignes JSON illisibles (troncature, contenu collé par
    erreur) sont silencieusement ignorées plutôt que de faire échouer l'import."""
    records = _load_records(content)
    session_ids = _resolve_session_ids(records)

    lines: list[str] = []
    for index, rec in enumerate(records):
        session_id = session_ids.get(index)
        if session_id is None:
            continue
        enriched = {**rec, "session_id": session_id}
        lines.append(json.dumps(enriched, ensure_ascii=False))

    return ("\n".join(lines) + "\n").encode("utf-8") if lines else b""
