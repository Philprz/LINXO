#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module de configuration unifié pour Linxo Agent
Gère les environnements Windows/Linux et charge toutes les configurations
"""

import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv

class Config:
    """Configuration unifiée pour tous les environnements"""

    def __init__(self):
        """Initialise la configuration en détectant l'environnement"""

        # Détecter l'environnement
        self.is_windows = sys.platform == 'win32'
        self.is_linux = sys.platform.startswith('linux')

        # Déterminer le répertoire racine du projet
        self.project_root = Path(__file__).parent.parent.resolve()

        # Charger le fichier .env depuis la racine
        env_file = self.project_root / '.env'
        if env_file.exists():
            load_dotenv(env_file)
            print(f"[OK] Configuration chargee depuis: {env_file}")
        else:
            print(f"[WARN] Fichier .env non trouve: {env_file}")

        # Définir les chemins selon l'environnement
        self._setup_paths()

        # Charger les configurations
        self._load_linxo_config()
        self._load_depenses_config()
        self._load_api_secrets()

    def _setup_paths(self):
        """Configure les chemins selon l'environnement (Windows/Linux)"""

        if self.is_linux and os.path.exists('/home/ubuntu'):
            # Environnement VPS (production)
            self.env_name = "VPS"
            self.base_dir = Path('/home/ubuntu')
            self.linxo_agent_dir = self.base_dir / 'linxo_agent'
            self.data_dir = self.base_dir / 'data'
            self.downloads_dir = self.base_dir / 'Downloads'
            self.logs_dir = self.base_dir / 'logs'
            self.reports_dir = self.base_dir / 'reports'
            self.api_secrets_file = self.base_dir / '.api_secret_infos' / 'api_secrets.json'
        else:
            # Environnement local (développement)
            self.env_name = "LOCAL"
            self.base_dir = self.project_root
            self.linxo_agent_dir = self.base_dir / 'linxo_agent'
            self.data_dir = self.base_dir / 'data'
            self.downloads_dir = self.base_dir / 'Downloads'
            self.logs_dir = self.base_dir / 'logs'
            self.reports_dir = self.base_dir / 'reports'
            self.api_secrets_file = self.base_dir / 'api_secrets.json'

        # Créer les dossiers si nécessaires
        for directory in [self.data_dir, self.downloads_dir, self.logs_dir, self.reports_dir]:
            directory.mkdir(parents=True, exist_ok=True)

        # Fichiers de configuration
        self.config_linxo_file = self.linxo_agent_dir / 'config_linxo.json'
        self.depenses_file = self.linxo_agent_dir / 'depenses_recurrentes.json'

        print(f"[ENV] Environnement: {self.env_name}")
        print(f"[DIR] Repertoire racine: {self.base_dir}")

    def _load_linxo_config(self):
        """Charge la configuration Linxo depuis .env"""
        self.linxo_url = os.getenv('LINXO_URL', 'https://wwws.linxo.com/auth.page#Login')
        self.linxo_email = os.getenv('LINXO_EMAIL', '')
        self.linxo_password = os.getenv('LINXO_PASSWORD', '')

        if not self.linxo_email or not self.linxo_password:
            print("[WARN] ATTENTION: Credentials Linxo manquants dans .env")

    def _load_depenses_config(self):
        """Charge la configuration des dépenses depuis .env et JSON"""
        # Budget depuis .env (prioritaire)
        self.budget_variable = float(os.getenv('BUDGET_VARIABLE', '1300'))

        # Charger le fichier depenses_recurrentes.json si disponible
        if self.depenses_file.exists():
            try:
                with open(self.depenses_file, 'r', encoding='utf-8') as f:
                    self.depenses_data = json.load(f)

                # Utiliser le budget du .env comme référence (écrase le JSON)
                self.depenses_data['totaux']['budget_variable_max'] = self.budget_variable

                depenses_count = len(self.depenses_data.get('depenses_fixes', []))
                print(f"[OK] Depenses recurrentes chargees: {depenses_count} depenses fixes")
            except (OSError, ValueError, KeyError, json.JSONDecodeError) as e:
                print(f"[WARN] Erreur lors du chargement des depenses: {e}")
                self.depenses_data = {'depenses_fixes': [],
                                      'totaux': {'budget_variable_max': self.budget_variable}}
        else:
            print(f"[WARN] Fichier depenses_recurrentes.json non trouve: {self.depenses_file}")
            self.depenses_data = {'depenses_fixes': [],
                                  'totaux': {'budget_variable_max': self.budget_variable}}

    def _load_api_secrets(self):
        """Charge les secrets API depuis .env ou api_secrets.json"""

        # Priorité 1: Depuis .env
        self.smtp_email = os.getenv('SENDER_EMAIL', '')
        self.smtp_password = os.getenv('SENDER_PASSWORD', '')
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))

        # Configuration IMAP (utilise les mêmes credentials que SMTP par défaut)
        self.imap_email = os.getenv('IMAP_EMAIL', self.smtp_email)
        self.imap_password = os.getenv('IMAP_PASSWORD', self.smtp_password)
        self.imap_server = os.getenv('IMAP_SERVER', 'imap.gmail.com')
        self.imap_port = int(os.getenv('IMAP_PORT', '993'))

        self.notification_emails = [
            email.strip()
            for email in os.getenv('NOTIFICATION_EMAIL', '').split(',')
            if email.strip()
        ]

        # Configuration OVH SMS
        self.ovh_email_envoi = os.getenv('OVH_EMAIL_ENVOI', 'email2sms@ovh.net')
        self.ovh_app_secret = os.getenv('OVH_APP_SECRET', '')
        self.ovh_service_name = os.getenv('OVH_SERVICE_NAME', '')
        self.sms_sender = os.getenv('SMS_SENDER', 'PhiPEREZ')

        self.sms_recipients = [
            phone.strip()
            for phone in os.getenv('SMS_RECIPIENT', '').split(',')
            if phone.strip()
        ]

        # Priorité 2: Depuis api_secrets.json si disponible
        if self.api_secrets_file.exists():
            try:
                with open(self.api_secrets_file, 'r', encoding='utf-8') as f:
                    secrets = json.load(f)

                # Mettre à jour depuis le JSON si disponible
                if 'SMTP_GMAIL' in secrets:
                    smtp_secrets = secrets['SMTP_GMAIL'].get('secrets', {})
                    self.smtp_email = smtp_secrets.get('SMTP_EMAIL', self.smtp_email)
                    self.smtp_password = smtp_secrets.get('SMTP_PASSWORD', self.smtp_password)
                    self.smtp_server = smtp_secrets.get('SMTP_SERVER', self.smtp_server)
                    self.smtp_port = int(smtp_secrets.get('SMTP_PORT', self.smtp_port))

                if 'OVH_SMS' in secrets:
                    ovh_secrets = secrets['OVH_SMS'].get('secrets', {})
                    self.ovh_compte_sms = ovh_secrets.get('COMPTE_SMS', self.ovh_service_name)
                    self.ovh_utilisateur_sms = ovh_secrets.get('UTILISATEUR_SMS', 'default')
                    self.ovh_mot_de_passe_sms = ovh_secrets.get('MOT_DE_PASSE_SMS',
                                                                self.ovh_app_secret)
                    self.ovh_expediteur_sms = ovh_secrets.get('EXPEDITEUR_SMS', self.sms_sender)
                    self.ovh_email = ovh_secrets.get('OVH_EMAIL', self.ovh_email_envoi)

                print(f"[OK] Secrets API charges depuis: {self.api_secrets_file}")
            except (OSError, ValueError, KeyError, json.JSONDecodeError) as e:
                print(f"[WARN] Erreur lors du chargement des secrets: {e}")
        else:
            # Créer la structure OVH à partir du .env
            self.ovh_compte_sms = self.ovh_service_name
            self.ovh_utilisateur_sms = 'default'
            self.ovh_mot_de_passe_sms = self.ovh_app_secret
            self.ovh_expediteur_sms = self.sms_sender
            self.ovh_email = self.ovh_email_envoi

            print("[WARN] Fichier api_secrets.json non trouve, utilisation du .env")

        # Validation
        if not self.smtp_email or not self.smtp_password:
            print("[WARN] ATTENTION: Credentials SMTP manquants")

        if not self.imap_email or not self.imap_password:
            print("[WARN] ATTENTION: Credentials IMAP manquants (necessaires pour 2FA)")

        if not self.sms_recipients:
            print("[WARN] ATTENTION: Aucun destinataire SMS configure")

    def get_latest_csv(self):
        """Retourne le chemin du dernier fichier CSV téléchargé"""
        csv_files = list(self.data_dir.glob('*.csv'))
        if csv_files:
            return max(csv_files, key=lambda p: p.stat().st_mtime)

        # Fallback: chercher dans downloads
        csv_files = list(self.downloads_dir.glob('*.csv'))
        if csv_files:
            return max(csv_files, key=lambda p: p.stat().st_mtime)

        return self.data_dir / 'latest.csv'

    def print_summary(self):
        """Affiche un résumé de la configuration"""
        print("\n" + "=" * 80)
        print("CONFIGURATION LINXO AGENT")
        print("=" * 80)
        print(f"Environnement:          {self.env_name}")
        print(f"OS:                     {'Windows' if self.is_windows else 'Linux'}")
        print(f"Repertoire projet:      {self.project_root}")
        print(f"Repertoire donnees:     {self.data_dir}")
        print(f"Budget variable:        {self.budget_variable:.2f}E")
        print(f"Email SMTP:             {self.smtp_email}")
        print(f"Destinataires email:    {len(self.notification_emails)}")
        print(f"Destinataires SMS:      {len(self.sms_recipients)}")
        print(f"Linxo email:            {self.linxo_email}")
        print("=" * 80 + "\n")

# Instance globale de configuration (singleton)
_CONFIG_INSTANCE = None  # pylint: disable=invalid-name


def get_config():
    """Retourne l'instance de configuration (singleton)"""
    global _CONFIG_INSTANCE  # pylint: disable=global-statement
    if _CONFIG_INSTANCE is None:
        _CONFIG_INSTANCE = Config()
    return _CONFIG_INSTANCE


def reload_config():
    """Recharge la configuration"""
    global _CONFIG_INSTANCE  # pylint: disable=global-statement
    _CONFIG_INSTANCE = Config()
    return _CONFIG_INSTANCE

# Export pour faciliter l'usage
__all__ = ['Config', 'get_config', 'reload_config']
