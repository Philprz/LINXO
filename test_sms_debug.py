#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de test SMS avec affichage détaillé du format OVH
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import sys
from pathlib import Path

# Ajouter le chemin du module linxo_agent
sys.path.insert(0, str(Path(__file__).parent / 'linxo_agent'))

from config import get_config


def test_sms_debug():
    """
    Test SMS avec affichage détaillé de tous les paramètres
    """
    print("\n" + "=" * 80)
    print("TEST SMS OVH - MODE DEBUG COMPLET")
    print("=" * 80)

    # Charger la configuration
    config = get_config()

    print("\n[CONFIG] Configuration SMS OVH chargée:")
    print("-" * 80)
    print(f"Compte SMS (CompteSMS):      {config.ovh_compte_sms}")
    print(f"Utilisateur (UtilisateurSMS): {config.ovh_utilisateur_sms}")
    print(f"Mot de passe (MotDePasse):    {config.ovh_mot_de_passe_sms}")
    print(f"Expéditeur (Expediteur):      {config.ovh_expediteur_sms}")
    print(f"Email OVH destinataire:       {config.ovh_email}")
    print("")
    print(f"SMTP Server:                  {config.smtp_server}:{config.smtp_port}")
    print(f"SMTP Email (From):            {config.smtp_email}")
    print(f"SMTP Password:                {'*' * len(config.smtp_password)}")

    # Numéro destinataire
    phone = "+33626267421"

    # Construction du sujet selon le format OVH
    # Format: CompteSMS:UtilisateurSMS:MotDePasse:Expediteur:Destinataire
    subject = f"{config.ovh_compte_sms}:{config.ovh_utilisateur_sms}:{config.ovh_mot_de_passe_sms}:{config.ovh_expediteur_sms}:{phone}"

    print("\n[FORMAT OVH] Construction du sujet:")
    print("-" * 80)
    print("Format attendu: CompteSMS:UtilisateurSMS:MotDePasse:Expediteur:Destinataire")
    print("")
    print(f"Sujet complet: {subject}")
    print("")
    print("Décomposition:")
    print(f"  CompteSMS:       {config.ovh_compte_sms}")
    print(f"  UtilisateurSMS:  {config.ovh_utilisateur_sms}")
    print(f"  MotDePasse:      {config.ovh_mot_de_passe_sms}")
    print(f"  Expediteur:      {config.ovh_expediteur_sms}")
    print(f"  Destinataire:    {phone}")

    # Message SMS
    message = "Test OVH SMS: Message recu !"

    print("\n[MESSAGE]")
    print("-" * 80)
    print(f"Longueur: {len(message)} caractères")
    print(f"Contenu: {message}")

    print("\n[EMAIL] Construction de l'email à envoyer:")
    print("-" * 80)
    print(f"From:    {config.smtp_email}")
    print(f"To:      {config.ovh_email}")
    print(f"Subject: {subject}")
    print(f"Body:    {message}")

    print("\n" + "=" * 80)
    print("ENVOI DU SMS")
    print("=" * 80)

    try:
        # Construire le message email
        msg = MIMEMultipart()
        msg['Subject'] = subject
        msg['From'] = config.smtp_email
        msg['To'] = config.ovh_email

        body = MIMEText(message, 'plain', 'utf-8')
        msg.attach(body)

        print("\n[SMTP] Connexion au serveur SMTP Gmail...")
        server = smtplib.SMTP(config.smtp_server, config.smtp_port)

        print("[SMTP] Activation TLS...")
        server.starttls()

        print(f"[SMTP] Authentification avec {config.smtp_email}...")
        server.login(config.smtp_email, config.smtp_password)

        print(f"[SMTP] Envoi du message à {config.ovh_email}...")
        server.send_message(msg)

        print("[SMTP] Fermeture de la connexion...")
        server.quit()

        print("\n" + "=" * 80)
        print("[SUCCESS] SMS ENVOYÉ AVEC SUCCÈS")
        print("=" * 80)
        print(f"\nDestinataire: {phone}")
        print(f"Expéditeur affiché: {config.ovh_expediteur_sms}")
        print(f"Message: {message}")
        print("\nVérifiez votre téléphone dans 1-5 minutes.")
        print("\nSi vous ne recevez pas le SMS, vérifiez:")
        print("  1. Crédit OVH SMS sur https://www.ovh.com/manager/")
        print("  2. Logs d'envoi dans le manager OVH")
        print("  3. Que l'expéditeur 'PhiPEREZ' est bien autorisé")

    except smtplib.SMTPAuthenticationError as e:
        print(f"\n[ERREUR] Authentification SMTP échouée: {e}")
        print("\nVérifiez:")
        print("  - Le mot de passe d'application Gmail est correct")
        print("  - L'authentification à 2 facteurs est activée sur Gmail")

    except smtplib.SMTPException as e:
        print(f"\n[ERREUR] Erreur SMTP: {e}")

    except Exception as e:
        print(f"\n[ERREUR] Erreur inattendue: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 80)


if __name__ == "__main__":
    test_sms_debug()
