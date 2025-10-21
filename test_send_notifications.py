#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de test d'envoi RÉEL des notifications (Email + SMS)
ATTENTION: Ce script envoie réellement les messages !
Limité à: phiperez@gmail.com et +33626267421
"""

import sys
from pathlib import Path
from datetime import datetime

# Ajouter le chemin du module linxo_agent
sys.path.insert(0, str(Path(__file__).parent / 'linxo_agent'))

from analyzer import analyser_csv
from notifications import NotificationManager
from config import get_config


def test_envoi_notifications():
    """
    Teste l'envoi RÉEL des notifications avec destinataires limités
    """
    print("\n" + "=" * 80)
    print("TEST D'ENVOI REEL DES NOTIFICATIONS LINXO")
    print("=" * 80)
    print("\n[AVERTISSEMENT] Ce script va envoyer REELLEMENT des notifications !")
    print("Destinataires limites pour ce test :")
    print("  - Email: phiperez@gmail.com")
    print("  - SMS:   +33626267421")
    print("\n" + "=" * 80)

    # Demander confirmation
    response = input("\nConfirmez-vous l'envoi des notifications ? (oui/non): ")
    if response.lower() not in ['oui', 'o', 'yes', 'y']:
        print("\n[ANNULE] Envoi des notifications annule.")
        return

    # Obtenir la configuration
    config = get_config()

    print(f"\n[INFO] Analyse du dernier fichier CSV...")

    # Analyser les transactions
    analysis_result = analyser_csv()

    if not analysis_result:
        print("[ERREUR] Impossible d'analyser le fichier CSV")
        return

    # Créer le gestionnaire de notifications
    notif_manager = NotificationManager()

    # Destinataires de test (limités)
    test_email = "phiperez@gmail.com"
    test_sms = "+33626267421"

    print("\n" + "=" * 80)
    print("ENVOI DES NOTIFICATIONS")
    print("=" * 80)

    # Extraire les données pour les notifications
    total_depenses = analysis_result.get('total_variables', 0)
    budget_max = analysis_result.get('budget_max', config.budget_variable)
    reste = budget_max - total_depenses
    pourcentage = (total_depenses / budget_max * 100) if budget_max > 0 else 0

    # Déterminer le statut
    if reste < 0:
        emoji = "[ROUGE]"
        statut = "ALERTE - BUDGET DEPASSE"
        alerte = True
    elif pourcentage >= 80:
        emoji = "[ORANGE]"
        statut = "ATTENTION"
        alerte = False
    else:
        emoji = "[VERT]"
        statut = "OK"
        alerte = False

    # ========================================================================
    # ENVOI DU SMS
    # ========================================================================
    print("\n[SMS] Preparation du SMS...")

    if alerte:
        sms_msg = f"[ALERTE BUDGET!]\n"
        sms_msg += f"Depense: {total_depenses:.0f}E / {budget_max:.0f}E\n"
        sms_msg += f"DEPASSEMENT: {abs(reste):.0f}E"
    elif emoji == "[ORANGE]":
        sms_msg = f"[ATTENTION Budget]\n"
        sms_msg += f"Depense: {total_depenses:.0f}E / {budget_max:.0f}E ({pourcentage:.0f}%)\n"
        sms_msg += f"Reste: {reste:.0f}E"
    else:
        sms_msg = f"[Budget OK]\n"
        sms_msg += f"Depense: {total_depenses:.0f}E / {budget_max:.0f}E ({pourcentage:.0f}%)\n"
        sms_msg += f"Reste: {reste:.0f}E"

    print(f"[SMS] Message: {sms_msg[:50]}...")
    print(f"[SMS] Destinataire: {test_sms}")

    # Envoyer le SMS
    sms_results = notif_manager.send_sms_ovh(sms_msg, recipients=[test_sms])

    if sms_results.get(test_sms):
        print(f"[SUCCESS] SMS envoye avec succes a {test_sms}")
    else:
        print(f"[ERREUR] Echec de l'envoi du SMS a {test_sms}")

    # ========================================================================
    # ENVOI DE L'EMAIL
    # ========================================================================
    print("\n[EMAIL] Preparation de l'email...")

    # Sujet de l'email
    if alerte:
        email_subject = f"{emoji} [ALERTE BUDGET] - Depassement de {abs(reste):.0f}E !"
    elif emoji == "[ORANGE]":
        email_subject = f"{emoji} [ATTENTION Budget] - {pourcentage:.0f}% utilise"
    else:
        email_subject = f"{emoji} [Budget OK] - Rapport Linxo {datetime.now().strftime('%d/%m/%Y')}"

    # Corps de l'email (utiliser le rapport complet)
    email_body = analysis_result.get('rapport', '')

    # Chemin du fichier CSV pour la pièce jointe
    csv_path = analysis_result.get('csv_path')

    print(f"[EMAIL] Sujet: {email_subject}")
    print(f"[EMAIL] Destinataire: {test_email}")
    if csv_path and Path(csv_path).exists():
        print(f"[EMAIL] Piece jointe: {Path(csv_path).name}")

    # Envoyer l'email
    email_success = notif_manager.send_email(
        subject=email_subject,
        body=email_body,
        recipients=[test_email],
        attachment_path=csv_path
    )

    if email_success:
        print(f"[SUCCESS] Email envoye avec succes a {test_email}")
    else:
        print(f"[ERREUR] Echec de l'envoi de l'email a {test_email}")

    # ========================================================================
    # RÉSUMÉ
    # ========================================================================
    print("\n" + "=" * 80)
    print("RESUME DE L'ENVOI")
    print("=" * 80)

    total_succes = 0
    total_echecs = 0

    if sms_results.get(test_sms):
        print(f"[OK] SMS envoye a {test_sms}")
        total_succes += 1
    else:
        print(f"[ECHEC] SMS non envoye a {test_sms}")
        total_echecs += 1

    if email_success:
        print(f"[OK] Email envoye a {test_email}")
        total_succes += 1
    else:
        print(f"[ECHEC] Email non envoye a {test_email}")
        total_echecs += 1

    print("\n" + "-" * 80)
    print(f"Total: {total_succes} succes, {total_echecs} echec(s)")
    print("=" * 80)

    if total_succes == 2:
        print("\n[SUCCESS] Tous les tests d'envoi ont reussi !")
        print("Vous pouvez maintenant utiliser le systeme complet avec tous les destinataires.")
    elif total_succes > 0:
        print("\n[PARTIEL] Certains envois ont reussi, d'autres ont echoue.")
        print("Verifiez la configuration pour les envois en echec.")
    else:
        print("\n[ERREUR] Tous les envois ont echoue.")
        print("Verifiez votre configuration (SMTP, OVH SMS, etc.)")


if __name__ == "__main__":
    test_envoi_notifications()
