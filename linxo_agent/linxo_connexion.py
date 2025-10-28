#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module de connexion standardisé pour Linxo
Version 2.0 - Refactorisée avec configuration unifiée
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time
from pathlib import Path

# Import du module de configuration unifié
try:
    from config import get_config
except ImportError:
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    from config import get_config

# Import du module 2FA
try:
    from linxo_2fa import recuperer_code_2fa_email
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent))
    from linxo_2fa import recuperer_code_2fa_email


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

        # Méthode 1: Par nom "code"
        try:
            code_field = wait.until(
                EC.presence_of_element_located((By.NAME, "code"))
            )
            print("[2FA] Champ code trouvé (par name)")
        except:
            pass

        # Méthode 2: Par ID "code"
        if not code_field:
            try:
                code_field = driver.find_element(By.ID, "code")
                print("[2FA] Champ code trouvé (par ID)")
            except:
                pass

        # Méthode 3: Par type "text" et placeholder
        if not code_field:
            try:
                code_field = driver.find_element(
                    By.CSS_SELECTOR,
                    "input[type='text'][placeholder*='code' i]"
                )
                print("[2FA] Champ code trouvé (par CSS)")
            except:
                pass

        # Méthode 4: Premier champ input de type text visible
        if not code_field:
            try:
                code_field = driver.find_element(By.CSS_SELECTOR, "input[type='text']")
                print("[2FA] Champ code trouvé (input text)")
            except:
                pass

        if not code_field:
            print("[ERREUR] Champ de saisie du code 2FA introuvable")
            return False

        # Saisir le code
        code_field.clear()
        code_field.send_keys(code_2fa)
        print("[2FA] Code saisi")
        time.sleep(2)

        # Chercher et cliquer sur le bouton de validation
        submit_button = None

        # Méthode 1: Par texte "Valider", "Confirmer", "Vérifier"
        for button_text in ["Valider", "Confirmer", "Vérifier", "Envoyer", "Continuer"]:
            try:
                submit_button = driver.find_element(
                    By.XPATH,
                    f"//button[contains(text(), '{button_text}')]"
                )
                print(f"[2FA] Bouton '{button_text}' trouvé")
                break
            except:
                pass

        # Méthode 2: Par type submit
        if not submit_button:
            try:
                submit_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
                print("[2FA] Bouton submit trouvé")
            except:
                pass

        # Méthode 3: N'importe quel bouton
        if not submit_button:
            try:
                submit_button = driver.find_element(By.TAG_NAME, "button")
                print("[2FA] Bouton générique trouvé")
            except:
                pass

        if not submit_button:
            print("[WARNING] Bouton de validation 2FA introuvable, tentative Enter")
            # Essayer d'envoyer avec la touche Enter
            from selenium.webdriver.common.keys import Keys
            code_field.send_keys(Keys.RETURN)
        else:
            submit_button.click()
            print("[2FA] Bouton de validation cliqué")

        # Attendre la redirection
        time.sleep(8)

        print(f"[2FA] URL après validation: {driver.current_url}")

        # Vérifier si connecté
        if 'login' not in driver.current_url.lower() and 'auth' not in driver.current_url.lower() and '2fa' not in driver.current_url.lower():
            print("[SUCCESS] Connexion réussie après 2FA!")
            return True
        else:
            print("[ERREUR] Échec de la validation 2FA")
            return False

    except Exception as e:
        print(f"[ERREUR] Erreur lors de la gestion du 2FA: {e}")
        import traceback
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
        except Exception as e:
            print(f"[ERREUR] Champ username non trouve: {e}")
            return False

        # Chercher le champ password (name="password")
        try:
            password_field = driver.find_element(By.NAME, "password")
            print("[OK] Champ password trouve")
        except Exception as e:
            print(f"[ERREUR] Champ password non trouve: {e}")
            return False

        # Remplir les champs
        print("[ACTION] Remplissage des identifiants...")
        username_field.clear()
        username_field.send_keys(email)
        time.sleep(1)

        password_field.clear()
        password_field.send_keys(password)
        time.sleep(1)

        # Chercher et cliquer sur le bouton "Je me connecte"
        try:
            # Chercher par texte du bouton
            submit_button = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Je me connecte')]"))
            )
            print("[OK] Bouton 'Je me connecte' trouve")
        except:
            # Fallback: chercher par type submit
            try:
                submit_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
                print("[OK] Bouton submit trouve")
            except Exception as e:
                print(f"[ERREUR] Bouton de connexion non trouve: {e}")
                return False

        print("[ACTION] Tentative de connexion...")
        submit_button.click()

        # Attendre la redirection
        time.sleep(8)

        print(f"[OK] URL apres connexion: {driver.current_url}")

        # Vérifier si on est sur une page 2FA
        if '2fa' in driver.current_url.lower() or 'verification' in driver.current_url.lower():
            print("[2FA] Page de vérification 2FA détectée")
            return _gerer_2fa(driver, wait)

        # Vérifier si connecté (on ne doit plus être sur la page de login)
        if 'login' not in driver.current_url.lower() and 'auth' not in driver.current_url.lower():
            print("[SUCCESS] Connexion reussie!")
            return True

        # Peut-être qu'on est sur une page 2FA sans l'URL explicite
        # Chercher un champ de code 2FA
        try:
            code_field = driver.find_element(By.NAME, "code")
            print("[2FA] Champ de code 2FA détecté")
            return _gerer_2fa(driver, wait)
        except:
            pass

        try:
            code_field = driver.find_element(By.ID, "code")
            print("[2FA] Champ de code 2FA détecté (par ID)")
            return _gerer_2fa(driver, wait)
        except:
            pass

        # Vérifier par texte dans la page
        if 'code' in driver.page_source.lower() and 'verification' in driver.page_source.lower():
            print("[2FA] Page de vérification détectée (par contenu)")
            return _gerer_2fa(driver, wait)

        print("[ERREUR] Echec de la connexion (toujours sur la page de login)")
        return False

    except Exception as e:
        print(f"[ERREUR] Erreur lors de la connexion: {e}")
        import traceback
        traceback.print_exc()
        return False


def initialiser_driver_linxo(download_dir=None, headless=False):
    """
    Initialise un driver Chrome configuré pour Linxo
    Version 2.0 - Utilise la configuration unifiée

    Args:
        download_dir: Dossier de téléchargement (optionnel, utilise config par défaut)
        headless: Mode headless (sans interface graphique)

    Returns:
        tuple: (driver, wait)
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

    options = Options()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')

    if headless:
        options.add_argument('--headless')
        print("[INFO] Mode headless active")

    # Configuration des téléchargements
    prefs = {
        "download.default_directory": str(download_dir.absolute()),
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True
    }
    options.add_experimental_option("prefs", prefs)

    print(f"[INFO] Dossier de telechargement: {download_dir}")

    try:
        driver = webdriver.Chrome(options=options)
        wait = WebDriverWait(driver, 30)
        print("[OK] Navigateur initialise")

        return driver, wait

    except Exception as e:
        print(f"[ERREUR] Impossible d'initialiser le navigateur: {e}")
        print("[INFO] Verifiez que Chrome et ChromeDriver sont installes")
        raise


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
        except Exception as e:
            print(f"[WARNING] Impossible de cliquer sur 'Recherche avancee': {e}")
            # Continuer quand même, peut-être que c'est déjà ouvert

        # ÉTAPE 3: Sélectionner "Ce mois-ci" dans le menu déroulant
        print("[ETAPE 3] Selection de 'Ce mois-ci' dans le menu deroulant...")
        try:
            # Trouver le select par sa classe
            select_element = wait.until(
                EC.presence_of_element_located((By.CLASS_NAME, "GJALL4ABIY"))
            )

            # Utiliser la classe Select de Selenium
            from selenium.webdriver.support.ui import Select
            select = Select(select_element)

            # Sélectionner "Ce mois-ci" (value="3")
            select.select_by_value("3")
            print("[OK] 'Ce mois-ci' selectionne")
            time.sleep(2)
        except Exception as e:
            print(f"[WARNING] Impossible de selectionner 'Ce mois-ci': {e}")
            # Essayer par index (option 3)
            try:
                select.select_by_index(3)
                print("[OK] 'Ce mois-ci' selectionne (par index)")
                time.sleep(2)
            except:
                print("[WARNING] Selection impossible, continuer avec la periode par defaut")

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

        except Exception as e1:
            print(f"[WARNING] Methode 1 echouee: {e1}")

            # Méthode 2: Par le texte "CSV"
            try:
                csv_button = driver.find_element(By.XPATH, "//button[contains(text(), 'CSV')]")
                csv_button.click()
                print("[OK] Clic sur bouton CSV reussi (methode 2)")
                time.sleep(10)
            except Exception as e2:
                print(f"[WARNING] Methode 2 echouee: {e2}")

                # Méthode 3: Par classe partielle
                try:
                    csv_button = driver.find_element(By.CSS_SELECTOR, "button.GJALL4ABCV")
                    csv_button.click()
                    print("[OK] Clic sur bouton CSV reussi (methode 3)")
                    time.sleep(10)
                except Exception as e3:
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

            import shutil
            shutil.copy2(latest_csv, target_csv)

            print(f"[SUCCESS] CSV telecharge: {target_csv}")
            print(f"[INFO] Taille: {target_csv.stat().st_size} octets")

            return target_csv
        else:
            print("[ERREUR] Aucun fichier CSV trouve dans le dossier Downloads")
            print(f"[INFO] Dossier verifie: {config.downloads_dir}")
            return None

    except Exception as e:
        print(f"[ERREUR] Erreur lors du telechargement: {e}")
        import traceback
        traceback.print_exc()
        return None


# Fonction de test
if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("TEST DU MODULE DE CONNEXION LINXO")
    print("=" * 80)

    try:
        # Initialiser le driver
        driver, wait = initialiser_driver_linxo()

        # Se connecter
        success = se_connecter_linxo(driver, wait)

        if success:
            print("\n[SUCCESS] Test de connexion reussi!")

            # Tester le téléchargement (optionnel)
            response = input("\nTelecharger le CSV? (o/n): ")
            if response.lower() == 'o':
                csv_file = telecharger_csv_linxo(driver, wait)
                if csv_file:
                    print(f"\n[SUCCESS] CSV telecharge: {csv_file}")
                else:
                    print("\n[ERREUR] Echec du telechargement")
        else:
            print("\n[ERREUR] Test de connexion echoue")

        # Fermer le navigateur
        input("\nAppuyez sur Entree pour fermer le navigateur...")
        driver.quit()

    except KeyboardInterrupt:
        print("\n[INFO] Test interrompu par l'utilisateur")
        try:
            driver.quit()
        except:
            pass
    except Exception as e:
        print(f"\n[ERREUR] Erreur durant le test: {e}")
        import traceback
        traceback.print_exc()
