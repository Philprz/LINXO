"""
Module pour envoyer des messages WhatsApp via WhatsApp Web avec Selenium.
Utilise un profil Chrome persistant pour maintenir la session authentifiée.
"""

import time
import logging
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import undetected_chromedriver as uc

logger = logging.getLogger(__name__)


def initialiser_driver_whatsapp(profile_dir=None, headless=False):
    """
    Initialise le driver Chrome pour WhatsApp Web avec profil persistant.

    Args:
        profile_dir: Chemin vers le profil Chrome (défaut: ./whatsapp_profile)
        headless: Mode headless (déconseillé pour WhatsApp)

    Returns:
        WebDriver: Instance du driver Chrome
    """
    import os
    import platform

    # Gérer None et chaînes vides
    if not profile_dir:
        profile_dir = Path.cwd() / "whatsapp_profile"

    profile_dir = Path(profile_dir)
    profile_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Initialisation driver WhatsApp avec profil: {profile_dir}")

    options = uc.ChromeOptions()
    options.add_argument(f"--user-data-dir={profile_dir}")
    options.add_argument("--profile-directory=Default")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")

    # Détection environnement serveur (VPS)
    is_server = platform.system() == "Linux" and not os.environ.get("DISPLAY")
    if is_server and not os.environ.get("DISPLAY"):
        logger.warning("Environnement serveur détecté sans DISPLAY - assurez-vous d'utiliser Xvfb")

    # Options supplémentaires pour serveurs Linux
    if platform.system() == "Linux":
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-background-networking")
        options.add_argument("--disable-sync")
        options.add_argument("--metrics-recording-only")
        options.add_argument("--disable-default-apps")
        options.add_argument("--mute-audio")
        options.add_argument("--no-first-run")
        options.add_argument("--disable-setuid-sandbox")
        options.add_argument("--disable-web-security")

    # WhatsApp Web fonctionne mal en headless, on force la fenêtre visible
    if not headless:
        options.add_argument("--start-maximized")
    else:
        logger.warning("Mode headless activé - WhatsApp Web peut ne pas fonctionner correctement")
        options.add_argument("--headless=new")

    try:
        # CORRECTION: Détecter Chrome explicitement pour harmoniser avec Linxo
        # et éviter l'erreur "Binary Location Must be a String"
        try:
            from .chrome_detector import detect_chrome_binary
        except ImportError:
            from chrome_detector import detect_chrome_binary  # type: ignore

        chrome_binary = detect_chrome_binary()
        if chrome_binary:
            logger.info(f"Chrome trouvé: {chrome_binary}")
        else:
            logger.warning("Chrome non trouvé dans les chemins standards, tentative auto-détection")

        # Sur Linux/VPS, ne pas utiliser use_subprocess si on a Xvfb
        # IMPORTANT: Harmonisé avec linxo_connexion_undetected.py
        use_subprocess = True  # Toujours True pour cohérence avec module Linxo

        driver = uc.Chrome(
            options=options,
            browser_executable_path=chrome_binary,  # Spécifier explicitement le chemin
            use_subprocess=use_subprocess
        )
        logger.info("Driver WhatsApp initialisé avec succès")
        return driver
    except Exception as e:
        logger.error(f"Erreur lors de l'initialisation du driver WhatsApp: {e}")
        raise


def authentifier_whatsapp(driver, timeout=120):
    """
    Authentifie WhatsApp Web en scannant le QR code.
    Attend que l'utilisateur scanne le QR code avec son téléphone.

    Args:
        driver: Instance WebDriver
        timeout: Temps max d'attente pour le scan (secondes)

    Returns:
        bool: True si authentifié, False sinon
    """
    logger.info("Navigation vers WhatsApp Web...")
    driver.get("https://web.whatsapp.com")

    try:
        # Vérifier si déjà connecté (pas de QR code)
        logger.info("Vérification si déjà authentifié...")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//div[@contenteditable='true'][@data-tab='3']"))
        )
        logger.info("Session WhatsApp déjà active - authentification réussie")
        return True
    except TimeoutException:
        # QR code présent, attente du scan
        logger.info(f"QR Code détecté - veuillez scanner avec votre téléphone (timeout: {timeout}s)")
        print("\n" + "="*60)
        print("AUTHENTIFICATION WHATSAPP WEB")
        print("="*60)
        print("1. Ouvrez WhatsApp sur votre telephone")
        print("2. Allez dans Parametres > Appareils connectes")
        print("3. Scannez le QR code affiche dans le navigateur")
        print(f"4. Vous avez {timeout} secondes pour scanner")
        print("="*60 + "\n")

        try:
            # Attendre la disparition du QR code = authentification réussie
            WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((By.XPATH, "//div[@contenteditable='true'][@data-tab='3']"))
            )
            logger.info("Authentification WhatsApp réussie!")
            print("=> Authentification reussie!\n")
            return True
        except TimeoutException:
            logger.error(f"Timeout d'authentification WhatsApp ({timeout}s écoulées)")
            print("=> Timeout - QR code non scanne a temps\n")
            return False


def rechercher_contact(driver, nom_contact_ou_groupe, timeout=15):
    """
    Recherche et sélectionne un contact ou groupe WhatsApp.

    Args:
        driver: Instance WebDriver
        nom_contact_ou_groupe: Nom du contact ou groupe à rechercher
        timeout: Timeout pour la recherche

    Returns:
        bool: True si contact trouvé et sélectionné, False sinon
    """
    logger.info(f"Recherche du contact/groupe: {nom_contact_ou_groupe}")

    try:
        # Attendre que WhatsApp Web soit complètement chargé
        time.sleep(2)

        # Essayer de fermer les popups/overlays potentiels
        try:
            close_buttons = driver.find_elements(By.XPATH, "//div[@role='button'][@aria-label='Fermer' or @aria-label='Close']")
            for btn in close_buttons:
                try:
                    btn.click()
                    time.sleep(0.5)
                except Exception:
                    pass
        except Exception:
            pass

        # Trouver la barre de recherche - attendre qu'elle soit cliquable
        logger.debug("Recherche de la barre de recherche...")
        search_box = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((By.XPATH, "//div[@contenteditable='true'][@data-tab='3']"))
        )

        # Scroll vers l'élément si nécessaire
        driver.execute_script("arguments[0].scrollIntoView(true);", search_box)
        time.sleep(0.3)

        # Cliquer avec JavaScript pour être sûr
        driver.execute_script("arguments[0].click();", search_box)
        time.sleep(0.5)

        # Effacer le contenu existant avec Ctrl+A puis Backspace
        search_box.send_keys(Keys.CONTROL + "a")
        search_box.send_keys(Keys.BACKSPACE)
        time.sleep(0.3)

        # Taper le nom du contact
        logger.debug(f"Saisie du nom: {nom_contact_ou_groupe}")
        search_box.send_keys(nom_contact_ou_groupe)
        time.sleep(2)  # Attendre les résultats de recherche

        # Sélectionner le premier résultat
        try:
            # Chercher par titre exact
            contact_result = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, f"//span[@title='{nom_contact_ou_groupe}']"))
            )
            contact_result.click()
            logger.info(f"Contact '{nom_contact_ou_groupe}' sélectionné")
            time.sleep(1)
            return True
        except TimeoutException:
            logger.warning(f"Contact exact '{nom_contact_ou_groupe}' non trouvé, tentative avec premier résultat")
            # Si nom exact non trouvé, cliquer sur premier résultat
            try:
                first_result = WebDriverWait(driver, 3).until(
                    EC.element_to_be_clickable((By.XPATH, "//div[@role='listitem'][1]"))
                )
                first_result.click()
                logger.info("Premier résultat de recherche sélectionné")
                time.sleep(1)
                return True
            except (NoSuchElementException, TimeoutException):
                logger.error("Aucun résultat de recherche trouvé")
                return False

    except TimeoutException:
        logger.error("Barre de recherche WhatsApp non trouvée - vérifier que WhatsApp Web est chargé")
        return False
    except Exception as e:
        logger.error(f"Erreur lors de la recherche du contact: {e}")
        return False


def envoyer_message(driver, message, timeout=10):
    """
    Envoie un message dans la conversation actuellement ouverte.
    Utilise ActionChains pour simuler une vraie saisie clavier.

    Args:
        driver: Instance WebDriver
        message: Texte du message à envoyer
        timeout: Timeout pour l'envoi

    Returns:
        bool: True si message envoyé, False sinon
    """
    logger.info(f"Envoi du message ({len(message)} caractères)")

    try:
        # Trouver la zone de saisie du message
        message_box = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.XPATH, "//div[@contenteditable='true'][@data-tab='10']"))
        )

        # Cliquer sur la zone de saisie
        message_box.click()
        time.sleep(0.5)

        # Effacer le contenu existant
        message_box.send_keys(Keys.CONTROL + "a")
        time.sleep(0.2)
        message_box.send_keys(Keys.BACKSPACE)
        time.sleep(0.3)

        # Utiliser ActionChains pour saisir le message caractère par caractère
        # C'est plus lent mais plus fiable et déclenche tous les événements
        logger.debug("Saisie du message avec ActionChains")
        actions = ActionChains(driver)

        # Pour chaque ligne du message
        lines = message.split('\n')
        for i, line in enumerate(lines):
            # Taper la ligne
            actions.send_keys(line)
            # Ajouter Shift+Enter pour retour à la ligne (sauf dernière ligne)
            if i < len(lines) - 1:
                actions.key_down(Keys.SHIFT).send_keys(Keys.ENTER).key_up(Keys.SHIFT)

        # Exécuter toutes les actions
        actions.perform()
        time.sleep(1)  # Attendre que le texte soit bien saisi

        # Vérifier que le texte est présent
        try:
            text_content = message_box.text
            if text_content and len(text_content) >= len(message) * 0.8:  # Au moins 80% du message
                logger.debug(f"Message saisi correctement ({len(text_content)} caractères)")
            else:
                logger.warning(f"Message incomplet? Attendu ~{len(message)}, trouvé {len(text_content) if text_content else 0}")
        except Exception as e:
            logger.debug(f"Impossible de vérifier le contenu: {e}")

        # Envoyer avec Enter (sans Shift cette fois)
        logger.debug("Envoi du message avec Enter")
        message_box.send_keys(Keys.ENTER)
        logger.info("Message envoyé avec succès (méthode ActionChains + Enter)")
        time.sleep(2)  # Attendre que le message soit bien envoyé

        return True

    except TimeoutException:
        logger.error("Zone de message WhatsApp non trouvée - vérifier qu'une conversation est ouverte")
        return False
    except Exception as e:
        logger.error(f"Erreur lors de l'envoi du message: {e}")
        return False


def envoyer_message_whatsapp(destinataire, message, profile_dir=None, headless=False):
    """
    Fonction principale pour envoyer un message WhatsApp.
    Gère tout le cycle: init driver, recherche contact, envoi, cleanup.

    Args:
        destinataire: Nom du contact ou groupe WhatsApp
        message: Message à envoyer
        profile_dir: Chemin vers le profil Chrome (optionnel)
        headless: Mode headless (déconseillé)

    Returns:
        dict: {'success': bool, 'message': str, 'error': str (optionnel)}
    """
    driver = None

    try:
        # Initialiser le driver
        driver = initialiser_driver_whatsapp(profile_dir=profile_dir, headless=headless)

        # Authentifier (ou vérifier session existante)
        if not authentifier_whatsapp(driver):
            return {
                'success': False,
                'message': 'Échec authentification WhatsApp',
                'error': 'QR code non scanné ou timeout'
            }

        # Rechercher le contact/groupe
        if not rechercher_contact(driver, destinataire):
            return {
                'success': False,
                'message': f"Contact/groupe '{destinataire}' non trouvé",
                'error': 'Contact introuvable'
            }

        # Envoyer le message
        if not envoyer_message(driver, message):
            return {
                'success': False,
                'message': 'Échec envoi message',
                'error': 'Erreur lors de l\'envoi'
            }

        logger.info(f"Message WhatsApp envoyé avec succès à '{destinataire}'")
        return {
            'success': True,
            'message': f"Message envoyé à '{destinataire}'"
        }

    except Exception as e:
        logger.error(f"Erreur fatale lors de l'envoi WhatsApp: {e}")
        return {
            'success': False,
            'message': 'Erreur fatale',
            'error': str(e)
        }

    finally:
        # Cleanup
        if driver:
            try:
                logger.info("Fermeture du driver WhatsApp...")
                time.sleep(2)  # Laisser le temps au message d'être envoyé
                driver.quit()
                logger.info("Driver fermé")
            except Exception as e:
                logger.warning(f"Erreur lors de la fermeture du driver: {e}")


def tester_connexion_whatsapp(profile_dir=None):
    """
    Fonction de test pour vérifier la connexion WhatsApp.
    Utile pour le setup initial.

    Args:
        profile_dir: Chemin vers le profil Chrome

    Returns:
        bool: True si connexion OK, False sinon
    """
    driver = None

    try:
        driver = initialiser_driver_whatsapp(profile_dir=profile_dir)
        success = authentifier_whatsapp(driver, timeout=180)  # 3 minutes

        if success:
            print("\n=> Connexion WhatsApp Web reussie!")
            print("Le profil est sauvegarde - plus besoin de scanner le QR code.")
            input("\nAppuyez sur Entree pour fermer...")
        else:
            print("\n=> Echec de la connexion WhatsApp Web")

        return success

    finally:
        if driver:
            driver.quit()


if __name__ == "__main__":
    # Test du module
    print("Module WhatsApp Sender - Test de connexion")
    print("=" * 60)

    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        # Test de connexion uniquement
        tester_connexion_whatsapp()
    else:
        # Test d'envoi de message
        destinataire = input("Nom du contact/groupe: ")
        message = input("Message à envoyer: ")

        result = envoyer_message_whatsapp(destinataire, message)

        if result['success']:
            print(f"\n✅ {result['message']}")
        else:
            print(f"\n❌ {result['message']}")
            if 'error' in result:
                print(f"Erreur: {result['error']}")
