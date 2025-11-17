#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module de connexion Linxo avec undetected-chromedriver
Version spéciale pour contourner la détection anti-bot en mode headless
"""

import os
import platform
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path

try:
    import undetected_chromedriver as uc
except ImportError:
    print("[ERREUR] undetected-chromedriver n'est pas installé")
    print("[INFO] Installez-le avec: pip install undetected-chromedriver")
    sys.exit(1)

from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    WebDriverException
)
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

# Import du module de configuration unifié
try:
    from .config import get_config
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent))
    from config import get_config  # type: ignore

# Import du module 2FA
try:
    from .linxo_2fa import recuperer_code_2fa_email
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent))
    from linxo_2fa import recuperer_code_2fa_email  # type: ignore

# Importer les fonctions utilitaires du module standard
try:
    from .linxo_connexion import (
        _tuer_processus_chrome_zombies,
        _nettoyer_anciens_user_data_dirs,
        _creer_user_data_dir_unique,
        _gerer_2fa,
        se_connecter_linxo as se_connecter_linxo_standard
    )
except ImportError:
    from linxo_connexion import (  # type: ignore
        _tuer_processus_chrome_zombies,
        _nettoyer_anciens_user_data_dirs,
        _creer_user_data_dir_unique,
        _gerer_2fa,
        se_connecter_linxo as se_connecter_linxo_standard
    )


def initialiser_driver_linxo_undetected(
    download_dir=None,
    headless=False,
    cleanup=True,
    max_retries=3
):
    """
    Initialise un driver Chrome avec undetected-chromedriver pour contourner la détection

    Args:
        download_dir: Dossier de téléchargement (optionnel)
        headless: Mode headless (sans interface graphique)
        cleanup: Si True, nettoie les processus zombies (défaut: True)
        max_retries: Nombre de tentatives en cas d'échec (défaut: 3)

    Returns:
        tuple: (driver, wait, user_data_dir)

    Raises:
        WebDriverException: Si l'initialisation échoue après toutes les tentatives
    """
    print("[INIT] Initialisation avec undetected-chromedriver...")

    # Charger la config
    config = get_config()

    # Utiliser le dossier de téléchargement de la config si non fourni
    if download_dir is None:
        download_dir = config.downloads_dir

    # Créer le dossier s'il n'existe pas
    download_dir = Path(download_dir)
    download_dir.mkdir(parents=True, exist_ok=True)

    # CORRECTION: Créer un dossier de cache pour chromedriver dans le projet
    # pour éviter l'erreur "Read-only file system" sur VPS
    chromedriver_cache_dir = config.base_dir / '.chromedriver_cache'
    chromedriver_cache_dir.mkdir(parents=True, exist_ok=True)
    print(f"[INFO] Dossier de cache chromedriver: {chromedriver_cache_dir}")

    # ÉTAPE 1: Cleanup préventif (si activé)
    if cleanup:
        print("\n[CLEANUP] Nettoyage preventif...")
        _tuer_processus_chrome_zombies()
        _nettoyer_anciens_user_data_dirs(config.base_dir, max_age_hours=24)
        print("[CLEANUP] Nettoyage termine\n")

    # ÉTAPE 2: Tentatives d'initialisation avec retry
    last_exception = None
    user_data_dir = None

    for tentative in range(1, max_retries + 1):
        try:
            print(f"[INIT] Tentative {tentative}/{max_retries}...")

            # Créer un répertoire user-data UNIQUE pour cette session
            user_data_dir = _creer_user_data_dir_unique(config.base_dir)

            # Détection automatique du mode headless pour VPS/serveurs
            is_server = (
                os.environ.get('DISPLAY') is None or  # Pas d'affichage X
                'microsoft' in platform.uname().release.lower() or  # WSL
                headless  # Explicitement demandé
            )

            if is_server:
                print("[INFO] Mode headless actif (environnement serveur détecté)")

            print(f"[INFO] Dossier de téléchargement: {download_dir}")
            print(f"[INFO] Dossier user-data: {user_data_dir}")

            # Configuration des options pour undetected-chromedriver
            options = uc.ChromeOptions()

            # Options de base
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--window-size=1920,1080')
            options.add_argument(f'--user-data-dir={user_data_dir}')

            # Langue française
            options.add_argument('--lang=fr-FR')

            # Configuration des téléchargements
            prefs = {
                "download.default_directory": str(download_dir.absolute()),
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "safebrowsing.enabled": True,
                "intl.accept_languages": "fr-FR,fr"
            }
            options.add_experimental_option("prefs", prefs)

            # CORRECTION CRITIQUE : Rediriger le dossier de cache de undetected_chromedriver
            # pour éviter l'erreur "Read-only file system" sur VPS
            # On doit monkey-patcher la classe Patcher AVANT la création du driver
            print("[INFO] Configuration du cache chromedriver personnalisé...")

            import undetected_chromedriver.patcher as patcher_module

            # Sauvegarder la méthode originale __init__
            original_patcher_init = patcher_module.Patcher.__init__

            def patched_init(self, *args, **kwargs):
                # Appeler l'init original
                original_patcher_init(self, *args, **kwargs)
                # Rediriger data_path vers notre dossier personnalisé
                self.data_path = str(chromedriver_cache_dir)
                print(f"[DEBUG] Patcher redirigé vers: {self.data_path}")

            # Remplacer temporairement __init__
            patcher_module.Patcher.__init__ = patched_init

            try:
                # Création du driver avec undetected-chromedriver
                # Le patcher utilisera maintenant notre dossier personnalisé
                print("[INFO] Création du driver avec cache personnalisé...")
                driver = uc.Chrome(
                    options=options,
                    headless=is_server,
                    use_subprocess=True,
                    version_main=None  # Auto-detect Chrome version
                )
                print("[OK] Driver créé avec succès!")

            finally:
                # Restaurer la méthode originale pour ne pas affecter d'autres instances
                patcher_module.Patcher.__init__ = original_patcher_init

            # Configuration du timeout
            wait = WebDriverWait(driver, 30)

            print("[OK] Navigateur initialisé avec succès!")
            print("[OK] undetected-chromedriver actif (anti-détection)")

            # Retourner le driver, wait ET le user_data_dir pour cleanup ultérieur
            return driver, wait, user_data_dir

        except (WebDriverException, Exception) as e:
            last_exception = e
            error_msg = str(e)

            print(f"[ERREUR] Tentative {tentative} échouée: {error_msg[:200]}")

            # Cleanup du répertoire créé pour cette tentative
            if user_data_dir is not None:
                try:
                    if user_data_dir.exists():
                        import shutil
                        shutil.rmtree(user_data_dir, ignore_errors=True)
                        print(f"[CLEANUP] Répertoire temporaire supprimé: {user_data_dir.name}")
                except Exception as cleanup_error:
                    print(f"[WARN] Impossible de supprimer {user_data_dir.name}: {cleanup_error}")

            # Si c'est la dernière tentative, lever l'exception
            if tentative == max_retries:
                print(f"\n[ERREUR FATALE] Impossible d'initialiser le navigateur après {max_retries} tentatives")
                print("[INFO] Vérifiez que Chrome et ChromeDriver sont installés")
                raise

            # Attendre un peu avant la prochaine tentative
            time.sleep(2)

    # Cette ligne ne devrait jamais être atteinte, mais au cas où
    if last_exception:
        raise last_exception
    raise RuntimeError("Échec de l'initialisation du navigateur")


def se_connecter_linxo(driver, wait, email=None, password=None):
    """
    Fonction de connexion à Linxo (réutilise celle du module standard)

    Args:
        driver: Instance du WebDriver
        wait: Instance de WebDriverWait
        email: Email de connexion (optionnel)
        password: Mot de passe (optionnel)

    Returns:
        bool: True si connexion réussie, False sinon
    """
    # Utiliser la fonction standard qui gère déjà tout
    return se_connecter_linxo_standard(driver, wait, email, password)


# Fonction de test
if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("TEST DU MODULE UNDETECTED-CHROMEDRIVER")
    print("=" * 80)

    # pylint: disable=invalid-name
    test_driver = None
    test_user_data_dir = None
    try:
        # Initialiser le driver avec undetected-chromedriver
        test_driver, test_wait, test_user_data_dir = initialiser_driver_linxo_undetected(
            headless=True  # Forcer headless pour tester
        )

        # Se connecter
        success = se_connecter_linxo(test_driver, test_wait)

        if success:
            print("\n[SUCCESS] Test de connexion réussi avec undetected-chromedriver!")
            print(f"[INFO] URL finale: {test_driver.current_url}")
        else:
            print("\n[ERREUR] Test de connexion échoué")

        # Attendre avant fermeture
        input("\nAppuyez sur Entrée pour fermer le navigateur...")
        test_driver.quit()

        # Cleanup du répertoire temporaire
        if test_user_data_dir and test_user_data_dir.exists():
            import shutil
            shutil.rmtree(test_user_data_dir, ignore_errors=True)
            print(f"[CLEANUP] Répertoire temporaire supprimé: {test_user_data_dir.name}")

    except KeyboardInterrupt:
        print("\n[INFO] Test interrompu par l'utilisateur")
        if test_driver:
            try:
                test_driver.quit()
            except (WebDriverException, Exception):
                pass

        if test_user_data_dir and test_user_data_dir.exists():
            import shutil
            shutil.rmtree(test_user_data_dir, ignore_errors=True)

    except (WebDriverException, Exception) as e:
        print(f"\n[ERREUR] Erreur durant le test: {e}")
        traceback.print_exc()

        if test_user_data_dir and test_user_data_dir.exists():
            import shutil
            shutil.rmtree(test_user_data_dir, ignore_errors=True)
