#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de test simple pour la connexion Linxo
Lance Chrome et attend que vous vous connectiez manuellement
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time

def test_connexion_manuelle():
    """Lance Chrome et permet une connexion manuelle pour observer le comportement"""

    print("=== Test de connexion manuelle Linxo ===\n")
    print("Initialisation du navigateur...")

    options = Options()
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option('excludeSwitches', ['enable-automation'])
    options.add_experimental_option('useAutomationExtension', False)

    # Configuration des téléchargements
    download_dir = "c:/Users/PhilippePEREZ/OneDrive/LINXO/Downloads"
    prefs = {
        "download.default_directory": download_dir,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True
    }
    options.add_experimental_option('prefs', prefs)

    driver = webdriver.Chrome(options=options)

    try:
        print("Accès à la page de connexion Linxo...")
        driver.get("https://wwws.linxo.com/auth.page#Information")
        print(f"URL: {driver.current_url}")

        print("\n=== Instructions ===")
        print("1. Connectez-vous manuellement à Linxo")
        print("2. Attendez d'être sur la page principale")
        print("3. Appuyez sur Entrée dans ce terminal pour continuer...")
        input()

        print(f"\n[INFO] URL actuelle: {driver.current_url}")
        print("[INFO] Recherche du bouton d'export...")

        time.sleep(2)

        # Chercher le bouton d'export
        try:
            export_button = driver.find_element(By.CSS_SELECTOR, "button[aria-label='Exporter au format CSV']")
            print("[OK] Bouton d'export trouvé!")
            print(f"  - Text: {export_button.text}")
            print(f"  - Visible: {export_button.is_displayed()}")

            print("\n[ACTION] Clic sur le bouton d'export...")
            export_button.click()

            print("[INFO] Attente du téléchargement (10 secondes)...")
            time.sleep(10)

            print("\n[OK] Test terminé! Vérifiez le dossier Downloads.")

        except Exception as e:
            print(f"[ERREUR] Bouton d'export non trouvé: {e}")
            print("\n=== Recherche de tous les boutons ===")
            buttons = driver.find_elements(By.TAG_NAME, "button")
            for i, btn in enumerate(buttons[:10]):  # Afficher les 10 premiers
                print(f"Bouton {i+1}: {btn.text} | aria-label: {btn.get_attribute('aria-label')}")

        print("\nAppuyez sur Entrée pour fermer le navigateur...")
        input()

    except Exception as e:
        print(f"\n[ERREUR] {e}")
        import traceback
        traceback.print_exc()
    finally:
        driver.quit()
        print("Navigateur fermé.")

if __name__ == "__main__":
    test_connexion_manuelle()
