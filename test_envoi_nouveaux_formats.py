#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test d'envoi RÉEL avec les nouveaux formats épurés
Destinataires limités: phiperez@gmail.com et +33626267421
"""

import sys
from pathlib import Path

# Ajouter le chemin du module linxo_agent
sys.path.insert(0, str(Path(__file__).parent / 'linxo_agent'))

from analyzer import analyser_csv, generer_conseil_budget
from notifications import NotificationManager
from report_formatter_v2 import formater_email_html_v2, formater_sms_v2
from config import get_config
from datetime import datetime


def test_envoi_complet():
    """
    Teste l'envoi complet (email HTML + SMS) avec les nouveaux formats
    """
    print("\n" + "=" * 80)
    print("TEST D'ENVOI RÉEL - NOUVEAUX FORMATS")
    print("=" * 80)
    print("\n[AVERTISSEMENT] Ce script va envoyer RÉELLEMENT:")
    print("  - 1 Email HTML à: phiperez@gmail.com")
    print("  - 1 SMS à: +33626267421")
    print("\n" + "=" * 80)

    # Demander confirmation
    response = input("\nConfirmez-vous l'envoi ? (oui/non): ")
    if response.lower() not in ['oui', 'o', 'yes', 'y']:
        print("\n[ANNULÉ] Envoi annulé.")
        return

    print("\n[INFO] Analyse en cours...")

    # Analyser les données
    config = get_config()
    analysis_result = analyser_csv()

    if not analysis_result:
        print("[ERREUR] Impossible d'analyser le fichier CSV")
        return

    # Extraire les données
    total_depenses = analysis_result.get('total_variables', 0)
    budget_max = analysis_result.get('budget_max', config.budget_variable)
    reste = budget_max - total_depenses
    pourcentage = (total_depenses / budget_max * 100) if budget_max > 0 else 0

    print(f"\n[ANALYSE] Résultats:")
    print(f"  - Dépenses variables: {total_depenses:.2f}€")
    print(f"  - Budget: {budget_max:.2f}€")
    print(f"  - Reste: {reste:.2f}€")
    print(f"  - Pourcentage: {pourcentage:.1f}%")

    # Générer le conseil
    conseil = generer_conseil_budget(total_depenses, budget_max)

    # ========================================================================
    # ENVOI SMS
    # ========================================================================
    print("\n" + "=" * 80)
    print("[SMS] PRÉPARATION DU SMS")
    print("=" * 80)

    sms_msg = formater_sms_v2(total_depenses, budget_max, reste, pourcentage)
    phone = "+33626267421"

    print(f"\nDestinataire: {phone}")
    print(f"Longueur: {len(sms_msg)} caractères")
    print("\nContenu:")
    print("-" * 40)
    # Afficher le contenu sans emojis pour éviter les erreurs d'encodage
    print("[Message SMS avec emojis - voir apercu_sms.txt]")
    print("-" * 40)

    notif_manager = NotificationManager()

    print("\n[SMS] Envoi en cours...")
    sms_results = notif_manager.send_sms_ovh(sms_msg, recipients=[phone])

    if sms_results.get(phone):
        print(f"[SUCCESS] SMS envoyé avec succès à {phone}")
    else:
        print(f"[ERREUR] Échec de l'envoi du SMS")

    # ========================================================================
    # ENVOI EMAIL HTML
    # ========================================================================
    print("\n" + "=" * 80)
    print("[EMAIL] PRÉPARATION DE L'EMAIL HTML")
    print("=" * 80)

    email_html = formater_email_html_v2(analysis_result, budget_max, conseil)
    email_recipient = "phiperez@gmail.com"
    csv_path = analysis_result.get('csv_path')

    # Sujet de l'email
    if reste < 0:
        email_subject = f"ALERTE Budget - Dépassement de {abs(reste):.0f}€"
    elif pourcentage >= 80:
        email_subject = f"Budget à {pourcentage:.0f}% - Attention"
    else:
        email_subject = f"Rapport Budget - {datetime.now().strftime('%d/%m/%Y')}"

    print(f"\nDestinataire: {email_recipient}")
    print(f"Sujet: {email_subject}")
    print(f"Format: HTML épuré (style moderne)")
    print(f"Taille: {len(email_html)} caractères")
    if csv_path and Path(csv_path).exists():
        print(f"Pièce jointe: {Path(csv_path).name}")

    print("\n[EMAIL] Envoi en cours...")
    email_success = notif_manager.send_email(
        subject=email_subject,
        body=email_html,
        recipients=[email_recipient],
        attachment_path=csv_path,
        is_html=True
    )

    if email_success:
        print(f"[SUCCESS] Email envoyé avec succès à {email_recipient}")
    else:
        print(f"[ERREUR] Échec de l'envoi de l'email")

    # ========================================================================
    # RÉSUMÉ
    # ========================================================================
    print("\n" + "=" * 80)
    print("RÉSUMÉ DE L'ENVOI")
    print("=" * 80)

    total_succes = 0
    total_echecs = 0

    print("\n[SMS]")
    if sms_results.get(phone):
        print(f"  ✓ Envoyé à {phone}")
        total_succes += 1
    else:
        print(f"  ✗ Échec pour {phone}")
        total_echecs += 1

    print("\n[EMAIL]")
    if email_success:
        print(f"  ✓ Envoyé à {email_recipient}")
        total_succes += 1
    else:
        print(f"  ✗ Échec pour {email_recipient}")
        total_echecs += 1

    print("\n" + "-" * 80)
    print(f"Total: {total_succes} succès, {total_echecs} échec(s)")
    print("=" * 80)

    if total_succes == 2:
        print("\n[SUCCESS] Tous les envois ont réussi!")
        print("\nVérifiez:")
        print("  - Votre boîte mail: phiperez@gmail.com")
        print("  - Votre téléphone: +33626267421")
    elif total_succes > 0:
        print("\n[PARTIEL] Certains envois ont réussi, d'autres ont échoué.")
    else:
        print("\n[ERREUR] Tous les envois ont échoué.")
        print("Vérifiez votre configuration (SMTP, OVH SMS)")


if __name__ == "__main__":
    test_envoi_complet()
