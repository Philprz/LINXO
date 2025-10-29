#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de test pour l'envoi d'email avec rapports HTML
Envoie uniquement à l'adresse spécifiée
"""

import os
import sys
from pathlib import Path

# Configuration temporaire pour le test
print("Configuration du test...")
os.environ['REPORTS_BASE_URL'] = 'https://linxo.itspirit.ovh/reports'
os.environ['REPORTS_BASIC_USER'] = 'linxo'
os.environ['REPORTS_BASIC_PASS'] = 'test123'
os.environ['REPORTS_SIGNING_KEY'] = 'vzsLO33H_yweU27HxYiRxujGftujaoQ9gPPQBQcjuyQ'

# Adresse email de test
TEST_EMAIL = 'phiperez@gmail.com'

# Ajouter le répertoire au path
sys.path.insert(0, str(Path(__file__).parent))

from linxo_agent.config import get_config
from linxo_agent.analyzer import analyser_csv
from linxo_agent.notifications import NotificationManager
import pandas as pd
from linxo_agent.reports import build_daily_report

print("\n" + "=" * 80)
print("TEST D'ENVOI EMAIL AVEC RAPPORTS HTML")
print("=" * 80)
print(f"Destinataire: {TEST_EMAIL}")
print("=" * 80)

try:
    # Étape 1: Charger la config et analyser le dernier CSV
    print("\n[1/4] Analyse du dernier CSV...")
    config = get_config()
    csv_path = config.get_latest_csv()
    print(f"CSV: {csv_path}")

    analysis_result = analyser_csv(csv_path)

    if not analysis_result:
        print("[ERREUR] Échec de l'analyse")
        sys.exit(1)

    print(f"[OK] {analysis_result['total_transactions']} transactions analysées")
    print(f"     Dépenses variables: {analysis_result['total_variables']:.2f}€")

    # Étape 2: Générer les rapports HTML
    print("\n[2/4] Génération des rapports HTML...")

    # Convertir en DataFrame
    all_transactions = (
        analysis_result.get('depenses_fixes', []) +
        analysis_result.get('depenses_variables', [])
    )

    df_data = []
    for trans in all_transactions:
        df_data.append({
            'date': trans.get('date_str', ''),
            'libelle': trans.get('libelle', ''),
            'montant': trans.get('montant', 0),
            'categorie': trans.get('categorie', 'Non classé'),
            'date_str': trans.get('date_str', '')
        })

    df = pd.DataFrame(df_data)

    # Générer les rapports
    report_index = build_daily_report(
        df,
        report_date=None,
        base_url=os.environ['REPORTS_BASE_URL'],
        signing_key=os.environ['REPORTS_SIGNING_KEY']
    )

    print(f"[OK] Rapports générés dans: {report_index.base_dir}")
    print(f"     {len(report_index.families)} familles de dépenses")
    print(f"     Total: {report_index.grand_total:.2f}€")

    # Étape 3: Préparer l'envoi email
    print(f"\n[3/4] Préparation de l'email pour {TEST_EMAIL}...")

    notification_manager = NotificationManager()

    # Remplacer temporairement les destinataires
    notification_manager.config.notification_emails = [TEST_EMAIL]

    print(f"[INFO] Email sera envoyé depuis: {notification_manager.config.smtp_email}")

    # Étape 4: Envoyer l'email (sans SMS)
    print(f"\n[4/4] Envoi de l'email...")

    # Appeler send_budget_notification avec le report_index
    results = notification_manager.send_budget_notification(
        analysis_result,
        report_index=report_index
    )

    # Vérifier le résultat
    if results.get('email'):
        print("\n" + "=" * 80)
        print("✓ EMAIL ENVOYÉ AVEC SUCCÈS!")
        print("=" * 80)
        print(f"Destinataire: {TEST_EMAIL}")
        print(f"\nL'email contient:")
        print(f"  - Résumé par famille de dépenses")
        print(f"  - {len(report_index.families)} liens cliquables vers les rapports")
        print(f"  - Total: {report_index.grand_total:.2f}€")
        print(f"\nRapports accessibles sur:")
        print(f"  {os.environ['REPORTS_BASE_URL']}/{report_index.report_date}/index.html")
        print("\nNote: Le serveur de rapports doit être démarré pour que les liens")
        print("      fonctionnent. Voir: docs/EMAIL_REPORTS.md")
        print("=" * 80)
    else:
        print("\n[ERREUR] Échec de l'envoi de l'email")
        sys.exit(1)

except Exception as e:
    print(f"\n[ERREUR] {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
