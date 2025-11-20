#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gestionnaire de configuration pour l'interface d'administration.
Centralise la lecture/écriture de depenses_recurrentes.json et des variables .env.
"""

import json
import os
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv, set_key

BASE_DIR = Path(__file__).parent.parent.parent.parent
ENV_FILE = BASE_DIR / ".env"
EXPENSES_FILE = BASE_DIR / "linxo_agent" / "depenses_recurrentes.json"

DEFAULT_COLLECTIONS = {
    "depenses_fixes": [],
    "revenus": [],
    "ajustements_budget": [],
}


class ConfigManager:
    """Gestionnaire de configuration."""

    def __init__(self) -> None:
        self.env_file = ENV_FILE
        self.expenses_file = EXPENSES_FILE
        load_dotenv()

    # ------------------------------------------------------------------ #
    # Helpers                                                            #
    # ------------------------------------------------------------------ #

    def _load_data(self) -> Dict[str, Any]:
        """Charge le contenu du fichier JSON principal."""
        if not self.expenses_file.exists():
            return deepcopy(DEFAULT_COLLECTIONS)

        try:
            with open(self.expenses_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError):
            return deepcopy(DEFAULT_COLLECTIONS)

        # S'assurer que les collections essentielles existent
        for key, default_value in DEFAULT_COLLECTIONS.items():
            if key not in data or not isinstance(data[key], list):
                data[key] = deepcopy(default_value)

        return data

    def _save_data(self, data: Dict[str, Any]) -> None:
        """Écrit le JSON sur disque."""
        with open(self.expenses_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    @staticmethod
    def _next_id(items: List[Dict[str, Any]]) -> int:
        """Retourne le prochain ID disponible pour une collection."""
        existing_ids = [item.get("id") for item in items if isinstance(item.get("id"), int)]
        return (max(existing_ids) if existing_ids else 0) + 1

    @staticmethod
    def _find_index(items: List[Dict[str, Any]], entry_id: int) -> Optional[int]:
        """Trouve l'index d'un élément dans une liste par ID."""
        for idx, item in enumerate(items):
            if item.get("id") == entry_id:
                return idx
        return None

    def _ensure_ids(self, data: Dict[str, Any]) -> bool:
        """Garantit que chaque entrée possède un ID unique."""
        updated = False
        for key in DEFAULT_COLLECTIONS:
            items = data.get(key, [])
            if not isinstance(items, list):
                data[key] = []
                updated = True
                continue

            next_id = self._next_id(items) - 1
            for item in items:
                if not isinstance(item.get("id"), int):
                    next_id += 1
                    item["id"] = next_id
                    updated = True
        return updated

    # ------------------------------------------------------------------ #
    # Budget & notifications                                             #
    # ------------------------------------------------------------------ #

    def get_budget(self) -> Dict[str, Any]:
        """Récupère la configuration du budget."""
        return {
            "budget_variable": os.getenv("BUDGET_VARIABLE", "0"),
            "budget_variable_int": int(os.getenv("BUDGET_VARIABLE", "0")),
        }

    def update_budget(self, new_budget: int) -> bool:
        """Met à jour le budget variable."""
        try:
            set_key(str(self.env_file), "BUDGET_VARIABLE", str(new_budget))
            os.environ["BUDGET_VARIABLE"] = str(new_budget)
            return True
        except Exception:
            return False

    def get_reports_base_url(self) -> Dict[str, str]:
        """Retourne l'URL publique des rapports HTML."""
        base_url = os.getenv("REPORTS_BASE_URL", "https://linxo.appliprz.ovh/reports")
        return {"reports_base_url": base_url}

    def update_reports_base_url(self, base_url: str) -> bool:
        """Met à jour l'URL publique des rapports."""
        try:
            set_key(str(self.env_file), "REPORTS_BASE_URL", base_url.strip())
            os.environ["REPORTS_BASE_URL"] = base_url.strip()
            return True
        except Exception:
            return False

    def get_notification_recipients(self) -> Dict[str, Any]:
        """Récupère les destinataires email/SMS/WhatsApp."""
        email_recipients = os.getenv("NOTIFICATION_EMAIL", "").split(",")
        sms_recipients = os.getenv("SMS_RECIPIENT", "").split(",")

        # WhatsApp configuration
        whatsapp_enabled = os.getenv("WHATSAPP_ENABLED", "false").lower() == "true"
        whatsapp_group = os.getenv("WHATSAPP_GROUP_NAME", "").strip()
        whatsapp_contacts = os.getenv("WHATSAPP_CONTACTS", "").split(",")
        whatsapp_frequency = os.getenv("NOTIFICATION_FREQUENCY", "weekly").strip()

        return {
            "email": [email.strip() for email in email_recipients if email.strip()],
            "sms": [sms.strip() for sms in sms_recipients if sms.strip()],
            "whatsapp": {
                "enabled": whatsapp_enabled,
                "group_name": whatsapp_group if whatsapp_group else "",
                "contacts": [contact.strip() for contact in whatsapp_contacts if contact.strip()],
                "frequency": whatsapp_frequency
            }
        }

    def update_notification_recipients(
        self,
        emails: Optional[List[str]] = None,
        sms: Optional[List[str]] = None,
        whatsapp: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Met à jour les destinataires des notifications."""
        try:
            if emails is not None:
                emails_str = ", ".join(emails)
                set_key(str(self.env_file), "NOTIFICATION_EMAIL", emails_str)
                os.environ["NOTIFICATION_EMAIL"] = emails_str

            if sms is not None:
                sms_str = ", ".join(sms)
                set_key(str(self.env_file), "SMS_RECIPIENT", sms_str)
                os.environ["SMS_RECIPIENT"] = sms_str

            if whatsapp is not None:
                # WhatsApp enabled
                enabled = str(whatsapp.get("enabled", False)).lower()
                set_key(str(self.env_file), "WHATSAPP_ENABLED", enabled)
                os.environ["WHATSAPP_ENABLED"] = enabled

                # WhatsApp group name
                group_name = whatsapp.get("group_name", "").strip()
                set_key(str(self.env_file), "WHATSAPP_GROUP_NAME", group_name)
                os.environ["WHATSAPP_GROUP_NAME"] = group_name

                # WhatsApp contacts (individual recipients)
                contacts = whatsapp.get("contacts", [])
                if isinstance(contacts, list):
                    contacts_str = ", ".join(contacts)
                else:
                    contacts_str = ""
                set_key(str(self.env_file), "WHATSAPP_CONTACTS", contacts_str)
                os.environ["WHATSAPP_CONTACTS"] = contacts_str

                # Notification frequency
                frequency = whatsapp.get("frequency", "weekly").strip()
                set_key(str(self.env_file), "NOTIFICATION_FREQUENCY", frequency)
                os.environ["NOTIFICATION_FREQUENCY"] = frequency

            return True
        except Exception:
            return False

    # ------------------------------------------------------------------ #
    # Dépenses & revenus                                                 #
    # ------------------------------------------------------------------ #

    def get_expenses(self) -> Dict[str, Any]:
        """Retourne la configuration complète (dépenses, revenus, ajustements)."""
        data = self._load_data()
        if self._ensure_ids(data):
            self._save_data(data)
        return data

    def add_expense(self, expense: Dict[str, Any]) -> bool:
        """Ajoute une dépense récurrente."""
        try:
            data = self._load_data()
            expenses = data.get("depenses_fixes", [])
            expense["id"] = self._next_id(expenses)
            expenses.append(expense)
            data["depenses_fixes"] = expenses
            self._save_data(data)
            return True
        except Exception:
            return False

    def update_expense(self, expense_id: int, expense: Dict[str, Any]) -> bool:
        """Met à jour une dépense récurrente."""
        try:
            data = self._load_data()
            expenses = data.get("depenses_fixes", [])
            index = self._find_index(expenses, expense_id)
            if index is None:
                return False
            expense["id"] = expense_id
            expenses[index] = expense
            data["depenses_fixes"] = expenses
            self._save_data(data)
            return True
        except Exception:
            return False

    def delete_expense(self, expense_id: int) -> bool:
        """Supprime une dépense récurrente."""
        try:
            data = self._load_data()
            expenses = data.get("depenses_fixes", [])
            index = self._find_index(expenses, expense_id)
            if index is None:
                return False
            expenses.pop(index)
            data["depenses_fixes"] = expenses
            self._save_data(data)
            return True
        except Exception:
            return False

    # ------------------------------ Revenus --------------------------- #

    def add_income(self, income: Dict[str, Any]) -> bool:
        """Ajoute un revenu."""
        try:
            data = self._load_data()
            revenus = data.get("revenus", [])
            income["id"] = self._next_id(revenus)
            revenus.append(income)
            data["revenus"] = revenus
            self._save_data(data)
            return True
        except Exception:
            return False

    def update_income(self, income_id: int, income: Dict[str, Any]) -> bool:
        """Met à jour un revenu."""
        try:
            data = self._load_data()
            revenus = data.get("revenus", [])
            index = self._find_index(revenus, income_id)
            if index is None:
                return False
            income["id"] = income_id
            revenus[index] = income
            data["revenus"] = revenus
            self._save_data(data)
            return True
        except Exception:
            return False

    def delete_income(self, income_id: int) -> bool:
        """Supprime un revenu."""
        try:
            data = self._load_data()
            revenus = data.get("revenus", [])
            index = self._find_index(revenus, income_id)
            if index is None:
                return False
            revenus.pop(index)
            data["revenus"] = revenus
            self._save_data(data)
            return True
        except Exception:
            return False

    # ----------------------- Ajustements budget ----------------------- #

    def add_budget_adjustment(self, adjustment: Dict[str, Any]) -> bool:
        """Ajoute un ajustement manuel de budget."""
        try:
            data = self._load_data()
            adjustments = data.get("ajustements_budget", [])
            adjustment["id"] = self._next_id(adjustments)
            adjustments.append(adjustment)
            data["ajustements_budget"] = adjustments
            self._save_data(data)
            return True
        except Exception:
            return False

    def update_budget_adjustment(self, adjustment_id: int, adjustment: Dict[str, Any]) -> bool:
        """Met à jour un ajustement de budget."""
        try:
            data = self._load_data()
            adjustments = data.get("ajustements_budget", [])
            index = self._find_index(adjustments, adjustment_id)
            if index is None:
                return False
            adjustment["id"] = adjustment_id
            adjustments[index] = adjustment
            data["ajustements_budget"] = adjustments
            self._save_data(data)
            return True
        except Exception:
            return False

    def delete_budget_adjustment(self, adjustment_id: int) -> bool:
        """Supprime un ajustement de budget."""
        try:
            data = self._load_data()
            adjustments = data.get("ajustements_budget", [])
            index = self._find_index(adjustments, adjustment_id)
            if index is None:
                return False
            adjustments.pop(index)
            data["ajustements_budget"] = adjustments
            self._save_data(data)
            return True
        except Exception:
            return False


# Instance globale
config_manager = ConfigManager()
