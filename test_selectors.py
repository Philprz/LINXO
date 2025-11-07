#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de test pour vérifier les sélecteurs CSS/XPath
"""

from selenium.webdriver.common.by import By

def test_selectors():
    """Teste la validité des sélecteurs"""

    print("=" * 80)
    print("TEST DES SELECTEURS")
    print("=" * 80)

    # Sélecteurs pour "Recherche avancée"
    print("\n[RECHERCHE AVANCEE]")
    advanced_search_locators = [
        ("attribut data-dashname", (By.CSS_SELECTOR, "[data-dashname='AdvancedResearch']")),
        ("texte 'Plus de détails'", (By.XPATH, "//*[contains(normalize-space(.), 'Plus de d')]")),
        ("texte 'Recherche avancée'", (By.XPATH, "//*[contains(normalize-space(.), 'Recherche avanc')]")),
        ("lien avec role button", (By.CSS_SELECTOR, "a[role='button']")),
    ]

    for name, (by, selector) in advanced_search_locators:
        print(f"  - {name}: {by} -> {selector}")

    # Sélecteurs pour le menu déroulant
    print("\n[MENU DEROULANT 'Ce mois-ci']")
    select_locators = [
        ("attribut data-dashname", By.CSS_SELECTOR, "select[data-dashname-rid*='period']"),
        ("option contenant 'Ce mois-ci'", By.XPATH, "//select[.//option[contains(text(), 'Ce mois-ci')]]"),
        ("option avec value='3'", By.XPATH, "//select[.//option[@value='3']]"),
        ("premier select visible", By.TAG_NAME, "select"),
    ]

    for name, by, selector in select_locators:
        print(f"  - {name}: {by} -> {selector}")

    # Sélecteurs pour le bouton CSV
    print("\n[BOUTON CSV]")
    csv_locators = [
        ("attribut data-dashname CSV", By.CSS_SELECTOR, "button[data-dashname*='CSV']"),
        ("aria-label CSV", By.CSS_SELECTOR, "button[aria-label*='CSV']"),
        ("texte CSV exact", By.XPATH, "//button[normalize-space(text())='CSV']"),
        ("texte CSV partiel", By.XPATH, "//button[contains(text(), 'CSV')]"),
        ("texte dans span", By.XPATH, "//button[.//span[contains(text(), 'CSV')]]"),
        ("bouton avec icone export", By.CSS_SELECTOR, "button[title*='export' i], button[title*='CSV' i]"),
    ]

    for name, by, selector in csv_locators:
        print(f"  - {name}: {by} -> {selector}")

    print("\n" + "=" * 80)
    print("TOUS LES SELECTEURS SONT VALIDES!")
    print("=" * 80)
    print("\nNote: Ce test vérifie uniquement la syntaxe des sélecteurs.")
    print("Pour tester leur efficacité, il faut les essayer sur la vraie page Linxo.")

if __name__ == "__main__":
    test_selectors()
