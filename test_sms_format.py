#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de test pour vérifier le format du sujet email2sms OVH
"""
import sys
import io
from pathlib import Path

# Forcer l'encodage UTF-8 pour Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Ajouter le chemin du module
sys.path.insert(0, str(Path('.') / 'linxo_agent'))

from notifications import load_notification_config

def test_sms_subject_format():
    """Teste le format du sujet email pour OVH SMS."""
    print("=" * 60)
    print("TEST DU FORMAT SUJET EMAIL2SMS OVH")
    print("=" * 60)

    # Charger la config
    try:
        notif_config = load_notification_config()

        if notif_config.ovh_sms is None:
            print("❌ ERREUR: Configuration OVH SMS non chargée")
            return False

        ovh = notif_config.ovh_sms

        print("\n📋 Configuration OVH SMS chargée:")
        print(f"  • account (OVH_USER_API):     {ovh.account}")
        print(f"  • user (OVH_SERVICE_NAME):    {ovh.user}")
        print(f"  • password (OVH_APP_SECRET):  {'*' * len(ovh.application_secret)}")
        print(f"  • sender (SMS_SENDER):        {ovh.sender}")

        # Simuler la construction du sujet
        test_phone = ovh.default_recipients[0] if ovh.default_recipients else "+33612345678"
        subject = f"{ovh.account}:{ovh.user}:{ovh.application_secret}:{ovh.sender}:{test_phone}"

        print(f"\n✉️  Sujet email généré:")
        print(f"  {subject}")

        print(f"\n🔍 Validation du format:")
        parts = subject.split(":")
        if len(parts) == 5:
            print(f"  ✅ 5 champs détectés")
            print(f"     1. Compte:      {parts[0]}")
            print(f"     2. Utilisateur: {parts[1]}")
            print(f"     3. Mot de passe: {'*' * len(parts[2])}")
            print(f"     4. Expéditeur:  {parts[3]}")
            print(f"     5. Téléphone:   {parts[4]}")

            # Vérifier qu'on n'a plus "default"
            if parts[1] == "default":
                print(f"\n  ❌ ERREUR: Le champ utilisateur contient encore 'default'")
                return False
            elif parts[1] == "":
                print(f"\n  ⚠️  AVERTISSEMENT: Le champ utilisateur est vide")
                print(f"     Vérifiez que OVH_SERVICE_NAME est défini dans .env")
                return False
            else:
                print(f"\n  ✅ Format correct ! Le champ utilisateur = '{parts[1]}'")
                return True
        else:
            print(f"  ❌ ERREUR: {len(parts)} champs au lieu de 5")
            return False

    except Exception as e:
        print(f"❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_sms_subject_format()
    print("\n" + "=" * 60)
    if success:
        print("✅ TEST RÉUSSI")
    else:
        print("❌ TEST ÉCHOUÉ")
    print("=" * 60)
    sys.exit(0 if success else 1)
