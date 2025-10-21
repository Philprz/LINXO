#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de génération du fichier api_secrets.json à partir du .env
Utilise la configuration unifiée
"""

import json
import os
from pathlib import Path
from dotenv import load_dotenv

def generate_api_secrets():
    """Génère le fichier api_secrets.json depuis le .env"""

    # Charger le .env
    project_root = Path(__file__).parent.parent.resolve()
    env_file = project_root / '.env'

    if not env_file.exists():
        print(f"❌ Fichier .env non trouvé: {env_file}")
        return False

    load_dotenv(env_file)
    print(f"✅ Chargement du .env depuis: {env_file}")

    # Créer la structure api_secrets.json
    api_secrets = {
        "SMTP_GMAIL": {
            "service": "Gmail SMTP",
            "secrets": {
                "SMTP_SERVER": "smtp.gmail.com",
                "SMTP_PORT": 587,
                "SMTP_EMAIL": os.getenv('SENDER_EMAIL', ''),
                "SMTP_PASSWORD": os.getenv('SENDER_PASSWORD', '')
            }
        },
        "OVH_SMS": {
            "service": "OVH SMS via Email",
            "secrets": {
                "COMPTE_SMS": os.getenv('OVH_SERVICE_NAME', ''),
                "UTILISATEUR_SMS": "default",
                "MOT_DE_PASSE_SMS": os.getenv('OVH_APP_SECRET', ''),
                "EXPEDITEUR_SMS": os.getenv('SMS_SENDER', 'PhiPEREZ'),
                "OVH_EMAIL": os.getenv('OVH_EMAIL_ENVOI', 'email2sms@ovh.net')
            }
        }
    }

    # Validation
    if not api_secrets['SMTP_GMAIL']['secrets']['SMTP_EMAIL']:
        print("⚠️ ATTENTION: SENDER_EMAIL manquant dans .env")

    if not api_secrets['SMTP_GMAIL']['secrets']['SMTP_PASSWORD']:
        print("⚠️ ATTENTION: SENDER_PASSWORD manquant dans .env")

    if not api_secrets['OVH_SMS']['secrets']['COMPTE_SMS']:
        print("⚠️ ATTENTION: OVH_SERVICE_NAME manquant dans .env")

    # Déterminer le chemin de sortie selon l'environnement
    import sys
    if sys.platform.startswith('linux') and os.path.exists('/home/ubuntu'):
        # VPS
        output_dir = Path('/home/ubuntu/.api_secret_infos')
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / 'api_secrets.json'
    else:
        # Local
        output_file = project_root / 'api_secrets.json'

    # Écrire le fichier
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(api_secrets, f, indent=2, ensure_ascii=False)

        print(f"✅ Fichier api_secrets.json créé: {output_file}")

        # Afficher le résumé
        print("\n" + "=" * 80)
        print("📋 CONTENU DE api_secrets.json")
        print("=" * 80)
        print(json.dumps(api_secrets, indent=2, ensure_ascii=False))
        print("=" * 80)

        # Sécuriser les permissions sur Linux
        if sys.platform.startswith('linux'):
            os.chmod(output_file, 0o600)
            print(f"🔒 Permissions sécurisées (600) appliquées")

        return True

    except Exception as e:
        print(f"❌ Erreur lors de la création du fichier: {e}")
        return False

if __name__ == "__main__":
    import sys
    # Fix Windows encoding issues
    if sys.platform == 'win32':
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

    print("\n[GENERATION] api_secrets.json")
    print("=" * 80)

    success = generate_api_secrets()

    if success:
        print("\n✅ Génération terminée avec succès!")
    else:
        print("\n❌ Échec de la génération")
        exit(1)
