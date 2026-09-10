#!/usr/bin/env python3
"""Récupère un échantillon déterministe du dataset SWE-chat et l'aplatit en JSONL.

Issue I2.12 (WS-platform). ``SALT-NLP/SWE-chat`` est **gated** (accès à accepter sur
la page HF) et volumineux : ``conversations.parquet`` ≈ 1,3 Gio. On ne télécharge donc
pas le dataset entier — les petites tables (``sessions``, ``repositories``) sont lues
en entier, ``conversations`` est lu **row-group par row-group** via des requêtes HTTP
``Range`` et seuls les groupes couvrant les sessions retenues sont matérialisés.

(On n'utilise pas DuckDB ``hf://`` : sa pile HTTP échoue en ``HTTP 0`` sur
huggingface.co dans cet environnement. ``urllib`` + ``pyarrow`` suffisent.)

Pré-requis
----------
* accès accepté : https://huggingface.co/datasets/SALT-NLP/SWE-chat (bouton « Agree »)
* un token HF en lecture : ``export HF_TOKEN=hf_xxx`` (ou ``--token``)
* le venv backend (pyarrow) : ``backend/.venv/bin/python scripts/swe_chat_extract.py``

Méthode de sélection — même principe que TraceLab (``scripts/tracelab_extract.py``) :
session entière, ``sha1(session_id) % modulo == 0``, appliqué séparément par agent.

Sortie
------
Un JSONL **à plat, une ligne = un tour de conversation** (table ``conversations``),
avec les champs de session (``agent``, ``repository``, totaux de tokens) recopiés sur
chaque ligne pour que ``docs/data/mappings/swe-chat.json`` s'y retrouve sans jointure.
Un ``*.meta.json`` accompagne l'extrait (bilan chiffré).

    backend/.venv/bin/python scripts/swe_chat_extract.py --modulo 64 \
        --max-sessions-per-agent 2 --out data/swe_chat/extract-dev.jsonl

⚠️  Le schéma exact des colonnes (``repositories``, ``sessions``) n'a pas pu être
    vérifié hors-ligne : après le premier run, contrôler l'extrait et ajuster
    ``swe-chat.json`` + la fiche avant de considérer I2.12 comme fait.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

REPO_ID = "SALT-NLP/SWE-chat"
BASE = f"https://huggingface.co/datasets/{REPO_ID}/resolve/main"
REPO_ROOT = Path(__file__).resolve().parents[1]


# --------------------------------------------------------------------------- #
# Accès HTTP (stdlib) : téléchargement complet + fichier adossé à des Range    #
# --------------------------------------------------------------------------- #


TIMEOUT = 60
_WINDOW = 16 << 20  # 16 Mio : pyarrow lit par petits bouts, on amortit en gros blocs


def _log(msg: str) -> None:
    print(f"  {msg}", file=sys.stderr, flush=True)


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}", "User-Agent": "agentscope-swe-chat-extract"}


def _raise_http(path: str, exc: urllib.error.HTTPError) -> None:
    if exc.code in (401, 403):
        raise SystemExit(
            f"HTTP {exc.code} sur {path}. Vérifier que :\n"
            "  1. l'accès est accepté sur https://huggingface.co/datasets/SALT-NLP/SWE-chat\n"
            "  2. $HF_TOKEN est un token *Read* valide de ce compte"
        ) from exc
    raise SystemExit(f"HTTP {exc.code} sur {path} : {exc.reason}") from exc


def _download(path: str, token: str) -> bytes:
    _log(f"téléchargement {path} …")
    req = urllib.request.Request(f"{BASE}/{path}", headers=_auth(token))
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            data = resp.read()
    except urllib.error.HTTPError as exc:
        _raise_http(path, exc)
    _log(f"  {path} : {len(data) / 1e6:.1f} Mo")
    return data


class _HttpRangeFile(io.RawIOBase):
    """Fichier binaire distant servi par des requêtes HTTP ``Range``.

    ``pyarrow.parquet.ParquetFile`` lit un Parquet par petits morceaux (footer,
    puis colonne par colonne) : on suit la redirection CDN **une seule fois**, on
    réutilise l'URL signée, et on met en cache une fenêtre de 8 Mio pour ne pas
    refaire un aller-retour à chaque appel de ``readinto``.
    """

    def __init__(self, path: str, token: str) -> None:
        self._path = path
        self._token = token
        self._pos = 0
        self._buf = b""
        self._buf_start = 0
        self._resolved, self._size = self._resolve()

    def _resolve(self) -> tuple[str, int]:
        """1re requête Range : suit la redirection, renvoie (URL finale, taille)."""
        req = urllib.request.Request(
            f"{BASE}/{self._path}",
            headers={**_auth(self._token), "Range": "bytes=0-0"},
        )
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                final = resp.url
                content_range = resp.headers.get("Content-Range", "")
        except urllib.error.HTTPError as exc:
            _raise_http(self._path, exc)
        if "/" not in content_range:
            raise SystemExit(
                f"{self._path} : le serveur ne répond pas aux requêtes Range "
                f"(Content-Range absent) — lecture par morceaux impossible."
            )
        total = int(content_range.rsplit("/", 1)[1])
        _log(f"{self._path} : {total / 1e9:.2f} Go, lecture par Range")
        return final, total

    def _fetch(self, start: int, end: int) -> bytes:
        headers = {**_auth(self._token), "Range": f"bytes={start}-{end}"}
        for attempt in (1, 2):
            try:
                req = urllib.request.Request(self._resolved, headers=headers)
                with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                    return resp.read()
            except urllib.error.HTTPError as exc:
                if exc.code in (403, 410) and attempt == 1:  # URL signée expirée
                    self._resolved, _ = self._resolve()
                    continue
                _raise_http(self._path, exc)
        return b""

    # -- io.RawIOBase --------------------------------------------------------- #
    def seekable(self) -> bool:
        return True

    def readable(self) -> bool:
        return True

    def tell(self) -> int:
        return self._pos

    def seek(self, offset: int, whence: int = io.SEEK_SET) -> int:
        base = {io.SEEK_SET: 0, io.SEEK_CUR: self._pos, io.SEEK_END: self._size}[whence]
        self._pos = max(0, min(self._size, base + offset))
        return self._pos

    def readinto(self, buffer: Any) -> int:
        want = min(len(buffer), self._size - self._pos)
        if want <= 0:
            return 0
        buf_end = self._buf_start + len(self._buf)
        if not (self._buf_start <= self._pos and self._pos + want <= buf_end):
            start = self._pos
            end = min(self._size, start + max(want, _WINDOW)) - 1
            self._buf = self._fetch(start, end)
            self._buf_start = start
        offset = self._pos - self._buf_start
        chunk = self._buf[offset : offset + want]
        buffer[: len(chunk)] = chunk
        self._pos += len(chunk)
        return len(chunk)


# --------------------------------------------------------------------------- #
# Extraction                                                                   #
# --------------------------------------------------------------------------- #


def is_selected(session_id: str, modulo: int) -> bool:
    return int(hashlib.sha1(session_id.encode("utf-8")).hexdigest(), 16) % modulo == 0


def _rows(parquet_bytes: bytes) -> list[dict[str, Any]]:
    import pyarrow.parquet as pq

    return pq.read_table(io.BytesIO(parquet_bytes)).to_pylist()


def _pick_sessions(token: str, modulo: int, cap: int | None) -> list[dict[str, Any]]:
    rows = _rows(_download("sessions.parquet", token))
    kept: list[dict[str, Any]] = []
    per_agent: dict[str, int] = {}
    for row in sorted(rows, key=lambda r: str(r.get("session_id"))):
        sid = str(row.get("session_id"))
        if not is_selected(sid, modulo):
            continue
        agent = str(row.get("agent") or "?")
        if cap is not None and per_agent.get(agent, 0) >= cap:
            continue
        per_agent[agent] = per_agent.get(agent, 0) + 1
        kept.append(row)
    _log(f"{len(rows)} sessions lues → {len(kept)} retenues {dict(sorted(per_agent.items()))}")
    return kept


def _repo_names(token: str) -> dict[Any, str]:
    try:
        rows = _rows(_download("repositories.parquet", token))
    except SystemExit as exc:  # non bloquant : repository restera nul
        print(f"  repositories.parquet indisponible ({exc}) — repository = null", file=sys.stderr)
        return {}
    if not rows:
        return {}
    cols = rows[0].keys()
    id_col = next((c for c in ("repo_id", "id", "repository_id") if c in cols), None)
    name_col = next(
        (c for c in ("full_name", "name", "repo_name", "nwo", "repository") if c in cols), None
    )
    if not id_col or not name_col:
        return {}
    return {r[id_col]: str(r[name_col]) for r in rows}


def _conversation_turns(token: str, session_ids: set[str]) -> list[dict[str, Any]]:
    """Lit ``conversations.parquet`` distant en deux passes : d'abord la seule
    colonne ``session_id`` sur tous les row-groups (léger) pour localiser ceux qui
    contiennent une session retenue, puis la lecture complète de ces seuls groupes.
    """
    import pyarrow.parquet as pq

    handle = _HttpRangeFile("conversations.parquet", token)
    pf = pq.ParquetFile(handle)
    names = pf.schema_arrow.names
    if "session_id" not in names:
        raise SystemExit(
            f"conversations.parquet : pas de colonne `session_id` — colonnes : {names[:25]}"
        )
    sid_col = names.index("session_id")
    total_rg = pf.metadata.num_row_groups
    _log(f"conversations.parquet : {total_rg} row-groups")

    # Passe 1 — colonne session_id seule, + stats min/max quand elles existent.
    lo, hi = min(session_ids), max(session_ids)
    hit: list[int] = []
    for rg in range(total_rg):
        stats = pf.metadata.row_group(rg).column(sid_col).statistics
        if stats is not None and stats.has_min_max and (str(stats.max) < lo or str(stats.min) > hi):
            continue
        ids = pf.read_row_group(rg, columns=["session_id"]).column(0).to_pylist()
        if any(str(x) in session_ids for x in ids):
            hit.append(rg)
        if (rg + 1) % 100 == 0 or rg + 1 == total_rg:
            _log(f"  passe 1 : {rg + 1}/{total_rg} scannés, {len(hit)} groupes à lire")

    # Passe 2 — lecture complète des row-groups pertinents uniquement.
    turns: list[dict[str, Any]] = []
    for n, rg in enumerate(hit, 1):
        table = pf.read_row_group(rg)
        turns.extend(r for r in table.to_pylist() if str(r.get("session_id")) in session_ids)
        _log(f"  passe 2 : {n}/{len(hit)} groupes lus — {len(turns)} tours")
    _log(f"{len(turns)} tours retenus pour {len(session_ids)} sessions")
    return turns


def extract(token: str, out: Path, modulo: int, cap: int | None) -> dict[str, Any]:
    sessions = _pick_sessions(token, modulo, cap)
    if not sessions:
        raise SystemExit("aucune session sélectionnée — élargir --modulo")

    by_id = {str(s["session_id"]): s for s in sessions}
    repo_names = _repo_names(token)
    turns = _conversation_turns(token, set(by_id))
    turns.sort(key=lambda t: (str(t.get("session_id")), t.get("turn_number") or 0))

    # Sélection « session non dégénérée » : on écarte les sessions dont aucun tour
    # n'est un appel modèle (`assistant_response`) ni un appel d'outil (`tool_use`)
    # — fragments tronqués du dump (souvent 100 % `user_prompt`), rien à mesurer.
    active_kinds = {"assistant_response", "tool_use"}
    active_sessions = {
        str(t.get("session_id")) for t in turns if t.get("turn_type") in active_kinds
    }
    dropped = sorted(set(by_id) - active_sessions)
    if dropped:
        _log(f"{len(dropped)} session(s) écartée(s) (aucune activité modèle/outil)")
        by_id = {sid: s for sid, s in by_id.items() if sid in active_sessions}
        sessions = [s for s in sessions if str(s["session_id"]) in active_sessions]
        turns = [t for t in turns if str(t.get("session_id")) in active_sessions]

    out = (out if out.is_absolute() else REPO_ROOT / out).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    _log(f"écriture de {out.name} …")

    agents: dict[str, int] = {}
    tool_lines = 0
    with out.open("w", encoding="utf-8", newline="\n") as sink:
        for turn in turns:
            session = by_id.get(str(turn.get("session_id")), {})
            agent = str(session.get("agent") or "?")
            line = {
                **{k: _json_safe(v) for k, v in turn.items()},
                "agent": agent,
                "repository": repo_names.get(session.get("repo_id")),
                "session_input_tokens": _json_safe(session.get("input_tokens")),
                "session_output_tokens": _json_safe(session.get("output_tokens")),
            }
            sink.write(json.dumps(line, ensure_ascii=False) + "\n")
            agents[agent] = agents.get(agent, 0) + 1
            if turn.get("tool_name"):
                tool_lines += 1

    report = {
        "source": {"repo": REPO_ID, "gated": True, "license": "odc-by"},
        "selection": {
            "rule": "sha1(session_id) % modulo == 0",
            "modulo": modulo,
            "max_sessions_per_agent": cap,
            "requires_model_or_tool_activity": True,
        },
        "extract": {
            "path": out.relative_to(REPO_ROOT).as_posix()
            if out.is_relative_to(REPO_ROOT)
            else out.as_posix(),
            "sessions": len(sessions),
            "sessions_dropped_degenerate": len(dropped),
            "turns": sum(agents.values()),
            "turns_by_agent": dict(sorted(agents.items())),
            "turns_with_tool": tool_lines,
            "bytes": out.stat().st_size,
        },
    }
    out.with_suffix(out.suffix + ".meta.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return report


def _json_safe(value: Any) -> Any:
    """pandas/pyarrow renvoient des types numpy/Timestamp : ramener au JSON de base."""
    if value is None or isinstance(value, (str, bool, int, float)):
        return value
    for caster in (lambda v: v.item(), lambda v: v.isoformat(), str):
        try:
            return caster(value)
        except (AttributeError, ValueError, TypeError):
            continue
    return str(value)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--out", type=Path, required=True, help="fichier JSONL à écrire")
    parser.add_argument(
        "--token", default=os.environ.get("HF_TOKEN"), help="token HF (ou $HF_TOKEN)"
    )
    parser.add_argument("--modulo", type=int, default=64, help="1 session retenue sur N")
    parser.add_argument(
        "--max-sessions-per-agent", type=int, default=None, help="plafond par agent"
    )
    args = parser.parse_args()

    if not args.token:
        raise SystemExit(
            "token HF manquant. Accepter l'accès sur\n"
            "  https://huggingface.co/datasets/SALT-NLP/SWE-chat\n"
            "puis : export HF_TOKEN=hf_xxx   (ou --token hf_xxx)"
        )

    report = extract(args.token, args.out, args.modulo, args.max_sessions_per_agent)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
