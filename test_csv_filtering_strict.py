#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test du filtrage CSV strict - Vérifie que seul le mois courant est conservé
"""

import sys
from pathlib import Path
from datetime import datetime

# Ajouter le dossier parent au path pour les imports
sys.path.insert(0, str(Path(__file__).parent))

from linxo_agent.csv_filter import filter_csv_by_month, get_csv_date_range


def test_csv_filtering():
    """
    Test complet du filtrage CSV avec validation stricte
    """
    print("=" * 80)
    print("TEST DE FILTRAGE CSV STRICT")
    print("=" * 80)

    # Récupérer le dernier CSV téléchargé
    data_dir = Path(__file__).parent / "data"
    csv_file = data_dir / "latest.csv"

    if not csv_file.exists():
        print(f"[ERREUR] Fichier CSV introuvable: {csv_file}")
        print("[INFO] Telechargez d'abord un CSV depuis Linxo")
        return False

    print(f"\n[TEST 1] Analyse du fichier: {csv_file}")
    print(f"[INFO] Taille: {csv_file.stat().st_size} octets")

    # Obtenir la plage de dates AVANT filtrage
    print("\n[TEST 2] Plage de dates AVANT filtrage...")
    date_range = get_csv_date_range(csv_file)

    if not date_range:
        print("[ERREUR] Impossible de lire la plage de dates")
        return False

    min_date, max_date = date_range
    print(f"[OK] Periode: {min_date.strftime('%d/%m/%Y')} -> {max_date.strftime('%d/%m/%Y')}")

    # Compter les lignes AVANT
    with open(csv_file, 'r', encoding='utf-16') as f:
        lines_before = sum(1 for _ in f)
    print(f"[OK] Lignes AVANT filtrage: {lines_before}")

    # Vérifier si le fichier contient déjà uniquement le mois courant
    now = datetime.now()
    is_already_filtered = (
        min_date.year == now.year and min_date.month == now.month and
        max_date.year == now.year and max_date.month == now.month
    )

    if is_already_filtered:
        print(f"\n[INFO] Le CSV contient deja uniquement le mois courant ({now.month:02d}/{now.year})")
        print("[SUCCESS] Aucun filtrage necessaire")
        return True

    # Filtrer pour le mois courant
    print(f"\n[TEST 3] Filtrage pour le mois courant ({now.month:02d}/{now.year})...")

    # Créer une copie de sauvegarde
    backup_file = csv_file.parent / f"{csv_file.stem}_backup{csv_file.suffix}"
    import shutil
    shutil.copy2(csv_file, backup_file)
    print(f"[INFO] Sauvegarde creee: {backup_file}")

    # Filtrer
    filtered = filter_csv_by_month(csv_file)

    if not filtered:
        print("[ERREUR] Le filtrage a echoue!")
        print("[INFO] Restauration du fichier original...")
        shutil.move(str(backup_file), str(csv_file))
        return False

    print("[OK] Filtrage reussi")

    # Compter les lignes APRES
    with open(csv_file, 'r', encoding='utf-16') as f:
        lines_after = sum(1 for _ in f)
    print(f"[OK] Lignes APRES filtrage: {lines_after}")

    # Vérifier la plage de dates APRES
    print("\n[TEST 4] Validation de la plage de dates APRES filtrage...")
    date_range_after = get_csv_date_range(csv_file)

    if not date_range_after:
        print("[ERREUR] Impossible de lire la plage de dates apres filtrage")
        print("[INFO] Restauration du fichier original...")
        shutil.move(str(backup_file), str(csv_file))
        return False

    min_date_after, max_date_after = date_range_after
    print(f"[OK] Periode: {min_date_after.strftime('%d/%m/%Y')} -> {max_date_after.strftime('%d/%m/%Y')}")

    # VALIDATION STRICTE
    print("\n[TEST 5] Validation stricte du mois...")

    if min_date_after.year != now.year or min_date_after.month != now.month:
        print(f"[ERREUR] Date minimum hors du mois courant: {min_date_after.strftime('%d/%m/%Y')}")
        print(f"[ERREUR] Mois attendu: {now.month:02d}/{now.year}")
        print("[INFO] Restauration du fichier original...")
        shutil.move(str(backup_file), str(csv_file))
        return False

    if max_date_after.year != now.year or max_date_after.month != now.month:
        print(f"[ERREUR] Date maximum hors du mois courant: {max_date_after.strftime('%d/%m/%Y')}")
        print(f"[ERREUR] Mois attendu: {now.month:02d}/{now.year}")
        print("[INFO] Restauration du fichier original...")
        shutil.move(str(backup_file), str(csv_file))
        return False

    print(f"[VALIDATION OK] Toutes les dates sont du mois courant ({now.month:02d}/{now.year})")

    # Afficher le résumé
    print("\n" + "=" * 80)
    print("RESUME DU TEST")
    print("=" * 80)
    print(f"Lignes avant: {lines_before}")
    print(f"Lignes apres: {lines_after}")
    print(f"Reduction: {lines_before - lines_after} lignes")
    print(f"Periode avant: {min_date.strftime('%d/%m/%Y')} -> {max_date.strftime('%d/%m/%Y')}")
    print(f"Periode apres: {min_date_after.strftime('%d/%m/%Y')} -> {max_date_after.strftime('%d/%m/%Y')}")
    print("=" * 80)

    # Supprimer le backup si tout s'est bien passé
    if backup_file.exists():
        backup_file.unlink()
        print("\n[CLEANUP] Sauvegarde supprimee")

    print("\n[SUCCESS] Test reussi!")
    return True


if __name__ == "__main__":
    success = test_csv_filtering()
    sys.exit(0 if success else 1)
