#!/usr/bin/env python3
"""
Outil d'entraînement et de correction du classificateur intelligent.

Permet de :
- Corriger manuellement des classifications
- Entraîner le modèle avec de nouvelles données
- Voir les statistiques du classificateur
- Suggérer des améliorations pour les transactions
"""

import sys
from pathlib import Path

# Ajouter le chemin du module linxo_agent
sys.path.insert(0, str(Path(__file__).parent / "linxo_agent"))

from smart_classifier import create_classifier
from analyzer import lire_csv_linxo
from config import get_config


def afficher_menu():
    """Affiche le menu principal."""
    print("\n" + "="*80)
    print("OUTIL D'ENTRAINEMENT DU CLASSIFICATEUR INTELLIGENT")
    print("="*80)
    print("\n1. Voir les statistiques du classificateur")
    print("2. Entraîner avec le dernier CSV")
    print("3. Corriger des classifications")
    print("4. Suggérer des améliorations")
    print("5. Ajouter un exemple d'entraînement manuel")
    print("0. Quitter")
    print()


def afficher_statistiques(classifier):
    """Affiche les statistiques du classificateur."""
    stats = classifier.get_statistics()

    print("\n" + "="*80)
    print("STATISTIQUES DU CLASSIFICATEUR")
    print("="*80)
    print(f"\nExemples d'entraînement : {stats['training_examples']}")
    print(f"Corrections utilisateur : {stats['user_corrections']}")
    print(f"Modèle ML entraîné      : {'Oui' if stats['ml_model_trained'] else 'Non'}")
    print(f"Scikit-learn disponible : {'Oui' if stats['sklearn_available'] else 'Non'}")

    if stats['categories']:
        print(f"\nCatégories reconnues ({len(stats['categories'])}):")
        for i, cat in enumerate(sorted(stats['categories']), 1):
            print(f"  {i:2}. {cat}")


def entrainer_avec_csv(classifier):
    """Entraîne le classificateur avec les transactions du dernier CSV."""
    print("\n[1/2] Lecture du dernier CSV...")
    config = get_config()
    csv_path = config.get_latest_csv_path()

    if not csv_path or not csv_path.exists():
        print("[ERREUR] Aucun fichier CSV trouvé")
        return

    print(f"CSV: {csv_path}")

    transactions, _ = lire_csv_linxo(csv_path)

    if not transactions:
        print("[ERREUR] Aucune transaction trouvée")
        return

    print(f"\n[2/2] Extraction des exemples d'entraînement...")

    # Compter les transactions avec catégorie
    transactions_valides = [
        t for t in transactions
        if t.get('categorie') and
        t['categorie'] not in ['Non classé', 'Non classe', 'Autres', '']
    ]

    if not transactions_valides:
        print("[ERREUR] Aucune transaction avec catégorie valide")
        return

    print(f"Trouvé {len(transactions_valides)} transactions avec catégorie")

    # Demander confirmation
    reponse = input(f"\nAjouter ces {len(transactions_valides)} exemples ? (o/N): ")
    if reponse.lower() != 'o':
        print("Annulé")
        return

    # Ajouter les exemples
    ajouts = 0
    for trans in transactions_valides:
        description = trans.get('libelle_complet', trans.get('libelle', ''))
        categorie = trans['categorie']
        montant = abs(trans.get('montant', 0.0))

        if description and categorie:
            classifier.add_training_example(description, categorie, montant)
            ajouts += 1

    print(f"\n[OK] {ajouts} exemples ajoutés avec succès !")
    print("[INFO] Le modèle sera réentraîné automatiquement")


def corriger_classifications(classifier):
    """Interface pour corriger des classifications."""
    print("\n[1/2] Lecture du dernier CSV...")
    config = get_config()
    csv_path = config.get_latest_csv_path()

    if not csv_path or not csv_path.exists():
        print("[ERREUR] Aucun fichier CSV trouvé")
        return

    transactions, _ = lire_csv_linxo(csv_path)

    if not transactions:
        print("[ERREUR] Aucune transaction trouvée")
        return

    # Filtrer les transactions sans catégorie ou avec catégorie générique
    transactions_a_classifier = [
        t for t in transactions
        if not t.get('categorie') or
        t.get('categorie', '') in ['Non classé', 'Non classe', 'Autres', '']
    ]

    if not transactions_a_classifier:
        print("\n[OK] Toutes les transactions ont déjà une catégorie !")
        return

    print(f"\n[2/2] {len(transactions_a_classifier)} transactions sans catégorie trouvées\n")

    corrections = 0
    for i, trans in enumerate(transactions_a_classifier[:20], 1):  # Limiter à 20
        description = trans.get('libelle_complet', trans.get('libelle', ''))
        montant = abs(trans.get('montant', 0.0))

        # Obtenir une suggestion
        suggestion, confidence = classifier.classify(description, montant, None)

        print(f"\n--- Transaction {i}/{min(20, len(transactions_a_classifier))} ---")
        print(f"Description : {description}")
        print(f"Montant     : {montant:.2f} €")
        print(f"Suggestion  : {suggestion} (confiance: {confidence*100:.0f}%)")
        print("\nOptions:")
        print("  [Entrée]  Accepter la suggestion")
        print("  [texte]   Entrer une catégorie différente")
        print("  [skip]    Passer")
        print("  [quit]    Terminer")

        reponse = input("\nVotre choix: ").strip()

        if reponse.lower() == 'quit':
            break
        elif reponse.lower() == 'skip':
            continue
        elif reponse == '':
            # Accepter la suggestion
            classifier.add_training_example(description, suggestion, montant)
            corrections += 1
            print(f"[OK] Catégorie '{suggestion}' acceptée")
        else:
            # Catégorie personnalisée
            classifier.record_correction(
                description,
                trans.get('categorie', 'Non classé'),
                reponse,
                montant
            )
            corrections += 1
            print(f"[OK] Catégorie '{reponse}' enregistrée")

    if corrections > 0:
        print(f"\n[SUCCESS] {corrections} corrections enregistrées !")


def suggerer_ameliorations(classifier):
    """Suggère des améliorations pour les classifications existantes."""
    print("\n[1/2] Lecture du dernier CSV...")
    config = get_config()
    csv_path = config.get_latest_csv_path()

    if not csv_path or not csv_path.exists():
        print("[ERREUR] Aucun fichier CSV trouvé")
        return

    transactions, _ = lire_csv_linxo(csv_path)

    if not transactions:
        print("[ERREUR] Aucune transaction trouvée")
        return

    print(f"\n[2/2] Analyse des classifications...")
    suggestions = classifier.suggest_improvements(transactions)

    if not suggestions:
        print("\n[OK] Aucune amélioration suggérée !")
        return

    print(f"\n{len(suggestions)} améliorations suggérées:\n")

    for i, sugg in enumerate(suggestions[:10], 1):  # Limiter à 10
        trans = sugg['transaction']
        print(f"{i}. {trans.get('libelle_complet', trans.get('libelle', ''))}")
        print(f"   Actuel  : {sugg['old_category']}")
        print(f"   Suggéré : {sugg['suggested_category']} ({sugg['confidence']*100:.0f}%)")
        print()


def ajouter_exemple_manuel(classifier):
    """Ajoute un exemple d'entraînement manuellement."""
    print("\n" + "="*80)
    print("AJOUT D'UN EXEMPLE MANUEL")
    print("="*80)

    description = input("\nDescription de la transaction: ").strip()
    if not description:
        print("[ERREUR] Description requise")
        return

    categorie = input("Catégorie: ").strip()
    if not categorie:
        print("[ERREUR] Catégorie requise")
        return

    montant_str = input("Montant (optionnel, défaut=0): ").strip()
    montant = float(montant_str) if montant_str else 0.0

    classifier.add_training_example(description, categorie, montant)
    print(f"\n[OK] Exemple ajouté: '{description}' → {categorie}")


def main():
    """Fonction principale."""
    # Initialiser le classificateur
    try:
        classifier = create_classifier()
    except Exception as e:  # pylint: disable=broad-except
        print(f"[ERREUR] Impossible d'initialiser le classificateur: {e}")
        return 1

    while True:
        afficher_menu()
        choix = input("Votre choix: ").strip()

        if choix == '0':
            print("\nAu revoir !")
            break
        elif choix == '1':
            afficher_statistiques(classifier)
        elif choix == '2':
            entrainer_avec_csv(classifier)
        elif choix == '3':
            corriger_classifications(classifier)
        elif choix == '4':
            suggerer_ameliorations(classifier)
        elif choix == '5':
            ajouter_exemple_manuel(classifier)
        else:
            print("\n[ERREUR] Choix invalide")

        input("\nAppuyez sur Entrée pour continuer...")

    return 0


if __name__ == "__main__":
    sys.exit(main())
