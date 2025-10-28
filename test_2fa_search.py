#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de test pour rechercher les emails Linxo 2FA dans la boîte mail
"""

import sys
from pathlib import Path

# Ajouter le dossier linxo_agent au path
sys.path.insert(0, str(Path(__file__).parent / "linxo_agent"))

from linxo_2fa import tester_connexion_imap
import imaplib
from config import get_config
import email
from email.utils import parsedate_to_datetime
import datetime as dt

def rechercher_emails_linxo():
    """Recherche et affiche les emails Linxo récents"""
    print("\n" + "="*80)
    print("RECHERCHE D'EMAILS LINXO DANS LA BOITE MAIL")
    print("="*80)

    # Test de connexion
    if not tester_connexion_imap():
        print("\n[ERREUR] Impossible de se connecter à IMAP")
        return

    config = get_config()

    print("\n[INFO] Recherche des emails Linxo...")

    try:
        # Connexion IMAP
        mail = imaplib.IMAP4_SSL(config.imap_server, config.imap_port)
        mail.login(config.imap_email, config.imap_password)
        mail.select("INBOX")

        # Recherche des emails Linxo (recherche simple)
        status, messages = mail.search(None, 'FROM', '"linxo"')

        if status != "OK" or not messages or not messages[0]:
            print("[INFO] Aucun email Linxo trouvé")
            mail.close()
            mail.logout()
            return

        email_ids = messages[0].split()
        print(f"[INFO] {len(email_ids)} emails Linxo trouvés")

        # Afficher les 5 plus récents
        print("\n" + "-"*80)
        print("5 EMAILS LINXO LES PLUS RÉCENTS:")
        print("-"*80)

        for i, email_id in enumerate(reversed(email_ids[-5:]), 1):
            fetch_status, msg_data = mail.fetch(email_id, "(RFC822)")
            if fetch_status != "OK" or not msg_data:
                continue

            # Extraction du payload
            raw_email_bytes = None
            for item in msg_data:
                if isinstance(item, tuple):
                    for el in tuple(item):
                        if isinstance(el, (bytes, bytearray)):
                            raw_email_bytes = el
                            break
                elif isinstance(item, (bytes, bytearray)):
                    raw_email_bytes = item
                if raw_email_bytes:
                    break

            if not raw_email_bytes:
                continue

            # Parser l'email
            email_message = email.message_from_bytes(raw_email_bytes)

            # Infos de base
            subject = email_message.get("Subject", "")
            from_addr = email_message.get("From", "")
            date_hdr = email_message.get("Date")
            email_date = parsedate_to_datetime(date_hdr) if date_hdr else None

            if email_date and email_date.tzinfo is None:
                email_date = email_date.replace(tzinfo=dt.timezone.utc)

            print(f"\n#{i}")
            print(f"  De      : {from_addr}")
            print(f"  Sujet   : {subject}")
            print(f"  Date    : {email_date}")

            # Age de l'email
            if email_date:
                now = dt.datetime.now(tz=email_date.tzinfo)
                age_seconds = (now - email_date).total_seconds()
                age_minutes = int(age_seconds / 60)
                age_hours = int(age_minutes / 60)
                age_days = int(age_hours / 24)

                if age_days > 0:
                    print(f"  Age     : {age_days} jour(s)")
                elif age_hours > 0:
                    print(f"  Age     : {age_hours} heure(s)")
                else:
                    print(f"  Age     : {age_minutes} minute(s)")

        mail.close()
        mail.logout()

        print("\n" + "-"*80)
        print("[INFO] Recherche terminée")
        print("[INFO] Pour tester la récupération automatique du code 2FA:")
        print("       1. Déclenchez une connexion Linxo")
        print("       2. Attendez de recevoir l'email")
        print("       3. Le code sera extrait automatiquement (format avec ou sans espaces)")

    except Exception as e:
        print(f"[ERREUR] {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    rechercher_emails_linxo()
