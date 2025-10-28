#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test d'extraction du code depuis le dernier email Linxo (même ancien)
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "linxo_agent"))

import imaplib
import email
import email.header
import re
from config import get_config

def test_extraction_dernier_email():
    """Teste l'extraction du code depuis le dernier email (ignore le filtre de date)"""
    print("\n" + "="*80)
    print("TEST EXTRACTION CODE DU DERNIER EMAIL LINXO")
    print("="*80)

    config = get_config()

    try:
        # Connexion IMAP
        print("\n[INFO] Connexion à IMAP...")
        mail = imaplib.IMAP4_SSL(config.imap_server, config.imap_port)
        mail.login(config.imap_email, config.imap_password)
        mail.select("INBOX")

        # Recherche emails Linxo
        print("[INFO] Recherche des emails Linxo...")
        status, messages = mail.search(None, 'FROM', '"linxo"')

        if status != "OK" or not messages or not messages[0]:
            print("[ERREUR] Aucun email Linxo trouvé")
            return False

        email_ids = messages[0].split()
        print(f"[INFO] {len(email_ids)} emails Linxo trouvés")

        # Prendre le dernier
        last_id = email_ids[-1]
        print(f"[INFO] Analyse de l'email le plus récent (ID: {last_id.decode()})...\n")

        # Récupérer l'email
        fetch_status, msg_data = mail.fetch(last_id, "(RFC822)")

        if fetch_status != "OK" or not msg_data:
            print("[ERREUR] Échec du fetch")
            return False

        # Extraction du payload (plus gros élément bytes)
        raw_email_bytes = None
        for item in msg_data:
            if isinstance(item, tuple):
                for el in tuple(item):
                    if isinstance(el, (bytes, bytearray)):
                        if raw_email_bytes is None or len(el) > len(raw_email_bytes):
                            raw_email_bytes = el
            elif isinstance(item, (bytes, bytearray)):
                if raw_email_bytes is None or len(item) > len(raw_email_bytes):
                    raw_email_bytes = item

        if not raw_email_bytes:
            print("[ERREUR] Payload vide")
            return False

        # Parser l'email
        email_message = email.message_from_bytes(raw_email_bytes)

        # Afficher les infos
        subject_raw = email_message.get("Subject", "")
        from_addr = email_message.get("From", "")
        date = email_message.get("Date", "")

        print(f"De      : {from_addr}")
        print(f"Sujet   : {subject_raw}")
        print(f"Date    : {date}")

        # Décoder le sujet
        print("\n" + "-"*80)
        print("EXTRACTION DU CODE 2FA")
        print("-"*80)

        decoded_subject = ""
        if subject_raw:
            decoded_parts = email.header.decode_header(subject_raw)
            for part, encoding in decoded_parts:
                if isinstance(part, bytes):
                    decoded_subject += part.decode(encoding or "utf-8", errors="ignore")
                else:
                    decoded_subject += part

        print(f"\nSujet décodé : {decoded_subject}")

        # Chercher un code à 6 chiffres dans le sujet
        subject_match = re.search(r"\b(\d{6})\b", decoded_subject)
        if subject_match:
            code = subject_match.group(1)
            print(f"\n[SUCCESS] Code 2FA trouvé dans le SUJET: {code}")
            mail.close()
            mail.logout()
            return True

        print("\n[INFO] Pas de code dans le sujet, recherche dans le corps...")

        # Extraire le corps
        body_parts = []
        if email_message.is_multipart():
            for part in email_message.walk():
                ctype = part.get_content_type()
                if ctype in ("text/plain", "text/html"):
                    try:
                        payload = part.get_payload(decode=True)
                        if isinstance(payload, (bytes, bytearray)):
                            body_parts.append(payload.decode("utf-8", errors="ignore"))
                    except:
                        pass
        else:
            try:
                payload = email_message.get_payload(decode=True)
                if isinstance(payload, (bytes, bytearray)):
                    body_parts.append(payload.decode("utf-8", errors="ignore"))
            except:
                pass

        body = "\n".join(body_parts)

        # Patterns
        patterns = [
            (r"(\d)\s+(\d)\s+(\d)\s+(\d)\s+(\d)\s+(\d)", "Format avec espaces"),
            (r"(?:code|CODE)\s*(?:est)?\s*:?\s*(\d{6})", "Code est:"),
            (r"\b(\d{6})\b", "6 chiffres"),
        ]

        for pattern, desc in patterns:
            m = re.search(pattern, body, flags=re.IGNORECASE)
            if m:
                if len(m.groups()) > 1:
                    code = "".join(m.groups())
                else:
                    code = m.group(1)
                print(f"[SUCCESS] Code 2FA trouvé dans le CORPS ({desc}): {code}")
                mail.close()
                mail.logout()
                return True

        print("\n[INFO] Aucun code 2FA détecté dans cet email")
        mail.close()
        mail.logout()
        return False

    except Exception as e:
        print(f"[ERREUR] {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_extraction_dernier_email()
    if success:
        print("\n" + "="*80)
        print("TEST RÉUSSI - L'EXTRACTION DU CODE FONCTIONNE")
        print("="*80)
        print("\n[INFO] Le module 2FA est prêt.")
        print("[INFO] Pour l'utiliser en conditions réelles:")
        print("       1. Déclenchez une connexion Linxo")
        print("       2. Attendez de recevoir l'email (quelques secondes)")
        print("       3. Le code sera automatiquement extrait")
    else:
        print("\n" + "="*80)
        print("TEST ÉCHOUÉ")
        print("="*80)
