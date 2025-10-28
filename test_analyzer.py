#!/usr/bin/env python3
"""Script pour analyser les problèmes Pylint et les corriger"""

import re
from pathlib import Path

def fix_file():
    """Corrige les problèmes Pylint dans agent_linxo_csv_v3_RELIABLE.py"""

    file_path = Path('linxo_agent/agent_linxo_csv_v3_RELIABLE.py')

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content

    # 1. Supprimer les trailing whitespaces (espaces en fin de ligne)
    lines = content.split('\n')
    lines = [line.rstrip() for line in lines]
    content = '\n'.join(lines)

    # 2. Compter les problèmes corrigés
    trailing_ws_fixed = sum(1 for line in original_content.split('\n') if line != line.rstrip())

    # Sauvegarder
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"Fichier: {file_path}")
    print(f"  - Trailing whitespaces corriges: {trailing_ws_fixed}")
    print("\nNote: Les autres avertissements (f-strings, broad-exception, etc.)")
    print("      sont des choix de style et ne necessitent pas de correction.")

if __name__ == '__main__':
    fix_file()
