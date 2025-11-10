#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de test pour valider la sélection de période avec auto-correction
"""

import sys
import time
from pathlib import Path
from datetime import datetime

# Ajouter le dossier parent au path
sys.path.insert(0, str(Path(__file__).parent))

from linxo_agent.linxo_driver_factory import initialiser_driver_linxo, se_connecter_linxo
from linxo_agent.period_selector import PeriodSelector


def test_period_selection():
    """
    Test complet de la sélection de période
    """
    print("\n" + "=" * 80)
    print("TEST DE SELECTION DE PERIODE AVEC AUTO-CORRECTION")
    print("=" * 80)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    driver = None
    user_data_dir = None

    try:
        # ÉTAPE 1: Initialisation
        print("\n[ETAPE 1] Initialisation du navigateur...")
        driver, wait, user_data_dir = initialiser_driver_linxo()
        print("[SUCCESS] Navigateur initialise")

        # ÉTAPE 2: Connexion
        print("\n[ETAPE 2] Connexion a Linxo...")
        if not se_connecter_linxo(driver, wait):
            print("[ERROR] Echec de la connexion")
            return False

        print("[SUCCESS] Connexion reussie")
        time.sleep(3)

        # ÉTAPE 3: Navigation vers historique
        print("\n[ETAPE 3] Navigation vers la page Historique...")
        driver.get('https://wwws.linxo.com/secured/history.page')
        time.sleep(5)
        print(f"[OK] URL: {driver.current_url}")

        # Sauvegarder un screenshot avant
        try:
            screenshot_before = Path(__file__).parent / "test_screenshots" / "before_period_selection.png"
            screenshot_before.parent.mkdir(parents=True, exist_ok=True)
            driver.save_screenshot(str(screenshot_before))
            print(f"[DEBUG] Screenshot avant: {screenshot_before}")
        except Exception as e:
            print(f"[WARNING] Impossible de sauvegarder le screenshot: {e}")

        # ÉTAPE 4: Test de sélection de période
        print("\n[ETAPE 4] Test de selection de periode...")
        period_selector = PeriodSelector(driver, wait)
        success = period_selector.select_period_with_autocorrect()

        # Sauvegarder un screenshot après
        try:
            screenshot_after = Path(__file__).parent / "test_screenshots" / "after_period_selection.png"
            driver.save_screenshot(str(screenshot_after))
            print(f"[DEBUG] Screenshot apres: {screenshot_after}")
        except Exception as e:
            print(f"[WARNING] Impossible de sauvegarder le screenshot: {e}")

        # RÉSULTAT
        print("\n" + "=" * 80)
        if success:
            print("[SUCCESS] Test de selection de periode REUSSI!")
            print("=" * 80)
            print("\nLa periode 'Ce mois-ci' a ete selectionnee avec succes.")
            print("Le CSV telecharge devrait contenir uniquement les donnees du mois en cours.")
            return True
        else:
            print("[ERROR] Test de selection de periode ECHOUE!")
            print("=" * 80)
            print("\nLa selection de periode n'a pas fonctionne.")
            print("Le filtrage CSV (etape 6) devra etre utilise comme fallback.")
            return False

    except Exception as e:
        print(f"\n[ERROR] Erreur durant le test: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        # Cleanup
        if driver:
            print("\n[CLEANUP] Fermeture du navigateur...")
            try:
                # Laisser le temps de voir les résultats
                print("[INFO] Appuyez sur Ctrl+C pour fermer le navigateur...")
                time.sleep(10)
            except KeyboardInterrupt:
                print("\n[INFO] Interruption utilisateur")

            driver.quit()
            print("[OK] Navigateur ferme")

        if user_data_dir and user_data_dir.exists():
            import shutil
            shutil.rmtree(user_data_dir, ignore_errors=True)
            print("[OK] Repertoire temporaire supprime")


def main():
    """Point d'entrée principal"""
    success = test_period_selection()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
