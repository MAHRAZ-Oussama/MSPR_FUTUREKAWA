"""
Configuration commune des tests.

Les tests isolés (unitaires, app, alerting, subscriber) tournent sur SQLite en
mémoire, sans PostgreSQL ni Docker. On fige ici les variables d'environnement
avant tout import des modules applicatifs (config est un singleton).
"""
import os

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("COUNTRY", "BR")
os.environ.setdefault("SMTP_HOST", "localhost")
os.environ.setdefault("SMTP_PORT", "1025")
