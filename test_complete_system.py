#!/usr/bin/env python3
"""
Test complet du système amélioré
Vérifie toutes les nouvelles fonctionnalités
"""

import sys
from pathlib import Path

# Ajouter le répertoire linxo_agent au path
sys.path.insert(0, str(Path('.') / 'linxo_agent'))

from analyzer import est_depense_recurrente
from config import get_config

def test_multi_libelles():
    """Test des libellés multiples"""
    print("=" * 80)
    print("TEST 1 : LIBELLES MULTIPLES")
    print("=" * 80)

    config = get_config()
    depenses_fixes = config.depenses_data.get('depenses_fixes', [])

    # Trouver la dépense OURA qui a maintenant 2 libellés
    oura_config = next(
        (d for d in depenses_fixes if 'OURA' in str(d.get('libelle', ''))),
        None
    )

    if oura_config:
        print(f"\nConfiguration OURA:")
        print(f"  Libelles: {oura_config['libelle']}")
        print(f"  Type: {type(oura_config['libelle'])}")

        # Tester avec libellé REG.RECETTE OURA
        trans1 = {
            'libelle': 'REG.RECETTE OURA',
            'libelle_complet': 'REG.RECETTE OURA',
            'montant': -96.10
        }
        est_fixe1, info1 = est_depense_recurrente(trans1, depenses_fixes)

        # Tester avec libellé SNCF
        trans2 = {
            'libelle': 'SNCF-VOYAGEURS',
            'libelle_complet': 'SNCF-VOYAGEURS',
            'montant': -76.70
        }
        est_fixe2, info2 = est_depense_recurrente(trans2, depenses_fixes)

        print(f"\nTest REG.RECETTE OURA: {'[OK] DETECTE' if est_fixe1 else '[X] NON DETECTE'}")
        if info1:
            print(f"  Nom: {info1.get('nom')}")

        print(f"\nTest SNCF-VOYAGEURS: {'[OK] DETECTE' if est_fixe2 else '[X] NON DETECTE'}")
        if info2:
            print(f"  Nom: {info2.get('nom')}")

        success = est_fixe1 and est_fixe2
        print(f"\n{'[OK] Test reussi!' if success else '[X] Test echoue!'}")
        return success
    else:
        print("[WARN] Configuration OURA non trouvee")
        return False


def test_tolerance_flexible():
    """Test des tolérances flexibles"""
    print("\n" + "=" * 80)
    print("TEST 2 : TOLERANCES FLEXIBLES")
    print("=" * 80)

    config = get_config()
    depenses_fixes = config.depenses_data.get('depenses_fixes', [])

    # Test EDF avec 30% de tolérance
    edf_config = next(
        (d for d in depenses_fixes if 'EDF' in str(d.get('libelle', '')).upper()),
        None
    )

    if edf_config:
        print(f"\nConfiguration EDF:")
        print(f"  Montant ref: {edf_config.get('montant')} EUR")
        print(f"  Tolerance: {edf_config.get('montant_tolerance', 0.05) * 100}%")

        # Test avec montant dans la tolérance
        trans_ok = {
            'libelle': 'EDF clients particuliers',
            'libelle_complet': 'EDF clients particuliers',
            'montant': -117.14  # ~9% de différence avec 129
        }
        est_fixe_ok, info_ok = est_depense_recurrente(trans_ok, depenses_fixes)

        # Test avec montant hors tolérance si c'était encore 5%
        # Avec 30% de tolérance, cela devrait passer
        trans_limite = {
            'libelle': 'EDF clients particuliers',
            'libelle_complet': 'EDF clients particuliers',
            'montant': -100.00  # ~22% de différence
        }
        est_fixe_limite, info_limite = est_depense_recurrente(trans_limite, depenses_fixes)

        print(f"\nTest EDF 117.14 EUR (9% ecart): {'[OK] DETECTE' if est_fixe_ok else '[X] NON DETECTE'}")
        print(f"Test EDF 100.00 EUR (22% ecart): {'[OK] DETECTE' if est_fixe_limite else '[X] NON DETECTE'}")

        success = est_fixe_ok and est_fixe_limite
        print(f"\n{'[OK] Test reussi!' if success else '[X] Test echoue!'}")
        return success
    else:
        print("[WARN] Configuration EDF non trouvee")
        return False


def test_family_aggregator():
    """Test de l'agrégateur de familles"""
    print("\n" + "=" * 80)
    print("TEST 3 : AGREGATEUR DE FAMILLES")
    print("=" * 80)

    try:
        from family_aggregator import ExpenseFamilyAggregator

        config = get_config()
        aggregator = ExpenseFamilyAggregator(config)

        # Créer des transactions de test
        test_transactions = [
            {
                'libelle': 'REG.RECETTE OURA',
                'libelle_complet': 'REG.RECETTE OURA',
                'montant': -96.10,
                'date': '01/11/2025'
            },
            {
                'libelle': 'SNCF-VOYAGEURS',
                'libelle_complet': 'SNCF-VOYAGEURS',
                'montant': -76.70,
                'date': '02/11/2025'
            },
            {
                'libelle': 'EDF clients particuliers',
                'libelle_complet': 'EDF clients particuliers',
                'montant': -117.14,
                'date': '05/11/2025'
            },
            {
                'libelle': 'ENGIE',
                'libelle_complet': 'ENGIE',
                'montant': -124.05,
                'date': '04/11/2025'
            }
        ]

        # Agréger
        familles = aggregator.aggregate_by_family(test_transactions)

        print(f"\n{len(familles)} famille(s) detectee(s)")

        success = True
        for nom, data in familles.items():
            print(f"\nFamille: {nom}")
            print(f"  Total: {data['total']:.2f} EUR")
            print(f"  Budget: {data['budget']:.2f} EUR")
            print(f"  Statut: {data['statut']}")
            print(f"  Transactions: {data['nb_transactions']}")

            # Vérifier que les totaux sont corrects
            if nom == "Transports Personnel":
                expected = 96.10 + 76.70
                if abs(data['total'] - expected) > 0.01:
                    print(f"  [X] Total incorrect! Attendu {expected:.2f}, obtenu {data['total']:.2f}")
                    success = False

            if nom == "Energie Maison":
                expected = 117.14 + 124.05
                if abs(data['total'] - expected) > 0.01:
                    print(f"  [X] Total incorrect! Attendu {expected:.2f}, obtenu {data['total']:.2f}")
                    success = False

        # Tester les alertes
        alertes = aggregator.get_alerts(familles)
        print(f"\n{len(alertes)} alerte(s) budgetaire(s)")

        for alert in alertes:
            print(f"  - {alert['message']}")

        print(f"\n{'[OK] Test reussi!' if success else '[X] Test echoue!'}")
        return success

    except Exception as e:
        print(f"[ERREUR] {e}")
        import traceback
        traceback.print_exc()
        return False


def test_pattern_learner():
    """Test du pattern learner"""
    print("\n" + "=" * 80)
    print("TEST 4 : PATTERN LEARNER (Basique)")
    print("=" * 80)

    try:
        from pattern_learner import RecurringPatternLearner

        config = get_config()
        learner = RecurringPatternLearner(config)

        # Vérifier que les fichiers sont créés
        suggestions_file = learner.suggestions_file
        blacklist_file = learner.blacklist_file

        print(f"\nFichier suggestions: {suggestions_file}")
        print(f"  Existe: {suggestions_file.exists()}")

        print(f"\nFichier blacklist: {blacklist_file}")
        print(f"  Existe: {blacklist_file.exists()}")

        # Test de normalisation
        test_libelle = "  Test LibellE  "
        normalized = learner._normalize_libelle(test_libelle)
        expected = "TEST LIBELLE"

        print(f"\nTest normalisation:")
        print(f"  Input: '{test_libelle}'")
        print(f"  Output: '{normalized}'")
        print(f"  Expected: '{expected}'")

        success = normalized == expected
        print(f"\n{'[OK] Test reussi!' if success else '[X] Test echoue!'}")
        return success

    except Exception as e:
        print(f"[ERREUR] {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Lance tous les tests"""
    print("\n" + "=" * 80)
    print("TESTS COMPLETS DU SYSTEME AMELIORE")
    print("=" * 80)

    results = {
        'Libelles multiples': test_multi_libelles(),
        'Tolerances flexibles': test_tolerance_flexible(),
        'Agregateur familles': test_family_aggregator(),
        'Pattern learner': test_pattern_learner()
    }

    print("\n" + "=" * 80)
    print("RESUME DES TESTS")
    print("=" * 80)

    for test_name, success in results.items():
        status = "[OK] PASS" if success else "[X] FAIL"
        print(f"{status} - {test_name}")

    total_success = sum(1 for s in results.values() if s)
    total_tests = len(results)

    print(f"\nScore final: {total_success}/{total_tests} tests reussis")

    if total_success == total_tests:
        print("\n[OK] TOUS LES TESTS SONT PASSES!")
        return 0
    else:
        print(f"\n[X] {total_tests - total_success} test(s) echoue(s)")
        return 1


if __name__ == '__main__':
    sys.exit(main())
