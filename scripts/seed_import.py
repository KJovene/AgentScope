#!/usr/bin/env python3
"""Branche une source de données sur la stack en marche : enregistre son mapping
puis importe un ou plusieurs fichiers de traces via l'API REST (EPIC 4).

Le mapping vient de ``docs/data/mappings/*.json`` (format décrit par ADR-0004),
les fichiers de ``data/`` ou des fixtures commitées. L'API normalise l'import et
peuple la base que lit le dashboard — aucun accès direct à la base ici.

Exemples
--------
    # TraceLab — fixture commitée (hors-ligne, déterministe, CC BY 4.0)
    python scripts/seed_import.py --mapping docs/data/mappings/tracelab.json \
        backend/tests/fixtures/tracelab/sample.jsonl

    # TraceLab — extrait de développement (après `make data-tracelab`)
    python scripts/seed_import.py --mapping docs/data/mappings/tracelab.json \
        data/tracelab/extract-dev.jsonl

    # SWE-chat
    python scripts/seed_import.py --mapping docs/data/mappings/swe-chat.json \
        backend/tests/fixtures/swe_chat/sample.jsonl

    # API jointe autrement (depuis un autre conteneur : --api http://backend:8000)
    python scripts/seed_import.py --api http://localhost:8000 --mapping ... FICHIER...
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_API = "http://localhost:8000"
API_PREFIX = "/api/v1"


def _request(url: str, *, method: str, data: bytes | None, headers: dict[str, str]) -> Any:
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    with urllib.request.urlopen(req) as response:
        raw = response.read()
    return json.loads(raw) if raw else None


def _post_json(url: str, payload: dict[str, Any]) -> Any:
    body = json.dumps(payload).encode("utf-8")
    return _request(
        url, method="POST", data=body, headers={"Content-Type": "application/json"}
    )


def _encode_multipart(fields: dict[str, str], files: list[tuple[str, Path]]) -> tuple[str, bytes]:
    """Corps multipart/form-data minimal — pas de dépendance à `requests`."""
    boundary = uuid.uuid4().hex
    out = bytearray()
    for name, value in fields.items():
        out += f"--{boundary}\r\n".encode()
        out += f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode()
        out += f"{value}\r\n".encode()
    for name, path in files:
        out += f"--{boundary}\r\n".encode()
        out += (
            f'Content-Disposition: form-data; name="{name}"; filename="{path.name}"\r\n'
        ).encode()
        out += b"Content-Type: application/octet-stream\r\n\r\n"
        out += path.read_bytes()
        out += b"\r\n"
    out += f"--{boundary}--\r\n".encode()
    return boundary, bytes(out)


def register_mapping(api: str, definition_path: Path) -> str:
    """POST /mappings, idempotent : un mapping déjà présent est réutilisé tel quel."""
    definition = json.loads(definition_path.read_text(encoding="utf-8"))
    name = definition["name"]
    payload = {
        "name": name,
        "source_format": definition["source_format"],
        "definition": definition,
    }
    try:
        created = _post_json(f"{api}{API_PREFIX}/mappings", payload)
        print(f"  mapping « {name} » créé (v{created['version']})", file=sys.stderr)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")
        if exc.code == 400 and ("exist" in detail.lower() or "déjà" in detail.lower()):
            print(f"  mapping « {name} » déjà enregistré — réutilisé", file=sys.stderr)
        else:
            raise SystemExit(f"échec création du mapping ({exc.code}) : {detail}") from exc
    return name


def _repository_field(definition: dict[str, Any]) -> str | None:
    """Champ source alimentant ``session.repository_name``, s'il est mappé."""
    spec = (
        definition.get("entities", {})
        .get("session", {})
        .get("fields", {})
        .get("repository_name")
    )
    return spec.get("from") if isinstance(spec, dict) else None


def register_repositories(api: str, definition: dict[str, Any], files: list[Path]) -> None:
    """Déclare les dépôts référencés par les sessions AVANT l'import : le
    rattachement session → dépôt (best-effort) ne voit que les dépôts déjà connus.
    """
    field = _repository_field(definition)
    source_name = definition.get("constants", {}).get("source_name")
    if not field or not source_name:
        return

    names: set[str] = set()
    for path in files:
        if path.suffix.lower() not in (".jsonl", ".ndjson"):
            print(
                f"  dépôts : {path.name} n'est pas du JSONL — scan ignoré", file=sys.stderr
            )
            continue
        with path.open(encoding="utf-8") as stream:
            for line in stream:
                line = line.strip()
                if not line:
                    continue
                try:
                    value = json.loads(line).get(field)
                except json.JSONDecodeError:
                    continue
                if isinstance(value, str) and value:
                    names.add(value)
    if not names:
        return

    url = f"{api}{API_PREFIX}/sources/{urllib.parse.quote(source_name)}/repositories"
    payload = [{"name": name} for name in sorted(names)]
    try:
        result = _request(
            url,
            method="POST",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        print(
            f"  dépôts « {source_name} » : {result['registered']} créés, "
            f"{result['skipped']} déjà présents",
            file=sys.stderr,
        )
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")
        print(
            f"  dépôts non enregistrés (HTTP {exc.code}) — repository_name restera nul : "
            f"{detail[:120]}",
            file=sys.stderr,
        )


def run_import(api: str, mapping_id: str, files: list[Path]) -> dict[str, Any]:
    boundary, body = _encode_multipart(
        {"mapping_id": mapping_id}, [("files", p) for p in files]
    )
    try:
        return _request(
            f"{api}{API_PREFIX}/imports",
            method="POST",
            data=body,
            headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        )
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")
        raise SystemExit(f"échec de l'import ({exc.code}) : {detail}") from exc


def _resolve(raw: str) -> Path:
    path = Path(raw)
    if not path.is_absolute():
        path = (REPO_ROOT / path).resolve()
    if not path.exists():
        raise SystemExit(f"fichier introuvable : {raw}")
    return path


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--mapping",
        required=True,
        help="définition JSON du mapping (docs/data/mappings/*.json)",
    )
    parser.add_argument(
        "--api",
        default=DEFAULT_API,
        help=f"racine de l'API REST (défaut : {DEFAULT_API})",
    )
    parser.add_argument("files", nargs="+", help="fichiers de traces à importer")
    args = parser.parse_args()

    api = args.api.rstrip("/")
    mapping_path = _resolve(args.mapping)
    files = [_resolve(f) for f in args.files]

    print(f"→ {api}  |  mapping {mapping_path.name}", file=sys.stderr)
    definition = json.loads(mapping_path.read_text(encoding="utf-8"))
    mapping_id = register_mapping(api, mapping_path)
    register_repositories(api, definition, files)
    report = run_import(api, mapping_id, files)

    print(json.dumps(report, indent=2, ensure_ascii=False))
    print(
        f"  importés={report.get('imported_count')} "
        f"doublons={report.get('duplicate_count')} "
        f"rejetés={report.get('rejected_count')}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
