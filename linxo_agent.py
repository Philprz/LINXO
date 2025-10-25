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

import sys
import argparse
import traceback
from pathlib import Path
from datetime import datetime

# Imports des modules refactorisés
from linxo_agent.config import get_config
from linxo_agent.linxo_connexion import (
    initialiser_driver_linxo,
    se_connecter_linxo,
    telecharger_csv_linxo,
)
from linxo_agent.analyzer import analyser_csv
from linxo_agent.notifications import NotificationManager


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
    analysis_result = None

    try:
        # ÉTAPE 1: Téléchargement du CSV
        if not skip_download and csv_file is None:
            print("\n" + "=" * 80)
            print("ETAPE 1: TELECHARGEMENT CSV DEPUIS LINXO")
            print("=" * 80)

            try:
                # Initialiser le navigateur
                driver, wait = initialiser_driver_linxo()

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

            except Exception as e:
                print(f"[ERREUR] Erreur durant le telechargement: {e}")
                traceback.print_exc()
                return results

            finally:
                # Fermer le navigateur
                if driver:
                    try:
                        driver.quit()
                        print("[INFO] Navigateur ferme")
                    except Exception:
                        pass

        else:
            if csv_file:
                print(f"\n[INFO] Utilisation du fichier CSV fourni: {csv_file}")
                results['csv_path'] = csv_file
            else:
                print("\n[INFO] Telechargement saute, utilisation du dernier CSV disponible")
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

        except Exception as e:
            print(f"[ERREUR] Erreur durant l'analyse: {e}")
            traceback.print_exc()
            return results

        # ÉTAPE 3: Envoi des notifications
        if not skip_notifications:
            print("\n" + "=" * 80)
            print("ETAPE 3: ENVOI DES NOTIFICATIONS")
            print("=" * 80)

            try:
                notification_manager = NotificationManager()
                notif_results = notification_manager.send_budget_notification(analysis_result)

                # Vérifier les résultats
                sms_results = notif_results.get('sms', {})
                sms_ok = any(sms_results.values())
                email_ok = notif_results.get('email', False)

                if sms_ok or email_ok:
                    print("\n[SUCCESS] Notifications envoyees!")
                    print(f"  Email: {'OK' if email_ok else 'ECHEC'}")
                    sms_sent = sum(sms_results.values())
                    print(f"  SMS: {sms_sent} / {len(sms_results)}")
                    results['notification_success'] = True
                else:
                    print("[WARNING] Aucune notification n'a pu etre envoyee")

            except Exception as e:
                print(f"[ERREUR] Erreur durant l'envoi des notifications: {e}")
                traceback.print_exc()

        else:
            print("\n[INFO] Envoi des notifications saute")
            results['notification_success'] = True  # Considéré comme succès car sauté volontairement

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
            except Exception:
                pass
        return results

    except Exception as e:
        print(f"\n[ERREUR FATALE] Erreur inattendue: {e}")
        traceback.print_exc()
        if driver:
            try:
                driver.quit()
            except Exception:
                pass
        return results


def main():
    """Point d'entrée principal avec gestion des arguments"""

    parser = argparse.ArgumentParser(
        description="Linxo Agent - Analyse automatique des depenses",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples d'utilisation:

  # Workflow complet (téléchargement + analyse + notifications)
  python linxo_agent.py

  # Analyser un CSV existant sans télécharger
  python linxo_agent.py --skip-download

  # Analyser un fichier CSV spécifique
  python linxo_agent.py --csv-file /path/to/file.csv

  # Analyser sans envoyer de notifications (test)
  python linxo_agent.py --skip-notifications

  # Analyser un CSV sans envoyer de notifications
  python linxo_agent.py --csv-file data/export.csv --skip-notifications
        """
    )

    parser.add_argument(
        '--skip-download',
        action='store_true',
        help="Sauter le telechargement et utiliser le dernier CSV disponible"
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
