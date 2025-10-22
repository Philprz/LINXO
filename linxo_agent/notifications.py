#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module de notifications unifié pour Linxo Agent
Gère l'envoi d'emails et de SMS via différents canaux
Version 2.0 - Refactorisé avec configuration unifiée
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
import sys

# Import du module de configuration unifié
try:
    from config import get_config
    from report_formatter_v2 import formater_email_html_v2, formater_sms_v2
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent))
    from config import get_config
    from report_formatter_v2 import formater_email_html_v2, formater_sms_v2


class NotificationManager:
    """Gestionnaire centralisé des notifications"""

    def __init__(self):
        """Initialise le gestionnaire avec la configuration"""
        self.config = get_config()

    def send_email(self, subject, body, recipients=None, attachment_path=None, is_html=False):
        """
        Envoie un email via SMTP Gmail

        Args:
            subject: Sujet de l'email
            body: Corps de l'email (texte ou HTML)
            recipients: Liste d'adresses email (optionnel, utilise config par défaut)
            attachment_path: Chemin vers une pièce jointe (optionnel)
            is_html: True si le body est en HTML

        Returns:
            bool: True si envoi réussi, False sinon
        """
        try:
            # Utiliser les destinataires de la config si non fournis
            if recipients is None:
                recipients = self.config.notification_emails

            if not recipients:
                print("[ERREUR] Aucun destinataire email configure")
                return False

            # S'assurer que c'est une liste
            if isinstance(recipients, str):
                recipients = [recipients]

            # Créer le message
            msg = MIMEMultipart()
            msg['Subject'] = subject
            msg['From'] = f"Agent Linxo <{self.config.smtp_email}>"
            msg['To'] = ', '.join(recipients)

            # Ajouter le corps du message
            if is_html:
                body_part = MIMEText(body, 'html', 'utf-8')
            else:
                body_part = MIMEText(body, 'plain', 'utf-8')
            msg.attach(body_part)

            # Ajouter une pièce jointe si fournie
            if attachment_path and Path(attachment_path).exists():
                with open(attachment_path, 'rb') as f:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(f.read())
                    encoders.encode_base64(part)

                    filename = Path(attachment_path).name
                    part.add_header('Content-Disposition', f'attachment; filename={filename}')
                    msg.attach(part)

                print(f"[INFO] Piece jointe ajoutee: {filename}")

            # Envoyer l'email
            print(f"[EMAIL] Connexion au serveur SMTP {self.config.smtp_server}:{self.config.smtp_port}...")

            server = smtplib.SMTP(self.config.smtp_server, self.config.smtp_port)
            server.starttls()
            server.login(self.config.smtp_email, self.config.smtp_password)
            server.send_message(msg)
            server.quit()

            print(f"[SUCCESS] Email envoye a: {', '.join(recipients)}")
            return True

        except Exception as e:
            print(f"[ERREUR] Echec envoi email: {e}")
            import traceback
            traceback.print_exc()
            return False

    def send_sms_ovh(self, message, recipients=None):
        """
        Envoie un SMS via OVH (méthode email-to-SMS)

        Args:
            message: Texte du SMS (max 160 caractères)
            recipients: Liste de numéros de téléphone (optionnel, utilise config par défaut)

        Returns:
            dict: Résultats de l'envoi pour chaque destinataire
        """
        try:
            # Utiliser les destinataires de la config si non fournis
            if recipients is None:
                recipients = self.config.sms_recipients

            if not recipients:
                print("[ERREUR] Aucun destinataire SMS configure")
                return {}

            # S'assurer que c'est une liste
            if isinstance(recipients, str):
                recipients = [recipients]

            # Tronquer le message si trop long
            if len(message) > 160:
                message = message[:157] + "..."
                print(f"[WARNING] Message SMS tronque a 160 caracteres")

            results = {}

            # Envoyer un SMS à chaque destinataire
            for phone in recipients:
                try:
                    # Format du sujet pour OVH: compte:utilisateur:password:expediteur:destinataire
                    subject = f"{self.config.ovh_compte_sms}:{self.config.ovh_utilisateur_sms}:{self.config.ovh_mot_de_passe_sms}:{self.config.ovh_expediteur_sms}:{phone}"

                    msg = MIMEMultipart()
                    msg['Subject'] = subject
                    msg['From'] = self.config.smtp_email
                    msg['To'] = self.config.ovh_email

                    body = MIMEText(message, 'plain', 'utf-8')
                    msg.attach(body)

                    print(f"[SMS] Envoi SMS via OVH a {phone}...")

                    server = smtplib.SMTP(self.config.smtp_server, self.config.smtp_port)
                    server.starttls()
                    server.login(self.config.smtp_email, self.config.smtp_password)
                    server.send_message(msg)
                    server.quit()

                    print(f"[SUCCESS] SMS envoye a {phone}")
                    results[phone] = True

                except Exception as e:
                    print(f"[ERREUR] Echec SMS pour {phone}: {e}")
                    results[phone] = False

            return results

        except Exception as e:
            print(f"[ERREUR] Erreur generale SMS: {e}")
            import traceback
            traceback.print_exc()
            return {}

    def send_budget_notification(self, analysis_result):
        """
        Envoie les notifications (email + SMS) pour le rapport budgétaire
        Utilise le nouveau format visuel et épuré

        Args:
            analysis_result: Résultat de l'analyse budgétaire (dict)

        Returns:
            dict: Résultats de l'envoi (email et SMS)
        """
        from datetime import datetime
        from analyzer import generer_conseil_budget

        print("\n[NOTIFICATION] Preparation des notifications...")

        # Extraire les données
        total_depenses = analysis_result.get('total_variables', 0)
        budget_max = analysis_result.get('budget_max', self.config.budget_variable)
        reste = budget_max - total_depenses
        pourcentage = (total_depenses / budget_max * 100) if budget_max > 0 else 0

        # Générer le conseil personnalisé
        conseil = generer_conseil_budget(total_depenses, budget_max)

        # Préparer le message SMS avec le nouveau format
        sms_msg = formater_sms_v2(total_depenses, budget_max, reste, pourcentage)

        # Préparer l'email HTML avec le nouveau format
        email_body_html = formater_email_html_v2(analysis_result, budget_max, conseil)

        # Sujet de l'email
        if reste < 0:
            email_subject = f"🔴 ALERTE Budget - Dépassement de {abs(reste):.0f}€"
        elif pourcentage >= 80:
            email_subject = f"🟠 Budget à {pourcentage:.0f}% - Attention"
        else:
            email_subject = f"🟢 Rapport Budget - {datetime.now().strftime('%d/%m/%Y')}"

        # Envoyer les notifications
        results = {}

        # SMS
        print("\n[SMS] Envoi des SMS...")
        results['sms'] = self.send_sms_ovh(sms_msg)

        # Email
        print("\n[EMAIL] Envoi des emails...")
        csv_path = analysis_result.get('csv_path')
        results['email'] = self.send_email(
            email_subject,
            email_body_html,
            attachment_path=csv_path,
            is_html=True
        )

        return results


# Fonction de test
if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("TEST DU MODULE DE NOTIFICATIONS")
    print("=" * 80)

    manager = NotificationManager()

    # Afficher la configuration
    print(f"\nEmail SMTP: {manager.config.smtp_email}")
    print(f"Destinataires email: {manager.config.notification_emails}")
    print(f"Destinataires SMS: {manager.config.sms_recipients}")

    # Test email
    print("\n" + "=" * 80)
    response = input("\nEnvoyer un email de test? (o/n): ")
    if response.lower() == 'o':
        subject = "Test Agent Linxo"
        body = "Ceci est un email de test depuis le module de notifications unifie.\n\nSi vous recevez ce message, la configuration fonctionne correctement!"

        success = manager.send_email(subject, body)
        if success:
            print("\n[SUCCESS] Email de test envoye!")
        else:
            print("\n[ERREUR] Echec de l'envoi de l'email de test")

    # Test SMS
    print("\n" + "=" * 80)
    response = input("\nEnvoyer un SMS de test? (o/n): ")
    if response.lower() == 'o':
        message = "Test Agent Linxo: Si vous recevez ce SMS, la configuration fonctionne!"

        results = manager.send_sms_ovh(message)
        if any(results.values()):
            print("\n[SUCCESS] Au moins un SMS de test envoye!")
        else:
            print("\n[ERREUR] Echec de l'envoi des SMS de test")

    print("\n" + "=" * 80)
    print("Test termine")
    print("=" * 80)
