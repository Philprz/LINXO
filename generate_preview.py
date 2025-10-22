#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Génère un aperçu HTML du nouveau format de rapport
"""

import sys
from pathlib import Path

# Ajouter le chemin du module linxo_agent
sys.path.insert(0, str(Path(__file__).parent / 'linxo_agent'))

from analyzer import analyser_csv, generer_conseil_budget
from report_formatter_v2 import formater_email_html_v2, formater_sms_v2
from config import get_config


def generer_apercu():
    """
    Génère un fichier HTML d'aperçu du rapport
    """
    print("\nGeneration de l'apercu du rapport...")

    # Analyser les données
    config = get_config()
    analysis_result = analyser_csv()

    if not analysis_result:
        print("[ERREUR] Impossible d'analyser le fichier CSV")
        return

    # Extraire les données
    total_depenses = analysis_result.get('total_variables', 0)
    budget_max = analysis_result.get('budget_max', config.budget_variable)
    reste = budget_max - total_depenses
    pourcentage = (total_depenses / budget_max * 100) if budget_max > 0 else 0

    # Générer le conseil
    conseil = generer_conseil_budget(total_depenses, budget_max)

    # Générer le SMS
    sms_msg = formater_sms_v2(total_depenses, budget_max, reste, pourcentage)

    # Générer l'email HTML
    email_html = formater_email_html_v2(analysis_result, budget_max, conseil)

    # Sauvegarder le HTML
    html_file = Path(__file__).parent / "apercu_rapport.html"
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(email_html)

    # Sauvegarder le SMS
    sms_file = Path(__file__).parent / "apercu_sms.txt"
    with open(sms_file, 'w', encoding='utf-8') as f:
        f.write(sms_msg)
        f.write(f"\n\n({len(sms_msg)} caracteres)")

    print(f"\n[SUCCESS] Apercu genere!")
    print(f"\n  Email HTML: {html_file}")
    print(f"  SMS texte:  {sms_file}")
    print(f"\nOuvrez le fichier HTML dans votre navigateur pour voir le rendu.")


if __name__ == "__main__":
    generer_apercu()
