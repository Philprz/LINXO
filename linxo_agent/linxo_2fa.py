#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module de gestion du 2FA pour Linxo
Version 1.2 - Lecture automatique du code 2FA par email (IMAP)
"""

from __future__ import annotations

import datetime as dt
import email
import imaplib
import os
import re
import socket
import ssl
import sys
import time
from email.utils import parsedate_to_datetime
from pathlib import Path

# Gestion des imports avec conflit de nommage
try:
    from .config import get_config
except ImportError:
    # Fallback si importé depuis un autre contexte
    sys.path.insert(0, str(Path(__file__).parent))
    from config import get_config  # type: ignore


def recuperer_code_2fa_email(timeout: int = 120, check_interval: int = 5) -> str | None:
    """
    Récupère automatiquement le code 2FA depuis l'email.

    Args:
        timeout: Temps maximum d'attente (secondes).
        check_interval: Intervalle entre deux vérifications (secondes).

    Returns:
        str | None: Code 2FA (6 chiffres) ou None si échec.
    """
    print("\n[2FA] Recherche du code 2FA dans l'email...")

    # Charger la config unifiée
    config = get_config()

    # Paramètres IMAP depuis la config
    imap_email = config.imap_email
    imap_password = config.imap_password
    imap_server = config.imap_server
    imap_port = config.imap_port

    if not imap_email or not imap_password:
        print("[ERREUR] Credentials IMAP manquants dans la configuration.")
        print("[INFO] Configurez SENDER_EMAIL et SENDER_PASSWORD dans .env")
        print("[INFO] Ou definissez IMAP_EMAIL et IMAP_PASSWORD pour un compte different")
        return None

    start_time = time.time()
    attempts = 0

    # Motifs pour extraire un code 2FA (6 chiffres)
    patterns = [
        r"(?:code|CODE)\s*(?:est|:)?\s*(\d{6})",
        r"(?:vérification|verification)\s*:?\s*(\d{6})",
        r"(?:authentification|authentication)\s*:?\s*(\d{6})",
        r"\b(\d{6})\b",
    ]

    while time.time() - start_time < timeout:
        attempts += 1
        elapsed = int(time.time() - start_time)
        print(f"[2FA] Tentative {attempts} (après {elapsed}s)...")

        try:
            # Connexion IMAP
            mail = imaplib.IMAP4_SSL(imap_server, imap_port)
            mail.login(imap_email, imap_password)

            # Sélection INBOX
            sel_status, _ = mail.select("INBOX")
            if sel_status != "OK":
                print("[WARN] Impossible de sélectionner INBOX.")
                try:
                    mail.close()
                except imaplib.IMAP4.error:
                    pass
                mail.logout()
                time.sleep(check_interval)
                continue

            # Recherche des emails plausibles
            search_criteria = '(OR FROM "linxo" OR FROM "noreply" SUBJECT "code")'
            status, messages = mail.search(None, search_criteria)

            if status != "OK" or not messages or not messages[0]:
                print("[INFO] Aucun email trouvé pour l’instant…")
                mail.close()
                mail.logout()
                time.sleep(check_interval)
                continue

            email_ids = messages[0].split()
            if not email_ids:
                print("[INFO] Aucun email trouvé pour l’instant…")
                mail.close()
                mail.logout()
                time.sleep(check_interval)
                continue

            # Parcours des 10 plus récents (du plus récent au plus ancien)
            for email_id in reversed(email_ids[-10:]):
                fetch_status, msg_data = mail.fetch(email_id, "(RFC822)")
                if fetch_status != "OK" or not msg_data:
                    continue

                # ----- Extraction sûre du payload email -----
                raw_email_bytes = None

                for item in msg_data:
                    payload_candidate = None

                    if isinstance(item, tuple):
                        # Cast explicite pour rassurer l'analyseur statique
                        for el in tuple(item):
                            if isinstance(el, (bytes, bytearray)):
                                payload_candidate = el
                                break

                    elif isinstance(item, (bytes, bytearray)):
                        # Certains serveurs renvoient directement le corps ici
                        payload_candidate = item

                    if payload_candidate:
                        raw_email_bytes = payload_candidate
                        break

                if not raw_email_bytes:
                    continue
                # ----- fin extraction sûre -----

                # Parser l'email
                try:
                    email_message = email.message_from_bytes(raw_email_bytes)
                except (TypeError, ValueError):
                    continue

                # Date du mail et filtrage (< 5 min)
                date_hdr = email_message.get("Date")
                email_date = parsedate_to_datetime(date_hdr) if date_hdr else None
                if email_date is None:
                    continue
                if email_date.tzinfo is None:
                    email_date = email_date.replace(tzinfo=dt.timezone.utc)
                now = dt.datetime.now(tz=email_date.tzinfo)
                if (now - email_date).total_seconds() > 300:
                    continue

                subject = email_message.get("Subject", "")
                from_addr = email_message.get("From", "")
                print(f"[2FA] Email trouvé: De={from_addr}, Sujet={subject}")

                # Corps du message
                body_parts: list[str] = []
                if email_message.is_multipart():
                    for part in email_message.walk():
                        ctype = part.get_content_type()
                        if ctype in ("text/plain", "text/html"):
                            try:
                                payload = part.get_payload(decode=True)
                                if isinstance(payload, (bytes, bytearray)):
                                    body_parts.append(
                                        payload.decode("utf-8", errors="ignore")
                                    )
                            except (UnicodeDecodeError, AttributeError, TypeError):
                                continue
                else:
                    try:
                        payload = email_message.get_payload(decode=True)
                        if isinstance(payload, (bytes, bytearray)):
                            body_parts.append(payload.decode("utf-8", errors="ignore"))
                    except (UnicodeDecodeError, AttributeError, TypeError):
                        pass

                body = "\n".join(body_parts)

                # Extraction du code
                for pattern in patterns:
                    m = re.search(pattern, body, flags=re.IGNORECASE)
                    if m:
                        code_2fa = m.group(1)
                        print(f"[SUCCESS] Code 2FA trouvé: {code_2fa}")
                        try:
                            mail.close()
                        except imaplib.IMAP4.error:
                            pass
                        mail.logout()
                        return code_2fa

            # Aucun code trouvé pour ce passage
            try:
                mail.close()
            except imaplib.IMAP4.error:
                pass
            mail.logout()
            print(f"[INFO] Code non trouvé, nouvelle tentative dans {check_interval}s…")
            time.sleep(check_interval)

        except (imaplib.IMAP4.abort, imaplib.IMAP4.error) as e:
            print(f"[ERREUR] IMAP: {e}. Vérifiez identifiants et accès IMAP.")
            return None
        except (OSError, ssl.SSLError, socket.timeout) as e:
            # Regroupe TimeoutError / ConnectionRefusedError (sous-classes de OSError)
            print(f"[WARN] Réseau/SSL: {e}. Nouvelle tentative dans {check_interval}s…")
            time.sleep(check_interval)

    print(f"[ERREUR] Timeout de {timeout}s atteint, code 2FA non trouvé.")
    return None


def tester_connexion_imap() -> bool:
    """
    Teste la connexion IMAP pour vérifier les paramètres.

    Returns:
        bool: True si la connexion et la lecture sont possibles, False sinon.
    """
    print("\n[TEST] Test de la connexion IMAP...")
    config = get_config()

    # Paramètres IMAP depuis la config unifiée
    imap_email = config.imap_email
    imap_password = config.imap_password
    imap_server = config.imap_server
    imap_port = config.imap_port

    print(f"[INFO] Email IMAP: {imap_email}")
    print(f"[INFO] Serveur IMAP: {imap_server}:{imap_port}")

    if not imap_email or not imap_password:
        print("[ERREUR] Credentials IMAP manquants dans la configuration.")
        print("[INFO] Configurez SENDER_EMAIL et SENDER_PASSWORD dans .env")
        print("[INFO] Ou definissez IMAP_EMAIL et IMAP_PASSWORD pour un compte different")
        return False

    if not 0 < imap_port <= 65535:
        print("[ERREUR] Port IMAP invalide (1..65535).")
        return False

    mail: imaplib.IMAP4_SSL | None = None
    success = False
    try:
        mail = imaplib.IMAP4_SSL(imap_server, imap_port)
        mail.login(imap_email, imap_password)
        mail.select("INBOX")
        status, messages = mail.search(None, "ALL")
        if status == "OK":
            count = len(messages[0].split()) if messages[0] else 0
            print("[SUCCESS] Connexion IMAP réussie !")
            print(f"[INFO] {count} messages dans la boîte de réception")
            success = True

    except imaplib.IMAP4.error as e:
        print(f"[ERREUR IMAP] Échec de la connexion: {e}")
        print("[INFO] Vérifiez :")
        print("  1. IMAP activé sur le compte")
        print("  2. Mot de passe d'application correct")
    except (OSError, ssl.SSLError, socket.timeout) as e:
        # Regroupe TimeoutError / ConnectionRefusedError ici
        print(f"[ERREUR] Problème réseau/SSL: {e}")
    finally:
        if mail:
            try:
                mail.close()
                mail.logout()
            except imaplib.IMAP4.error:
                pass

    return success


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("TEST DU MODULE 2FA")
    print("=" * 80)

    if tester_connexion_imap():
        print("\n[INFO] Test de connexion IMAP réussi !")
        resp = input("\nTester la récupération du code 2FA ? (o/n): ")
        if resp.lower() == "o":
            print("\n[INFO] Déclenche une connexion Linxo pour recevoir un code 2FA…")
            print("[INFO] Attente max 2 minutes pour trouver le code.")
            code = recuperer_code_2fa_email(timeout=120, check_interval=5)
            if code:
                print(f"\n[SUCCESS] Code 2FA récupéré: {code}")
            else:
                print("\n[ERREUR] Impossible de récupérer le code 2FA.")
    else:
        print("\n[ERREUR] Test de connexion IMAP échoué.")
        print("[INFO] Corrigez les paramètres IMAP dans .env avant de continuer.")
