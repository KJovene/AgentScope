"""Recalcule les trois observations chiffrées de ``docs/findings.md`` (issue I6.7).

Lit l'extrait TraceLab épinglé et réaffiche, avec leurs numérateurs et dénominateurs,
les chiffres cités dans le document. Aucun chiffre du rapport n'est saisi à la main :
il sort d'ici.

Prérequis : ``make data-tracelab`` (télécharge la release ``v0.0.1``, vérifie son SHA256,
retient 1 session sur 32 — règle ``sha1(session_id) %% 32 == 0``).

    python scripts/findings_tracelab.py
    python scripts/findings_tracelab.py --input data/tracelab/extract-dev.jsonl
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

DEFAULT_INPUT = Path("data/tracelab/extract-dev.jsonl")


def _pct(numerator: float, denominator: float) -> str:
    return "n/d" if not denominator else f"{100 * numerator / denominator:.1f} %"


def collect(path: Path) -> dict[str, Any]:
    tokens: defaultdict[str, Counter[str]] = defaultdict(Counter)
    rounds_by_provider: Counter[str] = Counter()
    sessions_by_provider: defaultdict[str, set[str]] = defaultdict(set)
    rounds_per_session: Counter[str] = Counter()
    tools_by_name: defaultdict[str, list[int]] = defaultdict(lambda: [0, 0])
    tools_by_provider: defaultdict[str, list[int]] = defaultdict(lambda: [0, 0])
    rounds_with_cache_read = 0
    models: Counter[str] = Counter()
    first_seen: str | None = None
    last_seen: str | None = None

    with path.open(encoding="utf-8") as handle:
        for line in handle:
            record = json.loads(line)
            provider = record["provider"]
            rounds_by_provider[provider] += 1
            sessions_by_provider[provider].add(record["session_id"])
            rounds_per_session[record["session_id"]] += 1
            models[record.get("model")] += 1

            bucket = tokens[provider]
            for key in (
                "input_tokens_total",
                "output_tokens",
                "prefix_tokens",
                "newly_append_tokens",
                "claude_cache_read_input_tokens",
                "claude_cache_creation_input_tokens",
                "claude_uncached_input_tokens",
            ):
                value = record.get(key)
                if value is not None:
                    bucket[key] += value

            if provider == "claude" and (record.get("claude_cache_read_input_tokens") or 0) > 0:
                rounds_with_cache_read += 1

            for event in record.get("timing_events") or []:
                stamp = event.get("timestamp")
                if stamp:
                    first_seen = stamp if first_seen is None else min(first_seen, stamp)
                    last_seen = stamp if last_seen is None else max(last_seen, stamp)

            for call in record.get("tools") or []:
                name = call.get("tool_name") or "(sans nom)"
                failed = int(bool(call.get("is_error")))
                tools_by_name[name][0] += 1
                tools_by_name[name][1] += failed
                tools_by_provider[provider][0] += 1
                tools_by_provider[provider][1] += failed

    return {
        "tokens": tokens,
        "rounds_by_provider": rounds_by_provider,
        "sessions_by_provider": sessions_by_provider,
        "rounds_per_session": rounds_per_session,
        "tools_by_name": tools_by_name,
        "tools_by_provider": tools_by_provider,
        "rounds_with_cache_read": rounds_with_cache_read,
        "models": models,
        "period": (first_seen, last_seen),
    }


def report(data: dict[str, Any]) -> None:
    tokens = data["tokens"]
    claude = tokens["claude"]
    rounds = data["rounds_by_provider"]
    total_rounds = sum(rounds.values())
    total_sessions = sum(len(s) for s in data["sessions_by_provider"].values())

    print("=" * 78)
    print("PÉRIMÈTRE")
    print("=" * 78)
    print(f"  Sessions              : {total_sessions}  {dict((k, len(v)) for k, v in data['sessions_by_provider'].items())}")
    print(f"  Rounds                : {total_rounds}  {dict(rounds)}")
    print(f"  Modèles distincts     : {len(data['models'])}")
    print(f"  Période (timing_events): {data['period'][0]}  ->  {data['period'][1]}")

    print()
    print("=" * 78)
    print("OBSERVATION 1 — Le cache porte l'essentiel du contexte (sessions Claude)")
    print("=" * 78)
    read = claude["claude_cache_read_input_tokens"]
    created = claude["claude_cache_creation_input_tokens"]
    uncached = claude["claude_uncached_input_tokens"]
    total_in = claude["input_tokens_total"]
    print(f"  tokens d'entrée (Claude)      : {total_in:>15,}")
    print(f"    lus depuis le cache         : {read:>15,}   {_pct(read, total_in)}")
    print(f"    écrits dans le cache        : {created:>15,}   {_pct(created, total_in)}")
    print(f"    hors cache                  : {uncached:>15,}   {_pct(uncached, total_in)}")
    print(f"    contrôle (somme == total)   : {read + created + uncached == total_in}")
    print(f"  rounds Claude lisant le cache : {data['rounds_with_cache_read']} / {rounds['claude']}"
          f"   {_pct(data['rounds_with_cache_read'], rounds['claude'])}")
    print("  -> codex n'expose aucune comptabilité de cache : indicateur non comparable.")

    print()
    print("=" * 78)
    print("OBSERVATION 2 — Les tokens d'entrée sont massivement du contexte rejoué")
    print("=" * 78)
    total_input = sum(t["input_tokens_total"] for t in tokens.values())
    total_prefix = sum(t["prefix_tokens"] for t in tokens.values())
    total_new = sum(t["newly_append_tokens"] for t in tokens.values())
    total_output = sum(t["output_tokens"] for t in tokens.values())
    print(f"  tokens d'entrée (total)       : {total_input:>15,}")
    print(f"    contexte rejoué (prefix)    : {total_prefix:>15,}   {_pct(total_prefix, total_input)}")
    print(f"    nouveau contenu             : {total_new:>15,}   {_pct(total_new, total_input)}")
    print(f"    contrôle (somme == total)   : {total_prefix + total_new == total_input}")
    print(f"  tokens de sortie (total)      : {total_output:>15,}")
    print(f"  ratio entrée / sortie         : {total_input / total_output:>15.0f} : 1")
    for provider, bucket in sorted(tokens.items()):
        ratio = bucket["input_tokens_total"] / bucket["output_tokens"]
        print(f"    {provider:<8} : {ratio:>6.0f} : 1")

    print()
    print("=" * 78)
    print("OBSERVATION 3 — Un taux d'erreur global masque un écart de 1 à 40 entre outils")
    print("=" * 78)
    calls = sum(v[0] for v in data["tools_by_name"].values())
    errors = sum(v[1] for v in data["tools_by_name"].values())
    print(f"  appels d'outils               : {calls:>15,}")
    print(f"  en erreur                     : {errors:>15,}   {_pct(errors, calls)}")
    print("  par fournisseur :")
    for provider, (n, e) in sorted(data["tools_by_provider"].items()):
        print(f"    {provider:<8} {n:>7,} appels   {e:>5,} erreurs   {_pct(e, n)}")
    print("  par outil (>= 100 appels) :")
    frequent = [(name, n, e) for name, (n, e) in data["tools_by_name"].items() if n >= 100]
    for name, n, e in sorted(frequent, key=lambda row: -row[2] / row[1]):
        print(f"    {name:<16} {n:>7,} appels   {e:>5,} erreurs   {_pct(e, n)}")

    print()
    print("=" * 78)
    print("EN COMPLÉMENT — Distribution des sessions (pourquoi une médiane, pas une moyenne)")
    print("=" * 78)
    per_session = sorted(data["rounds_per_session"].values())
    index_p90 = max(0, int(0.9 * len(per_session)) - 1)
    print(f"  sessions                      : {len(per_session)}")
    print(f"  rounds par session — min      : {per_session[0]}")
    print(f"                       médiane  : {statistics.median(per_session):.0f}")
    print(f"                       moyenne  : {statistics.mean(per_session):.1f}")
    print(f"                       p90      : {per_session[index_p90]}")
    print(f"                       max      : {per_session[-1]}")


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    args = parser.parse_args()

    if not args.input.exists():
        print(f"Extrait introuvable : {args.input}\nLancer d'abord : make data-tracelab")
        return 1

    report(collect(args.input))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
