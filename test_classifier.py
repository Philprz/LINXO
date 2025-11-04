#!/usr/bin/env python3
"""Test du classificateur intelligent."""

import sys
from pathlib import Path

# Ajouter le chemin du module linxo_agent
sys.path.insert(0, str(Path(__file__).parent / "linxo_agent"))

from smart_classifier import create_classifier


def test_classifier():
    """Test basique du classificateur."""
    print("="*80)
    print("TEST DU CLASSIFICATEUR INTELLIGENT")
    print("="*80)

    # Créer le classificateur
    print("\n[1/3] Initialisation du classificateur...")
    classifier = create_classifier()

    # Statistiques
    stats = classifier.get_statistics()
    print(f"\n[2/3] Statistiques:")
    print(f"  - Exemples d'entrainement: {stats['training_examples']}")
    print(f"  - Corrections utilisateur: {stats['user_corrections']}")
    print(f"  - Modele ML entraine: {'Oui' if stats['ml_model_trained'] else 'Non'}")
    print(f"  - Scikit-learn: {'Oui' if stats['sklearn_available'] else 'Non'}")

    # Tests de classification
    print(f"\n[3/3] Tests de classification:")

    tests = [
        ("CARREFOUR EXPRESS PARIS", 0.0),
        ("LECLERC SUPERMARCHE", 0.0),
        ("STATION SERVICE TOTAL", 0.0),
        ("PHARMACIE CENTRALE", 0.0),
        ("SPOTIFY PREMIUM", 9.99),
        ("NETFLIX FRANCE", 13.49),
        ("EDF ELECTRICITE", 0.0),
        ("LOYER APPARTEMENT", 0.0),
        ("ZARA PARIS", 0.0),
        ("SNCF PARIS LYON", 0.0),
    ]

    print("\n{:<35} | {:<20} | {}".format("Description", "Catégorie", "Confiance"))
    print("-" * 80)

    for description, montant in tests:
        category, confidence = classifier.classify(description, montant)
        confidence_pct = f"{confidence*100:.0f}%"
        print(f"{description:<35} | {category:<20} | {confidence_pct}")

    # Test d'ajout d'exemple
    print(f"\n[TEST] Ajout d'un exemple d'apprentissage...")
    classifier.add_training_example(
        "MCDONALDS PARIS GARE",
        "Alimentation",
        15.50
    )
    print(f"[OK] Exemple ajoute")

    # Re-tester après ajout
    category, confidence = classifier.classify("MCDONALDS PARIS CENTRE", 12.0)
    print(f"\nTest apres apprentissage:")
    print(f"  Description: MCDONALDS PARIS CENTRE")
    print(f"  Categorie: {category} (confiance: {confidence*100:.0f}%)")

    print("\n" + "="*80)
    print("Test termine avec succes !")
    print("="*80)

    return True


if __name__ == "__main__":
    try:
        success = test_classifier()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n[ERREUR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
