#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gestionnaire de configuration pour l'interface d'administration
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional
from dotenv import load_dotenv, set_key

BASE_DIR = Path(__file__).parent.parent.parent.parent
ENV_FILE = BASE_DIR / ".env"
EXPENSES_FILE = BASE_DIR / "linxo_agent" / "depenses_recurrentes.json"


class ConfigManager:
    """Gestionnaire de configuration"""

    def __init__(self):
        self.env_file = ENV_FILE
        self.expenses_file = EXPENSES_FILE
        load_dotenv()

    def get_budget(self) -> Dict[str, any]:
        """
        Récupère la configuration du budget

        Returns:
            dict: Configuration du budget
        """
        return {
            'budget_variable': os.getenv('BUDGET_VARIABLE', '0'),
            'budget_variable_int': int(os.getenv('BUDGET_VARIABLE', '0'))
        }

    def update_budget(self, new_budget: int) -> bool:
        """
        Met à jour le budget

        Args:
            new_budget: Nouveau montant du budget

        Returns:
            bool: True si succès
        """
        try:
            set_key(str(self.env_file), 'BUDGET_VARIABLE', str(new_budget))
            os.environ['BUDGET_VARIABLE'] = str(new_budget)
            return True
        except Exception:
            return False

    def get_notification_recipients(self) -> Dict[str, any]:
        """
        Récupère les destinataires des notifications

        Returns:
            dict: Destinataires email et SMS
        """
        email_recipients = os.getenv('NOTIFICATION_EMAIL', '').split(',')
        sms_recipients = os.getenv('SMS_RECIPIENT', '').split(',')

        return {
            'email': [email.strip() for email in email_recipients if email.strip()],
            'sms': [sms.strip() for sms in sms_recipients if sms.strip()]
        }

    def update_notification_recipients(
        self,
        emails: Optional[List[str]] = None,
        sms: Optional[List[str]] = None
    ) -> bool:
        """
        Met à jour les destinataires des notifications

        Args:
            emails: Liste des emails (ou None pour ne pas modifier)
            sms: Liste des SMS (ou None pour ne pas modifier)

        Returns:
            bool: True si succès
        """
        try:
            if emails is not None:
                emails_str = ', '.join(emails)
                set_key(str(self.env_file), 'NOTIFICATION_EMAIL', emails_str)
                os.environ['NOTIFICATION_EMAIL'] = emails_str

            if sms is not None:
                sms_str = ', '.join(sms)
                set_key(str(self.env_file), 'SMS_RECIPIENT', sms_str)
                os.environ['SMS_RECIPIENT'] = sms_str

            return True
        except Exception:
            return False

    def get_expenses(self) -> Dict[str, any]:
        """
        Récupère toutes les dépenses récurrentes

        Returns:
            dict: Dépenses récurrentes
        """
        if not self.expenses_file.exists():
            return {'depenses_fixes': [], 'revenus': []}

        try:
            with open(self.expenses_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Ajouter un ID à chaque dépense si pas présent
            for i, expense in enumerate(data.get('depenses_fixes', [])):
                if 'id' not in expense:
                    expense['id'] = i

            return data

        except Exception:
            return {'depenses_fixes': [], 'revenus': []}

    def add_expense(self, expense: Dict) -> bool:
        """
        Ajoute une nouvelle dépense récurrente

        Args:
            expense: Dictionnaire de la dépense

        Returns:
            bool: True si succès
        """
        try:
            data = self.get_expenses()

            # Générer un nouvel ID
            max_id = max([e.get('id', 0) for e in data['depenses_fixes']], default=0)
            expense['id'] = max_id + 1

            data['depenses_fixes'].append(expense)

            with open(self.expenses_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            return True

        except Exception:
            return False

    def update_expense(self, expense_id: int, expense: Dict) -> bool:
        """
        Met à jour une dépense récurrente

        Args:
            expense_id: ID de la dépense
            expense: Nouvelles données

        Returns:
            bool: True si succès
        """
        try:
            data = self.get_expenses()

            # Trouver l'index de la dépense
            index = None
            for i, exp in enumerate(data['depenses_fixes']):
                if exp.get('id') == expense_id:
                    index = i
                    break

            if index is None:
                return False

            # Garder l'ID
            expense['id'] = expense_id
            data['depenses_fixes'][index] = expense

            with open(self.expenses_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            return True

        except Exception:
            return False

    def delete_expense(self, expense_id: int) -> bool:
        """
        Supprime une dépense récurrente

        Args:
            expense_id: ID de la dépense

        Returns:
            bool: True si succès
        """
        try:
            data = self.get_expenses()

            # Filtrer la dépense à supprimer
            data['depenses_fixes'] = [
                exp for exp in data['depenses_fixes']
                if exp.get('id') != expense_id
            ]

            with open(self.expenses_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            return True

        except Exception:
            return False


# Instance globale
config_manager = ConfigManager()
