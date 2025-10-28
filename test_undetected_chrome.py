#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de test pour undetected-chromedriver
Test de connexion Linxo en mode headless avec anti-détection avancée
"""

import shutil
import sys
import time
import traceback
from pathlib import Path

# Ajouter le répertoire linxo_agent au path
sys.path.insert(0, str(Path(__file__).parent / "linxo_agent"))

try:
    from linxo_agent.linxo_connexion_undetected import (
        initialiser_driver_linxo_undetected,
        se_connecter_linxo
    )
    from linxo_agent.config import get_config
except ImportError as e:
    print(f"[ERREUR] Import échoué: {e}")
    print("\n[INFO] Installez undetected-chromedriver:")
    print("  pip install undetected-chromedriver")
    sys.exit(1)


def main():
    """
    Fonction principale de test avec undetected-chromedriver.

    Teste la connexion en mode headless avec anti-détection avancée.
    """
    print("\n" + "=" * 80)
    print("TEST UNDETECTED-CHROMEDRIVER - MODE HEADLESS")
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

    print("\n[TEST] Initialisation avec undetected-chromedriver...")
    print("[INFO] Cette méthode contourne la détection anti-bot de Linxo")
    driver = None
    user_data_dir = None

    try:
        # Forcer le mode headless pour tester
        driver, wait, user_data_dir = initialiser_driver_linxo_undetected(headless=True)

        print("\n[TEST] Tentative de connexion...")
        success = se_connecter_linxo(driver, wait)

        if success:
            print("\n" + "=" * 80)
            print("[SUCCESS] CONNEXION RÉUSSIE AVEC UNDETECTED-CHROMEDRIVER!")
            print("=" * 80)
            print(f"[INFO] URL finale: {driver.current_url}")
            print("\n[SUCCESS] La solution fonctionne! Le problème VPS est résolu!")
            print("\n[INFO] Prochaines étapes:")
            print("  1. Transférer les fichiers sur le VPS")
            print("  2. Installer undetected-chromedriver: pip install undetected-chromedriver")
            print("  3. Modifier run_linxo_e2e.py pour utiliser linxo_connexion_undetected")
        else:
            print("\n" + "=" * 80)
            print("[ERREUR] CONNEXION ÉCHOUÉE MÊME AVEC UNDETECTED-CHROMEDRIVER")
            print("=" * 80)
            print("[INFO] Vérifiez les fichiers suivants:")
            print("  - /tmp/before_login_click.png")
            print("  - /tmp/after_login_click.png")
            print("  - /tmp/login_failed_page.html")
            print("\n[SUGGESTIONS]")
            print("  1. Vérifier les credentials dans .env")
            print("  2. Vérifier si Linxo a changé sa page de connexion")
            print("  3. Essayer depuis une autre IP (proxy/VPN)")

        # Attendre un peu pour voir le résultat
        print("\n[INFO] Attente de 5 secondes avant fermeture...")
        time.sleep(5)

    except KeyboardInterrupt:
        print("\n[INFO] Test interrompu par l'utilisateur")

    except Exception as e:  # pylint: disable=broad-exception-caught
        print(f"\n[ERREUR] Erreur durant le test: {e}")
        traceback.print_exc()
        print("\n[INFO] Si l'erreur mentionne 'undetected_chromedriver', installez-le:")
        print("  pip install undetected-chromedriver")

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
