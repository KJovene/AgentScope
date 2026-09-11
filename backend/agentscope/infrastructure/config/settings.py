"""Configuration centralisée, lue depuis l'environnement.

Aucune valeur secrète par défaut. Préfixe des variables : ``AGENTSCOPE_``.
Le cœur métier ne lit jamais l'environnement directement — il reçoit ces valeurs
via l'injection de dépendances (I0.5 / I4.10).
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

from agentscope.domain import RetentionMode

# ``backend/`` puis la racine du dépôt, déduits du fichier lui-même : hors Docker
# le backend se lance depuis ``backend/``, et un ``.env`` relatif ne trouverait
# jamais celui de la racine — celui que `docker compose` utilise.
_BACKEND_DIR = Path(__file__).resolve().parents[3]
_REPO_ROOT = _BACKEND_DIR.parent

# Emplacement du `.env` du dépôt dans le conteneur (montage `docker-compose.yml`,
# même convention que `/docs` pour le schéma de mapping). Hors Docker le chemin
# n'existe pas et le filtre ci-dessous l'écarte.
_DOCKER_ENV_FILE = Path("/config/.env")

# Du moins au plus spécifique : pydantic-settings donne la priorité au dernier
# fichier trouvé, et une variable d'environnement réelle l'emporte sur tous.
_ENV_FILE_CANDIDATES = (
    _DOCKER_ENV_FILE,
    _REPO_ROOT / ".env",
    _BACKEND_DIR / ".env",
    Path(".env"),
)

# `is_file()` et pas seulement `exists()` : `docker compose` crée un DOSSIER à la
# place d'un montage `./.env:/app/.env` quand le fichier hôte manque (clone sans
# `cp .env.example .env`). Le laisser passer ferait planter la lecture au
# démarrage ; on l'ignore et l'application repart sur ses valeurs par défaut.
_ENV_FILES = tuple(path for path in _ENV_FILE_CANDIDATES if path.is_file())


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="AGENTSCOPE_",
        env_file=_ENV_FILES,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Métadonnées applicatives.
    app_name: str = "AgentScope API"
    debug: bool = False

    # Base de données — SQLite par défaut (reproductible depuis un clone),
    # PostgreSQL via configuration (cf. ADR-0003).
    database_url: str = "sqlite:///./agentscope.db"
    db_echo: bool = False

    # Rétention des enregistrements bruts (cf. ADR-0006, I1.7).
    # "full" = payload conservé ; "minimal" = index + sha256, payload des rejets seulement.
    raw_record_retention: RetentionMode = RetentionMode.FULL

    # Origines autorisées pour le frontend. `NoDecode` : la valeur brute de l'env
    # (CSV) arrive au validateur au lieu d'être décodée en JSON par pydantic-settings.
    cors_origins: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: ["http://localhost:5173"]
    )

    # Fournisseur IA interchangeable (cf. ADR-0005). "fake" = aucun appel externe.
    llm_provider: str = "fake"
    llm_model: str | None = None
    llm_base_url: str | None = None
    llm_api_key: str | None = None

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_csv(cls, value: object) -> object:
        """Accepte une liste d'origines séparées par des virgules."""
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    """Instance unique, mémoïsée pour la durée du process."""
    return Settings()
