"""Erreurs du domaine metier."""


class DomainError(Exception):
    """Erreur de base pour toute violation d'une regle metier."""


class LLMError(DomainError):
    """Erreur levee par un LLMProvider : appel echoue, timeout, reponse malformee."""
