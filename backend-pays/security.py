"""
Sécurité applicative légère du backend-pays.

Protection optionnelle des routes d'écriture par clé API (en-tête X-API-Key).
Désactivée par défaut (API_KEY non défini) pour faciliter la démo ; activable
en production sans changement de code. Les routes de lecture restent ouvertes
(consultation siège/terrain), conformément à l'usage prévu.
"""
from fastapi import Header, HTTPException, status

from config import settings


def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    """Exige une clé API valide SI settings.api_key est configuré, sinon passe."""
    if settings.api_key and x_api_key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Clé API invalide ou manquante (en-tête X-API-Key).",
        )
