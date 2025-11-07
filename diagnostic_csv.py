#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de diagnostic pour vérifier si le filtrage CSV est appliqué
"""

import csv
import sys
from pathlib import Path
from datetime import datetime
from collections import Counter

def diagnostiquer_csv(csv_path):
    """Diagnostique le contenu d'un fichier CSV Linxo"""

    print("=" * 80)
    print("DIAGNOSTIC DU FICHIER CSV")
    print("=" * 80)
    print(f"Fichier: {csv_path}")
    print(f"Taille: {Path(csv_path).stat().st_size} octets")
    print()

    # Lire toutes les transactions
    transactions = []
    dates = []
    montants_depenses = []

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter=';')

        print("Colonnes disponibles:")
        for i, col in enumerate(reader.fieldnames, 1):
            print(f"  {i}. {col}")
        print()

        for row in reader:
            transactions.append(row)

            # Parser la date
            try:
                date_str = row.get('Date', '')
                if date_str:
                    date_obj = datetime.strptime(date_str, '%d/%m/%Y')
                    dates.append(date_obj)

                    # Analyser les montants (dépenses uniquement)
                    montant_str = row.get('Montant', '0').replace(',', '.')
                    try:
                        montant = float(montant_str)
                        if montant < 0:  # Dépense
                            montants_depenses.append(abs(montant))
                    except ValueError:
                        pass

            except (ValueError, KeyError):
                pass

    print(f"Nombre total de transactions: {len(transactions)}")
    print()

    if dates:
        min_date = min(dates)
        max_date = max(dates)

        print("PLAGE DE DATES:")
        print(f"  Plus ancienne: {min_date.strftime('%d/%m/%Y')}")
        print(f"  Plus récente:  {max_date.strftime('%d/%m/%Y')}")
        print(f"  Période:       {(max_date - min_date).days} jours")
        print()

        # Compter les transactions par mois
        mois_counter = Counter((d.year, d.month) for d in dates)

        print("RÉPARTITION PAR MOIS:")
        for (annee, mois), count in sorted(mois_counter.items()):
            mois_nom = datetime(annee, mois, 1).strftime('%B %Y')
            print(f"  {mois_nom}: {count} transactions")
        print()

        # Vérifier si filtré sur le mois courant
        now = datetime.now()
        mois_courant = (now.year, now.month)

        if len(mois_counter) == 1 and mois_courant in mois_counter:
            print(f"✅ FILTRE APPLIQUÉ: Le CSV contient uniquement {mois_counter[mois_courant]} transactions du mois courant ({now.strftime('%B %Y')})")
        elif len(mois_counter) > 1:
            print(f"❌ FILTRE NON APPLIQUÉ: Le CSV contient {len(mois_counter)} mois différents!")
            print(f"   Il devrait contenir uniquement le mois courant ({now.strftime('%B %Y')})")
        else:
            print(f"⚠️  Le CSV est filtré, mais pas sur le mois courant!")
            seul_mois = list(mois_counter.keys())[0]
            print(f"   Mois dans le CSV: {datetime(seul_mois[0], seul_mois[1], 1).strftime('%B %Y')}")
            print(f"   Mois attendu: {now.strftime('%B %Y')}")
        print()

    if montants_depenses:
        total_depenses = sum(montants_depenses)
        print("MONTANTS DES DÉPENSES:")
        print(f"  Total: {total_depenses:,.2f} €")
        print(f"  Nombre: {len(montants_depenses)}")
        print(f"  Moyenne: {total_depenses / len(montants_depenses):,.2f} €")
        print()

        # Si le total est très élevé (> 100 000€), c'est probablement historique
        if total_depenses > 100000:
            print(f"❌ ALERTE: Total de {total_depenses:,.2f} € suggère des données HISTORIQUES!")
            print(f"   Un mois normal devrait être < 10 000 €")
        else:
            print(f"✅ Total de {total_depenses:,.2f} € semble raisonnable pour un mois")
        print()

    print("=" * 80)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python diagnostic_csv.py <chemin_vers_csv>")
        print("\nExemple:")
        print("  python diagnostic_csv.py /home/linxo/LINXO/data/latest.csv")
        sys.exit(1)

    csv_path = sys.argv[1]
    if not Path(csv_path).exists():
        print(f"ERREUR: Fichier non trouvé: {csv_path}")
        sys.exit(1)

    diagnostiquer_csv(csv_path)
