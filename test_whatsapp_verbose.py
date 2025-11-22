#!/usr/bin/env python3
"""
Test WhatsApp avec logging verbeux et timeouts augmentés
pour identifier exactement où le processus échoue.
"""

import sys
import logging
import traceback
from pathlib import Path

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent))

# Configuration du logging au niveau DEBUG avec format détaillé
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(name)s:%(lineno)d - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('test_whatsapp_verbose.log', mode='w')
    ]
)

logger = logging.getLogger(__name__)

def test_whatsapp_avec_timeouts_augmentes():
    """
    Test WhatsApp avec timeouts augmentés et capture complète des erreurs.
    """
    try:
        logger.info("="*60)
        logger.info("DEBUT DU TEST WHATSAPP AVEC TIMEOUTS AUGMENTES")
        logger.info("="*60)

        # Import du module
        logger.info("Import du module whatsapp_sender...")
        from linxo_agent.whatsapp_sender import (
            initialiser_driver_whatsapp,
            authentifier_whatsapp,
            rechercher_contact,
            envoyer_message
        )
        logger.info("✅ Module importé avec succès")

        # Configuration
        destinataire = "Liste de courses"
        message = "Test avec timeouts augmentés"
        profile_dir = Path.cwd() / "whatsapp_profile"

        logger.info(f"Destinataire: {destinataire}")
        logger.info(f"Message: {message}")
        logger.info(f"Profile dir: {profile_dir}")

        driver = None
        try:
            # Étape 1: Initialisation du driver
            logger.info("-" * 60)
            logger.info("ETAPE 1: Initialisation du driver")
            logger.info("-" * 60)
            driver = initialiser_driver_whatsapp(profile_dir=profile_dir, headless=False)
            logger.info("✅ Driver initialisé")

            # Étape 2: Authentification avec timeout augmenté
            logger.info("-" * 60)
            logger.info("ETAPE 2: Authentification (timeout=180s)")
            logger.info("-" * 60)
            auth_result = authentifier_whatsapp(driver, timeout=180)
            if not auth_result:
                logger.error("❌ Échec authentification")
                return False
            logger.info("✅ Authentification réussie")

            # Étape 3: Recherche du contact avec timeout augmenté
            logger.info("-" * 60)
            logger.info("ETAPE 3: Recherche du contact (timeout=30s)")
            logger.info("-" * 60)
            search_result = rechercher_contact(driver, destinataire, timeout=30)
            if not search_result:
                logger.error(f"❌ Contact '{destinataire}' non trouvé")
                return False
            logger.info(f"✅ Contact '{destinataire}' trouvé et sélectionné")

            # Étape 4: Envoi du message avec timeout augmenté
            logger.info("-" * 60)
            logger.info("ETAPE 4: Envoi du message (timeout=30s)")
            logger.info("-" * 60)
            send_result = envoyer_message(driver, message, timeout=30)
            if not send_result:
                logger.error("❌ Échec envoi message")
                return False
            logger.info("✅ Message envoyé avec succès")

            logger.info("="*60)
            logger.info("TEST REUSSI!")
            logger.info("="*60)
            return True

        except Exception as e:
            logger.error("="*60)
            logger.error("EXCEPTION DURANT LE TEST")
            logger.error("="*60)
            logger.error(f"Type: {type(e).__name__}")
            logger.error(f"Message: {str(e)}")
            logger.error("Traceback complet:")
            logger.error(traceback.format_exc())
            return False

        finally:
            if driver:
                logger.info("Fermeture du driver...")
                try:
                    import time
                    time.sleep(3)  # Laisser le temps au message d'être envoyé
                    driver.quit()
                    logger.info("✅ Driver fermé")
                except Exception as e:
                    logger.warning(f"Erreur fermeture driver: {e}")

    except ImportError as e:
        logger.error("="*60)
        logger.error("ERREUR D'IMPORT")
        logger.error("="*60)
        logger.error(f"Impossible d'importer whatsapp_sender: {e}")
        logger.error(traceback.format_exc())
        return False

    except Exception as e:
        logger.error("="*60)
        logger.error("ERREUR FATALE")
        logger.error("="*60)
        logger.error(f"Type: {type(e).__name__}")
        logger.error(f"Message: {str(e)}")
        logger.error(traceback.format_exc())
        return False


if __name__ == "__main__":
    print("\n" + "="*60)
    print("TEST WHATSAPP AVEC LOGGING VERBOSE")
    print("="*60)
    print("Ce test va:")
    print("  1. Utiliser des timeouts augmentés (180s auth, 30s search, 30s send)")
    print("  2. Logger chaque étape avec détails")
    print("  3. Capturer le traceback complet en cas d'erreur")
    print("  4. Écrire les logs dans test_whatsapp_verbose.log")
    print("="*60 + "\n")

    result = test_whatsapp_avec_timeouts_augmentes()

    print("\n" + "="*60)
    if result:
        print("✅ TEST RÉUSSI - Message envoyé")
    else:
        print("❌ TEST ÉCHOUÉ - Voir logs ci-dessus et test_whatsapp_verbose.log")
    print("="*60)

    sys.exit(0 if result else 1)
