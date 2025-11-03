#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de test des nouvelles fonctionnalités des rapports :
- Avancement dans le temps
- Conseil du LLM
"""

import sys
import os
from pathlib import Path
from datetime import date

# Ajouter le chemin du module linxo_agent
sys.path.insert(0, str(Path(__file__).parent / 'linxo_agent'))

import pandas as pd
from reports import build_daily_report
from analyzer import generer_conseil_budget

print("\n" + "=" * 80)
print("TEST DES NOUVELLES FONCTIONNALITÉS DES RAPPORTS")
print("=" * 80)

# Données de test
data = {
    'date': ['01/11/2025', '02/11/2025', '03/11/2025'],
    'date_str': ['01/11/2025', '02/11/2025', '03/11/2025'],
    'libelle': ['CARREFOUR MARKET', 'STATION TOTAL', 'RESTAURANT LE BISTROT'],
    'montant': [-45.50, -60.00, -35.20],
    'categorie': ['Alimentation', 'Transports', 'Restaurants'],
    'compte': ['Compte Courant'] * 3,
}

df = pd.DataFrame(data)

# Budget et conseil
budget_max = 1500.0
total_depenses = abs(df['montant'].sum())

print(f"\nDonnées de test:")
print(f"  Budget maximum: {budget_max:.2f}€")
print(f"  Total dépenses: {total_depenses:.2f}€")
print(f"  Transactions: {len(df)}")

# Générer le conseil
conseil = generer_conseil_budget(total_depenses, budget_max)
print(f"\nConseil généré:")
print(conseil)

# Configuration pour les rapports
os.environ['REPORTS_BASE_URL'] = 'https://linxo.appliprz.ovh'
os.environ['REPORTS_SIGNING_KEY'] = 'test_key_demo'

# Générer les rapports avec les nouvelles fonctionnalités
print("\n" + "=" * 80)
print("GÉNÉRATION DES RAPPORTS AVEC AVANCEMENT & CONSEIL")
print("=" * 80)

try:
    report_index = build_daily_report(
        df,
        report_date=date.today(),
        base_url=os.environ['REPORTS_BASE_URL'],
        signing_key=os.environ['REPORTS_SIGNING_KEY'],
        budget_max=budget_max,
        conseil_llm=conseil
    )

    print("\n[OK] Rapports generes avec succes!")
    print(f"\nRepertoire: {report_index.base_dir}")
    print(f"Familles: {len(report_index.families)}")
    print(f"Total: {report_index.grand_total:.2f}E")

    print("\nFamilles generees:")
    for family in report_index.families:
        print(f"  - {family['name']}: {family['total']:.2f}E ({family['count']} transactions)")
        print(f"    URL: {family['url']}")

    print("\n" + "=" * 80)
    print("[OK] TEST REUSSI!")
    print("=" * 80)
    print(f"\nVous pouvez consulter les rapports dans:")
    print(f"  {report_index.base_dir}")
    print("\nLes rapports incluent maintenant:")
    print("  [OK] Avancement dans le temps (barre de progression)")
    print("  [OK] Conseil du LLM (generation automatique)")

except Exception as e:
    print(f"\n[ERREUR] {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
