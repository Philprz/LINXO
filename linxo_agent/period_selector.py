#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module d'auto-correction pour la sélection de période sur Linxo
Teste plusieurs méthodes et s'adapte automatiquement
"""

import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    ElementClickInterceptedException,
    ElementNotInteractableException,
    StaleElementReferenceException
)


class PeriodSelector:
    """Sélecteur de période auto-adaptatif pour Linxo"""

    def __init__(self, driver, wait):
        self.driver = driver
        self.wait = wait

    def click_advanced_search(self):
        """
        Clique sur "Recherche avancée" avec plusieurs méthodes de fallback

        Returns:
            bool: True si succès, False sinon
        """
        print("[PERIOD] Tentative de clic sur 'Recherche avancee'...")

        # Méthodes à essayer dans l'ordre
        methods = [
            {
                'name': 'data-dashname=AdvancedResearch',
                'locator': (By.CSS_SELECTOR, "[data-dashname='AdvancedResearch']")
            },
            {
                'name': 'Texte "Plus de détails"',
                'locator': (By.XPATH, "//*[contains(normalize-space(.), 'Plus de d')]")
            },
            {
                'name': 'Texte "Recherche avancée"',
                'locator': (By.XPATH, "//*[contains(normalize-space(.), 'Recherche avanc')]")
            },
            {
                'name': 'Lien avec role button',
                'locator': (By.CSS_SELECTOR, "a[role='button']")
            },
            {
                'name': 'Div cliquable avec classe search',
                'locator': (By.CSS_SELECTOR, "div[class*='search' i]")
            }
        ]

        for method in methods:
            try:
                print(f"  [Tentative] {method['name']}")

                # Essayer de trouver et cliquer sur l'élément
                element = self.wait.until(EC.element_to_be_clickable(method['locator']))

                # Tenter un clic normal
                try:
                    element.click()
                except (ElementClickInterceptedException, ElementNotInteractableException):
                    # Fallback: clic JavaScript
                    print(f"    [Fallback] Clic JavaScript")
                    self.driver.execute_script("arguments[0].click();", element)

                print(f"  [SUCCESS] Clic reussi: {method['name']}")
                time.sleep(2)
                return True

            except (TimeoutException, NoSuchElementException) as e:
                print(f"    [WARNING] Methode echouee: {type(e).__name__}")
                continue

        print("[ERROR] Impossible de cliquer sur 'Recherche avancee' avec aucune methode")
        return False

    def select_current_month(self):
        """
        Sélectionne "Ce mois-ci" dans le menu déroulant avec auto-détection

        Returns:
            bool: True si succès, False sinon
        """
        print("[PERIOD] Selection de 'Ce mois-ci'...")

        # Méthodes pour trouver le select
        select_methods = [
            {
                'name': 'Select par ID #gwt-container',
                'locator': (By.CSS_SELECTOR, "#gwt-container select"),
            },
            {
                'name': 'Select dans div.GJYWTJUCBY',
                'locator': (By.CSS_SELECTOR, "div.GJYWTJUCBY > select"),
            },
            {
                'name': 'Select avec option "Ce mois-ci"',
                'locator': (By.XPATH, "//select[.//option[contains(text(), 'Ce mois-ci')]]"),
            },
            {
                'name': 'Select avec option value=3',
                'locator': (By.XPATH, "//select[.//option[@value='3']]"),
            },
            {
                'name': 'Premier select visible',
                'locator': (By.TAG_NAME, "select"),
                'filter_visible': True
            }
        ]

        for method in select_methods:
            try:
                print(f"  [Tentative] {method['name']}")

                # Trouver le select
                if method.get('filter_visible'):
                    # Trouver tous les selects et filtrer les visibles
                    elements = self.driver.find_elements(*method['locator'])
                    select_element = None
                    for elem in elements:
                        try:
                            if elem.is_displayed() and elem.is_enabled():
                                select_element = elem
                                break
                        except StaleElementReferenceException:
                            continue

                    if not select_element:
                        print(f"    [WARNING] Aucun select visible trouve")
                        continue
                else:
                    select_element = self.wait.until(
                        EC.presence_of_element_located(method['locator'])
                    )

                # Vérifier que l'élément est visible
                if not select_element.is_displayed():
                    print(f"    [WARNING] Element trouve mais non visible")
                    continue

                # Créer l'objet Select
                select_obj = Select(select_element)

                # Afficher les options disponibles pour debug
                print(f"    [INFO] Options disponibles:")
                for opt in select_obj.options:
                    marker = " [CURRENT]" if opt.is_selected() else ""
                    print(f"      - {opt.text} (value={opt.get_attribute('value')}){marker}")

                # Tenter de sélectionner "Ce mois-ci" par différentes méthodes
                selection_success = False

                # Méthode 1: Par value="3"
                try:
                    select_obj.select_by_value("3")
                    print(f"    [SUCCESS] Selection par value=3")
                    selection_success = True
                except Exception as e:
                    print(f"    [WARNING] Selection par value echouee: {e}")

                # Méthode 2: Par texte visible
                if not selection_success:
                    try:
                        select_obj.select_by_visible_text("Ce mois-ci")
                        print(f"    [SUCCESS] Selection par texte visible")
                        selection_success = True
                    except Exception as e:
                        print(f"    [WARNING] Selection par texte echouee: {e}")

                # Méthode 3: Par texte partiel
                if not selection_success:
                    try:
                        for option in select_obj.options:
                            if "mois" in option.text.lower():
                                option.click()
                                print(f"    [SUCCESS] Selection par texte partiel: {option.text}")
                                selection_success = True
                                break
                    except Exception as e:
                        print(f"    [WARNING] Selection par texte partiel echouee: {e}")

                if selection_success:
                    print(f"  [SUCCESS] Periode selectionnee: {method['name']}")
                    time.sleep(2)
                    return True

            except (TimeoutException, NoSuchElementException) as e:
                print(f"    [WARNING] Methode echouee: {type(e).__name__}")
                continue
            except Exception as e:
                print(f"    [ERROR] Erreur inattendue: {e}")
                continue

        print("[ERROR] Impossible de selectionner 'Ce mois-ci' avec aucune methode")
        return False

    def click_validation_button(self):
        """
        Clique sur le bouton de validation du filtre

        Returns:
            bool: True si succès, False sinon
        """
        print("[PERIOD] Recherche du bouton de validation...")

        # Méthodes pour trouver le bouton
        button_methods = [
            {
                'name': 'Bouton "Valider"',
                'locator': (By.XPATH, "//button[contains(text(), 'Valider')]")
            },
            {
                'name': 'Bouton "Appliquer"',
                'locator': (By.XPATH, "//button[contains(text(), 'Appliquer')]")
            },
            {
                'name': 'Bouton "Filtrer"',
                'locator': (By.XPATH, "//button[contains(text(), 'Filtrer')]")
            },
            {
                'name': 'Bouton "OK"',
                'locator': (By.XPATH, "//button[contains(text(), 'OK')]")
            },
            {
                'name': 'Input type submit',
                'locator': (By.CSS_SELECTOR, "input[type='submit']")
            },
            {
                'name': 'Button type submit',
                'locator': (By.CSS_SELECTOR, "button[type='submit']")
            },
            {
                'name': 'Bouton dans le conteneur du select',
                'locator': (By.XPATH, "//select/ancestor::div[1]//button")
            }
        ]

        for method in button_methods:
            try:
                print(f"  [Tentative] {method['name']}")

                button = self.wait.until(EC.element_to_be_clickable(method['locator']))

                # Tenter un clic normal
                try:
                    button.click()
                except (ElementClickInterceptedException, ElementNotInteractableException):
                    # Fallback: clic JavaScript
                    print(f"    [Fallback] Clic JavaScript")
                    self.driver.execute_script("arguments[0].click();", button)

                print(f"  [SUCCESS] Bouton clique: {method['name']}")
                time.sleep(5)  # Attendre le rafraîchissement de la page
                return True

            except (TimeoutException, NoSuchElementException) as e:
                print(f"    [WARNING] Methode echouee: {type(e).__name__}")
                continue

        print("[WARNING] Aucun bouton de validation trouve - la selection pourrait etre appliquee automatiquement")
        return False

    def select_period_with_autocorrect(self):
        """
        Workflow complet avec auto-correction

        Returns:
            bool: True si la période a été sélectionnée avec succès
        """
        print("\n" + "=" * 80)
        print("[PERIOD] SELECTION DE PERIODE AVEC AUTO-CORRECTION")
        print("=" * 80)

        # Étape 1: Cliquer sur "Recherche avancée"
        advanced_clicked = self.click_advanced_search()

        if not advanced_clicked:
            print("[WARNING] Impossible de cliquer sur 'Recherche avancee'")
            print("[WARNING] Tentative de selection de periode sans recherche avancee...")

        # Étape 2: Sélectionner "Ce mois-ci"
        period_selected = self.select_current_month()

        if not period_selected:
            print("[ERROR] Echec de la selection de periode")
            return False

        # Étape 3: Cliquer sur le bouton de validation
        validated = self.click_validation_button()

        if not validated:
            print("[WARNING] Pas de bouton de validation trouve")
            print("[INFO] La periode pourrait etre appliquee automatiquement")

        print("=" * 80)
        print("[PERIOD] Selection de periode terminee")
        print("=" * 80 + "\n")

        return True
