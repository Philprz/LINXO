#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de test des nouveaux formats de rapport (épurés et visuels)
"""

import sys
from pathlib import Path

# Ajouter le chemin du module linxo_agent
sys.path.insert(0, str(Path(__file__).parent / 'linxo_agent'))

from analyzer import analyser_csv, generer_conseil_budget
from report_formatter_v2 import formater_email_html_v2, formater_sms_v2
from config import get_config


def test_nouveaux_formats():
    """
    Teste et affiche les nouveaux formats de rapport
    """
    print("\n" + "=" * 80)
    print("TEST DES NOUVEAUX FORMATS DE RAPPORT")
    print("=" * 80)

    # Analyser les données
    config = get_config()
    print(f"\n[INFO] Analyse du dernier fichier CSV...")

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

    # ========================================================================
    # TEST FORMAT SMS
    # ========================================================================
    print("\n" + "=" * 80)
    print("[SMS] NOUVEAU FORMAT SMS")
    print("=" * 80)

    sms_msg = formater_sms_v2(total_depenses, budget_max, reste, pourcentage)

    print("\n" + sms_msg)
    print(f"\nLongueur: {len(sms_msg)} caractères (max 160)")

    # ========================================================================
    # TEST FORMAT EMAIL HTML
    # ========================================================================
    print("\n" + "=" * 80)
    print("[EMAIL] NOUVEAU FORMAT EMAIL HTML")
    print("=" * 80)

    email_html = formater_email_html_v2(analysis_result, budget_max, conseil)

    # Sauvegarder le HTML pour prévisualisation
    html_file = Path(__file__).parent / "test_rapport.html"
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(email_html)

    print(f"\n[SUCCESS] Rapport HTML généré: {html_file}")
    print("\nOuvrez ce fichier dans votre navigateur pour voir le rendu complet.")

    # Afficher un extrait du HTML
    print("\n[PREVIEW] Extrait du code HTML:")
    print("-" * 80)
    lines = email_html.split('\n')
    for i, line in enumerate(lines[:30]):
        print(line)
    print("...")
    print(f"\n({len(lines)} lignes au total)")

    print("\n" + "=" * 80)
    print("INFORMATIONS")
    print("=" * 80)
    print(f"\n1. SMS: {len(sms_msg)} caractères")
    print(f"2. Email HTML: {len(email_html)} caractères")
    print(f"3. Fichier HTML: {html_file}")
    print("\nOuvrez le fichier HTML dans votre navigateur pour voir le résultat final.")
    print("=" * 80)


if __name__ == "__main__":
    test_nouveaux_formats()
