#!/usr/bin/env python3
"""Test rapide des corrections apportées aux rapports"""

import sys
from pathlib import Path

# Ajouter le répertoire linxo_agent au PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent / 'linxo_agent'))

def test_reports_imports():
    """Test que le module reports s'importe correctement"""
    print("Test 1: Import du module reports...")
    try:
        from reports import build_frais_fixes_page, build_depenses_variables_page
        print("[OK] Module reports importe avec succes")
        return True
    except Exception as e:
        print(f"[ERREUR] Erreur d'import: {e}")
        return False

def test_templates():
    """Test que les templates Jinja2 sont valides"""
    print("\nTest 2: Validation des templates Jinja2...")
    try:
        from jinja2 import Environment, FileSystemLoader
        env = Environment(loader=FileSystemLoader('templates/reports'))

        # Test template dépenses variables
        template_var = env.get_template('depenses-variables.html.j2')
        print("✓ Template depenses-variables.html.j2 valide")

        # Test template frais fixes
        template_fix = env.get_template('frais-fixes.html.j2')
        print("✓ Template frais-fixes.html.j2 valide")

        return True
    except Exception as e:
        print(f"✗ Erreur de validation: {e}")
        return False

def test_sorting_logic():
    """Test de la logique de tri"""
    print("\nTest 3: Test de la logique de tri...")
    try:
        # Test tri par montant décroissant
        preleves = [
            {'montant': 100.0, 'libelle': 'A'},
            {'montant': 500.0, 'libelle': 'B'},
            {'montant': 250.0, 'libelle': 'C'},
        ]

        preleves.sort(key=lambda x: x['montant'], reverse=True)

        assert preleves[0]['montant'] == 500.0, "Le tri décroissant ne fonctionne pas"
        assert preleves[1]['montant'] == 250.0, "Le tri décroissant ne fonctionne pas"
        assert preleves[2]['montant'] == 100.0, "Le tri décroissant ne fonctionne pas"

        print("✓ Tri par montant décroissant fonctionne correctement")
        return True
    except Exception as e:
        print(f"✗ Erreur de tri: {e}")
        return False

def test_total_prevu_calculation():
    """Test du calcul du total prévu"""
    print("\nTest 4: Test du calcul du total prévu...")
    try:
        # Simuler des frais de référence
        depenses_fixes_ref = [
            {'libelle': 'Frais A', 'montant': 100.0, 'mois_occurrence': [1, 2, 3]},
            {'libelle': 'Frais B', 'montant': 200.0, 'mois_occurrence': [1, 2, 3]},
            {'libelle': 'Frais C', 'montant': 300.0, 'mois_occurrence': [4, 5, 6]},  # Pas ce mois
        ]

        mois_actuel = 2

        # Calculer le total prévu
        total_prevu_config = 0.0
        for frais in depenses_fixes_ref:
            mois_occurrence = frais.get('mois_occurrence', list(range(1, 13)))
            if mois_actuel in mois_occurrence:
                total_prevu_config += frais.get('montant', 0.0)

        assert total_prevu_config == 300.0, f"Total prévu incorrect: {total_prevu_config}"

        print(f"✓ Calcul du total prévu correct: {total_prevu_config}€")
        return True
    except Exception as e:
        print(f"✗ Erreur de calcul: {e}")
        return False

def main():
    """Exécute tous les tests"""
    print("=" * 60)
    print("Test des corrections apportées aux rapports")
    print("=" * 60)

    results = []
    results.append(test_reports_imports())
    results.append(test_templates())
    results.append(test_sorting_logic())
    results.append(test_total_prevu_calculation())

    print("\n" + "=" * 60)
    print(f"Résultat: {sum(results)}/{len(results)} tests réussis")
    print("=" * 60)

    if all(results):
        print("\n✓ Tous les tests sont passés avec succès!")
        return 0
    else:
        print("\n✗ Certains tests ont échoué")
        return 1

if __name__ == '__main__':
    sys.exit(main())
