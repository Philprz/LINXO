#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Script de test pour l'analyzer"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'linxo_agent'))

from analyzer import analyser_csv

if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("TEST DE L'ANALYSEUR")
    print("=" * 80)

    result = analyser_csv()

    if result:
        print("\n" + "=" * 80)
        print("RESULTATS DE L'ANALYSE")
        print("=" * 80)
        print(f"Total transactions: {result['total_transactions']}")
        print(f"\nDepenses FIXES:")
        print(f"  - Nombre: {len(result['depenses_fixes'])} transactions")
        print(f"  - Total:  {result['total_fixes']:.2f} EUR")
        print(f"\nDepenses VARIABLES:")
        print(f"  - Nombre: {len(result['depenses_variables'])} transactions")
        print(f"  - Total:  {result['total_variables']:.2f} EUR")
        print(f"\nBudget variable: {result['budget_max']:.2f} EUR")
        print(f"Reste: {result['reste']:.2f} EUR")
        print("=" * 80)

        # Afficher quelques exemples de dépenses fixes détectées
        print("\nExemples de depenses FIXES detectees:")
        for dep in result['depenses_fixes'][:10]:
            print(f"  - {dep['libelle'][:40]:40} {dep['montant']:8.2f} EUR")

        if len(result['depenses_fixes']) > 10:
            print(f"  ... et {len(result['depenses_fixes']) - 10} autres")
    else:
        print("\n[ERREUR] Echec de l'analyse")
