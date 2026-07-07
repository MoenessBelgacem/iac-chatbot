"""
Historique des déploiements — SQLite.

Stocke chaque requête (réussie, échouée, ou en attente de clarification)
pour la traçabilité et l'auditabilité exigées par le cahier des charges.
"""

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from backend.app.models import HistoryEntry

DB_DIR = Path(__file__).parent.parent.parent / "data"
DB_PATH = DB_DIR / "history.db"


def _get_connection() -> sqlite3.Connection:
    """Crée/ouvre la base SQLite et initialise le schéma si nécessaire."""
    DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS deployments (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp       TEXT    NOT NULL,
            prompt          TEXT    NOT NULL,
            demande_json    TEXT,
            type_generation TEXT,
            fichiers_generes TEXT,
            statut          TEXT    NOT NULL DEFAULT 'pending',
            erreur          TEXT
        )
    """)
    conn.commit()
    return conn


def enregistrer_requete(
    prompt: str,
    demande_json: Optional[str] = None,
    type_generation: Optional[str] = None,
    fichiers_generes: Optional[list[str]] = None,
    statut: str = "success",
    erreur: Optional[str] = None,
) -> int:
    """Enregistre une requête dans l'historique. Retourne l'ID créé."""
    conn = _get_connection()
    try:
        cursor = conn.execute(
            """
            INSERT INTO deployments
                (timestamp, prompt, demande_json, type_generation, fichiers_generes, statut, erreur)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                datetime.now(timezone.utc).isoformat(),
                prompt,
                demande_json,
                type_generation,
                json.dumps(fichiers_generes) if fichiers_generes else None,
                statut,
                erreur,
            ),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def lister_historique(limit: int = 50, offset: int = 0) -> list[HistoryEntry]:
    """Retourne les dernières entrées de l'historique (plus récentes d'abord)."""
    conn = _get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM deployments ORDER BY id DESC LIMIT ? OFFSET ?",
            (limit, offset),
        ).fetchall()
        return [HistoryEntry(**dict(row)) for row in rows]
    finally:
        conn.close()


def obtenir_requete(entry_id: int) -> Optional[HistoryEntry]:
    """Retourne une entrée spécifique par son ID."""
    conn = _get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM deployments WHERE id = ?", (entry_id,)
        ).fetchone()
        if row:
            return HistoryEntry(**dict(row))
        return None
    finally:
        conn.close()


def compter_requetes() -> dict:
    """Retourne des statistiques sur l'historique."""
    conn = _get_connection()
    try:
        total = conn.execute("SELECT COUNT(*) FROM deployments").fetchone()[0]
        success = conn.execute(
            "SELECT COUNT(*) FROM deployments WHERE statut = 'success'"
        ).fetchone()[0]
        errors = conn.execute(
            "SELECT COUNT(*) FROM deployments WHERE statut = 'error'"
        ).fetchone()[0]
        return {"total": total, "success": success, "errors": errors}
    finally:
        conn.close()
