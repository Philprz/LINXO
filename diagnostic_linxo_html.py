#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de diagnostic pour analyser la page Linxo et corriger la sélection de période
Capture le HTML et teste toutes les méthodes possibles pour sélectionner "Ce mois-ci"
"""

import sys
import time
import json
from pathlib import Path
from datetime import datetime

# Imports Selenium
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    ElementClickInterceptedException,
    ElementNotInteractableException
)

# Imports du projet
sys.path.insert(0, str(Path(__file__).parent))
from linxo_agent.linxo_driver_factory import initialiser_driver_linxo, se_connecter_linxo


class LinxoHTMLDiagnostic:
    """Classe de diagnostic pour analyser la page Linxo"""

    def __init__(self, output_dir=None):
        self.output_dir = Path(output_dir or "diagnostic_html")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.driver = None
        self.wait = None
        self.user_data_dir = None
        self.results = {
            'timestamp': self.timestamp,
            'steps': [],
            'selectors_found': {},
            'working_methods': [],
            'recommendations': []
        }

    def log(self, message, level="INFO"):
        """Affiche et enregistre un message"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        print(f"[{timestamp}] [{level}] {message}")
        self.results['steps'].append({
            'time': timestamp,
            'level': level,
            'message': message
        })

    def save_html(self, filename, description):
        """Sauvegarde le HTML de la page courante"""
        filepath = self.output_dir / f"{self.timestamp}_{filename}.html"
        try:
            html_content = self.driver.page_source
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html_content)
            self.log(f"HTML sauvegarde: {filepath.name} ({description})")
            return filepath
        except Exception as e:
            self.log(f"Erreur sauvegarde HTML: {e}", "ERROR")
            return None

    def save_screenshot(self, filename, description):
        """Sauvegarde un screenshot"""
        filepath = self.output_dir / f"{self.timestamp}_{filename}.png"
        try:
            self.driver.save_screenshot(str(filepath))
            self.log(f"Screenshot sauvegarde: {filepath.name} ({description})")
            return filepath
        except Exception as e:
            self.log(f"Erreur screenshot: {e}", "ERROR")
            return None

    def analyze_selects(self):
        """Analyse tous les éléments <select> de la page"""
        self.log("=== ANALYSE DES ELEMENTS <SELECT> ===")

        try:
            selects = self.driver.find_elements(By.TAG_NAME, "select")
            self.log(f"Nombre de <select> trouves: {len(selects)}")

            select_info = []
            for i, select_elem in enumerate(selects):
                info = {
                    'index': i,
                    'id': select_elem.get_attribute('id'),
                    'name': select_elem.get_attribute('name'),
                    'class': select_elem.get_attribute('class'),
                    'visible': select_elem.is_displayed(),
                    'enabled': select_elem.is_enabled(),
                    'options': []
                }

                try:
                    select_obj = Select(select_elem)
                    for option in select_obj.options:
                        info['options'].append({
                            'text': option.text,
                            'value': option.get_attribute('value'),
                            'selected': option.is_selected()
                        })
                except Exception as e:
                    info['error'] = str(e)

                select_info.append(info)

                self.log(f"  Select #{i}:")
                self.log(f"    - ID: {info['id']}")
                self.log(f"    - Name: {info['name']}")
                self.log(f"    - Visible: {info['visible']}, Enabled: {info['enabled']}")
                self.log(f"    - Options: {len(info['options'])}")
                for opt in info['options']:
                    marker = " [SELECTED]" if opt['selected'] else ""
                    self.log(f"      * {opt['text']} (value={opt['value']}){marker}")

            self.results['selectors_found']['selects'] = select_info
            return select_info

        except Exception as e:
            self.log(f"Erreur lors de l'analyse des selects: {e}", "ERROR")
            return []

    def analyze_buttons(self):
        """Analyse tous les boutons de la page"""
        self.log("=== ANALYSE DES BOUTONS ===")

        try:
            buttons = self.driver.find_elements(By.TAG_NAME, "button")
            self.log(f"Nombre de boutons trouves: {len(buttons)}")

            button_info = []
            for i, button in enumerate(buttons):
                info = {
                    'index': i,
                    'text': button.text.strip(),
                    'id': button.get_attribute('id'),
                    'class': button.get_attribute('class'),
                    'type': button.get_attribute('type'),
                    'data-dashname': button.get_attribute('data-dashname'),
                    'visible': button.is_displayed(),
                    'enabled': button.is_enabled()
                }

                button_info.append(info)

                if info['visible'] and info['text']:
                    self.log(f"  Button #{i}: '{info['text']}'")
                    self.log(f"    - ID: {info['id']}")
                    self.log(f"    - data-dashname: {info['data-dashname']}")

            self.results['selectors_found']['buttons'] = button_info
            return button_info

        except Exception as e:
            self.log(f"Erreur lors de l'analyse des boutons: {e}", "ERROR")
            return []

    def test_period_selection_methods(self):
        """Teste toutes les méthodes possibles pour sélectionner "Ce mois-ci" """
        self.log("=== TEST DES METHODES DE SELECTION DE PERIODE ===")

        methods = [
            {
                'name': 'Methode 1: Select par ID gwt-container',
                'selector': (By.CSS_SELECTOR, "#gwt-container select"),
                'value': '3'  # "Ce mois-ci"
            },
            {
                'name': 'Methode 2: Select dans div.GJYWTJUCBY',
                'selector': (By.CSS_SELECTOR, "div.GJYWTJUCBY > select"),
                'value': '3'
            },
            {
                'name': 'Methode 3: Select avec option "Ce mois-ci"',
                'selector': (By.XPATH, "//select[.//option[contains(text(), 'Ce mois-ci')]]"),
                'value': '3'
            },
            {
                'name': 'Methode 4: Premier select visible',
                'selector': (By.TAG_NAME, "select"),
                'value': '3',
                'filter_visible': True
            }
        ]

        for method in methods:
            self.log(f"Test: {method['name']}")
            try:
                # Trouver l'élément
                if method.get('filter_visible'):
                    elements = self.driver.find_elements(*method['selector'])
                    select_elem = None
                    for elem in elements:
                        if elem.is_displayed():
                            select_elem = elem
                            break
                    if not select_elem:
                        raise NoSuchElementException("Aucun select visible")
                else:
                    select_elem = self.driver.find_element(*method['selector'])

                # Vérifier visibilité
                if not select_elem.is_displayed():
                    self.log(f"  -> Element trouve mais non visible", "WARNING")
                    continue

                # Tester la sélection
                select_obj = Select(select_elem)

                # Afficher les options disponibles
                self.log(f"  -> Options disponibles:")
                for opt in select_obj.options:
                    self.log(f"     * {opt.text} (value={opt.get_attribute('value')})")

                # Sélectionner "Ce mois-ci" (value=3)
                select_obj.select_by_value(method['value'])
                self.log(f"  -> SUCCES: Selection par value={method['value']}", "SUCCESS")

                # Attendre un peu pour voir si ça prend effet
                time.sleep(2)

                # Enregistrer comme méthode fonctionnelle
                self.results['working_methods'].append({
                    'method': method['name'],
                    'selector': str(method['selector']),
                    'value': method['value'],
                    'success': True
                })

                return True

            except (NoSuchElementException, TimeoutException) as e:
                self.log(f"  -> Element non trouve: {e}", "WARNING")
            except Exception as e:
                self.log(f"  -> Erreur: {e}", "ERROR")

        self.log("Aucune methode de selection n'a fonctionne", "ERROR")
        return False

    def test_validation_button(self):
        """Teste la recherche du bouton de validation"""
        self.log("=== TEST DU BOUTON DE VALIDATION ===")

        button_methods = [
            ('Bouton "Valider"', By.XPATH, "//button[contains(text(), 'Valider')]"),
            ('Bouton "Appliquer"', By.XPATH, "//button[contains(text(), 'Appliquer')]"),
            ('Bouton "Filtrer"', By.XPATH, "//button[contains(text(), 'Filtrer')]"),
            ('Bouton "OK"', By.XPATH, "//button[contains(text(), 'OK')]"),
            ('Input submit', By.CSS_SELECTOR, "input[type='submit']"),
            ('Button submit', By.CSS_SELECTOR, "button[type='submit']"),
        ]

        for method_name, by_method, selector in button_methods:
            self.log(f"Test: {method_name}")
            try:
                button = self.driver.find_element(by_method, selector)

                if button.is_displayed() and button.is_enabled():
                    self.log(f"  -> TROUVE et cliquable", "SUCCESS")
                    self.results['working_methods'].append({
                        'method': f'Validation button: {method_name}',
                        'selector': f"{by_method}: {selector}",
                        'success': True
                    })
                    return button
                else:
                    self.log(f"  -> Trouve mais non cliquable", "WARNING")

            except NoSuchElementException:
                self.log(f"  -> Non trouve", "WARNING")
            except Exception as e:
                self.log(f"  -> Erreur: {e}", "ERROR")

        self.log("Aucun bouton de validation trouve", "WARNING")
        return None

    def run_diagnostic(self):
        """Exécute le diagnostic complet"""
        print("\n" + "=" * 80)
        print("DIAGNOSTIC LINXO - ANALYSE HTML ET SELECTION DE PERIODE")
        print("=" * 80)

        try:
            # ETAPE 1: Initialisation
            self.log("ETAPE 1: Initialisation du navigateur")
            self.driver, self.wait, self.user_data_dir = initialiser_driver_linxo()

            # ETAPE 2: Connexion
            self.log("ETAPE 2: Connexion a Linxo")
            if not se_connecter_linxo(self.driver, self.wait):
                self.log("Echec de la connexion", "ERROR")
                return False

            self.log("Connexion reussie", "SUCCESS")
            time.sleep(3)

            # ETAPE 3: Navigation vers historique
            self.log("ETAPE 3: Navigation vers la page Historique")
            self.driver.get('https://wwws.linxo.com/secured/history.page')
            time.sleep(5)

            self.save_html("01_historique_initial", "Page historique initiale")
            self.save_screenshot("01_historique_initial", "Page historique initiale")

            # ETAPE 4: Analyse initiale
            self.log("ETAPE 4: Analyse des elements de la page")
            self.analyze_buttons()
            self.analyze_selects()

            # ETAPE 5: Clic sur "Recherche avancée"
            self.log("ETAPE 5: Tentative de clic sur 'Recherche avancee'")

            advanced_search_clicked = False
            advanced_locators = [
                ("data-dashname='AdvancedResearch'", By.CSS_SELECTOR, "[data-dashname='AdvancedResearch']"),
                ("Texte 'Plus de détails'", By.XPATH, "//*[contains(text(), 'Plus de d')]"),
                ("Texte 'Recherche avancée'", By.XPATH, "//*[contains(text(), 'Recherche avanc')]"),
            ]

            for name, by_method, selector in advanced_locators:
                try:
                    self.log(f"  Tentative: {name}")
                    recherche_btn = self.wait.until(EC.element_to_be_clickable((by_method, selector)))

                    try:
                        recherche_btn.click()
                    except (ElementClickInterceptedException, ElementNotInteractableException):
                        self.driver.execute_script("arguments[0].click();", recherche_btn)

                    self.log(f"  -> SUCCES: Clic sur recherche avancee ({name})", "SUCCESS")
                    advanced_search_clicked = True
                    time.sleep(3)
                    break

                except (TimeoutException, NoSuchElementException) as e:
                    self.log(f"  -> Echec: {e}", "WARNING")

            if not advanced_search_clicked:
                self.log("Impossible de cliquer sur 'Recherche avancee'", "ERROR")
                self.results['recommendations'].append(
                    "Le bouton 'Recherche avancée' n'a pas été trouvé. "
                    "L'interface Linxo a peut-être changé."
                )

            self.save_html("02_apres_recherche_avancee", "Après clic recherche avancée")
            self.save_screenshot("02_apres_recherche_avancee", "Après clic recherche avancée")

            # ETAPE 6: Re-analyser les selects
            self.log("ETAPE 6: Re-analyse des selects apres recherche avancee")
            self.analyze_selects()
            self.analyze_buttons()

            # ETAPE 7: Tester sélection période
            self.log("ETAPE 7: Test de la selection de periode")
            period_selected = self.test_period_selection_methods()

            if period_selected:
                self.save_html("03_apres_selection_periode", "Après sélection période")
                self.save_screenshot("03_apres_selection_periode", "Après sélection période")

                # ETAPE 8: Chercher bouton validation
                self.log("ETAPE 8: Recherche du bouton de validation")
                validation_btn = self.test_validation_button()

                if validation_btn:
                    self.log("Clic sur le bouton de validation")
                    validation_btn.click()
                    time.sleep(5)

                    self.save_html("04_apres_validation", "Après validation filtre")
                    self.save_screenshot("04_apres_validation", "Après validation filtre")

            # ETAPE 9: Générer le rapport
            self.log("ETAPE 9: Generation du rapport")
            self.generate_report()

            # ETAPE 10: Auto-correction du code
            self.log("ETAPE 10: Auto-correction du code period_selector.py")
            self.auto_correct_period_selector()

            return True

        except Exception as e:
            self.log(f"Erreur fatale: {e}", "ERROR")
            import traceback
            traceback.print_exc()
            return False

        finally:
            # Cleanup
            if self.driver:
                self.log("Fermeture du navigateur")
                self.driver.quit()

            if self.user_data_dir and self.user_data_dir.exists():
                import shutil
                shutil.rmtree(self.user_data_dir, ignore_errors=True)

    def auto_correct_period_selector(self):
        """
        Auto-corrige le fichier period_selector.py avec les sélecteurs fonctionnels
        """
        self.log("=== AUTO-CORRECTION DU CODE ===")

        if not self.results['working_methods']:
            self.log("Aucune methode fonctionnelle trouvee, auto-correction impossible", "WARNING")
            return False

        try:
            # Chemin du fichier à corriger
            period_selector_file = Path(__file__).parent / "linxo_agent" / "period_selector.py"

            if not period_selector_file.exists():
                self.log(f"Fichier introuvable: {period_selector_file}", "ERROR")
                return False

            self.log(f"Fichier a corriger: {period_selector_file}")

            # Créer une sauvegarde
            backup_file = period_selector_file.with_suffix('.py.bak')
            import shutil
            shutil.copy2(period_selector_file, backup_file)
            self.log(f"Sauvegarde creee: {backup_file}")

            # Extraire les sélecteurs fonctionnels
            advanced_search_selector = None
            period_select_selector = None
            validation_button_selector = None

            for method in self.results['working_methods']:
                method_name = method['method'].lower()

                if 'recherche' in method_name or 'advanced' in method_name:
                    advanced_search_selector = method['selector']
                elif 'select' in method_name or 'periode' in method_name or 'mois' in method_name:
                    period_select_selector = method['selector']
                elif 'valid' in method_name or 'button' in method_name:
                    validation_button_selector = method['selector']

            # Générer le nouveau code
            updates = []

            if advanced_search_selector:
                self.log(f"Selecteur 'Recherche avancee' trouve: {advanced_search_selector}")
                updates.append(('advanced_search', advanced_search_selector))

            if period_select_selector:
                self.log(f"Selecteur 'Period select' trouve: {period_select_selector}")
                updates.append(('period_select', period_select_selector))

            if validation_button_selector:
                self.log(f"Selecteur 'Bouton validation' trouve: {validation_button_selector}")
                updates.append(('validation_button', validation_button_selector))

            if not updates:
                self.log("Aucun selecteur a mettre a jour", "WARNING")
                return False

            # Lire le fichier actuel
            with open(period_selector_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Ajouter un commentaire avec l'horodatage de l'auto-correction
            timestamp_comment = f"\n# [AUTO-CORRECTED {self.timestamp}] Updated selectors from diagnostic\n"

            # Insérer le commentaire au début (après les imports)
            if '"""' in content:
                # Trouver la fin du docstring
                docstring_end = content.find('"""', content.find('"""') + 3) + 3
                content = content[:docstring_end] + timestamp_comment + content[docstring_end:]
            else:
                content = timestamp_comment + content

            # Sauvegarder le fichier modifié
            with open(period_selector_file, 'w', encoding='utf-8') as f:
                f.write(content)

            self.log(f"Fichier corrige: {period_selector_file}", "SUCCESS")
            self.log(f"Nombre de selecteurs mis a jour: {len(updates)}", "SUCCESS")

            # Enregistrer dans les recommandations
            self.results['recommendations'].append(
                f"Code auto-corrige avec {len(updates)} nouveaux selecteurs. "
                f"Sauvegarde: {backup_file.name}"
            )

            return True

        except Exception as e:
            self.log(f"Erreur lors de l'auto-correction: {e}", "ERROR")
            import traceback
            traceback.print_exc()
            return False

    def generate_report(self):
        """Génère un rapport JSON et texte"""
        # Rapport JSON
        json_file = self.output_dir / f"{self.timestamp}_rapport.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)

        self.log(f"Rapport JSON sauvegarde: {json_file}")

        # Rapport texte
        txt_file = self.output_dir / f"{self.timestamp}_rapport.txt"
        with open(txt_file, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("RAPPORT DE DIAGNOSTIC LINXO\n")
            f.write("=" * 80 + "\n\n")
            f.write(f"Date: {self.timestamp}\n\n")

            f.write("=== ETAPES EXECUTEES ===\n")
            for step in self.results['steps']:
                f.write(f"[{step['time']}] [{step['level']}] {step['message']}\n")

            f.write("\n=== SELECTEURS TROUVES ===\n")

            if 'selects' in self.results['selectors_found']:
                f.write(f"\nElements <select>: {len(self.results['selectors_found']['selects'])}\n")
                for select in self.results['selectors_found']['selects']:
                    f.write(f"\nSelect #{select['index']}:\n")
                    f.write(f"  ID: {select['id']}\n")
                    f.write(f"  Name: {select['name']}\n")
                    f.write(f"  Visible: {select['visible']}\n")
                    f.write(f"  Options:\n")
                    for opt in select.get('options', []):
                        f.write(f"    - {opt['text']} (value={opt['value']})\n")

            if 'buttons' in self.results['selectors_found']:
                f.write(f"\nBoutons: {len(self.results['selectors_found']['buttons'])}\n")
                for btn in self.results['selectors_found']['buttons']:
                    if btn['visible'] and btn['text']:
                        f.write(f"  - '{btn['text']}' (data-dashname={btn['data-dashname']})\n")

            f.write("\n=== METHODES FONCTIONNELLES ===\n")
            for method in self.results['working_methods']:
                f.write(f"\n{method['method']}:\n")
                f.write(f"  Selector: {method['selector']}\n")
                f.write(f"  Success: {method['success']}\n")

            f.write("\n=== RECOMMANDATIONS ===\n")
            if self.results['recommendations']:
                for rec in self.results['recommendations']:
                    f.write(f"  - {rec}\n")
            else:
                f.write("  Aucune recommandation specifique\n")

        self.log(f"Rapport texte sauvegarde: {txt_file}")

        print("\n" + "=" * 80)
        print("DIAGNOSTIC TERMINE")
        print("=" * 80)
        print(f"Fichiers generes dans: {self.output_dir}")
        print(f"  - Rapport JSON: {json_file.name}")
        print(f"  - Rapport texte: {txt_file.name}")
        print("=" * 80)


def main():
    """Point d'entrée principal"""
    diagnostic = LinxoHTMLDiagnostic()
    success = diagnostic.run_diagnostic()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
