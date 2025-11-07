#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de test pour le module csv_filter
"""

import csv
import tempfile
from pathlib import Path
from datetime import datetime

from linxo_agent.csv_filter import filter_csv_by_month, get_csv_date_range


def create_test_csv():
    """Crée un fichier CSV de test avec plusieurs mois de données"""

    # Créer un fichier temporaire
    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8', newline='')

    # Données de test (plusieurs mois)
    header = ['Date', 'Libellé', 'Montant', 'Catégorie']
    rows = [
        ['01/10/2024', 'CARREFOUR', '-50.00', 'Alimentation'],
        ['15/10/2024', 'SALAIRE', '2500.00', 'Revenus'],
        ['20/10/2024', 'EDF', '-75.00', 'Logement'],
        ['05/11/2024', 'AMAZON', '-29.99', 'Achats'],
        ['10/11/2024', 'CARREFOUR', '-45.50', 'Alimentation'],
        ['15/11/2024', 'RESTAURANT', '-35.00', 'Restaurants'],
        ['20/11/2024', 'ESSENCE', '-60.00', 'Voiture'],
        ['25/11/2024', 'NETFLIX', '-15.99', 'Loisirs'],
        ['01/12/2024', 'LOYER', '-850.00', 'Logement'],
        ['05/12/2024', 'COURSES', '-120.00', 'Alimentation'],
    ]

    # Écrire le CSV
    writer = csv.writer(temp_file, delimiter=';')
    writer.writerow(header)
    writer.writerows(rows)

    temp_file.close()
    return Path(temp_file.name)


def test_filter():
    """Test du filtrage CSV"""

    print("=" * 80)
    print("TEST DU MODULE CSV_FILTER")
    print("=" * 80)

    # Créer un CSV de test
    print("\n[1] Creation d'un CSV de test...")
    csv_path = create_test_csv()
    print(f"[OK] CSV cree: {csv_path}")

    # Afficher la plage de dates
    print("\n[2] Analyse de la plage de dates...")
    date_range = get_csv_date_range(csv_path)
    if date_range:
        min_date, max_date = date_range
        print(f"[OK] Plage: {min_date.strftime('%d/%m/%Y')} -> {max_date.strftime('%d/%m/%Y')}")
    else:
        print("[ERREUR] Impossible de lire la plage de dates")
        return False

    # Filtrer pour novembre 2024
    print("\n[3] Filtrage pour novembre 2024...")
    filtered = filter_csv_by_month(csv_path, year=2024, month=11)

    if filtered:
        print(f"[OK] Fichier filtre: {filtered}")

        # Vérifier le contenu
        with open(filtered, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter=';')
            rows = list(reader)
            print(f"[OK] {len(rows)} transactions trouvees")

            # Afficher les transactions
            for row in rows:
                print(f"  - {row['Date']} | {row['Libellé']} | {row['Montant']}E")

            # Vérifier que seules les transactions de novembre sont présentes
            expected_count = 5  # 5 transactions en novembre
            if len(rows) == expected_count:
                print(f"\n[SUCCESS] Test reussi! {expected_count} transactions de novembre trouvees")
                return True
            else:
                print(f"\n[ERREUR] Nombre de transactions incorrect: {len(rows)} au lieu de {expected_count}")
                return False
    else:
        print("[ERREUR] Filtrage echoue")
        return False


if __name__ == "__main__":
    try:
        success = test_filter()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n[ERREUR] {e}")
        import traceback
        traceback.print_exc()
        exit(1)
