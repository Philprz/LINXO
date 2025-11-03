#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module pour uploader les rapports HTML générés vers le VPS.
"""

import os
import subprocess
from pathlib import Path
from typing import Optional


def upload_reports_to_vps(
    report_dir: Path,
    vps_host: Optional[str] = None,
    vps_path: Optional[str] = None,
    vps_user: Optional[str] = None
) -> bool:
    """
    Upload les rapports HTML vers le VPS via rsync.

    Args:
        report_dir: Répertoire local contenant les rapports
        vps_host: Adresse du VPS (défaut: variable d'environnement VPS_HOST)
        vps_path: Chemin sur le VPS (défaut: /var/www/html/reports)
        vps_user: Utilisateur SSH (défaut: ubuntu)

    Returns:
        bool: True si l'upload a réussi, False sinon
    """
    # Configuration par défaut depuis les variables d'environnement
    if not vps_host:
        vps_host = os.getenv('VPS_HOST', '152.228.218.1')

    if not vps_user:
        vps_user = os.getenv('VPS_USER', 'ubuntu')

    if not vps_path:
        vps_path = os.getenv('VPS_REPORTS_PATH', '/var/www/html/reports')

    if not report_dir.exists():
        print(f"[ERREUR] Le répertoire {report_dir} n'existe pas")
        return False

    print(f"\nUpload des rapports vers le VPS:")
    print(f"  Source: {report_dir}")
    print(f"  Destination: {vps_user}@{vps_host}:{vps_path}")

    try:
        # Créer le répertoire sur le VPS si nécessaire
        ssh_cmd = [
            'ssh',
            f'{vps_user}@{vps_host}',
            f'mkdir -p {vps_path}'
        ]

        print(f"\n[INFO] Création du répertoire sur le VPS...")
        result = subprocess.run(
            ssh_cmd,
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode != 0:
            print(f"[WARN] Impossible de créer le répertoire: {result.stderr}")

        # Upload avec rsync
        rsync_cmd = [
            'rsync',
            '-avz',
            '--delete',  # Supprimer les fichiers qui n'existent plus localement
            f'{report_dir}/',  # Trailing slash important pour rsync
            f'{vps_user}@{vps_host}:{vps_path}/'
        ]

        print(f"\n[INFO] Synchronisation via rsync...")
        result = subprocess.run(
            rsync_cmd,
            capture_output=True,
            text=True,
            timeout=120
        )

        if result.returncode == 0:
            print(f"\n[OK] Rapports uploadés avec succès!")
            return True
        else:
            print(f"\n[ERREUR] Échec de l'upload:")
            print(f"  Code: {result.returncode}")
            print(f"  Stderr: {result.stderr}")
            return False

    except subprocess.TimeoutExpired:
        print(f"\n[ERREUR] Timeout lors de l'upload (>120s)")
        return False
    except FileNotFoundError as e:
        print(f"\n[ERREUR] Commande non trouvée: {e}")
        print("  Assurez-vous que rsync et ssh sont installés")
        return False
    except Exception as e:
        print(f"\n[ERREUR] Erreur inattendue lors de l'upload: {e}")
        return False


def upload_static_files(
    static_dir: Path,
    vps_host: Optional[str] = None,
    vps_static_path: Optional[str] = None,
    vps_user: Optional[str] = None
) -> bool:
    """
    Upload les fichiers statiques (CSS, etc.) vers le VPS.

    Args:
        static_dir: Répertoire local contenant les fichiers statiques
        vps_host: Adresse du VPS
        vps_static_path: Chemin des fichiers statiques sur le VPS
        vps_user: Utilisateur SSH

    Returns:
        bool: True si l'upload a réussi, False sinon
    """
    if not vps_host:
        vps_host = os.getenv('VPS_HOST', '152.228.218.1')

    if not vps_user:
        vps_user = os.getenv('VPS_USER', 'ubuntu')

    if not vps_static_path:
        vps_static_path = os.getenv('VPS_STATIC_PATH', '/var/www/html/static')

    if not static_dir.exists():
        print(f"[ERREUR] Le répertoire {static_dir} n'existe pas")
        return False

    print(f"\nUpload des fichiers statiques vers le VPS:")
    print(f"  Source: {static_dir}")
    print(f"  Destination: {vps_user}@{vps_host}:{vps_static_path}")

    try:
        # Créer le répertoire sur le VPS
        ssh_cmd = [
            'ssh',
            f'{vps_user}@{vps_host}',
            f'mkdir -p {vps_static_path}/reports'
        ]

        result = subprocess.run(
            ssh_cmd,
            capture_output=True,
            text=True,
            timeout=30
        )

        # Upload avec rsync
        rsync_cmd = [
            'rsync',
            '-avz',
            f'{static_dir}/reports/',
            f'{vps_user}@{vps_host}:{vps_static_path}/reports/'
        ]

        result = subprocess.run(
            rsync_cmd,
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode == 0:
            print(f"\n[OK] Fichiers statiques uploadés!")
            return True
        else:
            print(f"\n[ERREUR] Échec de l'upload des fichiers statiques")
            return False

    except Exception as e:
        print(f"\n[ERREUR] {e}")
        return False


if __name__ == "__main__":
    # Test de la fonction d'upload
    project_root = Path(__file__).parent.parent
    data_reports = project_root / "data" / "reports"
    static_dir = project_root / "static"

    if data_reports.exists():
        print("Test d'upload des rapports...")
        upload_reports_to_vps(data_reports)

    if static_dir.exists():
        print("\nTest d'upload des fichiers statiques...")
        upload_static_files(static_dir)
