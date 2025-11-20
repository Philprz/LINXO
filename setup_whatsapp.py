#!/usr/bin/env python3
"""
Script d'initialisation pour WhatsApp Web.
Configure l'authentification initiale en scannant le QR code.
"""

import sys
from pathlib import Path

# Ajouter le répertoire parent au path pour importer linxo_agent
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


def setup_whatsapp_initial():
    """
    Configuration initiale de WhatsApp Web.
    Scanne le QR code et sauvegarde la session.
    """
    print("\n" + "="*70)
    print("🚀 CONFIGURATION INITIALE DE WHATSAPP WEB")
    print("="*70)
    print("\nCe script va:")
    print("1. Ouvrir WhatsApp Web dans Chrome")
    print("2. Afficher un QR code à scanner avec votre téléphone")
    print("3. Sauvegarder la session pour les prochaines utilisations")
    print("\n⚠️  Assurez-vous que:")
    print("   - Votre téléphone a accès à Internet")
    print("   - WhatsApp est installé sur votre téléphone")
    print("   - Vous êtes prêt à scanner le QR code")
    print("="*70 + "\n")

    input("Appuyez sur Entrée pour continuer...")

    driver = None
    try:
        # Charger la config pour obtenir le chemin du profil
        try:
            config = get_config()
            profile_dir = config.whatsapp_profile_dir if hasattr(config, 'whatsapp_profile_dir') else None
        except Exception:
            profile_dir = None
            logger.info("Config non chargée, utilisation du profil par défaut")

        # Initialiser le driver
        print("\n📱 Ouverture de Chrome...")
        driver = initialiser_driver_whatsapp(profile_dir=profile_dir, headless=False)

        # Authentifier
        print("\n🔐 Connexion à WhatsApp Web...")
        success = authentifier_whatsapp(driver, timeout=180)  # 3 minutes

        if success:
            print("\n" + "="*70)
            print("✅ CONFIGURATION RÉUSSIE!")
            print("="*70)
            print("\nLa session WhatsApp est maintenant sauvegardée.")
            print("Vous n'aurez plus besoin de scanner le QR code.")
            print("\n📝 Prochaines étapes:")
            print("   1. Configurez vos destinataires dans .env")
            print("   2. Testez l'envoi avec: python setup_whatsapp.py --test-send")
            print("="*70 + "\n")

            # Demander si on veut tester l'envoi
            test_now = input("Voulez-vous tester l'envoi d'un message maintenant? (o/n): ")
            if test_now.lower() in ['o', 'oui', 'y', 'yes']:
                test_send_message(driver)
        else:
            print("\n" + "="*70)
            print("❌ CONFIGURATION ÉCHOUÉE")
            print("="*70)
            print("\nLe QR code n'a pas été scanné à temps.")
            print("Veuillez réessayer: python setup_whatsapp.py")
            print("="*70 + "\n")
            return False

        return success

    except KeyboardInterrupt:
        print("\n\n⚠️  Configuration interrompue par l'utilisateur")
        return False
    except Exception as e:
        logger.error(f"Erreur lors du setup: {e}")
        print(f"\n❌ Erreur: {e}")
        return False
    finally:
        if driver:
            input("\nAppuyez sur Entrée pour fermer le navigateur...")
            driver.quit()


def test_send_message(driver=None):
    """
    Test d'envoi d'un message WhatsApp.

    Args:
        driver: Driver déjà initialisé (optionnel)
    """
    print("\n" + "="*70)
    print("📤 TEST D'ENVOI DE MESSAGE")
    print("="*70)

    close_driver = False
    if driver is None:
        try:
            config = get_config()
            profile_dir = config.whatsapp_profile_dir if hasattr(config, 'whatsapp_profile_dir') else None
        except Exception:
            profile_dir = None

        print("\n📱 Ouverture de Chrome...")
        driver = initialiser_driver_whatsapp(profile_dir=profile_dir, headless=False)
        close_driver = True

        print("\n🔐 Vérification de la connexion...")
        if not authentifier_whatsapp(driver, timeout=30):
            print("❌ Non connecté à WhatsApp Web. Lancez d'abord: python setup_whatsapp.py")
            if close_driver:
                driver.quit()
            return

    try:
        # Demander le destinataire
        print("\n💬 Configuration du test:")
        destinataire = input("Nom du contact ou groupe (ex: 'Budget Famille'): ").strip()

        if not destinataire:
            print("❌ Nom de destinataire requis")
            return

        # Message de test
        message = """🤖 Message de test - LINXO Agent

Ceci est un message de test pour vérifier l'intégration WhatsApp.

Si vous recevez ce message, la configuration est réussie! ✅"""

        # Confirmer
        print(f"\n📋 Résumé:")
        print(f"   Destinataire: {destinataire}")
        print(f"   Message: {len(message)} caractères")
        confirm = input("\nEnvoyer ce message de test? (o/n): ")

        if confirm.lower() not in ['o', 'oui', 'y', 'yes']:
            print("❌ Test annulé")
            return

        # Rechercher et envoyer
        print(f"\n🔍 Recherche de '{destinataire}'...")
        if not rechercher_contact(driver, destinataire):
            print(f"❌ Contact/groupe '{destinataire}' non trouvé")
            print("\n💡 Vérifiez:")
            print("   - Le nom exact du contact/groupe")
            print("   - Que le contact/groupe existe dans votre WhatsApp")
            return

        print("📤 Envoi du message...")
        if envoyer_message(driver, message):
            print("\n" + "="*70)
            print("✅ MESSAGE ENVOYÉ AVEC SUCCÈS!")
            print("="*70)
            print(f"\nVérifiez WhatsApp pour confirmer la réception.")
            print("="*70 + "\n")
        else:
            print("\n❌ Échec de l'envoi du message")

    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrompu")
    except Exception as e:
        logger.error(f"Erreur lors du test: {e}")
        print(f"\n❌ Erreur: {e}")
    finally:
        if close_driver and driver:
            input("\nAppuyez sur Entrée pour fermer...")
            driver.quit()


def show_config_info():
    """
    Affiche les informations de configuration WhatsApp.
    """
    print("\n" + "="*70)
    print("📋 CONFIGURATION WHATSAPP")
    print("="*70)

    try:
        config = get_config()
        if hasattr(config, 'whatsapp_enabled') and config.whatsapp_enabled:
            print(f"\n✅ Configuration détectée:")
            print(f"   Activé: {config.whatsapp_enabled}")
            print(f"   Groupe: {config.whatsapp_group_name or 'Non défini'}")
            print(f"   Contacts: {', '.join(config.whatsapp_contacts) if config.whatsapp_contacts else 'Non définis'}")
            print(f"   Profil Chrome: {config.whatsapp_profile_dir}")
        else:
            print("\n⚠️  Configuration WhatsApp non trouvée")
            print("\n📝 Ajoutez dans votre fichier .env:")
            print("   WHATSAPP_ENABLED=true")
            print("   WHATSAPP_GROUP_NAME=Nom du groupe")
            print("   ou")
            print("   WHATSAPP_CONTACTS=Contact1,Contact2")
    except Exception as e:
        print(f"\n❌ Erreur lors du chargement de la config: {e}")
        print("\n📝 Assurez-vous que .env contient:")
        print("   WHATSAPP_ENABLED=true")
        print("   WHATSAPP_GROUP_NAME=Nom du groupe (ou WHATSAPP_CONTACTS)")

    print("="*70 + "\n")


def main():
    """Point d'entrée principal du script."""
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()

        if arg in ['--test', '--test-send', '-t']:
            test_send_message()
        elif arg in ['--config', '--info', '-c']:
            show_config_info()
        elif arg in ['--help', '-h']:
            print("\n" + "="*70)
            print("📖 AIDE - Setup WhatsApp")
            print("="*70)
            print("\nUsage:")
            print("  python setup_whatsapp.py              Configuration initiale (scan QR)")
            print("  python setup_whatsapp.py --test       Tester l'envoi d'un message")
            print("  python setup_whatsapp.py --config     Afficher la configuration")
            print("  python setup_whatsapp.py --help       Afficher cette aide")
            print("="*70 + "\n")
        else:
            print(f"❌ Option inconnue: {arg}")
            print("Utilisez --help pour voir les options disponibles")
    else:
        # Configuration initiale par défaut
        setup_whatsapp_initial()


if __name__ == "__main__":
    main()
