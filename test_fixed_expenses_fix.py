#!/usr/bin/env python3
"""
Script de test pour vérifier la correction de la détection des dépenses fixes
Tests les 3 transactions problématiques : EDF, ENGIE, OURA
"""

import sys
from pathlib import Path

# Ajouter le répertoire linxo_agent au path
sys.path.insert(0, str(Path('.') / 'linxo_agent'))

from analyzer import est_depense_recurrente
from config import get_config

def test_fixed_expenses():
    """Teste les 3 transactions problématiques"""

    # Charger la configuration
    config = get_config()
    depenses_fixes = config.depenses_data.get('depenses_fixes', [])

    print("=" * 80)
    print("TEST DE DÉTECTION DES DÉPENSES FIXES")
    print("=" * 80)
    print()

    # Transactions problématiques d'origine
    transactions_test = [
        {
            'libelle': 'EDF clients particuliers',
            'libelle_complet': 'EDF clients particuliers',
            'montant': -117.14,
            'date': '05/11/2025',
            'test_name': 'EDF (-117.14€)'
        },
        {
            'libelle': 'ENGIE',
            'libelle_complet': 'ENGIE',
            'montant': -124.05,
            'date': '04/11/2025',
            'test_name': 'ENGIE (-124.05€)'
        },
        {
            'libelle': 'REG.RECETTE OURA',
            'libelle_complet': 'REG.RECETTE OURA',
            'montant': -172.80,
            'date': '03/11/2025',
            'test_name': 'REG.RECETTE OURA (-172.80€)'
        }
    ]

    resultats = []

    for transaction in transactions_test:
        test_name = transaction.pop('test_name')
        est_fixe, depense_info = est_depense_recurrente(transaction, depenses_fixes)

        print(f"Transaction: {test_name}")
        print(f"  Libelle complet: {transaction['libelle_complet']}")
        print(f"  Montant: {transaction['montant']} EUR")
        print(f"  Detectee comme fixe: {'[OK] OUI' if est_fixe else '[X] NON'}")

        if est_fixe and depense_info:
            print(f"  Nom identifie: {depense_info.get('nom', 'N/A')}")
            print(f"  Categorie: {depense_info.get('categorie', 'N/A')}")

        print()

        resultats.append({
            'nom': test_name,
            'success': est_fixe
        })

    # Résumé
    print("=" * 80)
    print("RÉSUMÉ DES TESTS")
    print("=" * 80)

    succes = sum(1 for r in resultats if r['success'])
    total = len(resultats)

    for resultat in resultats:
        status = "[OK] PASS" if resultat['success'] else "[X] FAIL"
        print(f"{status} - {resultat['nom']}")

    print()
    print(f"Score: {succes}/{total} tests reussis")

    if succes == total:
        print("\n[OK] TOUS LES TESTS SONT PASSES!")
        return 0
    else:
        print(f"\n[X] {total - succes} test(s) echoue(s)")
        return 1


if __name__ == '__main__':
    sys.exit(test_fixed_expenses())
