#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de prévisualisation des notifications (Email + SMS)
Montre le rendu sans envoyer réellement les messages
"""

import sys
from pathlib import Path
from datetime import datetime

# Ajouter le chemin du module linxo_agent
sys.path.insert(0, str(Path(__file__).parent / 'linxo_agent'))

from analyzer import analyser_csv
from config import get_config


def preview_notifications():
    """
    Génère et affiche un aperçu des notifications sans les envoyer
    """
    print("\n" + "=" * 80)
    print("APERÇU DES NOTIFICATIONS LINXO")
    print("=" * 80)

    # Obtenir la configuration
    config = get_config()

    print(f"\n[INFO] Analyse du dernier fichier CSV...")

    # Analyser les transactions
    analysis_result = analyser_csv()

    if not analysis_result:
        print("[ERREUR] Impossible d'analyser le fichier CSV")
        return

    # Extraire les données
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
    # APERÇU DU SMS
    # ========================================================================
    print("\n" + "=" * 80)
    print("[SMS] APERCU DU SMS")
    print("=" * 80)
    print(f"Destinataire: +33626267421")
    print("-" * 80)

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

    print(sms_msg)
    print(f"\n[INFO] Longueur du SMS: {len(sms_msg)} caractères (max 160)")

    # ========================================================================
    # APERÇU DE L'EMAIL
    # ========================================================================
    print("\n" + "=" * 80)
    print("[EMAIL] APERCU DE L'EMAIL")
    print("=" * 80)
    print(f"Destinataire: phiperez@gmail.com")
    print("-" * 80)

    # Sujet de l'email
    if alerte:
        email_subject = f"{emoji} [ALERTE BUDGET] - Depassement de {abs(reste):.0f}E !"
    elif emoji == "🟠":
        email_subject = f"{emoji} [ATTENTION Budget] - {pourcentage:.0f}% utilise"
    else:
        email_subject = f"{emoji} [Budget OK] - Rapport Linxo {datetime.now().strftime('%d/%m/%Y')}"

    print(f"\nSUJET: {email_subject}")
    print("\nCORPS DE L'EMAIL:")
    print("-" * 80)

    # Corps de l'email (utiliser le rapport complet)
    email_body = analysis_result.get('rapport', '')
    print(email_body)

    # Informations sur la pièce jointe
    csv_path = analysis_result.get('csv_path')
    if csv_path and Path(csv_path).exists():
        print("\n" + "-" * 80)
        print(f"PIECE JOINTE: {Path(csv_path).name}")
        print(f"Taille: {Path(csv_path).stat().st_size / 1024:.2f} Ko")

    # ========================================================================
    # RÉSUMÉ DES DESTINATAIRES
    # ========================================================================
    print("\n" + "=" * 80)
    print("[CONFIG] DESTINATAIRES CONFIGURES")
    print("=" * 80)
    print("\nEmails:")
    for email in config.notification_emails:
        print(f"  - {email}")

    print("\nSMS:")
    for phone in config.sms_recipients:
        print(f"  - {phone}")

    print("\n" + "=" * 80)
    print("[INFO] INFORMATIONS")
    print("=" * 80)
    print("Ce script montre un aperçu des notifications SANS les envoyer.")
    print("Pour tester l'envoi réel uniquement à phiperez@gmail.com et +33626267421,")
    print("utilisez le script: test_send_notifications.py")
    print("=" * 80)


if __name__ == "__main__":
    preview_notifications()
