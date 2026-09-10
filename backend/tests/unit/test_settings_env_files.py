"""La configuration doit trouver le `.env` du dépôt même lancée hors Docker.

Hors conteneur le backend démarre depuis ``backend/``, alors que le ``.env`` que
`docker compose` utilise vit à la racine du dépôt. Un ``env_file`` relatif ne
l'aurait jamais trouvé, et l'application repartait sur ses valeurs par défaut
(fournisseur LLM ``fake``, notamment).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from agentscope.infrastructure.config.settings import (
    _BACKEND_DIR,
    _ENV_FILES,
    _REPO_ROOT,
    Settings,
)


def test_backend_dir_is_correctly_located() -> None:
    """L'index de `parents[...]` est la partie fragile : on l'ancre sur un
    fichier dont la place ne bougera pas. Vrai partout, y compris dans l'image
    Docker où seul ``backend/`` est monté."""
    assert (_BACKEND_DIR / "agentscope" / "__init__.py").is_file()
    assert _BACKEND_DIR.parent == _REPO_ROOT


def test_repo_root_is_the_directory_holding_the_compose_file() -> None:
    """Complète le test ci-dessus quand le dépôt entier est sur le disque. Dans
    l'image Docker, ``backend/`` est monté seul : il n'y a pas de racine à
    vérifier, et le `.env` arrive par l'environnement de Compose."""
    if not (_REPO_ROOT / "backend").is_dir():
        pytest.skip("dépôt non monté en entier (image Docker)")
    assert (_REPO_ROOT / "docker-compose.yml").is_file()


def test_repo_root_env_is_a_candidate_before_the_more_specific_ones() -> None:
    """pydantic-settings donne la priorité au dernier fichier : la racine passe
    donc en premier, `backend/` puis le répertoire courant peuvent l'affiner."""
    # Ruff (SIM300) veut la constante à gauche.
    expected = (_REPO_ROOT / ".env", _BACKEND_DIR / ".env", Path(".env"))
    assert expected[0] == _ENV_FILES[0]
    assert expected == _ENV_FILES


def test_env_file_is_read_when_the_process_environment_says_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Le mécanisme lui-même : un fichier fournit la valeur, sans variable
    d'environnement (`isolate_configuration` les a retirées)."""
    env_file = tmp_path / ".env"
    env_file.write_text("AGENTSCOPE_LLM_PROVIDER=anthropic\n", encoding="utf-8")

    settings = Settings(_env_file=env_file)  # type: ignore[call-arg]

    assert settings.llm_provider == "anthropic"


def test_the_process_environment_still_wins_over_any_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Indispensable pour la stack Docker : Compose injecte des variables, et
    elles doivent l'emporter sur tout `.env` présent dans l'image."""
    env_file = tmp_path / ".env"
    env_file.write_text("AGENTSCOPE_LLM_PROVIDER=anthropic\n", encoding="utf-8")
    monkeypatch.setenv("AGENTSCOPE_LLM_PROVIDER", "openai")

    settings = Settings(_env_file=env_file)  # type: ignore[call-arg]

    assert settings.llm_provider == "openai"
