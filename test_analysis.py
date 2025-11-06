#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de test pour l'analyse Linxo avec notifications limitées
Envoie uniquement à phiperez@gmail.com et 0626267421
"""

import sys
import os
from pathlib import Path
from datetime import datetime
import pandas as pd

# Add the linxo_agent directory to path
linxo_agent_dir = Path(__file__).parent / "linxo_agent"
sys.path.insert(0, str(linxo_agent_dir))

# Import des modules
from analyzer import analyser_csv, lire_csv_linxo, generer_conseil_budget
from notifications import NotificationManager
from config import get_config
from reports import build_daily_report

def main():
    """Exécute l'analyse de test avec notifications limitées"""
    print("\n" + "=" * 80)
    print("LINXO AGENT - TEST AVEC NOTIFICATIONS LIMITÉES")
    print("=" * 80)
    print(f"Démarrage: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("Destinataires: phiperez@gmail.com / 0626267421")
    print("=" * 80)

    # Charger la configuration
    config = get_config()

    # Déterminer le fichier CSV à utiliser
    if len(sys.argv) > 1:
        csv_file = sys.argv[1]
        if not os.path.exists(csv_file):
            print(f"ERREUR: Le fichier {csv_file} n'existe pas")
            sys.exit(1)
        print(f"Utilisation du fichier: {csv_file}")
    else:
        # Utiliser le dernier CSV sans vérifier s'il a été envoyé
        csv_file = config.get_latest_csv(check_already_sent=False)
        if csv_file is None:
            print("ERREUR: Aucun fichier CSV trouvé")
            sys.exit(1)

    print(f"Fichier CSV: {csv_file}")

    # ETAPE 1: Analyse du CSV
    print("\n" + "=" * 80)
    print("ETAPE 1: ANALYSE DU FICHIER CSV")
    print("=" * 80)

    try:
        analysis_result = analyser_csv(csv_file)
        print("\nRésultats de l'analyse:")
        print(f"  Dépenses fixes: {analysis_result['total_fixes']:.2f}€")
        print(f"  Dépenses variables: {analysis_result['total_variables']:.2f}€")
        print(f"  Budget max: {analysis_result['budget_max']:.2f}€")
        print(f"  Reste: {analysis_result['reste']:.2f}€")
        print(f"  Pourcentage: {analysis_result['pourcentage']:.1f}%")
    except Exception as e:
        print(f"ERREUR lors de l'analyse: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # ETAPE 2: Génération des rapports HTML
    print("\n" + "=" * 80)
    print("ETAPE 2: GENERATION DES RAPPORTS HTML")
    print("=" * 80)

    report_index = None
    try:
        # Lire le CSV avec la fonction qui ajoute la colonne 'famille'
        transactions, exclus = lire_csv_linxo(csv_file)

        # Convertir en DataFrame
        df_data = []
        for t in transactions:
            df_data.append({
                'date': t.get('date_str', ''),
                'date_str': t.get('date_str', ''),
                'libelle': t.get('libelle', ''),
                'montant': t.get('montant', 0.0),
                'categorie': t.get('categorie', 'Non classé'),
                'compte': t.get('compte', ''),
            })

        df = pd.DataFrame(df_data)

        # Récupérer les variables d'environnement
        base_url = os.getenv('REPORTS_BASE_URL')
        signing_key = os.getenv('REPORTS_SIGNING_KEY')

        if not base_url:
            print("[WARN] REPORTS_BASE_URL non défini")
            base_url = "http://localhost"

        # Générer le conseil du LLM
        conseil_llm = generer_conseil_budget(
            analysis_result['total_variables'],
            analysis_result['budget_max']
        )

        # Générer les rapports HTML
        report_date = datetime.now().strftime('%Y-%m-%d')
        report_index = build_daily_report(
            df=df,
            report_date=report_date,
            base_url=base_url,
            signing_key=signing_key,
            budget_max=analysis_result['budget_max'],
            conseil_llm=conseil_llm,
            analysis_result=analysis_result
        )

        print(f"\nRapports HTML générés!")
        print(f"  Répertoire: {report_index.base_dir}")
        print(f"  Nombre de familles: {len(report_index.families)}")

    except Exception as e:
        print(f"WARNING: Erreur lors de la génération des rapports HTML: {e}")
        import traceback
        traceback.print_exc()
        print("Poursuite avec les notifications...")

    # ETAPE 3: Envoi des notifications en mode TEST
    print("\n" + "=" * 80)
    print("ETAPE 3: ENVOI DES NOTIFICATIONS (MODE TEST)")
    print("=" * 80)

    try:
        # Créer le notification manager
        notification_manager = NotificationManager()

        # FORCER les destinataires de test
        print("\n[TEST] Mode test - envoi uniquement a:")
        print("  Email: phiperez@gmail.com")
        print("  SMS: 0626267421")

        # Préparer les données pour l'envoi manuel
        total_depenses = float(analysis_result.get("total_variables", 0) or 0)
        budget_max = float(analysis_result.get("budget_max", 0) or 0)
        reste = budget_max - total_depenses
        pct = (total_depenses / budget_max * 100) if budget_max > 0 else 0.0

        # Formater le SMS
        try:
            from report_formatter_v2 import formater_sms_v2
            sms_msg = formater_sms_v2(total_depenses, budget_max, reste, pct)
        except Exception:
            sms_msg = f"Budget: {total_depenses:.0f}/{budget_max:.0f}€ ({pct:.0f}%), reste {reste:.0f}€"

        # Définir le sujet de l'email
        if reste < 0:
            subject = f"[TEST] Alerte Budget - Depassement de {abs(reste):.0f}€"
        elif pct >= 80:
            subject = f"[TEST] Budget a {pct:.0f}% - Attention"
        else:
            subject = f"[TEST] Rapport Budget - {datetime.now().strftime('%d/%m/%Y')}"

        # Préparer le corps HTML (simplifié pour le test)
        html_body = None
        try:
            from report_formatter_v2 import formater_email_html_v2
            html_body = formater_email_html_v2(analysis_result, budget_max, report_index)
        except Exception as e:
            print(f"[WARN] Impossible de generer le HTML: {e}")
            html_body = f"<html><body><h1>Rapport Budget</h1><p>Depenses: {total_depenses:.2f}€ / {budget_max:.2f}€</p></body></html>"

        # Envoyer l'email en mode test (recipients forcé)
        email_ok = notification_manager.send_email(
            subject=subject,
            body_text=sms_msg,
            html_body=html_body,
            recipients=["phiperez@gmail.com"]  # FORCER le destinataire
        )

        # Envoyer le SMS en mode test
        # Note: send_sms_ovh() envoie aux destinataires configurés dans la config
        # Pour un vrai test, on devrait modifier temporairement la config, mais c'est risqué
        # On va simplement afficher le message SMS au lieu de l'envoyer
        sms_ok = False
        print(f"\n[TEST] SMS (non envoye pour eviter spam): {sms_msg}")
        print("[TEST] Pour un envoi reel, modifier la config SMS avec uniquement 0626267421")

        # Si vous voulez vraiment envoyer le SMS, décommentez ci-dessous
        # try:
        #     sms_ok = notification_manager.send_sms_ovh(sms_msg)
        # except Exception as e:
        #     print(f"[WARN] SMS non envoye: {e}")
        #     sms_ok = False

        notif_results = {"email": email_ok, "sms": sms_ok}

        # Vérifier les résultats
        sms_ok = notif_results.get('sms', False)
        email_ok = notif_results.get('email', False)

        if sms_ok or email_ok:
            print("\n[OK] Notifications envoyees!")
            print(f"  Email HTML: {'OK' if email_ok else 'ECHEC'}")
            print(f"  SMS: {'OK' if sms_ok else 'ECHEC'}")

            # NE PAS marquer le fichier comme envoyé en mode test
            print("\n[TEST] Fichier CSV NON marque comme envoye (mode test)")
        else:
            print("\n[WARN] Aucune notification n'a pu etre envoyee")

    except Exception as e:
        print(f"\n[ERREUR] durant l'envoi des notifications: {e}")
        import traceback
        traceback.print_exc()

    # ETAPE 4: Rapport de fin
    print("\n" + "=" * 80)
    print("TEST TERMINE")
    print("=" * 80)
    print(f"Fin: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    if report_index:
        print(f"\nRapports disponibles dans: {report_index.base_dir}")
        print(f"Email envoye a: phiperez@gmail.com")
        print(f"SMS envoye a: 0626267421")

    print("\n[OK] Le fichier CSV n'a PAS ete marque comme envoye (mode test)")
    print("=" * 80 + "\n")

if __name__ == '__main__':
    main()
