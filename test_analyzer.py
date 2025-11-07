#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de test pour l'analyzer et les modifications récentes
"""

import sys
from pathlib import Path

# Ajouter le répertoire du projet au path
sys.path.insert(0, str(Path(__file__).parent))

from linxo_agent.analyzer import doit_exclure_transaction

def test_exclusions():
    """Teste les nouvelles exclusions"""

    print("=" * 80)
    print("TEST DES EXCLUSIONS DE TRANSACTIONS")
    print("=" * 80)

    # Test 1: Transaction Amazon Payments
    print("\n[TEST 1] Transaction Amazon Payments")
    libelle = "AMAZON PAYMENTS LUXEMBOURG"
    exclure, raison = doit_exclure_transaction(libelle)
    print(f"  Libellé: {libelle}")
    print(f"  Exclu: {exclure}")
    print(f"  Raison: {raison}")
    assert exclure == True, "Amazon Payments devrait être exclu"
    print("  [OK] Test reussi")

    # Test 2: Transaction normale (non exclue)
    print("\n[TEST 2] Transaction normale")
    libelle = "CARREFOUR MARKET"
    exclure, raison = doit_exclure_transaction(libelle)
    print(f"  Libellé: {libelle}")
    print(f"  Exclu: {exclure}")
    print(f"  Raison: {raison}")
    assert exclure == False, "Carrefour Market ne devrait pas être exclu"
    print("  [OK] Test reussi")

    # Test 3: Virement interne
    print("\n[TEST 3] Virement interne")
    libelle = "VIREMENT INTERNE"
    exclure, raison = doit_exclure_transaction(libelle)
    print(f"  Libellé: {libelle}")
    print(f"  Exclu: {exclure}")
    print(f"  Raison: {raison}")
    assert exclure == True, "Virement interne devrait être exclu"
    print("  [OK] Test reussi")

    # Test 4: Préautorisation carburant
    print("\n[TEST 4] Préautorisation carburant")
    libelle = "TOTAL ENERGY 120,00 CARTE"
    exclure, raison = doit_exclure_transaction(libelle, montant=120.0)
    print(f"  Libellé: {libelle}")
    print(f"  Montant: 120.0")
    print(f"  Exclu: {exclure}")
    print(f"  Raison: {raison}")
    assert exclure == True, "Préautorisation carburant devrait être exclue"
    print("  [OK] Test reussi")

    print("\n" + "=" * 80)
    print("TOUS LES TESTS SONT RÉUSSIS!")
    print("=" * 80)

if __name__ == "__main__":
    try:
        test_exclusions()
    except Exception as e:
        print(f"\n[ERREUR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
