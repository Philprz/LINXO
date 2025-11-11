#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gestionnaire de logs pour l'interface d'administration
"""

import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple

BASE_DIR = Path(__file__).parent.parent.parent.parent
LOGS_DIR = BASE_DIR / "logs"


class LogEntry:
    """Représente une ligne de log"""

    def __init__(self, line: str, line_number: int):
        self.line = line
        self.line_number = line_number
        self.level = self._detect_level()
        self.timestamp = self._extract_timestamp()

    def _detect_level(self) -> str:
        """Détecte le niveau de log"""
        line_upper = self.line.upper()
        if '[SUCCESS]' in line_upper or 'SUCCÈS' in line_upper or 'RÉUSSI' in line_upper:
            return 'SUCCESS'
        elif '[ERROR]' in line_upper or 'ERREUR' in line_upper or 'ÉCHEC' in line_upper:
            return 'ERROR'
        elif '[WARNING]' in line_upper or '[WARN]' in line_upper or 'ATTENTION' in line_upper:
            return 'WARNING'
        elif '[INFO]' in line_upper:
            return 'INFO'
        else:
            return 'INFO'

    def _extract_timestamp(self) -> Optional[str]:
        """Extrait le timestamp de la ligne si présent"""
        # Format: 2025-11-11 10:03:21
        timestamp_pattern = r'\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}'
        match = re.search(timestamp_pattern, self.line)
        return match.group(0) if match else None

    def to_dict(self) -> dict:
        """Convertit l'entrée en dictionnaire"""
        return {
            'line': self.line,
            'line_number': self.line_number,
            'level': self.level,
            'timestamp': self.timestamp
        }


class LogsManager:
    """Gestionnaire de logs"""

    def __init__(self):
        self.logs_dir = LOGS_DIR

    def list_log_files(self) -> List[Dict[str, any]]:
        """
        Liste tous les fichiers de logs disponibles

        Returns:
            List[Dict]: Liste des fichiers avec métadonnées
        """
        if not self.logs_dir.exists():
            return []

        log_files = []
        for log_file in sorted(self.logs_dir.glob('*.log'), reverse=True):
            try:
                stat = log_file.stat()
                log_files.append({
                    'name': log_file.name,
                    'path': str(log_file),
                    'size_bytes': stat.st_size,
                    'size_mb': round(stat.st_size / (1024 * 1024), 2),
                    'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    'is_cron': 'daily_report' in log_file.name
                })
            except Exception:
                continue

        return log_files

    def get_latest_log_file(self) -> Optional[Path]:
        """
        Récupère le dernier fichier de log cron

        Returns:
            Path: Chemin du dernier fichier ou None
        """
        if not self.logs_dir.exists():
            return None

        log_files = sorted(self.logs_dir.glob('daily_report_*.log'), reverse=True)
        return log_files[0] if log_files else None

    def read_log_file(
        self,
        file_name: str,
        offset: int = 0,
        limit: int = 100,
        level_filter: Optional[str] = None,
        search_query: Optional[str] = None
    ) -> Tuple[List[Dict], int, bool]:
        """
        Lit un fichier de log avec pagination et filtres

        Args:
            file_name: Nom du fichier de log
            offset: Ligne de départ
            limit: Nombre de lignes à retourner
            level_filter: Filtrer par niveau (SUCCESS, ERROR, WARNING, INFO)
            search_query: Recherche dans le contenu

        Returns:
            Tuple[List[Dict], int, bool]: (lignes, total_lignes, has_more)
        """
        log_path = self.logs_dir / file_name

        if not log_path.exists() or not log_path.is_file():
            return [], 0, False

        # Vérifier que le fichier est bien dans logs_dir (sécurité)
        try:
            log_path.resolve().relative_to(self.logs_dir.resolve())
        except ValueError:
            return [], 0, False

        # Lire le fichier
        try:
            with open(log_path, 'r', encoding='utf-8', errors='replace') as f:
                lines = f.readlines()
        except Exception:
            return [], 0, False

        # Créer des LogEntry
        log_entries = [LogEntry(line.rstrip(), i + 1) for i, line in enumerate(lines)]

        # Appliquer les filtres
        if level_filter:
            log_entries = [entry for entry in log_entries if entry.level == level_filter]

        if search_query:
            search_lower = search_query.lower()
            log_entries = [
                entry for entry in log_entries
                if search_lower in entry.line.lower()
            ]

        total_lines = len(log_entries)

        # Appliquer la pagination
        end_index = offset + limit
        paginated_entries = log_entries[offset:end_index]
        has_more = end_index < total_lines

        return (
            [entry.to_dict() for entry in paginated_entries],
            total_lines,
            has_more
        )

    def tail_log_file(
        self,
        file_name: str,
        lines: int = 50
    ) -> List[Dict]:
        """
        Lit les dernières lignes d'un fichier (comme tail -f)

        Args:
            file_name: Nom du fichier
            lines: Nombre de lignes à retourner

        Returns:
            List[Dict]: Dernières lignes
        """
        log_path = self.logs_dir / file_name

        if not log_path.exists() or not log_path.is_file():
            return []

        try:
            with open(log_path, 'r', encoding='utf-8', errors='replace') as f:
                all_lines = f.readlines()

            # Prendre les N dernières lignes
            last_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines

            # Créer des LogEntry
            start_line = max(0, len(all_lines) - lines)
            log_entries = [
                LogEntry(line.rstrip(), start_line + i + 1)
                for i, line in enumerate(last_lines)
            ]

            return [entry.to_dict() for entry in log_entries]

        except Exception:
            return []


# Instance globale
logs_manager = LogsManager()
