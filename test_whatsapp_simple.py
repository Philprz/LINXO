#!/usr/bin/env python3
"""Test simple d'envoi WhatsApp sans emojis dans les prints."""

import sys
from pathlib import Path

# Ajouter le répertoire au path
sys.path.insert(0, str(Path(__file__).parent))

from linxo_agent.whatsapp_sender import (
    initialiser_driver_whatsapp,
    authentifier_whatsapp,
    rechercher_contact,
    envoyer_message
)
from linxo_agent.config import get_config
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_envoi():
    """Test d'envoi simple."""
    print("\n" + "="*70)
    print("TEST D'ENVOI WHATSAPP (methode presse-papiers)")
    print("="*70)

    driver = None
    try:
        # Config
        try:
            config = get_config()
            profile_dir = config.whatsapp_profile_dir if hasattr(config, 'whatsapp_profile_dir') else None
        except Exception:
            profile_dir = None

        # Init driver
        print("\nOuverture de Chrome...")
        driver = initialiser_driver_whatsapp(profile_dir=profile_dir, headless=False)

        # Auth
        print("Verification de la connexion WhatsApp...")
        if not authentifier_whatsapp(driver, timeout=30):
            print("ERREUR: Non connecte a WhatsApp Web")
            return

        # Destinataire
        destinataire = "Liste de courses"
        message = """Test message LINXO Agent

Ceci est un test de la methode presse-papiers.

Si vous recevez ce message, l'integration fonctionne!"""

        print(f"\nDestinataire: {destinataire}")
        print(f"Longueur message: {len(message)} caracteres")

        # Recherche
        print(f"\nRecherche de '{destinataire}'...")
        if not rechercher_contact(driver, destinataire):
            print(f"ERREUR: Contact/groupe '{destinataire}' non trouve")
            return

        # Envoi
        print("Envoi du message...")
        if envoyer_message(driver, message):
            print("\n" + "="*70)
            print("SUCCES! Message envoye")
            print("="*70)
            print("\nVerifiez votre WhatsApp pour confirmer la reception.")
        else:
            print("\nERREUR: Echec de l'envoi")

    except KeyboardInterrupt:
        print("\n\nTest interrompu")
    except Exception as e:
        logger.error(f"Erreur: {e}")
        print(f"\nERREUR: {e}")
    finally:
        if driver:
            input("\nAppuyez sur Entree pour fermer...")
            driver.quit()

if __name__ == "__main__":
    test_envoi()
