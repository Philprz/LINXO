#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de test DÉDIÉ à l'envoi de SMS via OVH
Permet de diagnostiquer les problèmes d'envoi
"""

import sys
from pathlib import Path

# Ajouter le chemin du module linxo_agent
sys.path.insert(0, str(Path(__file__).parent / 'linxo_agent'))

from notifications import NotificationManager
from config import get_config


def test_sms_simple():
    """
    Test simple d'envoi de SMS avec affichage détaillé
    """
    print("\n" + "=" * 80)
    print("TEST D'ENVOI SMS VIA OVH")
    print("=" * 80)

    # Charger la configuration
    config = get_config()

    print("\n[CONFIG] Vérification de la configuration OVH SMS...")
    print(f"  - Compte SMS: {config.ovh_compte_sms}")
    print(f"  - Utilisateur: {config.ovh_utilisateur_sms}")
    print(f"  - Mot de passe: {'*' * len(config.ovh_mot_de_passe_sms) if config.ovh_mot_de_passe_sms else '[VIDE]'}")
    print(f"  - Expéditeur: {config.ovh_expediteur_sms}")
    print(f"  - Email OVH: {config.ovh_email}")
    print(f"\n  - SMTP Server: {config.smtp_server}:{config.smtp_port}")
    print(f"  - SMTP Email: {config.smtp_email}")
    print(f"  - SMTP Password: {'*' * len(config.smtp_password) if config.smtp_password else '[VIDE]'}")

    # Vérifier que tous les champs sont remplis
    missing_fields = []
    if not config.ovh_compte_sms:
        missing_fields.append("OVH_COMPTE_SMS")
    if not config.ovh_utilisateur_sms:
        missing_fields.append("OVH_UTILISATEUR_SMS")
    if not config.ovh_mot_de_passe_sms:
        missing_fields.append("OVH_MOT_DE_PASSE_SMS")
    if not config.ovh_expediteur_sms:
        missing_fields.append("OVH_EXPEDITEUR_SMS")
    if not config.ovh_email:
        missing_fields.append("OVH_EMAIL")

    if missing_fields:
        print("\n[ERREUR] Champs de configuration manquants:")
        for field in missing_fields:
            print(f"  - {field}")
        print("\nVeuillez vérifier votre fichier .env ou api_secrets.json")
        return

    print("\n[OK] Configuration complète")

    # Demander confirmation
    print("\n" + "=" * 80)
    phone = "+33626267421"
    print(f"Destinataire SMS: {phone}")
    print("=" * 80)

    response = input("\nConfirmez-vous l'envoi du SMS de test ? (oui/non): ")
    if response.lower() not in ['oui', 'o', 'yes', 'y']:
        print("\n[ANNULE] Test d'envoi SMS annulé.")
        return

    # Créer le gestionnaire de notifications
    notif_manager = NotificationManager()

    # Message de test simple
    message = "Test SMS Agent Linxo: Si vous recevez ce message, l'envoi fonctionne !"

    print(f"\n[SMS] Envoi du message...")
    print(f"[SMS] Message ({len(message)} caractères): {message}")
    print(f"[SMS] Destinataire: {phone}")

    # Format du sujet OVH attendu
    print(f"\n[DEBUG] Format du sujet OVH:")
    print(f"  compte:utilisateur:password:expediteur:destinataire")
    subject_format = f"{config.ovh_compte_sms}:{config.ovh_utilisateur_sms}:[PASSWORD]:{config.ovh_expediteur_sms}:{phone}"
    print(f"  {subject_format}")

    print("\n" + "-" * 80)

    # Envoyer le SMS
    try:
        results = notif_manager.send_sms_ovh(message, recipients=[phone])

        print("\n" + "=" * 80)
        print("RÉSULTAT DE L'ENVOI")
        print("=" * 80)

        if results.get(phone):
            print(f"[SUCCESS] SMS envoyé avec succès à {phone}")
            print("\nVérifiez votre téléphone dans quelques instants.")
            print("Délai de réception: généralement 1-5 minutes")
        else:
            print(f"[ERREUR] Échec de l'envoi du SMS à {phone}")
            print("\nPossibles causes:")
            print("  1. Identifiants OVH incorrects")
            print("  2. Compte OVH SMS non activé ou sans crédit")
            print("  3. Numéro d'expéditeur non valide")
            print("  4. Problème de connexion SMTP")

    except Exception as e:
        print(f"\n[ERREUR] Exception lors de l'envoi: {e}")
        import traceback
        traceback.print_exc()


def test_sms_avec_config_manuelle():
    """
    Test SMS avec saisie manuelle des paramètres (mode debug)
    """
    print("\n" + "=" * 80)
    print("TEST SMS - MODE CONFIGURATION MANUELLE")
    print("=" * 80)

    print("\nCe mode permet de tester avec des paramètres saisis manuellement")
    print("pour diagnostiquer les problèmes de configuration.")

    response = input("\nUtiliser ce mode ? (oui/non): ")
    if response.lower() not in ['oui', 'o', 'yes', 'y']:
        return

    # Demander les paramètres
    print("\n[CONFIG] Saisissez les paramètres OVH SMS:")
    compte = input("  Compte SMS (ex: sms-ab12345-1): ")
    utilisateur = input("  Utilisateur: ")
    password = input("  Mot de passe: ")
    expediteur = input("  Expéditeur (11 caractères max): ")
    phone = input("  Numéro destinataire (format international, ex: +33626267421): ")

    print("\n[CONFIG] Paramètres SMTP Gmail:")
    smtp_email = input("  Email SMTP: ")
    smtp_password = input("  Mot de passe SMTP: ")

    # Afficher récapitulatif
    print("\n" + "=" * 80)
    print("RÉCAPITULATIF")
    print("=" * 80)
    print(f"Compte SMS: {compte}")
    print(f"Utilisateur: {utilisateur}")
    print(f"Mot de passe: {'*' * len(password)}")
    print(f"Expéditeur: {expediteur}")
    print(f"Destinataire: {phone}")
    print(f"SMTP Email: {smtp_email}")

    response = input("\nConfirmer l'envoi avec ces paramètres ? (oui/non): ")
    if response.lower() not in ['oui', 'o', 'yes', 'y']:
        print("\n[ANNULE] Test annulé.")
        return

    # Envoyer le SMS manuellement
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart

    try:
        message = "Test SMS manuel Agent Linxo"

        # Format du sujet pour OVH
        subject = f"{compte}:{utilisateur}:{password}:{expediteur}:{phone}"

        msg = MIMEMultipart()
        msg['Subject'] = subject
        msg['From'] = smtp_email
        msg['To'] = "sms@ovh.net"

        body = MIMEText(message, 'plain', 'utf-8')
        msg.attach(body)

        print("\n[SMS] Connexion au serveur SMTP...")
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(smtp_email, smtp_password)
        server.send_message(msg)
        server.quit()

        print("[SUCCESS] SMS envoyé avec succès !")
        print("\nVérifiez votre téléphone dans quelques instants.")

    except Exception as e:
        print(f"\n[ERREUR] Échec de l'envoi: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Menu principal"""
    print("\n" + "=" * 80)
    print("TESTS D'ENVOI SMS OVH - MENU")
    print("=" * 80)
    print("\n1. Test simple avec configuration du fichier .env")
    print("2. Test avec configuration manuelle (mode debug)")
    print("3. Afficher la configuration actuelle")
    print("4. Quitter")

    choice = input("\nVotre choix (1-4): ")

    if choice == "1":
        test_sms_simple()
    elif choice == "2":
        test_sms_avec_config_manuelle()
    elif choice == "3":
        config = get_config()
        print("\n" + "=" * 80)
        print("CONFIGURATION ACTUELLE")
        print("=" * 80)
        print(f"Compte SMS: {config.ovh_compte_sms}")
        print(f"Utilisateur: {config.ovh_utilisateur_sms}")
        print(f"Mot de passe: {'*' * len(config.ovh_mot_de_passe_sms) if config.ovh_mot_de_passe_sms else '[VIDE]'}")
        print(f"Expéditeur: {config.ovh_expediteur_sms}")
        print(f"Email OVH: {config.ovh_email}")
        print(f"SMTP Server: {config.smtp_server}:{config.smtp_port}")
        print(f"SMTP Email: {config.smtp_email}")
    elif choice == "4":
        print("\nAu revoir !")
    else:
        print("\nChoix invalide.")


if __name__ == "__main__":
    main()
