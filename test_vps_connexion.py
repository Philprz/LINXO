#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de test pour la connexion Linxo sur VPS (mode headless)
Ce script simule exactement les conditions du VPS
"""

import shutil
import sys
import time
import traceback
from pathlib import Path

# Ajouter le répertoire linxo_agent au path
sys.path.insert(0, str(Path(__file__).parent / "linxo_agent"))

from linxo_agent.linxo_connexion import initialiser_driver_linxo, se_connecter_linxo
from linxo_agent.config import get_config


def main():
    """
    Fonction principale de test en mode headless.

    Simule les conditions exactes du VPS pour diagnostic.
    """
    print("\n" + "=" * 80)
    print("TEST DE CONNEXION LINXO - MODE VPS (HEADLESS)")
    print("=" * 80)

    # Charger la configuration
    config = get_config()

    print("\n[CONFIG] Vérification de la configuration...")
    print(f"[CONFIG] Email Linxo: {config.linxo_email}")
    print(f"[CONFIG] URL Linxo: {config.linxo_url}")
    print(f"[CONFIG] Password présent: {'Oui' if config.linxo_password else 'Non'}")

    if not config.linxo_email or not config.linxo_password:
        print("\n[ERREUR] Credentials Linxo manquants!")
        print("[INFO] Vérifiez votre fichier .env")
        return

    print("\n[TEST] Initialisation du navigateur en mode headless...")
    driver = None
    user_data_dir = None

    try:
        # Forcer le mode headless pour simuler le VPS
        driver, wait, user_data_dir = initialiser_driver_linxo(headless=True)

        print("\n[TEST] Tentative de connexion...")
        success = se_connecter_linxo(driver, wait)

        if success:
            print("\n" + "=" * 80)
            print("[SUCCESS] CONNEXION RÉUSSIE EN MODE HEADLESS!")
            print("=" * 80)
            print(f"[INFO] URL finale: {driver.current_url}")
            print("\n[INFO] Le problème VPS devrait être résolu!")
        else:
            print("\n" + "=" * 80)
            print("[ERREUR] CONNEXION ÉCHOUÉE EN MODE HEADLESS")
            print("=" * 80)
            print("[INFO] Vérifiez les fichiers suivants pour le diagnostic:")
            print("  - /tmp/before_login_click.png")
            print("  - /tmp/after_login_click.png")
            print("  - /tmp/login_failed_page.html")
            print("\n[SUGGESTIONS]")
            print("  1. Vérifier si Linxo bloque les connexions headless")
            print("  2. Essayer avec undetected-chromedriver (pip install undetected-chromedriver)")
            print("  3. Utiliser un proxy ou VPN pour masquer l'IP du VPS")

        # Attendre un peu pour voir le résultat
        print("\n[INFO] Attente de 5 secondes avant fermeture...")
        time.sleep(5)

    except KeyboardInterrupt:
        print("\n[INFO] Test interrompu par l'utilisateur")

    except Exception as e:  # pylint: disable=broad-exception-caught
        print(f"\n[ERREUR] Erreur durant le test: {e}")
        traceback.print_exc()

    finally:
        # Cleanup
        if driver:
            try:
                driver.quit()
                print("[INFO] Navigateur fermé")
            except Exception:  # pylint: disable=broad-exception-caught
                pass

        if user_data_dir and user_data_dir.exists():
            shutil.rmtree(user_data_dir, ignore_errors=True)
            print(f"[CLEANUP] Répertoire temporaire supprimé: {user_data_dir.name}")


if __name__ == "__main__":
    main()
