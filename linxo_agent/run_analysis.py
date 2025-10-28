#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Linxo Analysis Runner - Version moderne avec emails HTML
Utilise le système d'analyse moderne avec notifications HTML épurées
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# Add the linxo_agent directory to path
linxo_agent_dir = Path(__file__).parent
sys.path.insert(0, str(linxo_agent_dir))

# Import des modules modernes
from analyzer import analyser_csv
from notifications import NotificationManager
from config import get_config

def main():
    """Exécute l'analyse avec notifications modernes (emails HTML)"""
    print("\n" + "=" * 80)
    print("LINXO AGENT - ANALYSE AVEC NOTIFICATIONS HTML")
    print("=" * 80)
    print(f"Demarrage: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    # Charger la configuration
    config = get_config()

    # Determiner le fichier CSV a utiliser
    if len(sys.argv) > 1:
        # Custom CSV file provided
        csv_file = sys.argv[1]
        if not os.path.exists(csv_file):
            print(f"ERREUR: Le fichier {csv_file} n'existe pas")
            sys.exit(1)
        print(f"Utilisation du fichier: {csv_file}")
    else:
        # Use default CSV file
        csv_file = config.get_latest_csv()
        print(f"Utilisation du dernier CSV: {csv_file}")

    # ETAPE 1: Analyse des depenses
    print("\n" + "=" * 80)
    print("ETAPE 1: ANALYSE DES DEPENSES")
    print("=" * 80)

    try:
        analysis_result = analyser_csv(csv_file)

        if not analysis_result:
            print("ERREUR: Echec de l'analyse")
            sys.exit(1)

        print("\nAnalyse terminee!")
        print(f"  Transactions: {analysis_result['total_transactions']}")
        print(f"  Depenses fixes: {analysis_result['total_fixes']:.2f}E")
        print(f"  Depenses variables: {analysis_result['total_variables']:.2f}E")
        print(f"  Budget: {analysis_result['budget_max']:.2f}E")
        print(f"  Reste: {analysis_result['reste']:.2f}E")

        # Afficher le rapport texte
        print("\n" + analysis_result['rapport'])

    except Exception as e:
        print(f"ERREUR durant l'analyse: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # ETAPE 2: Envoi des notifications (email HTML + SMS)
    print("\n" + "=" * 80)
    print("ETAPE 2: ENVOI DES NOTIFICATIONS (EMAIL HTML + SMS)")
    print("=" * 80)

    try:
        notification_manager = NotificationManager()
        notif_results = notification_manager.send_budget_notification(analysis_result)

        # Verifier les resultats
        sms_results = notif_results.get('sms', {})
        sms_ok = any(sms_results.values())
        email_ok = notif_results.get('email', False)

        if sms_ok or email_ok:
            print("\nNotifications envoyees!")
            print(f"  Email HTML: {'OK' if email_ok else 'ECHEC'}")
            sms_sent = sum(sms_results.values())
            print(f"  SMS: {sms_sent} / {len(sms_results)}")
        else:
            print("WARNING: Aucune notification n'a pu etre envoyee")

    except Exception as e:
        print(f"ERREUR durant l'envoi des notifications: {e}")
        import traceback
        traceback.print_exc()
        # Ne pas quitter avec erreur, l'analyse a reussi

    # ETAPE 3: Sauvegarder le rapport
    print("\n" + "=" * 80)
    print("ETAPE 3: SAUVEGARDE DU RAPPORT")
    print("=" * 80)

    try:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        rapport_file = config.reports_dir / f"rapport_linxo_{timestamp}.txt"

        with open(rapport_file, 'w', encoding='utf-8') as f:
            f.write(analysis_result['rapport'])

        print(f"Rapport sauvegarde: {rapport_file}")

    except Exception as e:
        print(f"WARNING: Erreur lors de la sauvegarde du rapport: {e}")

    # RESUME FINAL
    print("\n" + "=" * 80)
    print("ANALYSE TERMINEE AVEC SUCCES")
    print("=" * 80)
    print(f"Fin: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

if __name__ == "__main__":
    main()
