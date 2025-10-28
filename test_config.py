#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de test pour vérifier la configuration
"""

import sys
from pathlib import Path

# Ajouter le répertoire linxo_agent au path
sys.path.insert(0, str(Path(__file__).parent / 'linxo_agent'))

from config import get_config

def main():
    """Teste la configuration et affiche les chemins détectés"""
    print("\n" + "=" * 80)
    print("TEST DE CONFIGURATION - LINXO AGENT")
    print("=" * 80)

    config = get_config()

    print(f"\nEnvironnement détecté: {config.env_name}")
    print(f"OS: {'Windows' if config.is_windows else 'Linux'}")
    print(f"\nChemins configurés:")
    print(f"  - Base dir:        {config.base_dir}")
    print(f"  - Linxo agent:     {config.linxo_agent_dir}")
    print(f"  - Data dir:        {config.data_dir}")
    print(f"  - Downloads dir:   {config.downloads_dir}")
    print(f"  - Logs dir:        {config.logs_dir}")
    print(f"  - Reports dir:     {config.reports_dir}")
    print(f"  - API secrets:     {config.api_secrets_file}")

    print(f"\nFichiers de configuration:")
    print(f"  - Config Linxo:    {config.config_linxo_file}")
    print(f"  - Dépenses:        {config.depenses_file}")
    print(f"  - CSV latest:      {config.get_latest_csv()}")

    print(f"\nVérification de l'existence des fichiers:")
    print(f"  - config_linxo.json:           {'✅' if config.config_linxo_file.exists() else '❌'}")
    print(f"  - depenses_recurrentes.json:   {'✅' if config.depenses_file.exists() else '❌'}")
    print(f"  - api_secrets.json:            {'✅' if config.api_secrets_file.exists() else '❌'}")

    print(f"\nVérification de l'existence des répertoires:")
    print(f"  - data/:           {'✅' if config.data_dir.exists() else '❌'}")
    print(f"  - logs/:           {'✅' if config.logs_dir.exists() else '❌'}")
    print(f"  - reports/:        {'✅' if config.reports_dir.exists() else '❌'}")

    print("\n" + "=" * 80)
    print("✅ Test de configuration terminé")
    print("=" * 80 + "\n")

if __name__ == "__main__":
    main()
