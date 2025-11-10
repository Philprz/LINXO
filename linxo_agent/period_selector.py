#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module d'auto-correction pour la sélection de période sur Linxo
Teste plusieurs méthodes et s'adapte automatiquement
"""

import time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
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

    PERIOD_DROPDOWN_LOCATORS = [
        (By.CSS_SELECTOR, "select.GJYWTJUCKY"),
        (By.CSS_SELECTOR, "div.GJYWTJUCBY > select"),
        (By.CSS_SELECTOR, "#gwt-container select"),
        (By.XPATH, "//select[.//option[contains(., 'mois')]]"),
        (By.XPATH, "//select[.//option[@value='3']]")
    ]

    def __init__(self, driver, wait):
        self.driver = driver
        self.wait = wait

    def _find_period_dropdown(self):
        """Retourne le premier select affichant la période"""
        fallback = None
        for locator in self.PERIOD_DROPDOWN_LOCATORS:
            try:
                elements = self.driver.find_elements(*locator)
            except Exception:
                continue

            for element in elements:
                try:
                    if element.is_displayed() and element.is_enabled():
                        return element
                    if fallback is None:
                        fallback = element
                except StaleElementReferenceException:
                    continue

        return fallback

    def _wait_for_period_dropdown(self, timeout=10):
        """Attend qu'un select de période soit disponible"""
        deadline = time.time() + timeout
        while time.time() < deadline:
            dropdown = self._find_period_dropdown()
            if dropdown is not None:
                return dropdown
            time.sleep(0.5)

        raise TimeoutException("Aucun menu déroulant de période détecté")

    def _select_option_from_dropdown(self, dropdown_element, identifier):
        """Sélectionne l'option 'Ce mois-ci' sur un select donné"""
        if dropdown_element is None:
            return False

        try:
            visible = dropdown_element.is_displayed()
            enabled = dropdown_element.is_enabled()
        except StaleElementReferenceException:
            print(f"    [WARNING] {identifier}: element stale")
            return False

        if not visible or not enabled:
            print(f"    [INFO] {identifier}: element non interactif (visible={visible}, enabled={enabled})")
            return self._try_select_with_javascript(dropdown_element, identifier)

        try:
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", dropdown_element)
            time.sleep(0.3)
        except Exception:
            pass

        try:
            dropdown_element.click()
        except (ElementClickInterceptedException, ElementNotInteractableException):
            self.driver.execute_script("arguments[0].click();", dropdown_element)

        try:
            select_obj = Select(dropdown_element)
        except Exception as e:
            print(f"    [WARNING] {identifier}: impossible de creer Select ({e})")
            return self._try_select_with_javascript(dropdown_element, identifier)

        selection_success = False

        try:
            select_obj.select_by_value("3")
            print(f"    [SUCCESS] {identifier}: selection via value=3")
            selection_success = True
        except Exception as e:
            print(f"    [INFO] {identifier}: selection par value impossible ({e})")

        if not selection_success:
            try:
                select_obj.select_by_visible_text("Ce mois-ci")
                print(f"    [SUCCESS] {identifier}: selection via texte exact")
                selection_success = True
            except Exception as e:
                print(f"    [INFO] {identifier}: selection par texte exact impossible ({e})")

        if not selection_success:
            try:
                for option in select_obj.options:
                    if "mois" in option.text.lower():
                        option.click()
                        print(f"    [SUCCESS] {identifier}: selection via texte partiel ({option.text})")
                        selection_success = True
                        break
            except Exception as e:
                print(f"    [INFO] {identifier}: selection par texte partiel impossible ({e})")

        if selection_success:
            time.sleep(1)
            selected_value = None
            selected_text = ""
            try:
                selected_value = dropdown_element.get_attribute("value")
            except Exception:
                pass

            try:
                selected_text = select_obj.first_selected_option.text.strip()
            except Exception:
                pass

            if selected_value == "3" or "mois" in selected_text.lower():
                print(f"    [SUCCESS] {identifier}: 'Ce mois-ci' est actif (value={selected_value}, text='{selected_text}')")
                return True

            print(f"    [WARNING] {identifier}: valeur selectionnee inattendue (value={selected_value}, text='{selected_text}')")

        print(f"    [INFO] {identifier}: tentative de selection via JavaScript")
        return self._try_select_with_javascript(dropdown_element, identifier)

    def _select_with_keyboard(self, dropdown_element):
        """Dernier recours: navigation clavier sur le select courant"""
        if dropdown_element is None:
            return False

        print("  [Fallback] Tentative de selection par clavier...")
        try:
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", dropdown_element)
            time.sleep(0.3)
        except Exception:
            pass

        try:
            dropdown_element.click()
        except (ElementClickInterceptedException, ElementNotInteractableException):
            self.driver.execute_script("arguments[0].click();", dropdown_element)

        try:
            for i in range(4):
                dropdown_element.send_keys(Keys.ARROW_DOWN)
                time.sleep(0.3)
                print(f"      [OK] Fleche bas {i+1}/4")
            dropdown_element.send_keys(Keys.ENTER)
            time.sleep(1)
        except Exception as e:
            print(f"    [ERROR] Impossible d'utiliser le clavier: {e}")
            return False

        try:
            value = dropdown_element.get_attribute("value")
        except Exception:
            value = None

        if value == "3":
            print("    [SUCCESS] Selection clavier confirmee (value=3)")
            return True

        print(f"    [WARNING] Selection clavier non confirme (value={value})")
        return False

    def _try_select_with_javascript(self, select_element, identifier):
        """
        Essaie de sélectionner 'Ce mois-ci' via JavaScript sur un élément select

        Args:
            select_element: L'élément select
            identifier: Identifiant pour le logging (nom ou numéro)

        Returns:
            bool: True si succès, False sinon
        """
        try:
            # Créer l'objet Select pour récupérer les options
            select_obj = Select(select_element)

            # Afficher les options disponibles
            print(f"    [INFO] Options disponibles dans {identifier}:")
            for opt in select_obj.options:
                marker = " [CURRENT]" if opt.is_selected() else ""
                print(f"      - '{opt.text}' (value='{opt.get_attribute('value')}'){marker}")

            # Chercher l'option qui correspond à "Ce mois-ci"
            target_option = None
            for option in select_obj.options:
                option_value = option.get_attribute('value')
                option_text = option.text.strip()

                # Essayer de matcher par value=3 ou par texte
                if option_value == '3' or 'mois' in option_text.lower():
                    target_option = option
                    print(f"    [INFO] Option trouvee: '{option_text}' (value={option_value})")
                    break

            if not target_option:
                print(f"    [WARNING] Aucune option 'Ce mois-ci' trouvee dans {identifier}")
                return False

            # Méthode 1: Sélection JavaScript directe avec déclenchement d'événements
            print(f"    [INFO] Tentative de selection JavaScript...")
            success = self.driver.execute_script("""
                var select = arguments[0];
                var option = arguments[1];

                // Changer la sélection
                select.value = option.value;
                option.selected = true;

                // Déclencher les événements pour notifier l'application
                var events = ['change', 'input', 'click'];
                events.forEach(function(eventType) {
                    var event = new Event(eventType, { bubbles: true, cancelable: true });
                    select.dispatchEvent(event);
                });

                return select.value === option.value;
            """, select_element, target_option)

            if success:
                print(f"    [SUCCESS] Selection JavaScript reussie pour {identifier}")
                time.sleep(2)
                return True
            else:
                print(f"    [WARNING] Selection JavaScript echouee pour {identifier}")
                return False

        except Exception as e:
            print(f"    [ERROR] Erreur JavaScript pour {identifier}: {e}")
            return False

    def click_advanced_search(self):
        """
        Clique sur "Recherche avancée" avec plusieurs méthodes de fallback

        Returns:
            bool: True si succès, False sinon
        """
        print("[PERIOD] Tentative de clic sur 'Recherche avancee'...")

        # Si le panneau est déjà ouvert, inutile de cliquer
        if self._find_period_dropdown():
            print("  [INFO] Le panneau 'Recherche avancee' est deja visible")
            return True

        # Méthodes à essayer dans l'ordre
        methods = [
            {
                'name': 'Classe Linxo GJYWTJUCKGC',
                'locator': (By.CSS_SELECTOR, "a.GJYWTJUCKGC, button.GJYWTJUCKGC")
            },
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
                element = self.wait.until(EC.element_to_be_clickable(method['locator']))

                try:
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                except Exception:
                    pass

                try:
                    element.click()
                except (ElementClickInterceptedException, ElementNotInteractableException):
                    print("    [Fallback] Clic JavaScript")
                    self.driver.execute_script("arguments[0].click();", element)

                try:
                    self._wait_for_period_dropdown(timeout=8)
                    print(f"  [SUCCESS] Formulaire avance affiche apres {method['name']}")
                    return True
                except TimeoutException:
                    print("    [WARNING] Aucun dropdown visible apres le clic - on tente la methode suivante")
                    continue

            except (TimeoutException, NoSuchElementException) as e:
                print(f"    [WARNING] Methode echouee: {type(e).__name__}")
                continue

        print("[ERROR] Impossible de cliquer sur 'Recherche avancee' avec aucune methode")
        return False

    def select_current_month(self):
        """Sélectionne "Ce mois-ci" dans le menu déroulant de Linxo"""
        print("[PERIOD] Selection de 'Ce mois-ci'...")

        dropdown_element = None
        try:
            dropdown_element = self._wait_for_period_dropdown(timeout=15)
            print("  [INFO] Dropdown principal detecte")
        except TimeoutException as e:
            print(f"  [WARNING] Aucun dropdown visible apres 15s: {e}")

        if dropdown_element and self._select_option_from_dropdown(dropdown_element, "Select principal (GJYWTJUCKY)"):
            return True

        if dropdown_element and self._select_with_keyboard(dropdown_element):
            return True

        print("  [Methode 2] Recherche exhaustive des autres selects...")

        select_methods = [
            {
                'name': 'Select classe Linxo (GJYWTJUCKY)',
                'locator': (By.CSS_SELECTOR, "select.GJYWTJUCKY"),
            },
            {
                'name': 'Select dans div.GJYWTJUCBY',
                'locator': (By.CSS_SELECTOR, "div.GJYWTJUCBY > select"),
            },
            {
                'name': 'Select #gwt-container',
                'locator': (By.CSS_SELECTOR, "#gwt-container select"),
            },
            {
                'name': 'Select contenant "mois"',
                'locator': (By.XPATH, "//select[.//option[contains(., 'mois')]]"),
            },
            {
                'name': 'Select avec option value=3',
                'locator': (By.XPATH, "//select[.//option[@value='3']]")
            },
            {
                'name': 'Premier select visible',
                'locator': (By.TAG_NAME, "select"),
                'filter_visible': True
            },
            {
                'name': 'Tous les selects (iteration)',
                'locator': (By.TAG_NAME, "select"),
                'try_all': True
            }
        ]

        for method in select_methods:
            try:
                print(f"  [Tentative] {method['name']}")

                if method.get('try_all'):
                    elements = self.driver.find_elements(*method['locator'])
                    print(f"    [INFO] {len(elements)} select(s) trouves")
                    for idx, elem in enumerate(elements):
                        if self._select_option_from_dropdown(elem, f"{method['name']} #{idx+1}"):
                            return True
                    continue

                if method.get('filter_visible'):
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
                        print("    [WARNING] Aucun select visible trouve")
                        continue
                else:
                    select_element = self.wait.until(
                        EC.presence_of_element_located(method['locator'])
                    )

                if self._select_option_from_dropdown(select_element, method['name']):
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
                'name': 'Bouton classes Linxo (Valider)',
                'locator': (By.CSS_SELECTOR, "button.GJYWTJUCEV.GJYWTJUCMW.GJYWTJUCHV")
            },
            {
                'name': 'Bouton action data-dashlane',
                'locator': (By.CSS_SELECTOR, "button[data-dashlane-label='true'][data-dashlane-classification='action']")
            },
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
