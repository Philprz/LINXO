#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test de génération du rapport HTML"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'linxo_agent'))

from analyzer import analyser_csv, generer_conseil_budget
from report_formatter_v2 import formater_email_html_v2

if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("TEST DE GENERATION DU RAPPORT HTML")
    print("=" * 80)

    # Analyser le CSV
    result = analyser_csv()

    if result:
        print("\n[OK] Analyse terminée")

        # Générer le conseil
        conseil = generer_conseil_budget(result['total_variables'], result['budget_max'])

        # Générer le rapport HTML
        html = formater_email_html_v2(result, result['budget_max'], conseil)

        # Sauvegarder le HTML
        html_file = Path(__file__).parent / 'reports' / 'rapport_test.html'
        html_file.write_text(html, encoding='utf-8')

        print(f"\n[SUCCESS] Rapport HTML généré: {html_file}")
        print(f"\nTaille: {len(html)} caractères")
        print(f"\nOuvrez ce fichier dans un navigateur pour voir le résultat.")
    else:
        print("\n[ERREUR] Echec de l'analyse")
