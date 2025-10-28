#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de test pour rechercher TOUS les emails contenant "linxo" ou "code"
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

def rechercher_tous_emails():
    """Recherche large pour trouver les emails Linxo"""
    print("\n" + "="*80)
    print("RECHERCHE LARGE D'EMAILS")
    print("="*80)

    config = get_config()

    try:
        # Connexion IMAP
        mail = imaplib.IMAP4_SSL(config.imap_server, config.imap_port)
        mail.login(config.imap_email, config.imap_password)
        mail.select("INBOX")

        # Test 1: Recherche par FROM linxo
        print("\n[TEST 1] Recherche FROM 'linxo'...")
        status1, messages1 = mail.search(None, 'FROM', '"linxo"')
        count1 = len(messages1[0].split()) if status1 == "OK" and messages1[0] else 0
        print(f"  Résultat: {count1} emails")

        # Test 2: Recherche par SUBJECT code
        print("\n[TEST 2] Recherche SUBJECT 'code'...")
        status2, messages2 = mail.search(None, 'SUBJECT', '"code"')
        count2 = len(messages2[0].split()) if status2 == "OK" and messages2[0] else 0
        print(f"  Résultat: {count2} emails")

        # Test 3: Recherche combinée simple
        print("\n[TEST 3] Recherche '(OR FROM linxo SUBJECT code)'...")
        status3, messages3 = mail.search(None, '(OR FROM "linxo" SUBJECT "code")')
        count3 = len(messages3[0].split()) if status3 == "OK" and messages3[0] else 0
        print(f"  Résultat: {count3} emails")

        # Test 4: Recherche récents (7 derniers jours)
        print("\n[TEST 4] Recherche emails récents (7 jours) avec 'linxo' ou 'code'...")
        # Date il y a 7 jours
        date_limit = (dt.datetime.now() - dt.timedelta(days=7)).strftime("%d-%b-%Y")
        status4, messages4 = mail.search(None, f'(OR FROM "linxo" SUBJECT "code") SINCE {date_limit}')
        count4 = len(messages4[0].split()) if status4 == "OK" and messages4[0] else 0
        print(f"  Résultat: {count4} emails depuis le {date_limit}")

        # Si on a des résultats, afficher les plus récents
        if count4 > 0:
            email_ids = messages4[0].split()
            print(f"\n[INFO] Affichage des 3 emails les plus récents:")
            print("-"*80)

            for i, email_id in enumerate(reversed(email_ids[-3:]), 1):
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

                subject = email_message.get("Subject", "")
                from_addr = email_message.get("From", "")
                date_hdr = email_message.get("Date")
                email_date = parsedate_to_datetime(date_hdr) if date_hdr else None

                print(f"\n#{i}")
                print(f"  De    : {from_addr}")
                print(f"  Sujet : {subject}")
                print(f"  Date  : {email_date}")

        mail.close()
        mail.logout()

        print("\n" + "="*80)
        print("[INFO] Tests terminés")

    except Exception as e:
        print(f"[ERREUR] {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    rechercher_tous_emails()
