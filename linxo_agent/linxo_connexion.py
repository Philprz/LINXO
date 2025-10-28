#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module de connexion standardisé pour Linxo
Version 2.0 - Refactorisée avec configuration unifiée
"""

import os
import platform
import sys
import time
import traceback
import signal
import shutil
import psutil
from pathlib import Path
from datetime import datetime, timedelta

from selenium import webdriver
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    WebDriverException
)
from selenium.webdriver.chrome.options import Options
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


def _tuer_processus_chrome_zombies():
    """
    Tue tous les processus Chrome/ChromeDriver zombies ou orphelins
    Utile pour nettoyer avant de démarrer une nouvelle session

    Returns:
        int: Nombre de processus tués
    """
    processus_tues = 0

    try:
        # Liste des processus à tuer
        process_names = ['chrome', 'chromedriver', 'chromium']

        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                proc_name = proc.info['name'].lower() if proc.info['name'] else ''
                cmdline = proc.info['cmdline'] if proc.info['cmdline'] else []
                cmdline_str = ' '.join(cmdline).lower()

                # Vérifier si c'est un processus Chrome/ChromeDriver lié à notre projet
                is_target = any(name in proc_name for name in process_names)
                is_selenium = 'selenium' in cmdline_str or 'webdriver' in cmdline_str

                if is_target and (is_selenium or '--remote-debugging-port=9222' in cmdline_str):
                    print(f"[CLEANUP] Arret du processus zombie: {proc.info['name']} (PID: {proc.info['pid']})")
                    proc.terminate()

                    # Attendre 2 secondes pour la terminaison gracieuse
                    try:
                        proc.wait(timeout=2)
                    except psutil.TimeoutExpired:
                        # Force kill si nécessaire
                        proc.kill()

                    processus_tues += 1

            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                # Le processus a déjà disparu ou on n'a pas les droits
                continue

    except Exception as e:
        print(f"[WARN] Erreur lors du nettoyage des processus: {e}")

    if processus_tues > 0:
        print(f"[CLEANUP] {processus_tues} processus Chrome/ChromeDriver arretes")
        # Attendre un peu pour que les locks soient libérés
        time.sleep(2)

    return processus_tues


def _nettoyer_anciens_user_data_dirs(base_dir, max_age_hours=24):
    """
    Nettoie les anciens répertoires user-data temporaires

    Args:
        base_dir: Répertoire de base contenant les répertoires temporaires
        max_age_hours: Age maximum en heures avant suppression (défaut: 24h)

    Returns:
        int: Nombre de répertoires supprimés
    """
    repertoires_supprimes = 0

    try:
        base_path = Path(base_dir)
        if not base_path.exists():
            return 0

        # Chercher tous les répertoires correspondant au pattern
        pattern = '.chrome_user_data_*'
        current_time = datetime.now()
        max_age = timedelta(hours=max_age_hours)

        for user_data_dir in base_path.glob(pattern):
            if not user_data_dir.is_dir():
                continue

            try:
                # Vérifier l'âge du répertoire
                dir_mtime = datetime.fromtimestamp(user_data_dir.stat().st_mtime)
                age = current_time - dir_mtime

                if age > max_age:
                    print(f"[CLEANUP] Suppression du repertoire ancien: {user_data_dir.name} (age: {age.total_seconds()/3600:.1f}h)")
                    shutil.rmtree(user_data_dir, ignore_errors=True)
                    repertoires_supprimes += 1

            except (OSError, ValueError) as e:
                print(f"[WARN] Impossible de supprimer {user_data_dir.name}: {e}")
                continue

    except Exception as e:
        print(f"[WARN] Erreur lors du nettoyage des repertoires: {e}")

    if repertoires_supprimes > 0:
        print(f"[CLEANUP] {repertoires_supprimes} anciens repertoires supprimes")

    return repertoires_supprimes


def _creer_user_data_dir_unique(base_dir):
    """
    Crée un répertoire user-data-dir unique pour cette session

    Args:
        base_dir: Répertoire de base où créer le répertoire temporaire

    Returns:
        Path: Chemin du répertoire créé
    """
    # Format: .chrome_user_data_YYYYMMDD_HHMMSS_PID
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    pid = os.getpid()
    user_data_dir = Path(base_dir) / f".chrome_user_data_{timestamp}_{pid}"

    # Créer le répertoire
    user_data_dir.mkdir(parents=True, exist_ok=True)

    return user_data_dir


def _gerer_2fa(driver, wait):
    """
    Gère l'étape de vérification 2FA automatiquement

    Args:
        driver: Instance du WebDriver Selenium
        wait: Instance de WebDriverWait

    Returns:
        bool: True si 2FA réussi et connexion OK, False sinon
    """
    print("\n[2FA] Gestion du 2FA...")

    try:
        # Récupérer le code 2FA depuis l'email
        code_2fa = recuperer_code_2fa_email(timeout=120, check_interval=5)

        if not code_2fa:
            print("[ERREUR] Impossible de récupérer le code 2FA")
            return False

        print(f"[2FA] Code récupéré: {code_2fa}")

        # Chercher le champ de saisie du code 2FA
        code_field = None

        print(f"[2FA] URL actuelle: {driver.current_url}")
        print("[2FA] Recherche du champ de saisie...")

        # Méthode 1: Par nom "code"
        try:
            code_field = wait.until(
                EC.presence_of_element_located((By.NAME, "code"))
            )
            print("[2FA] Champ code trouvé (par name)")
        except (TimeoutException, NoSuchElementException) as e:
            print(f"[DEBUG] Méthode 1 échouée: {e}")

        # Méthode 2: Par ID "code"
        if not code_field:
            try:
                code_field = driver.find_element(By.ID, "code")
                print("[2FA] Champ code trouvé (par ID)")
            except NoSuchElementException as e:
                print(f"[DEBUG] Méthode 2 échouée: {e}")

        # Méthode 3: Par type "text" et placeholder
        if not code_field:
            try:
                code_field = driver.find_element(
                    By.CSS_SELECTOR,
                    "input[type='text'][placeholder*='code' i]"
                )
                print("[2FA] Champ code trouvé (par CSS)")
            except NoSuchElementException as e:
                print(f"[DEBUG] Méthode 3 échouée: {e}")

        # Méthode 4: N'importe quel input type="text"
        if not code_field:
            try:
                code_field = driver.find_element(By.CSS_SELECTOR, "input[type='text']")
                print("[2FA] Champ code trouvé (input text)")
            except NoSuchElementException as e:
                print(f"[DEBUG] Méthode 4 échouée: {e}")

        # Méthode 5: N'importe quel input type="number" (parfois utilisé pour les codes)
        if not code_field:
            try:
                code_field = driver.find_element(By.CSS_SELECTOR, "input[type='number']")
                print("[2FA] Champ code trouvé (input number)")
            except NoSuchElementException as e:
                print(f"[DEBUG] Méthode 5 échouée: {e}")

        # Méthode 6: N'importe quel input
        if not code_field:
            try:
                code_field = driver.find_element(By.TAG_NAME, "input")
                print("[2FA] Champ code trouvé (input générique)")
            except NoSuchElementException as e:
                print(f"[DEBUG] Méthode 6 échouée: {e}")

        if not code_field:
            print("[ERREUR] Champ de saisie du code 2FA introuvable")
            print("[DEBUG] Sauvegarde du HTML de la page pour diagnostic...")
            try:
                with open("/tmp/2fa_page.html", "w", encoding="utf-8") as f:
                    f.write(driver.page_source)
                print("[DEBUG] HTML sauvegardé dans /tmp/2fa_page.html")
            except Exception as save_error:
                print(f"[WARN] Impossible de sauvegarder le HTML: {save_error}")
            return False

        # Saisir le code
        code_field.clear()
        code_field.send_keys(code_2fa)
        print("[2FA] Code saisi")
        time.sleep(2)

        # ESSAYER D'ABORD AVEC LA TOUCHE ENTER (plus fiable)
        print("[2FA] Tentative de validation avec la touche Enter...")
        from selenium.webdriver.common.keys import Keys  # pylint: disable=import-outside-toplevel
        code_field.send_keys(Keys.RETURN)
        time.sleep(3)  # Attendre un peu pour voir si ça marche

        # Vérifier si on est toujours sur la page 2FA
        current_url_after_enter = driver.current_url.lower()
        if 'login' not in current_url_after_enter and 'auth' not in current_url_after_enter:
            print("[2FA] Validation réussie avec Enter!")
            print(f"[2FA] URL après validation: {driver.current_url}")
            print("[SUCCESS] Connexion réussie après 2FA!")
            return True

        # Si Enter n'a pas marché, chercher le bouton
        print("[2FA] Enter n'a pas fonctionné, recherche du bouton...")
        submit_button = None

        # Méthode 1: Par texte "Valider", "Confirmer", "Vérifier"
        for button_text in ["Valider", "Confirmer", "Vérifier", "Envoyer", "Continuer"]:
            try:
                # Attendre que le bouton soit cliquable
                submit_button = wait.until(
                    EC.element_to_be_clickable((
                        By.XPATH,
                        f"//button[contains(text(), '{button_text}')]"
                    ))
                )
                print(f"[2FA] Bouton '{button_text}' trouvé et cliquable")
                break
            except (TimeoutException, NoSuchElementException):
                pass

        # Méthode 2: Par type submit avec attente
        if not submit_button:
            try:
                submit_button = wait.until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']"))
                )
                print("[2FA] Bouton submit trouvé et cliquable")
            except (TimeoutException, NoSuchElementException):
                pass

        # Méthode 3: N'importe quel bouton avec attente
        if not submit_button:
            try:
                submit_button = wait.until(
                    EC.element_to_be_clickable((By.TAG_NAME, "button"))
                )
                print("[2FA] Bouton générique trouvé et cliquable")
            except (TimeoutException, NoSuchElementException):
                pass

        if not submit_button:
            print("[WARNING] Aucun bouton cliquable trouvé")
            # On a déjà essayé Enter plus haut, donc rien de plus à faire
        else:
            # Cliquer sur le bouton
            submit_button.click()
            print("[2FA] Bouton de validation cliqué")

        # Attendre la redirection
        time.sleep(8)

        print(f"[2FA] URL après validation: {driver.current_url}")

        # Sauvegarder un screenshot pour debug
        try:
            screenshot_path = "/tmp/2fa_after_submit.png"
            driver.save_screenshot(screenshot_path)
            print(f"[DEBUG] Screenshot sauvegardé: {screenshot_path}")
        except Exception as screenshot_error:
            print(f"[WARN] Impossible de sauvegarder le screenshot: {screenshot_error}")

        # Vérifier si connecté
        current_url_lower = driver.current_url.lower()
        if ('login' not in current_url_lower and
            'auth' not in current_url_lower and
            '2fa' not in current_url_lower):
            print("[SUCCESS] Connexion réussie après 2FA!")
            return True

        # Vérifier s'il y a un message d'erreur sur la page
        page_source_lower = driver.page_source.lower()
        if 'incorrect' in page_source_lower or 'invalide' in page_source_lower or 'erreur' in page_source_lower:
            print("[ERREUR] Code 2FA incorrect ou invalide détecté sur la page")
        else:
            print("[ERREUR] Échec de la validation 2FA (raison inconnue)")

        print("[DEBUG] Contenu de la page pour diagnostic:")
        print(driver.page_source[:500])  # Afficher les 500 premiers caractères

        return False

    except Exception as e:
        print(f"[ERREUR] Erreur lors de la gestion du 2FA: {e}")
        traceback.print_exc()
        return False


def se_connecter_linxo(driver, wait, email=None, password=None):
    """
    Fonction standardisée de connexion à Linxo

    Args:
        driver: Instance du WebDriver Selenium
        wait: Instance de WebDriverWait
        email: Email de connexion (optionnel, utilise config si non fourni)
        password: Mot de passe (optionnel, utilise config si non fourni)

    Returns:
        bool: True si connexion réussie, False sinon
    """
    print("\n[CONNEXION] Connexion a Linxo...")

    try:
        # Charger les credentials depuis la config si non fournis
        if email is None or password is None:
            config = get_config()
            email = config.linxo_email
            password = config.linxo_password
            linxo_url = config.linxo_url
        else:
            linxo_url = 'https://wwws.linxo.com/auth.page#Login'

        if not email or not password:
            print("[ERREUR] Credentials Linxo manquants dans la configuration")
            return False

        # Aller directement sur la page de login
        driver.get(linxo_url)
        time.sleep(3)

        print(f"[OK] URL: {driver.current_url}")

        # Chercher le champ username (name="username")
        try:
            username_field = wait.until(
                EC.presence_of_element_located((By.NAME, "username"))
            )
            print("[OK] Champ username trouve")
        except (TimeoutException, NoSuchElementException) as e:
            print(f"[ERREUR] Champ username non trouve: {e}")
            return False

        # Chercher le champ password (name="password")
        try:
            password_field = driver.find_element(By.NAME, "password")
            print("[OK] Champ password trouve")
        except NoSuchElementException as e:
            print(f"[ERREUR] Champ password non trouve: {e}")
            return False

        # Remplir les champs avec des délais plus "humains"
        print("[ACTION] Remplissage des identifiants...")
        username_field.clear()
        time.sleep(0.5)  # Petite pause après clear

        # Taper l'email caractère par caractère (plus humain)
        for char in email:
            username_field.send_keys(char)
            time.sleep(0.1)  # 100ms entre chaque caractère
        time.sleep(1)

        password_field.clear()
        time.sleep(0.5)

        # Taper le mot de passe caractère par caractère
        for char in password:
            password_field.send_keys(char)
            time.sleep(0.1)
        time.sleep(2)  # Pause plus longue après remplissage

        # Chercher et cliquer sur le bouton "Je me connecte"
        submit_button = None
        try:
            # Chercher par texte du bouton
            submit_button = wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//button[contains(text(), 'Je me connecte')]")
                )
            )
            print("[OK] Bouton 'Je me connecte' trouve")
        except (TimeoutException, NoSuchElementException):
            # Fallback: chercher par type submit
            try:
                submit_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
                print("[OK] Bouton submit trouve")
            except NoSuchElementException as e:
                print(f"[ERREUR] Bouton de connexion non trouve: {e}")
                return False

        print("[ACTION] Tentative de connexion...")

        # Sauvegarder un screenshot avant le clic
        try:
            screenshot_path = "/tmp/before_login_click.png"
            driver.save_screenshot(screenshot_path)
            print(f"[DEBUG] Screenshot avant clic sauvegardé: {screenshot_path}")
        except Exception as e:
            print(f"[WARN] Screenshot impossible: {e}")

        submit_button.click()

        # Attendre la redirection (délai important pour laisser le temps au 2FA)
        # En mode headless, la page peut mettre plus de temps à se charger
        print("[INFO] Attente de la redirection...")
        time.sleep(8)  # Augmenter à 8 secondes pour le 2FA

        # Sauvegarder un screenshot après le clic
        try:
            screenshot_path = "/tmp/after_login_click.png"
            driver.save_screenshot(screenshot_path)
            print(f"[DEBUG] Screenshot après clic sauvegardé: {screenshot_path}")
        except Exception as e:
            print(f"[WARN] Screenshot impossible: {e}")

        print(f"[OK] URL apres connexion: {driver.current_url}")

        # Debug: afficher un extrait de la page pour voir s'il y a un message d'erreur
        page_text = driver.page_source[:1000].lower()
        if 'erreur' in page_text or 'incorrect' in page_text or 'invalide' in page_text:
            print("[DEBUG] Message d'erreur détecté dans la page!")
            print("[DEBUG] Extrait de la page:")
            print(driver.page_source[:500])

        # ÉTAPE 1: Vérifier si on est sur une page 2FA (par URL)
        current_url_lower = driver.current_url.lower()
        if '2fa' in current_url_lower or 'verification' in current_url_lower:
            print("[2FA] Page de vérification 2FA détectée (par URL)")
            return _gerer_2fa(driver, wait)

        # ÉTAPE 2: Chercher un champ de code 2FA (même si l'URL ne change pas)
        # Ceci est crucial car Linxo peut afficher le 2FA sur la même URL
        try:
            driver.find_element(By.NAME, "code")
            print("[2FA] Champ de code 2FA détecté (par name='code')")
            return _gerer_2fa(driver, wait)
        except NoSuchElementException:
            pass

        try:
            driver.find_element(By.ID, "code")
            print("[2FA] Champ de code 2FA détecté (par id='code')")
            return _gerer_2fa(driver, wait)
        except NoSuchElementException:
            pass

        # Chercher par placeholder (ex: "Entrez le code")
        try:
            code_input = driver.find_element(By.CSS_SELECTOR, "input[placeholder*='code' i]")
            if code_input.is_displayed():
                print("[2FA] Champ de code 2FA détecté (par placeholder)")
                return _gerer_2fa(driver, wait)
        except NoSuchElementException:
            pass

        # ÉTAPE 3: Vérifier par texte dans la page
        page_source_lower = driver.page_source.lower()

        # Rechercher des mots-clés spécifiques au 2FA
        keywords_2fa = [
            ('code', 'verification'),
            ('code', 'validation'),
            ('double authentification', ''),
            ('authentification forte', ''),
            ('code de sécurité', ''),
            ('code reçu par', ''),
        ]

        for keyword1, keyword2 in keywords_2fa:
            if keyword1 in page_source_lower and (not keyword2 or keyword2 in page_source_lower):
                print(f"[2FA] Page de vérification détectée (mots-clés: '{keyword1}' + '{keyword2}')")
                return _gerer_2fa(driver, wait)

        # ÉTAPE 4: Vérifier si connecté (on ne doit plus être sur la page de login)
        if 'login' not in current_url_lower and 'auth' not in current_url_lower:
            print("[SUCCESS] Connexion reussie!")
            return True

        print("[ERREUR] Echec de la connexion (toujours sur la page de login)")

        # Sauvegarder le HTML complet de la page pour diagnostic
        try:
            html_path = "/tmp/login_failed_page.html"
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            print(f"[DEBUG] HTML complet sauvegardé: {html_path}")
            print("[DEBUG] Vérifiez ce fichier pour voir les messages d'erreur")
        except Exception as save_error:
            print(f"[WARN] Impossible de sauvegarder le HTML: {save_error}")

        return False

    except Exception as e:
        print(f"[ERREUR] Erreur lors de la connexion: {e}")
        traceback.print_exc()
        return False


def initialiser_driver_linxo(download_dir=None, headless=False, cleanup=True, max_retries=3):
    """
    Initialise un driver Chrome configuré pour Linxo
    Version 3.0 - Avec gestion robuste des conflits et cleanup automatique

    Args:
        download_dir: Dossier de téléchargement (optionnel, utilise config par défaut)
        headless: Mode headless (sans interface graphique)
        cleanup: Si True, nettoie les processus zombies et anciens répertoires (défaut: True)
        max_retries: Nombre de tentatives en cas d'échec (défaut: 3)

    Returns:
        tuple: (driver, wait, user_data_dir)
              Le user_data_dir est retourné pour permettre le cleanup après utilisation

    Raises:
        WebDriverException: Si l'initialisation échoue après toutes les tentatives
    """
    print("[INIT] Initialisation du navigateur...")

    # Charger la config
    config = get_config()

    # Utiliser le dossier de téléchargement de la config si non fourni
    if download_dir is None:
        download_dir = config.downloads_dir

    # Créer le dossier s'il n'existe pas
    download_dir = Path(download_dir)
    download_dir.mkdir(parents=True, exist_ok=True)

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

            options = Options()
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--window-size=1920,1080')
            options.add_argument(f'--user-data-dir={user_data_dir}')

            # Options pour éviter la détection d'automatisation
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)

            # User-Agent réaliste (Chrome 120 sur Linux)
            user_agent = (
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            options.add_argument(f'user-agent={user_agent}')

            # Options GPU améliorées pour headless
            options.add_argument('--disable-gpu')
            options.add_argument('--disable-software-rasterizer')
            options.add_argument('--disable-dev-shm-usage')

            # Options supplémentaires pour masquer l'automatisation
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_argument('--disable-infobars')
            options.add_argument('--disable-browser-side-navigation')
            options.add_argument('--disable-features=VizDisplayCompositor')

            # Langue et localisation
            options.add_argument('--lang=fr-FR')

            # Port de debugging unique basé sur le PID pour éviter les conflits
            debug_port = 9222 + (os.getpid() % 1000)
            options.add_argument(f'--remote-debugging-port={debug_port}')

            # Détection automatique du mode headless pour VPS/serveurs
            is_server = (
                os.environ.get('DISPLAY') is None or  # Pas d'affichage X
                'microsoft' in platform.uname().release.lower() or  # WSL
                headless  # Explicitement demandé
            )

            if is_server:
                options.add_argument('--headless=new')
                print("[INFO] Mode headless active (environnement serveur detecte)")

            # Configuration complète des préférences (téléchargements + langue)
            prefs = {
                "download.default_directory": str(download_dir.absolute()),
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "safebrowsing.enabled": True,
                "intl.accept_languages": "fr-FR,fr"
            }
            options.add_experimental_option("prefs", prefs)

            print(f"[INFO] Dossier de telechargement: {download_dir}")
            print(f"[INFO] Dossier user-data: {user_data_dir}")
            print(f"[INFO] Port de debugging: {debug_port}")

            # Tentative de création du driver
            driver = webdriver.Chrome(options=options)

            # Masquer les propriétés webdriver avec JavaScript
            driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                'source': '''
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    });
                    Object.defineProperty(navigator, 'plugins', {
                        get: () => [1, 2, 3, 4, 5]
                    });
                    Object.defineProperty(navigator, 'languages', {
                        get: () => ['fr-FR', 'fr', 'en-US', 'en']
                    });
                    window.chrome = {
                        runtime: {}
                    };
                '''
            })

            wait = WebDriverWait(driver, 30)
            print("[OK] Navigateur initialise avec succes!")
            print("[OK] Masquage des proprietes webdriver applique")

            # Retourner le driver, wait ET le user_data_dir pour cleanup ultérieur
            return driver, wait, user_data_dir

        except WebDriverException as e:
            last_exception = e
            error_msg = str(e)

            print(f"[ERREUR] Tentative {tentative} echouee: {error_msg[:200]}")

            # Cleanup du répertoire créé pour cette tentative
            if user_data_dir is not None:
                try:
                    if user_data_dir.exists():
                        shutil.rmtree(user_data_dir, ignore_errors=True)
                        print(f"[CLEANUP] Repertoire temporaire supprime: {user_data_dir.name}")
                except Exception as cleanup_error:
                    print(f"[WARN] Impossible de supprimer {user_data_dir.name}: {cleanup_error}")

            # Si c'est un problème de user-data-dir et qu'il reste des tentatives
            if 'user data directory' in error_msg.lower() and tentative < max_retries:
                print("[RETRY] Nouveau nettoyage des processus et nouvelle tentative...")
                _tuer_processus_chrome_zombies()
                time.sleep(3)  # Attendre que les locks soient libérés
                continue

            # Si c'est la dernière tentative, lever l'exception
            if tentative == max_retries:
                print(f"\n[ERREUR FATALE] Impossible d'initialiser le navigateur apres {max_retries} tentatives")
                print("[INFO] Verifiez que Chrome et ChromeDriver sont installes")
                print("[INFO] Verifiez qu'aucune autre instance n'est en cours d'execution")
                raise

            # Attendre un peu avant la prochaine tentative
            time.sleep(2)

        except Exception as e:
            # Erreur inattendue
            print(f"[ERREUR] Erreur inattendue lors de l'initialisation: {e}")
            traceback.print_exc()
            raise

    # Cette ligne ne devrait jamais être atteinte, mais au cas où
    if last_exception:
        raise last_exception
    raise RuntimeError("Echec de l'initialisation du navigateur")


def telecharger_csv_linxo(driver, wait):
    """
    Télécharge le CSV depuis Linxo après connexion

    Workflow complet :
    1. Aller sur /secured/history.page (Historique)
    2. Cliquer sur "Recherche avancée"
    3. Sélectionner "Ce mois-ci" dans le menu déroulant
    4. Cliquer sur le bouton "CSV"

    Args:
        driver: Instance du WebDriver Selenium (doit être connecté)
        wait: Instance de WebDriverWait

    Returns:
        Path ou None: Chemin du fichier téléchargé ou None si échec
    """
    print("\n[DOWNLOAD] Telechargement du CSV...")

    config = get_config()

    try:
        # ÉTAPE 1: Naviguer vers la page Historique
        print("[ETAPE 1] Navigation vers la page Historique...")
        driver.get('https://wwws.linxo.com/secured/history.page')
        time.sleep(5)

        print(f"[OK] URL actuelle: {driver.current_url}")

        # ÉTAPE 2: Cliquer sur "Recherche avancée"
        print("[ETAPE 2] Clic sur 'Recherche avancee'...")
        try:
            # Chercher le lien "Recherche avancée" par sa classe
            recherche_avancee = wait.until(
                EC.element_to_be_clickable((By.CLASS_NAME, "GJALL4ABIGC"))
            )
            recherche_avancee.click()
            print("[OK] Clic sur 'Recherche avancee' reussi")
            time.sleep(2)
        except ImportError:
            print("[WARNING] Impossible de cliquer sur 'Recherche avancee': ")
            # Continuer quand même, peut-être que c'est déjà ouvert

        # ÉTAPE 3: Sélectionner "Ce mois-ci" dans le menu déroulant
        print("[ETAPE 3] Selection de 'Ce mois-ci' dans le menu deroulant...")
        from selenium.webdriver.support.select import Select  # pylint: disable=import-outside-toplevel

        try:
            # Trouver le select par sa classe
            select_element = wait.until(
                EC.presence_of_element_located((By.CLASS_NAME, "GJALL4ABIY"))
            )

            select = Select(select_element)

            # Sélectionner "Ce mois-ci" (value="3")
            select.select_by_value("3")
            print("[OK] 'Ce mois-ci' selectionne")
            time.sleep(2)
        except (TimeoutException, NoSuchElementException, WebDriverException) as e:
            print(f"[WARNING] Impossible de selectionner 'Ce mois-ci': {e}")
            print("[WARNING] Continuer avec la periode par defaut")

        # ÉTAPE 4: Cliquer sur le bouton "CSV"
        print("[ETAPE 4] Clic sur le bouton CSV...")
        try:
            # Méthode 1: Par les classes exactes
            csv_button = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button.GJALL4ABCV.GJALL4ABLW"))
            )
            csv_button.click()
            print("[OK] Clic sur bouton CSV reussi")
            time.sleep(10)  # Attendre le téléchargement

        except (TimeoutException, NoSuchElementException) as e1:
            print(f"[WARNING] Methode 1 echouee: {e1}")

            # Méthode 2: Par le texte "CSV"
            try:
                csv_button = driver.find_element(By.XPATH, "//button[contains(text(), 'CSV')]")
                csv_button.click()
                print("[OK] Clic sur bouton CSV reussi (methode 2)")
                time.sleep(10)
            except NoSuchElementException as e2:
                print(f"[WARNING] Methode 2 echouee: {e2}")

                # Méthode 3: Par classe partielle
                try:
                    csv_button = driver.find_element(By.CSS_SELECTOR, "button.GJALL4ABCV")
                    csv_button.click()
                    print("[OK] Clic sur bouton CSV reussi (methode 3)")
                    time.sleep(10)
                except NoSuchElementException as e3:
                    print(f"[ERREUR] Impossible de trouver le bouton CSV: {e3}")
                    return None

        # ÉTAPE 5: Vérifier le téléchargement
        print("[ETAPE 5] Verification du telechargement...")
        time.sleep(5)

        csv_files = list(config.downloads_dir.glob("*.csv"))

        if csv_files:
            # Prendre le fichier le plus récent
            latest_csv = max(csv_files, key=lambda p: p.stat().st_mtime)

            # Le copier dans data_dir
            target_csv = config.data_dir / "latest.csv"

            import shutil  # pylint: disable=import-outside-toplevel
            shutil.copy2(latest_csv, target_csv)

            print(f"[SUCCESS] CSV telecharge: {target_csv}")
            print(f"[INFO] Taille: {target_csv.stat().st_size} octets")

            return target_csv

        print("[ERREUR] Aucun fichier CSV trouve dans le dossier Downloads")
        print(f"[INFO] Dossier verifie: {config.downloads_dir}")
        return None

    except ImportError:
        print("[ERREUR] Erreur lors du telechargement: ")
        traceback.print_exc()
        return None


# Fonction de test
if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("TEST DU MODULE DE CONNEXION LINXO")
    print("=" * 80)

    # pylint: disable=invalid-name
    test_driver = None
    test_user_data_dir = None
    try:
        # Initialiser le driver (retourne maintenant driver, wait, user_data_dir)
        test_driver, test_wait, test_user_data_dir = initialiser_driver_linxo()

        # Se connecter
        success = se_connecter_linxo(test_driver, test_wait)

        if success:
            print("\n[SUCCESS] Test de connexion reussi!")

            # Tester le téléchargement (optionnel)
            response = input("\nTelecharger le CSV? (o/n): ")
            if response.lower() == 'o':
                csv_file = telecharger_csv_linxo(test_driver, test_wait)
                if csv_file:
                    print(f"\n[SUCCESS] CSV telecharge: {csv_file}")
                else:
                    print("\n[ERREUR] Echec du telechargement")
        else:
            print("\n[ERREUR] Test de connexion echoue")

        # Fermer le navigateur
        input("\nAppuyez sur Entree pour fermer le navigateur...")
        test_driver.quit()

        # Cleanup du répertoire temporaire
        if test_user_data_dir and test_user_data_dir.exists():
            shutil.rmtree(test_user_data_dir, ignore_errors=True)
            print(f"[CLEANUP] Repertoire temporaire supprime: {test_user_data_dir.name}")

    except KeyboardInterrupt:
        print("\n[INFO] Test interrompu par l'utilisateur")
        if test_driver:
            try:
                test_driver.quit()
            except WebDriverException:
                pass

        # Cleanup du répertoire temporaire
        if test_user_data_dir and test_user_data_dir.exists():
            shutil.rmtree(test_user_data_dir, ignore_errors=True)
            print(f"[CLEANUP] Repertoire temporaire supprime: {test_user_data_dir.name}")

    except WebDriverException as e:
        print(f"\n[ERREUR] Erreur durant le test: {e}")
        traceback.print_exc()

        # Cleanup du répertoire temporaire
        if test_user_data_dir and test_user_data_dir.exists():
            shutil.rmtree(test_user_data_dir, ignore_errors=True)
            print(f"[CLEANUP] Repertoire temporaire supprime: {test_user_data_dir.name}")
