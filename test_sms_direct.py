#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de test DIRECT d'envoi de SMS via OVH (sans interaction)
"""

import sys
from pathlib import Path

# Ajouter le chemin du module linxo_agent
sys.path.insert(0, str(Path(__file__).parent / 'linxo_agent'))

from notifications import NotificationManager
from config import get_config


def test_sms_direct():
    """
    Test direct d'envoi de SMS avec affichage détaillé
    """
    print("\n" + "=" * 80)
    print("TEST DIRECT D'ENVOI SMS VIA OVH")
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

    # Numéro de test
    phone = "+33626267421"

    # Créer le gestionnaire de notifications
    notif_manager = NotificationManager()

    # Message de test simple
    message = "Test SMS Agent Linxo: Si vous recevez ce message, l'envoi fonctionne !"

    print(f"\n[SMS] Envoi du message de test...")
    print(f"[SMS] Message ({len(message)} caractères): {message}")
    print(f"[SMS] Destinataire: {phone}")

    # Format du sujet OVH attendu
    print(f"\n[DEBUG] Format du sujet OVH:")
    print(f"  Format: compte:utilisateur:password:expediteur:destinataire")
    subject_format = f"{config.ovh_compte_sms}:{config.ovh_utilisateur_sms}:[PASSWORD]:{config.ovh_expediteur_sms}:{phone}"
    print(f"  Sujet: {subject_format}")

    print("\n" + "-" * 80)
    print("[INFO] Envoi en cours...")
    print("-" * 80)

    # Envoyer le SMS
    try:
        results = notif_manager.send_sms_ovh(message, recipients=[phone])

        print("\n" + "=" * 80)
        print("RÉSULTAT DE L'ENVOI")
        print("=" * 80)

        if results.get(phone):
            print(f"\n[SUCCESS] SMS envoyé avec succès à {phone}")
            print("\nVérifiez votre téléphone dans quelques instants.")
            print("Délai de réception: généralement 1-5 minutes")
            print("\nSi vous ne recevez pas le SMS, vérifiez:")
            print("  1. Que votre compte OVH SMS a du crédit")
            print("  2. Que le numéro d'expéditeur 'PhiPEREZ' est autorisé")
            print("  3. Les logs OVH sur https://www.ovh.com/manager/")
        else:
            print(f"\n[ERREUR] Échec de l'envoi du SMS à {phone}")
            print("\nPossibles causes:")
            print("  1. Identifiants OVH incorrects (compte, utilisateur ou mot de passe)")
            print("  2. Compte OVH SMS non activé ou sans crédit")
            print("  3. Numéro d'expéditeur 'PhiPEREZ' non valide (max 11 caractères)")
            print("  4. Problème de connexion SMTP Gmail")
            print("\nVérifiez les logs ci-dessus pour plus de détails.")

    except Exception as e:
        print(f"\n[ERREUR] Exception lors de l'envoi: {e}")
        import traceback
        traceback.print_exc()

        print("\n[DIAGNOSTIC] Vérifications à effectuer:")
        print("  1. Connexion SMTP Gmail: mot de passe d'application valide ?")
        print("  2. Configuration OVH: identifiants corrects ?")
        print("  3. Connectivité réseau: pas de firewall bloquant SMTP ?")


if __name__ == "__main__":
    test_sms_direct()
