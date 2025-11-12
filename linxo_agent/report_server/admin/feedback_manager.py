#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gestionnaire SQLite pour stocker les retours de classification utilisateur.
"""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

BASE_DIR = Path(__file__).parent.parent.parent.parent
DATA_DIR = BASE_DIR / "data" / "ml"


class FeedbackManager:
    """Gère l'historique des corrections/validations de classification."""

    def __init__(self) -> None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.db_path = DATA_DIR / "classification_feedback.db"
        self._ensure_tables()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_tables(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    transaction_id TEXT,
                    libelle TEXT,
                    categorie_initiale TEXT,
                    categorie_corrigee TEXT,
                    statut TEXT,
                    commentaire TEXT,
                    montant REAL,
                    compte TEXT,
                    date_transaction TEXT,
                    confiance REAL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_feedback_tx ON feedback(transaction_id)"
            )

    # ------------------------------------------------------------------ #
    # Public API                                                         #
    # ------------------------------------------------------------------ #

    def add_feedback(self, feedback: Dict[str, Any]) -> int:
        """Insère un retour utilisateur et retourne son ID."""
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO feedback (
                    transaction_id,
                    libelle,
                    categorie_initiale,
                    categorie_corrigee,
                    statut,
                    commentaire,
                    montant,
                    compte,
                    date_transaction,
                    confiance,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    feedback.get("transaction_id"),
                    feedback.get("libelle"),
                    feedback.get("categorie_initiale"),
                    feedback.get("categorie_corrigee"),
                    feedback.get("statut"),
                    feedback.get("commentaire"),
                    feedback.get("montant"),
                    feedback.get("compte"),
                    feedback.get("date_transaction"),
                    feedback.get("confiance"),
                    feedback.get("created_at", datetime.utcnow().isoformat()),
                ),
            )
            return cursor.lastrowid

    def list_feedback(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Retourne les dernières corrections."""
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, transaction_id, libelle, categorie_initiale,
                       categorie_corrigee, statut, commentaire, montant,
                       compte, date_transaction, confiance, created_at
                FROM feedback
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

        return [dict(row) for row in rows]


feedback_manager = FeedbackManager()
