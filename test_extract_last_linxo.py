#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour extraire et analyser le dernier email Linxo
"""

import sys
import re
from pathlib import Path

# Ajouter le dossier linxo_agent au path
sys.path.insert(0, str(Path(__file__).parent / "linxo_agent"))

import imaplib
import email
import email.header
from email.utils import parsedate_to_datetime
import datetime as dt
from config import get_config

def extraire_dernier_email():
    """Extrait le dernier email Linxo pour tests"""
    print("\n" + "="*80)
    print("EXTRACTION DU DERNIER EMAIL LINXO")
    print("="*80)

    config = get_config()

    try:
        # Connexion IMAP
        mail = imaplib.IMAP4_SSL(config.imap_server, config.imap_port)
        mail.login(config.imap_email, config.imap_password)
        mail.select("INBOX")

        # Recherche emails Linxo
        status, messages = mail.search(None, 'FROM', '"linxo"')

        if status != "OK" or not messages or not messages[0]:
            print("[INFO] Aucun email Linxo trouvé")
            return

        email_ids = messages[0].split()
        print(f"[INFO] {len(email_ids)} emails Linxo trouvés")
        print(f"[INFO] Analyse du dernier email (ID: {email_ids[-1].decode()})...")

        # Récupérer le dernier email
        last_id = email_ids[-1]
        fetch_status, msg_data = mail.fetch(last_id, "(RFC822)")

        print(f"\n[DEBUG] fetch_status: {fetch_status}")
        print(f"[DEBUG] msg_data type: {type(msg_data)}")
        print(f"[DEBUG] msg_data length: {len(msg_data)}")

        if fetch_status != "OK" or not msg_data:
            print("[ERREUR] Échec du fetch")
            return

        # Extraction du payload
        raw_email_bytes = None
        for i, item in enumerate(msg_data):
            print(f"\n[DEBUG] Item {i} type: {type(item)}")

            if isinstance(item, tuple):
                print(f"[DEBUG] Item {i} est un tuple de longueur {len(item)}")
                for j, el in enumerate(item):
                    print(f"[DEBUG]   Element {j} type: {type(el)}, len: {len(el) if isinstance(el, (bytes, bytearray, str)) else 'N/A'}")
                    # On veut le plus gros élément bytes (le vrai contenu)
                    if isinstance(el, (bytes, bytearray)):
                        if raw_email_bytes is None or len(el) > len(raw_email_bytes):
                            raw_email_bytes = el
                            print(f"[DEBUG]   => Payload mis à jour depuis tuple[{j}] ({len(el)} bytes)")
            elif isinstance(item, (bytes, bytearray)):
                if raw_email_bytes is None or len(item) > len(raw_email_bytes):
                    raw_email_bytes = item
                    print(f"[DEBUG] => Payload mis à jour directement ({len(item)} bytes)")


        if not raw_email_bytes:
            print("[ERREUR] Impossible d'extraire le payload")
            return

        print(f"\n[OK] Payload extrait: {len(raw_email_bytes)} bytes")

        # Parser l'email
        email_message = email.message_from_bytes(raw_email_bytes)

        # Extraire les headers
        print("\n" + "-"*80)
        print("HEADERS:")
        print("-"*80)
        print(f"From    : {email_message.get('From', 'N/A')}")
        print(f"To      : {email_message.get('To', 'N/A')}")
        subject_raw = email_message.get('Subject', 'N/A')
        print(f"Subject : {subject_raw}")

        # Décoder le sujet
        decoded_subject = ""
        if subject_raw and subject_raw != 'N/A':
            decoded_parts = email.header.decode_header(subject_raw)
            for part, encoding in decoded_parts:
                if isinstance(part, bytes):
                    decoded_subject += part.decode(encoding or "utf-8", errors="ignore")
                else:
                    decoded_subject += part
            print(f"Subject décodé : {decoded_subject}")

            # Test extraction depuis le sujet
            subject_match = re.search(r"\b(\d{6})\b", decoded_subject)
            if subject_match:
                print(f"  => Code trouvé dans le sujet: {subject_match.group(1)}")
        print(f"Date    : {email_message.get('Date', 'N/A')}")

        # Extraire le corps
        print("\n" + "-"*80)
        print("CORPS DU MESSAGE:")
        print("-"*80)

        body_parts = []
        if email_message.is_multipart():
            print("[INFO] Email multipart")
            for i, part in enumerate(email_message.walk()):
                ctype = part.get_content_type()
                print(f"[DEBUG] Part {i}: {ctype}")
                if ctype in ("text/plain", "text/html"):
                    try:
                        payload = part.get_payload(decode=True)
                        if isinstance(payload, (bytes, bytearray)):
                            text = payload.decode("utf-8", errors="ignore")
                            body_parts.append(text)
                            print(f"[OK] Part {i} décodé: {len(text)} caractères")
                    except Exception as e:
                        print(f"[WARN] Erreur part {i}: {e}")
        else:
            print("[INFO] Email simple (non-multipart)")
            try:
                payload = email_message.get_payload(decode=True)
                if isinstance(payload, (bytes, bytearray)):
                    text = payload.decode("utf-8", errors="ignore")
                    body_parts.append(text)
                    print(f"[OK] Corps décodé: {len(text)} caractères")
            except Exception as e:
                print(f"[WARN] Erreur décodage: {e}")

        body = "\n".join(body_parts)

        # Afficher le début du corps
        print("\n" + "-"*80)
        print("EXTRAIT DU CORPS (200 premiers caractères):")
        print("-"*80)
        print(body[:200] if len(body) > 200 else body)

        # Tester les patterns de détection
        print("\n" + "-"*80)
        print("TEST DES PATTERNS:")
        print("-"*80)

        patterns = [
            (r"(\d)\s+(\d)\s+(\d)\s+(\d)\s+(\d)\s+(\d)", "Format avec espaces"),
            (r"(?:code|CODE)\s*(?:est)?\s*:?\s*(\d{6})", "Code est:"),
            (r"(?:vérification|verification)\s*:?\s*(\d{6})", "Vérification:"),
            (r"\b(\d{6})\b", "6 chiffres"),
        ]

        for pattern, desc in patterns:
            m = re.search(pattern, body, flags=re.IGNORECASE)
            if m:
                if len(m.groups()) > 1:
                    code = "".join(m.groups())
                else:
                    code = m.group(1)
                print(f"[OK] {desc:30s} => Code: {code}")
                break
            else:
                print(f"[--] {desc:30s} => Non trouvé")

        mail.close()
        mail.logout()

    except Exception as e:
        print(f"[ERREUR] {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    extraire_dernier_email()
