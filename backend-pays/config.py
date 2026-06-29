"""
Configuration centralisée du backend-pays (typée, validée).

Remplace les os.getenv() dispersés par une source unique. pydantic-settings
lit automatiquement les variables d'environnement (insensibles à la casse)
puis un éventuel fichier .env, avec valeurs par défaut sûres pour le dev.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # ── Identité / base de données ───────────────────────────────────────────
    country: str = "BR"
    database_url: str = (
        "postgresql+asyncpg://futurekawa:futurekawa@localhost:5432/futurekawa"
    )

    # ── SMTP (alerting email, cf. O1 péremption) ─────────────────────────────
    smtp_host: str = "mailhog"
    smtp_port: int = 1025
    alert_sender: str = "alertes@futurekawa.com"

    # ── Règles métier ────────────────────────────────────────────────────────
    expiry_days: int = 365            # lot trop ancien -> PERIME + alerte
    flood_window_minutes: int = 30    # fenêtre anti-flood des alertes
    check_interval_minutes: int = 5   # période de la tâche de vérification (O3)

    # ── Sécurité (B4) ────────────────────────────────────────────────────────
    # Clé API exigée sur les routes d'écriture si définie ; None = ouvert (dev).
    api_key: str | None = None
    # Origines CORS autorisées, séparées par des virgules. "*" = tout (dev).
    cors_origins: str = "*"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
