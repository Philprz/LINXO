#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests unitaires pour le module de génération de rapports
"""

import unittest
import tempfile
import shutil
from pathlib import Path
from datetime import date
import pandas as pd
import os
import sys

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from linxo_agent.reports import (
    slugify,
    classify_famille,
    generate_token,
    verify_token,
    build_daily_report
)


class TestSlugify(unittest.TestCase):
    """Tests pour la fonction slugify"""

    def test_slugify_basic(self):
        self.assertEqual(slugify("Alimentation"), "alimentation")
        self.assertEqual(slugify("Restaurants & Cafés"), "restaurants-cafes")

    def test_slugify_accents(self):
        self.assertEqual(slugify("Logement & Énergie"), "logement-energie")
        self.assertEqual(slugify("Santé"), "sante")

    def test_slugify_special_chars(self):
        self.assertEqual(slugify("Shopping/Mode"), "shopping-mode")
        self.assertEqual(slugify("Impôts & Taxes"), "impots-taxes")

    def test_slugify_spaces(self):
        self.assertEqual(slugify("Frais bancaires"), "frais-bancaires")


class TestClassifyFamille(unittest.TestCase):
    """Tests pour la classification des dépenses en familles"""

    def test_classify_alimentation(self):
        famille = classify_famille("Alimentation", "CARREFOUR")
        self.assertEqual(famille, "Alimentation")

    def test_classify_transports(self):
        famille = classify_famille("Transport", "STATION TOTAL")
        self.assertEqual(famille, "Transports")

    def test_classify_restaurants(self):
        famille = classify_famille("Restaurant", "LE PARIS")
        self.assertEqual(famille, "Restaurants & Cafés")

    def test_classify_logement(self):
        famille = classify_famille("", "EDF FACTURE")
        self.assertEqual(famille, "Logement & Énergie")

    def test_classify_abonnements(self):
        famille = classify_famille("Abonnement", "NETFLIX")
        self.assertEqual(famille, "Abonnements")

    def test_classify_default(self):
        famille = classify_famille("Autre", "DIVERS")
        self.assertEqual(famille, "Autres dépenses")


class TestTokenGeneration(unittest.TestCase):
    """Tests pour la génération et vérification de tokens HMAC"""

    def setUp(self):
        self.signing_key = "test_secret_key_123"
        self.url = "/reports/2025-01-15/index.html"

    def test_generate_token(self):
        token = generate_token(self.url, self.signing_key)
        self.assertIsInstance(token, str)
        self.assertIn(':', token)

        parts = token.split(':')
        self.assertEqual(len(parts), 2)

        signature, expiry = parts
        self.assertEqual(len(signature), 64)  # SHA256 hex
        self.assertTrue(expiry.isdigit())

    def test_verify_valid_token(self):
        token = generate_token(self.url, self.signing_key)

        # Import de la fonction de vérification
        from linxo_agent.report_server.app import verify_token as verify_token_app

        # Mock de REPORTS_SIGNING_KEY
        os.environ['REPORTS_SIGNING_KEY'] = self.signing_key

        # Le token devrait être valide
        is_valid = verify_token_app(self.url, token)
        self.assertTrue(is_valid)

    def test_verify_invalid_signature(self):
        from linxo_agent.report_server.app import verify_token as verify_token_app

        os.environ['REPORTS_SIGNING_KEY'] = self.signing_key

        # Token avec signature invalide
        invalid_token = "invalid_signature:9999999999"
        is_valid = verify_token_app(self.url, invalid_token)
        self.assertFalse(is_valid)


class TestBuildDailyReport(unittest.TestCase):
    """Tests pour la génération de rapports complets"""

    def setUp(self):
        """Créer un environnement de test temporaire"""
        self.temp_dir = tempfile.mkdtemp()
        self.old_cwd = os.getcwd()

        # Créer une structure de répertoires simulée
        self.test_project_dir = Path(self.temp_dir) / 'LINXO'
        self.test_project_dir.mkdir()

        # Créer les répertoires nécessaires
        (self.test_project_dir / 'data' / 'reports').mkdir(parents=True)
        (self.test_project_dir / 'templates' / 'reports').mkdir(parents=True)
        (self.test_project_dir / 'static' / 'reports').mkdir(parents=True)
        (self.test_project_dir / 'linxo_agent').mkdir(parents=True)

        # Copier les templates
        project_root = Path(__file__).parent.parent
        templates_src = project_root / 'templates' / 'reports'

        if templates_src.exists():
            for template_file in templates_src.glob('*.j2'):
                shutil.copy(
                    template_file,
                    self.test_project_dir / 'templates' / 'reports' / template_file.name
                )

        # Créer le fichier reports.py dans le temp
        shutil.copy(
            project_root / 'linxo_agent' / 'reports.py',
            self.test_project_dir / 'linxo_agent' / 'reports.py'
        )

        os.chdir(self.test_project_dir)

    def tearDown(self):
        """Nettoyer l'environnement de test"""
        os.chdir(self.old_cwd)
        shutil.rmtree(self.temp_dir)

    def test_build_report_basic(self):
        """Test de génération de rapport basique"""
        # Créer un DataFrame de test
        data = {
            'date': ['15/01/2025', '14/01/2025', '13/01/2025'],
            'libelle': ['CARREFOUR', 'TOTAL STATION', 'RESTAURANT'],
            'montant': [-45.50, -60.00, -35.00],
            'categorie': ['Alimentation', 'Transport', 'Restaurant'],
            'date_str': ['15/01/2025', '14/01/2025', '13/01/2025']
        }
        df = pd.DataFrame(data)

        # Générer le rapport
        report_index = build_daily_report(
            df,
            report_date=date(2025, 1, 15),
            base_url='http://localhost:8810/reports',
            signing_key='test_key'
        )

        # Vérifications
        self.assertEqual(report_index.report_date, '2025-01-15')
        self.assertGreater(len(report_index.families), 0)
        self.assertAlmostEqual(report_index.grand_total, 140.50, places=2)
        self.assertEqual(report_index.total_transactions, 3)

        # Vérifier que les fichiers ont été créés
        self.assertTrue(report_index.base_dir.exists())
        self.assertTrue((report_index.base_dir / 'index.html').exists())

    def test_build_report_missing_base_url(self):
        """Test que l'erreur est levée si base_url manquant"""
        data = {'date': ['15/01/2025'], 'libelle': ['TEST'], 'montant': [-10.0], 'categorie': ['Test']}
        df = pd.DataFrame(data)

        with self.assertRaises(ValueError) as context:
            build_daily_report(df, base_url=None)

        self.assertIn('REPORTS_BASE_URL', str(context.exception))

    def test_groupby_famille(self):
        """Test du groupby par famille"""
        data = {
            'date': ['15/01/2025', '14/01/2025', '13/01/2025', '12/01/2025'],
            'libelle': ['CARREFOUR', 'AUCHAN', 'TOTAL', 'SHELL'],
            'montant': [-45.50, -30.00, -60.00, -50.00],
            'categorie': ['Alimentation', 'Alimentation', 'Transport', 'Transport'],
            'date_str': ['15/01/2025', '14/01/2025', '13/01/2025', '12/01/2025']
        }
        df = pd.DataFrame(data)

        report_index = build_daily_report(
            df,
            report_date=date(2025, 1, 15),
            base_url='http://localhost:8810/reports'
        )

        # On devrait avoir 2 familles
        self.assertEqual(len(report_index.families), 2)

        # Vérifier les totaux
        totals = {f['name']: f['total'] for f in report_index.families}

        # Alimentation: 45.50 + 30.00 = 75.50
        self.assertAlmostEqual(totals['Alimentation'], 75.50, places=2)

        # Transports: 60.00 + 50.00 = 110.00
        self.assertAlmostEqual(totals['Transports'], 110.00, places=2)


if __name__ == '__main__':
    unittest.main()
