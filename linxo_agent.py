#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Linxo Agent - Point d'entrée principal
Version 2.0 - Architecture unifiée et multi-environnement

Ce script orchestre l'ensemble du processus:
1. Connexion à Linxo
2. Téléchargement du CSV
3. Analyse des dépenses
4. Envoi des notifications (email + SMS)
"""

import argparse
import sys
import traceback
import shutil
from csv import Error as CsvError
from datetime import datetime
from pathlib import Path
from smtplib import SMTPException
from contextlib import suppress
from selenium.common.exceptions import TimeoutException, WebDriverException

# Imports des modules refactorisés
from linxo_agent.config import get_config
from linxo_agent.linxo_driver_factory import (
    initialiser_driver_linxo,
    se_connecter_linxo,
    telecharger_csv_linxo
)
from linxo_agent.analyzer import analyser_csv
from linxo_agent.notifications import NotificationManager

DOWNLOAD_ERRORS = (
    OSError,
    ConnectionError,
    TimeoutError,
    TimeoutException,
    WebDriverException,
    RuntimeError,
)

ANALYSIS_ERRORS = (
    OSError,
    ValueError,
    CsvError,
    RuntimeError,
)

NOTIFICATION_ERRORS = (
    SMTPException,
    ConnectionError,
    OSError,
    RuntimeError,
    ValueError,
)

GENERAL_WORKFLOW_ERRORS = DOWNLOAD_ERRORS + ANALYSIS_ERRORS + NOTIFICATION_ERRORS
QUIT_ERRORS = (AttributeError, OSError, RuntimeError, WebDriverException)

def run_full_workflow(skip_download=False, skip_notifications=False, csv_file=None):
    """
    Exécute le workflow complet de l'agent Linxo

    Args:
        skip_download: Si True, saute le téléchargement et utilise le dernier CSV
        skip_notifications: Si True, saute l'envoi des notifications
        csv_file: Chemin vers un fichier CSV spécifique à analyser

    Returns:
        dict: Résultats de l'exécution
    """
    print("\n" + "=" * 80)
    print("LINXO AGENT - WORKFLOW COMPLET")
    print("=" * 80)
    print(f"Demarrage: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    results = {
        'download_success': False,
        'analysis_success': False,
        'notification_success': False,
        'csv_path': None,
        'analysis_result': None
    }

    # Charger la configuration
    config = get_config()
    config.print_summary()

    driver = None
    user_data_dir = None
    analysis_result = None

    try:
        # ÉTAPE 1: Téléchargement du CSV
        if not skip_download and csv_file is None:
            print("\n" + "=" * 80)
            print("ETAPE 1: TELECHARGEMENT CSV DEPUIS LINXO")
            print("=" * 80)

            try:
                # Initialiser le navigateur (retourne maintenant driver, wait, user_data_dir)
                driver, wait, user_data_dir = initialiser_driver_linxo()

                # Se connecter à Linxo
                connexion_ok = se_connecter_linxo(driver, wait)

                if not connexion_ok:
                    print("[ERREUR] Echec de la connexion a Linxo")
                    return results

                # Télécharger le CSV
                csv_path = telecharger_csv_linxo(driver, wait)

                if csv_path and Path(csv_path).exists():
                    print(f"[SUCCESS] CSV telecharge: {csv_path}")
                    results['download_success'] = True
                    results['csv_path'] = str(csv_path)
                else:
                    print("[ERREUR] Echec du telechargement du CSV")
                    return results

            except DOWNLOAD_ERRORS as error:
                print(f"[ERREUR] Erreur durant le telechargement: {error}")
                traceback.print_exc()
                return results

            finally:
                # Fermer le navigateur sans attraper trop large
                if driver:
                    with suppress(*QUIT_ERRORS):
                        driver.quit()
                    print("[INFO] Navigateur ferme")

                # Cleanup du répertoire user-data temporaire
                if user_data_dir and user_data_dir.exists():
                    try:
                        shutil.rmtree(user_data_dir, ignore_errors=True)
                        print(
                            f"[CLEANUP] Repertoire temporaire supprime: "
                            f"{user_data_dir.name}"
                        )
                    except (OSError, PermissionError) as cleanup_error:
                        print(
                            f"[WARN] Impossible de supprimer le "
                            f"repertoire temporaire: {cleanup_error}"
                        )

        else:
            if csv_file:
                print(f"\n[INFO] Utilisation du fichier CSV fourni: {csv_file}")
                results['csv_path'] = csv_file
            else:
                print(
                    "\n[INFO] Telechargement saute, "
                    "utilisation du dernier CSV disponible"
                )
                results['csv_path'] = str(config.get_latest_csv())

            results['download_success'] = True

        # ÉTAPE 2: Analyse des dépenses
        print("\n" + "=" * 80)
        print("ETAPE 2: ANALYSE DES DEPENSES")
        print("=" * 80)

        try:
            analysis_result = analyser_csv(results['csv_path'])

            if analysis_result:
                print("\n[SUCCESS] Analyse terminee!")
                print(f"  Transactions: {analysis_result['total_transactions']}")
                print(f"  Depenses variables: {analysis_result['total_variables']:.2f}E")
                print(f"  Budget: {analysis_result['budget_max']:.2f}E")
                print(f"  Reste: {analysis_result['reste']:.2f}E")

                results['analysis_success'] = True
                results['analysis_result'] = analysis_result

                # Afficher le rapport
                print("\n" + analysis_result['rapport'])

            else:
                print("[ERREUR] Echec de l'analyse")
                return results

        except ANALYSIS_ERRORS as error:
            print(f"[ERREUR] Erreur durant l'analyse: {error}")
            traceback.print_exc()
            return results

        # ÉTAPE 2.5: Génération des rapports HTML
        print("\n" + "=" * 80)
        print("ETAPE 2.5: GENERATION DES RAPPORTS HTML")
        print("=" * 80)

        report_index = None
        try:
            import pandas as pd
            import os
            from linxo_agent.reports import build_daily_report

            # Vérifier que REPORTS_BASE_URL est configuré
            base_url = os.getenv('REPORTS_BASE_URL')
            if not base_url:
                print("[WARNING] REPORTS_BASE_URL non configure, rapports HTML desactives")
                print("[INFO] Definissez REPORTS_BASE_URL dans .env pour activer les rapports")
            else:
                # Convertir les données en DataFrame
                all_transactions = (
                    analysis_result.get('depenses_fixes', []) +
                    analysis_result.get('depenses_variables', [])
                )

                if all_transactions:
                    # Créer le DataFrame
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
                    signing_key = os.getenv('REPORTS_SIGNING_KEY')
                    report_index = build_daily_report(
                        df,
                        report_date=None,  # Aujourd'hui par défaut
                        base_url=base_url,
                        signing_key=signing_key
                    )

                    print(f"[SUCCESS] Rapports HTML generes dans {report_index.base_dir}")
                    print(f"  - {len(report_index.families)} familles de depenses")
                    print(f"  - Total: {report_index.grand_total:.2f}E")
                else:
                    print("[WARNING] Aucune transaction a reporter")

        except ValueError as ve:
            # Erreur de configuration (REPORTS_BASE_URL manquant)
            print(f"[WARNING] {ve}")
            print("[INFO] Les notifications utiliseront le format classique")
        except ImportError as ie:
            print(f"[WARNING] Impossible de generer les rapports HTML: {ie}")
            print("[INFO] Installez les dependances: pip install pandas jinja2")
        except Exception as e:
            print(f"[WARNING] Erreur lors de la generation des rapports HTML: {e}")
            print("[INFO] Les notifications utiliseront le format classique")
            traceback.print_exc()

        # ÉTAPE 3: Envoi des notifications
        if not skip_notifications:
            print("\n" + "=" * 80)
            print("ETAPE 3: ENVOI DES NOTIFICATIONS")
            print("=" * 80)

            try:
                notification_manager = NotificationManager()
                notif_results = notification_manager.send_budget_notification(
                    analysis_result,
                    report_index=report_index
                )

                # Vérifier les résultats
                sms_ok = notif_results.get('sms', False)
                email_ok = notif_results.get('email', False)

                if sms_ok or email_ok:
                    print("\n[SUCCESS] Notifications envoyees!")
                    print(f"  Email: {'OK' if email_ok else 'ECHEC'}")
                    print(f"  SMS: {'OK' if sms_ok else 'ECHEC'}")
                    results['notification_success'] = True
                else:
                    print("[WARNING] Aucune notification n'a pu etre envoyee")

            except NOTIFICATION_ERRORS as error:
                print(f"[ERREUR] Erreur durant l'envoi des notifications: {error}")
                traceback.print_exc()
            except ImportError:
                print("[ERREUR] Erreur inattendue durant l'envoi des notifications")
                traceback.print_exc()

        else:
            print("\n[INFO] Envoi des notifications saute")
            # Considéré comme succès car sauté volontairement
            results['notification_success'] = True

        # RÉSUMÉ FINAL
        print("\n" + "=" * 80)
        print("RESUME DE L'EXECUTION")
        print("=" * 80)
        print(f"Telechargement CSV: {'OK' if results['download_success'] else 'ECHEC'}")
        print(f"Analyse:            {'OK' if results['analysis_success'] else 'ECHEC'}")
        print(f"Notifications:      {'OK' if results['notification_success'] else 'ECHEC'}")
        print("=" * 80)

        # Sauvegarder le rapport
        if analysis_result:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            rapport_file = config.reports_dir / f"rapport_linxo_{timestamp}.txt"

            with open(rapport_file, 'w', encoding='utf-8') as f:
                f.write(analysis_result['rapport'])

            print(f"\nRapport sauvegarde: {rapport_file}")

        return results

    except KeyboardInterrupt:
        print("\n[INFO] Execution interrompue par l'utilisateur")
        if driver:
            try:
                driver.quit()
            except (AttributeError, OSError, RuntimeError, WebDriverException) as quit_error:
                print(f"[WARNING] Impossible de fermer le navigateur proprement: {quit_error}")
            except ImportError:
                print("[WARNING] Erreur inattendue lors de la fermeture")

        # Cleanup du répertoire user-data temporaire
        if user_data_dir and user_data_dir.exists():
            try:
                shutil.rmtree(user_data_dir, ignore_errors=True)
                print(
                    f"[CLEANUP] Repertoire temporaire supprime: "
                    f"{user_data_dir.name}"
                )
            except (OSError, PermissionError) as cleanup_error:
                print(
                    f"[WARN] Impossible de supprimer le "
                    f"repertoire temporaire: {cleanup_error}"
                )

        return results

    except GENERAL_WORKFLOW_ERRORS as error:
        print(f"\n[ERREUR FATALE] Erreur inattendue: {error}")
        traceback.print_exc()
        if driver:
            try:
                driver.quit()
            except (AttributeError, OSError, RuntimeError, WebDriverException) as quit_error:
                print(f"[WARNING] Impossible de fermer le navigateur proprement: {quit_error}")
            except ImportError:
                print("[WARNING] Erreur inattendue lors de la fermeture")

        # Cleanup du répertoire user-data temporaire
        if user_data_dir and user_data_dir.exists():
            try:
                shutil.rmtree(user_data_dir, ignore_errors=True)
                print(
                    f"[CLEANUP] Repertoire temporaire supprime: "
                    f"{user_data_dir.name}"
                )
            except (OSError, PermissionError) as cleanup_error:
                print(
                    f"[WARN] Impossible de supprimer le "
                    f"repertoire temporaire: {cleanup_error}"
                )

        return results

    except ImportError:
        print("\n[ERREUR FATALE] Erreur non gérée")
        traceback.print_exc()
        if driver:
            try:
                driver.quit()
            except ImportError:
                print("[WARNING] Erreur lors de la fermeture")

        # Cleanup du répertoire user-data temporaire
        if user_data_dir and user_data_dir.exists():
            try:
                shutil.rmtree(user_data_dir, ignore_errors=True)
                print(
                    f"[CLEANUP] Repertoire temporaire supprime: "
                    f"{user_data_dir.name}"
                )
            except (OSError, PermissionError) as cleanup_error:
                print(
                    f"[WARN] Impossible de supprimer le "
                    f"repertoire temporaire: {cleanup_error}"
                )

        return results


def main():
    """Point d'entrée principal avec gestion des arguments"""

    parser = argparse.ArgumentParser(
        description="Linxo Agent - Analyse automatique des depenses",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "\nExemples d'utilisation:\n\n"
            "  # Workflow complet (téléchargement + analyse + notifications)\n"
            "  python linxo_agent.py\n\n"
            "  # Analyser un CSV existant sans télécharger\n"
            "  python linxo_agent.py --skip-download\n\n"
            "  # Analyser un fichier CSV spécifique\n"
            "  python linxo_agent.py --csv-file /path/to/file.csv\n\n"
            "  # Analyser sans envoyer de notifications (test)\n"
            "  python linxo_agent.py --skip-notifications\n\n"
            "  # Analyser un CSV sans envoyer de notifications\n"
            "  python linxo_agent.py --csv-file data/export.csv --skip-notifications\n"
        )
    )
    parser.add_argument(
        '--skip-download',
        action='store_true',
        help=(
            "Sauter le telechargement et utiliser le dernier CSV disponible"
        )
    )

    parser.add_argument(
        '--skip-notifications',
        action='store_true',
        help="Sauter l'envoi des notifications (email et SMS)"
    )

    parser.add_argument(
        '--csv-file',
        type=str,
        help="Chemin vers un fichier CSV specifique a analyser"
    )

    parser.add_argument(
        '--config-check',
        action='store_true',
        help="Afficher la configuration et quitter"
    )

    args = parser.parse_args()

    # Mode vérification de configuration
    if args.config_check:
        config = get_config()
        config.print_summary()
        return 0

    # Exécuter le workflow
    results = run_full_workflow(
        skip_download=args.skip_download,
        skip_notifications=args.skip_notifications,
        csv_file=args.csv_file
    )

    # Code de sortie
    if results['analysis_success']:
        print("\n[SUCCESS] Execution terminee avec succes!")
        return 0
    else:
        print("\n[ERREUR] Execution terminee avec des erreurs")
        return 1


if __name__ == "__main__":
    sys.exit(main())
