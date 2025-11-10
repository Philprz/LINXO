#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module de filtrage des fichiers CSV téléchargés depuis Linxo
Permet de filtrer les transactions par période même si la sélection web échoue
"""

import csv
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict


def filter_csv_by_month(
    input_csv: Path,
    output_csv: Optional[Path] = None,
    year: Optional[int] = None,
    month: Optional[int] = None,
    date_column: str = "Date",
    date_format: str = "%d/%m/%Y"
) -> Optional[Path]:
    """
    Filtre un fichier CSV pour ne garder que les transactions d'un mois donné.

    Args:
        input_csv: Chemin du fichier CSV source
        output_csv: Chemin du fichier CSV de sortie (optionnel, sinon remplace input_csv)
        year: Année à filtrer (par défaut: année courante)
        month: Mois à filtrer (par défaut: mois courant)
        date_column: Nom de la colonne contenant la date
        date_format: Format de la date dans le CSV

    Returns:
        Path du fichier filtré, ou None en cas d'erreur
    """
    try:
        # Utiliser le mois/année courant par défaut
        now = datetime.now()
        year = year or now.year
        month = month or now.month

        print(f"[FILTER] Filtrage du CSV pour {month:02d}/{year}")
        print(f"[FILTER] Fichier source: {input_csv}")

        # Détecter automatiquement l'encodage et le délimiteur
        detected_encoding = None
        detected_delimiter = None

        # Essayer les encodages dans l'ordre le plus probable pour Linxo
        # UTF-16 est utilisé par Linxo, donc on le teste en premier
        encodings_to_try = ['utf-16', 'utf-16-le', 'utf-16-be', 'utf-8', 'latin-1', 'cp1252']
        delimiters_to_try = ['\t', ';', ',']

        for encoding in encodings_to_try:
            for delimiter in delimiters_to_try:
                try:
                    with open(input_csv, 'r', encoding=encoding) as f:
                        # Lire la première ligne pour vérifier l'encodage
                        first_line = f.readline()
                        if not first_line:
                            continue

                        # Revenir au début du fichier
                        f.seek(0)

                        test_reader = csv.DictReader(f, delimiter=delimiter)
                        fieldnames = test_reader.fieldnames

                        if fieldnames and date_column in fieldnames:
                            detected_encoding = encoding
                            detected_delimiter = delimiter
                            print(f"[FILTER] Detection reussie: encodage={encoding}, delimiteur={repr(delimiter)}")
                            break
                except Exception:
                    # Ignorer les erreurs d'encodage et continuer
                    continue
            if detected_encoding:
                break

        if not detected_encoding:
            print(f"[ERREUR] Impossible de detecter l'encodage du CSV")
            print(f"[DEBUG] Colonne recherchee: '{date_column}'")
            print(f"[DEBUG] Fichier: {input_csv}")
            return None

        # Lire le CSV avec l'encodage détecté
        fieldnames = None  # Sauvegarder les noms de colonnes
        with open(input_csv, 'r', encoding=detected_encoding) as f:
            reader = csv.DictReader(f, delimiter=detected_delimiter)

            # Vérifier que la colonne de date existe
            if date_column not in reader.fieldnames:
                print(f"[ERREUR] Colonne '{date_column}' non trouvée dans le CSV")
                print(f"[INFO] Colonnes disponibles: {', '.join(reader.fieldnames)}")
                return None

            # SAUVEGARDER les fieldnames AVANT de fermer le fichier
            fieldnames = reader.fieldnames

            # Filtrer les lignes
            filtered_rows = []
            total_rows = 0
            for row in reader:
                total_rows += 1
                try:
                    # Parser la date
                    date_str = row[date_column]
                    date_obj = datetime.strptime(date_str, date_format)

                    # Vérifier si la date correspond au mois/année
                    if date_obj.year == year and date_obj.month == month:
                        filtered_rows.append(row)
                except (ValueError, KeyError) as e:
                    # Ignorer les lignes avec des dates invalides
                    continue

        print(f"[FILTER] {len(filtered_rows)} transactions trouvées sur {total_rows} au total")

        # Si aucune transaction, ne pas créer de fichier
        if not filtered_rows:
            print(f"[WARNING] Aucune transaction pour {month:02d}/{year}")
            return None

        # Déterminer le fichier de sortie
        if output_csv is None:
            output_csv = input_csv.parent / f"filtered_{input_csv.name}"

        # Écrire le fichier filtré AVEC LE MÊME ENCODAGE ET DÉLIMITEUR
        with open(output_csv, 'w', encoding=detected_encoding, newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=detected_delimiter)
            writer.writeheader()
            writer.writerows(filtered_rows)

        print(f"[SUCCESS] Fichier filtré créé: {output_csv}")
        print(f"[INFO] Taille: {output_csv.stat().st_size} octets")

        # Si on a créé un nouveau fichier, remplacer l'original
        if output_csv != input_csv:
            import shutil
            shutil.move(str(output_csv), str(input_csv))
            print(f"[INFO] Fichier original remplacé par la version filtrée")

        return input_csv

    except Exception as e:
        print(f"[ERREUR] Erreur lors du filtrage: {e}")
        import traceback
        traceback.print_exc()
        return None


def get_csv_date_range(csv_path: Path, date_column: str = "Date", date_format: str = "%d/%m/%Y") -> Optional[tuple]:
    """
    Retourne la plage de dates dans un fichier CSV.

    Args:
        csv_path: Chemin du fichier CSV
        date_column: Nom de la colonne contenant la date
        date_format: Format de la date

    Returns:
        Tuple (date_min, date_max) ou None en cas d'erreur
    """
    try:
        # Détecter automatiquement l'encodage et le délimiteur
        detected_encoding = None
        detected_delimiter = None

        # Essayer les encodages dans l'ordre le plus probable pour Linxo
        encodings_to_try = ['utf-16', 'utf-16-le', 'utf-16-be', 'utf-8', 'latin-1', 'cp1252']
        delimiters_to_try = ['\t', ';', ',']

        for encoding in encodings_to_try:
            for delimiter in delimiters_to_try:
                try:
                    with open(csv_path, 'r', encoding=encoding) as f:
                        first_line = f.readline()
                        if not first_line:
                            continue
                        f.seek(0)

                        test_reader = csv.DictReader(f, delimiter=delimiter)
                        fieldnames = test_reader.fieldnames

                        if fieldnames and date_column in fieldnames:
                            detected_encoding = encoding
                            detected_delimiter = delimiter
                            break
                except Exception:
                    continue
            if detected_encoding:
                break

        if not detected_encoding:
            return None

        # Lire les dates avec l'encodage détecté
        dates = []
        with open(csv_path, 'r', encoding=detected_encoding) as f:
            reader = csv.DictReader(f, delimiter=detected_delimiter)

            if date_column not in reader.fieldnames:
                return None

            for row in reader:
                try:
                    date_str = row[date_column]
                    date_obj = datetime.strptime(date_str, date_format)
                    dates.append(date_obj)
                except (ValueError, KeyError):
                    continue

        if not dates:
            return None

        return min(dates), max(dates)

    except Exception:
        return None


# Fonction de test
if __name__ == "__main__":
    import sys
    from pathlib import Path

    print("=" * 80)
    print("TEST DU MODULE CSV_FILTER")
    print("=" * 80)

    # Test avec un fichier CSV
    if len(sys.argv) > 1:
        csv_path = Path(sys.argv[1])
        if csv_path.exists():
            print(f"\n[TEST] Analyse du fichier: {csv_path}")

            # Afficher la plage de dates
            date_range = get_csv_date_range(csv_path)
            if date_range:
                min_date, max_date = date_range
                print(f"[INFO] Plage de dates: {min_date.strftime('%d/%m/%Y')} -> {max_date.strftime('%d/%m/%Y')}")

            # Filtrer pour le mois courant
            filtered = filter_csv_by_month(csv_path)
            if filtered:
                print(f"\n[SUCCESS] Test réussi!")
            else:
                print(f"\n[ERREUR] Test échoué!")
        else:
            print(f"[ERREUR] Fichier non trouvé: {csv_path}")
    else:
        print("\nUsage: python csv_filter.py <chemin_vers_csv>")
