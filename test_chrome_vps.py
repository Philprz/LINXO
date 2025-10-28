#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de test pour vérifier que Chrome fonctionne correctement sur le VPS
"""

import sys
import os
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

def test_chrome_setup():
    """Teste la configuration Chrome sur le VPS"""

    print("=" * 80)
    print("TEST DE CONFIGURATION CHROME POUR VPS")
    print("=" * 80)

    # Test 1: Vérifier les imports
    print("\n[TEST 1/5] Vérification des imports Selenium...")
    try:

        print("✓ Imports Selenium OK")
    except ImportError as e:
        print(f"✗ ERREUR : {e}")
        print("  Solution : pip install selenium")
        return False

    # Test 2: Vérifier l'environnement
    print("\n[TEST 2/5] Vérification de l'environnement...")
    print(f"  Python : {sys.version.split()[0]}")
    print(f"  OS : {sys.platform}")
    print(f"  DISPLAY : {os.environ.get('DISPLAY', 'Non défini (mode headless détecté)')}")

    display_available = os.environ.get('DISPLAY') is not None
    if not display_available:
        print("✓ Mode headless sera activé automatiquement")
    else:
        print("  Mode GUI disponible")

    # Test 3: Tester l'initialisation de Chrome
    print("\n[TEST 3/5] Test d'initialisation de Chrome...")

    # Configuration similaire à celle du projet
    user_data_dir = Path.cwd() / ".chrome_user_data_test"
    user_data_dir.mkdir(parents=True, exist_ok=True)

    options = Options()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-software-rasterizer')
    options.add_argument(f'--user-data-dir={user_data_dir}')
    options.add_argument('--remote-debugging-port=9223')  # Port différent pour le test

    # Forcer headless si pas de DISPLAY
    if not display_available:
        options.add_argument('--headless=new')
        print("  Mode headless activé")

    try:
        driver = webdriver.Chrome(options=options)
        print("✓ Chrome initialisé avec succès")

        # Test 4: Naviguer vers une page simple
        print("\n[TEST 4/5] Test de navigation...")
        driver.get("https://www.google.com")
        print(f"✓ Navigation réussie : {driver.title}")

        # Test 5: Vérifier les capacités
        print("\n[TEST 5/5] Vérification des capacités...")
        capabilities = driver.capabilities
        print(f"  Chrome version : {capabilities.get('browserVersion', 'Inconnue')}")
        print(f"  ChromeDriver version : 
              {capabilities.get('chrome', {}).get('chromedriverVersion', 'Inconnue').split()[0]}"
            )

        # Nettoyage
        driver.quit()
        print("\n✓ Driver fermé proprement")

        # Nettoyer le répertoire de test
        import shutil
        try:
            shutil.rmtree(user_data_dir)
            print("✓ Répertoire de test nettoyé")
        except Exception as e:
            print(f"⚠ Impossible de nettoyer {user_data_dir}: {e}")

        print("\n" + "=" * 80)
        print("✓ TOUS LES TESTS RÉUSSIS !")
        print("=" * 80)
        print("\nVotre configuration Chrome est prête pour Linxo Agent.")
        return True

    except Exception as e:
        print("\n✗ ERREUR lors de l'initialisation de Chrome :")
        print(f"  {e}")
        print("\nDiagnostic :")
        print("  1. Vérifiez que Chrome est installé : google-chrome --version")
        print("  2. Vérifiez que ChromeDriver est installé : chromedriver --version")
        print("  3. Assurez-vous que les versions correspondent")
        print("  4. Exécutez le script de nettoyage : ./cleanup_chrome.sh")
        print("\nConsultez VPS_SETUP.md pour plus d'informations.")

        # Tentative de nettoyage
        try:
            driver.quit()
        except:
            pass

        return False

def check_chrome_processes():
    """Vérifie les processus Chrome en cours"""
    print("\n[BONUS] Vérification des processus Chrome...")

    try:
        import subprocess
        result = subprocess.run(
            ['ps', 'aux'],
            capture_output=True,
            text=True
        )

        chrome_lines = [
            line for line in result.stdout.split('\n')
            if 'chrome' in line.lower() and 'grep' not in line.lower()
        ]

        if chrome_lines:
            print(f"⚠ {len(chrome_lines)} processus Chrome détectés :")
            for line in chrome_lines[:5]:  # Limiter à 5 pour la lisibilité
                print(f"  {line}")
            if len(chrome_lines) > 5:
                print(f"  ... et {len(chrome_lines) - 5} autres")
            print("\n  Conseil : Exécutez ./cleanup_chrome.sh avant de lancer l'agent")
        else:
            print("✓ Aucun processus Chrome en cours")

    except Exception as e:
        print(f"  Impossible de vérifier les processus : {e}")

if __name__ == "__main__":
    print("\n")

    # Vérifier les processus avant le test
    check_chrome_processes()

    print("\n")

    # Exécuter les tests
    success = test_chrome_setup()

    # Code de sortie
    sys.exit(0 if success else 1)
