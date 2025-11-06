#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de debug pour analyser la page de connexion Linxo
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

def debug_linxo_page():
    """Analyse la structure de la page de connexion Linxo"""

    print("Initialisation du navigateur...")
    options = Options()
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option('excludeSwitches', ['enable-automation'])
    options.add_experimental_option('useAutomationExtension', False)

    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 10)

    try:
        print("Accès à la page de connexion Linxo...")
        driver.get("https://wwws.linxo.com/auth.page#Information")
        time.sleep(3)

        print(f"\n[DEBUG] URL actuelle: {driver.current_url}")
        print(f"[DEBUG] Titre de la page: {driver.title}")

        # Chercher tous les inputs
        print("\n=== Recherche de tous les champs input ===")
        inputs = driver.find_elements(By.TAG_NAME, "input")
        print(f"Nombre d'inputs trouvés: {len(inputs)}")

        for i, input_elem in enumerate(inputs):
            try:
                input_type = input_elem.get_attribute("type")
                input_name = input_elem.get_attribute("name")
                input_id = input_elem.get_attribute("id")
                input_class = input_elem.get_attribute("class")
                input_placeholder = input_elem.get_attribute("placeholder")

                print(f"\nInput {i+1}:")
                print(f"  - Type: {input_type}")
                print(f"  - Name: {input_name}")
                print(f"  - ID: {input_id}")
                print(f"  - Class: {input_class}")
                print(f"  - Placeholder: {input_placeholder}")
            except Exception as e:
                print(f"  Erreur: {e}")

        # Chercher tous les boutons
        print("\n=== Recherche de tous les boutons ===")
        buttons = driver.find_elements(By.TAG_NAME, "button")
        print(f"Nombre de boutons trouvés: {len(buttons)}")

        for i, button in enumerate(buttons):
            try:
                button_type = button.get_attribute("type")
                button_text = button.text
                button_class = button.get_attribute("class")

                print(f"\nBouton {i+1}:")
                print(f"  - Type: {button_type}")
                print(f"  - Text: {button_text}")
                print(f"  - Class: {button_class}")
            except Exception as e:
                print(f"  Erreur: {e}")

        # Sauvegarder un screenshot
        screenshot_path = "c:/Users/PhilippePEREZ/OneDrive/LINXO/debug_linxo_page.png"
        driver.save_screenshot(screenshot_path)
        print(f"\n[DEBUG] Screenshot sauvegardé: {screenshot_path}")

        # Sauvegarder le HTML de la page
        html_path = "c:/Users/PhilippePEREZ/OneDrive/LINXO/debug_linxo_page.html"
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        print(f"[DEBUG] HTML sauvegardé: {html_path}")

        print("\nAppuyez sur Entrée pour fermer le navigateur...")
        input()

    except Exception as e:
        print(f"\n[ERREUR] {e}")
        import traceback
        traceback.print_exc()
    finally:
        driver.quit()

if __name__ == "__main__":
    debug_linxo_page()
