#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test de validation stricte du CSV
Vérifie que le système détecte et rejette les CSV avec des dates hors du mois courant
"""

import sys
from pathlib import Path
from datetime import datetime
import pandas as pd

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent))

from linxo_agent.csv_filter import filter_csv_by_month


def test_csv_validation():
    """Test que la validation stricte fonctionne correctement"""

    print("=" * 80)
    print("TEST DE VALIDATION STRICTE DU CSV")
    print("=" * 80)

    # Test avec le CSV actuel
    csv_path = Path("data/latest.csv")

    if not csv_path.exists():
        print(f"[ERREUR] CSV non trouvé: {csv_path}")
        return False

    print(f"\n[TEST] Analyse du CSV: {csv_path}")
    print(f"[TEST] Date du fichier: {datetime.fromtimestamp(csv_path.stat().st_mtime)}")

    # Lire et analyser le CSV sans filtrage
    encodings = ['utf-16', 'utf-16-le', 'utf-8', 'latin-1']
    df = None
    detected_encoding = None

    for encoding in encodings:
        try:
            df = pd.read_csv(csv_path, encoding=encoding, sep='\t')
            detected_encoding = encoding
            print(f"[OK] Encodage détecté: {encoding}")
            break
        except:
            continue

    if df is None:
        print("[ERREUR] Impossible de lire le CSV")
        return False

    # Trouver la colonne de date
    date_column = None
    for col in ['Date', 'date', 'Date de valeur', 'Date comptable']:
        if col in df.columns:
            date_column = col
            break

    if not date_column:
        print(f"[ERREUR] Colonne de date non trouvée. Colonnes: {list(df.columns)}")
        return False

    print(f"[OK] Colonne date: {date_column}")

    # Analyser les dates
    df[date_column] = pd.to_datetime(df[date_column], format='%d/%m/%Y', errors='coerce')

    min_date = df[date_column].min()
    max_date = df[date_column].max()

    print(f"\n[INFO] Nombre de transactions: {len(df)}")
    print(f"[INFO] Date minimum: {min_date}")
    print(f"[INFO] Date maximum: {max_date}")

    # Vérifier le mois courant
    now = datetime.now()
    print(f"\n[INFO] Mois courant: {now.month}/{now.year}")

    current_month_mask = (df[date_column].dt.year == now.year) & (df[date_column].dt.month == now.month)
    transactions_mois_courant = current_month_mask.sum()
    transactions_hors_mois = (~current_month_mask).sum()

    print(f"[INFO] Transactions mois courant: {transactions_mois_courant}")
    print(f"[INFO] Transactions hors mois: {transactions_hors_mois}")

    # Test de validation stricte
    print("\n" + "=" * 80)
    print("TEST DE VALIDATION STRICTE")
    print("=" * 80)

    if min_date.year != now.year or min_date.month != now.month or max_date.year != now.year or max_date.month != now.month:
        print("[VALIDATION] ERREUR - Le CSV contient des dates HORS du mois courant")
        print(f"[VALIDATION] Attendu: {now.month}/{now.year}")
        print(f"[VALIDATION] Obtenu: {min_date.month}/{min_date.year} a {max_date.month}/{max_date.year}")
        print("\n[RESULTAT] OK - La validation stricte DOIT rejeter ce CSV")
        print("[RESULTAT] OK - Le systeme DOIT lancer le filtrage")

        # Test du filtrage
        print("\n" + "=" * 80)
        print("TEST DU FILTRAGE")
        print("=" * 80)

        try:
            output_path = Path("data/filtered_test.csv")
            filter_csv_by_month(str(csv_path), str(output_path), now.year, now.month)

            if output_path.exists():
                # Vérifier le CSV filtré
                df_filtered = None
                for encoding in encodings:
                    try:
                        df_filtered = pd.read_csv(output_path, encoding=encoding, sep='\t')
                        break
                    except:
                        continue

                if df_filtered is not None and len(df_filtered) > 0:
                    df_filtered[date_column] = pd.to_datetime(df_filtered[date_column], format='%d/%m/%Y', errors='coerce')
                    min_filtered = df_filtered[date_column].min()
                    max_filtered = df_filtered[date_column].max()

                    print(f"[FILTRAGE] OK - CSV filtre cree: {len(df_filtered)} transactions")
                    print(f"[FILTRAGE] Date min filtrée: {min_filtered}")
                    print(f"[FILTRAGE] Date max filtrée: {max_filtered}")

                    # Validation post-filtrage
                    if min_filtered.year == now.year and min_filtered.month == now.month and max_filtered.year == now.year and max_filtered.month == now.month:
                        print("[FILTRAGE] SUCCES - Le CSV filtre contient UNIQUEMENT le mois courant")
                        return True
                    else:
                        print("[FILTRAGE] ECHEC - Le CSV filtre contient encore des dates hors mois")
                        print("[FILTRAGE] Le systeme DOIT s'arreter et lancer le diagnostic")
                        return False
                else:
                    print("[FILTRAGE] WARNING - Aucune transaction apres filtrage")
                    print("[FILTRAGE] Le CSV d'origine ne contient aucune donnee du mois courant")
                    return False
            else:
                print("[ERREUR] Le filtrage n'a pas créé de fichier")
                return False

        except Exception as e:
            print(f"[ERREUR] Erreur durant le filtrage: {e}")
            import traceback
            traceback.print_exc()
            return False
    else:
        print("[VALIDATION] OK - Le CSV contient UNIQUEMENT des dates du mois courant")
        print("[RESULTAT] OK - La validation stricte ACCEPTE ce CSV")
        print("[RESULTAT] OK - Aucun filtrage necessaire")
        return True


if __name__ == "__main__":
    success = test_csv_validation()

    print("\n" + "=" * 80)
    print("RESULTAT FINAL")
    print("=" * 80)

    if success:
        print("OK - Le systeme de validation fonctionne correctement")
        sys.exit(0)
    else:
        print("ERREUR - Des problemes ont ete detectes")
        sys.exit(1)
