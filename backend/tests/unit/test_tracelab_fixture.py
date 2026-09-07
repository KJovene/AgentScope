"""La fixture TraceLab commitée est lisible et conforme à son bilan (I0.10).

Provenance, licence et méthode de sélection : `data/README.md` et le `NOTICE.md`
du dossier de la fixture. Régénération : `make fixtures`.
"""

from __future__ import annotations

import collections
import json
from pathlib import Path

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "tracelab" / "sample.jsonl"
META = FIXTURE.with_suffix(FIXTURE.suffix + ".meta.json")


def _rows() -> list[dict]:
    with FIXTURE.open(encoding="utf-8") as stream:
        return [json.loads(line) for line in stream if line.strip()]


def test_la_fixture_est_du_jsonl_lisible() -> None:
    rows = _rows()

    assert rows, "fixture vide — lancer `make fixtures`"
    for row in rows:
        assert {"provider", "session_id", "round_index", "model"} <= row.keys()


def test_les_deux_providers_sont_representes() -> None:
    """Un mapping testé sur un seul provider ne prouve pas grand-chose."""
    providers = {row["provider"] for row in _rows()}

    assert providers == {"claude", "codex"}


def test_les_sessions_retenues_sont_entieres() -> None:
    """Une session tronquée fausserait durées et comptages : les rounds sont contigus."""
    by_session: dict[str, list[int]] = collections.defaultdict(list)
    for row in _rows():
        by_session[row["session_id"]].append(row["round_index"])

    for session_id, indexes in by_session.items():
        assert sorted(indexes) == list(range(len(indexes))), f"session {session_id} trouée"


def test_le_bilan_decrit_bien_la_fixture() -> None:
    """Garde contre une fixture régénérée sans son bilan (ou l'inverse)."""
    rows = _rows()
    meta = json.loads(META.read_text(encoding="utf-8"))

    counts = collections.Counter(row["provider"] for row in rows)
    sessions = collections.Counter()
    for session_id in {(r["provider"], r["session_id"]) for r in rows}:
        sessions[session_id[0]] += 1

    assert meta["extract"]["rounds"] == len(rows)
    assert meta["extract"]["rounds_by_provider"] == dict(sorted(counts.items()))
    assert meta["extract"]["sessions"] == dict(sorted(sessions.items()))
    assert meta["source"]["release"] == "v0.0.1"
