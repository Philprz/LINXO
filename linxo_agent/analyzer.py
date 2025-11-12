#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module d'analyse des dépenses Linxo
Version 2.0 - Refactorisé et simplifié avec configuration unifiée
"""

import csv
import re
import calendar
from datetime import datetime
from pathlib import Path
import sys

# Import du module de configuration unifié
try:
    from config import get_config
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent))
    from config import get_config

# Import du classificateur intelligent (optionnel)
try:
    from smart_classifier import create_classifier
    SMART_CLASSIFIER_AVAILABLE = True
except ImportError:
    SMART_CLASSIFIER_AVAILABLE = False
    print("[INFO] Classificateur ML non disponible, mode standard actif")


# Patterns d'exclusion
EXCLUSIONS = {
    'releves_differes': [
        r'RELEVE\s+DIFFERE.*CARTE\s+\d{4}\*+\d{4}',
        r'CARTE\s+\d{4}\*+\d{4}.*RELEVE',
        r'RELEVE.*DIFFERE',
    ],
    'virements_internes': [
        r'VIREMENT\s+(INTERNE|ENTRE\s+COMPTES)',
        r'VIREMENT\s+DE\s+COMPTE\s+A\s+COMPTE',
        r'TRANSFERT\s+(INTERNE|ENTRE\s+COMPTES)',
        r'VIR\.PERMANENT.*INTERNE',
        r'VIR\s+SEPA.*INTERNE',
        r'VIR\s+INST.*INTERNE',
        r'VIREMENT.*INTERNE',
    ],
    'preautorisation_carburant': [
        # Détection des préautorisations carburant (montants ronds typiques)
        # Auchan, Carrefour, Leclerc, Intermarché, etc.
        (r'AUCHAN', [150.0, 120.0]),
        (r'CARREFOUR', [150.0, 120.0]),
        (r'LECLERC', [150.0, 120.0]),
        (r'INTERMARCHE', [150.0, 120.0]),
        (r'SUPER\s*U', [150.0, 120.0]),
        (r'TOTAL', [150.0, 120.0]),
        (r'SHELL', [150.0, 120.0]),
        (r'ESSO', [150.0, 120.0]),
        (r'BP\s', [150.0, 120.0]),
    ],
    'categories_exclues': [
        'Prél. carte débit différé',
        'Prél. carte debit differe',
        'Virements internes',
    ],
    'marchands_internes': [
        r'AMAZON\s+PAYMENTS',
    ],
}

# Exceptions pour les dépenses récurrentes qui doivent rester variables
EXCEPTIONS_VARIABLES = [
    'OPENAI',
    'CLAUDE',
    'CHATGPT',
    'BITSTACK',
]


def doit_exclure_transaction(libelle, categorie="", notes="", montant=0.0):
    """
    Vérifie si une transaction doit être exclue de l'analyse

    Args:
        libelle: Libellé de la transaction
        categorie: Catégorie de la transaction
        notes: Notes de la transaction
        montant: Montant de la transaction (pour détecter préautorisations)

    Returns:
        tuple: (bool, str) - (doit_exclure, raison)
    """
    libelle_upper = libelle.upper()
    categorie_upper = categorie.upper()
    notes_upper = notes.upper() if notes else ""

    # Vérifier la catégorie directement
    for cat_exclue in EXCLUSIONS['categories_exclues']:
        if cat_exclue.upper() in categorie_upper:
            return True, f"Categorie exclue: {cat_exclue}"

    # Vérifier les relevés différés
    for pattern in EXCLUSIONS['releves_differes']:
        if re.search(pattern, libelle_upper, re.IGNORECASE):
            return True, "Releve differe (deja comptabilise)"

    # Vérifier les virements internes par catégorie
    if "VIREMENT" in categorie_upper and "INTERNE" in categorie_upper:
        return True, "Virement interne (transfert de compte)"

    # Vérifier les virements internes par libellé
    for pattern in EXCLUSIONS['virements_internes']:
        if re.search(pattern, libelle_upper, re.IGNORECASE):
            return True, "Virement interne (transfert de compte)"

    # Vérifier les virements internes dans les notes
    if "INTERNE" in notes_upper and ("VIR" in notes_upper or "VIREMENT" in notes_upper):
        return True, "Virement interne (detecte dans notes)"

    # Vérifier les préautorisations carburant
    montant_abs = abs(montant)
    for pattern, montants_suspects in EXCLUSIONS['preautorisation_carburant']:
        if re.search(pattern, libelle_upper, re.IGNORECASE):
            # Si le montant correspond à un montant de préautorisation typique
            for montant_preauth in montants_suspects:
                if abs(montant_abs - montant_preauth) < 0.01:  # Tolérance de 1 centime
                    return True, f"Preautorisation carburant ({montant_preauth}E)"

    # Vérifier les marchands à exclure (dépenses internes)
    for pattern in EXCLUSIONS['marchands_internes']:
        if re.search(pattern, libelle_upper, re.IGNORECASE):
            return True, "Transaction interne (marchand exclu)"

    return False, None


def est_depense_recurrente(transaction, depenses_fixes):
    """
    Détermine si une transaction est une dépense récurrente

    Args:
        transaction: Transaction à vérifier
        depenses_fixes: Liste des dépenses fixes de référence

    Returns:
        tuple: (bool, dict ou None) - (est_recurrente, depense_match)
    """
    libelle = transaction.get('libelle_complet', transaction.get('libelle', ''))
    libelle_upper = libelle.upper()

    # Vérifier d'abord les exceptions (dépenses qui doivent rester variables)
    for exception in EXCEPTIONS_VARIABLES:
        if exception in libelle_upper:
            return False, None

    # RÈGLE SPÉCIALE: Exclure les virements avec mots-clés ponctuels
    mots_cles_ponctuels = ['REMBOURSEMENT', 'REMBOURSE', 'AVANCE', 'PRET']
    if 'VIR' in libelle_upper or 'VIREMENT' in libelle_upper:
        for mot_cle in mots_cles_ponctuels:
            if mot_cle in libelle_upper:
                # C'est un virement ponctuel (remboursement, avance, etc.)
                return False, None

    # Méthode 1: Matching avec le fichier depenses_recurrentes.json
    for depense_fixe in depenses_fixes:
        # Support de libellés multiples: string OU array
        pattern_libelle_raw = depense_fixe.get('libelle', '')
        if isinstance(pattern_libelle_raw, str):
            patterns_libelle = [pattern_libelle_raw] if pattern_libelle_raw else []
        else:
            patterns_libelle = pattern_libelle_raw  # Déjà une liste

        identifiant = depense_fixe.get('identifiant', '')
        montant_reference = depense_fixe.get('montant', 0)
        # Tolérance personnalisable (défaut 5%)
        montant_tolerance = depense_fixe.get('montant_tolerance', 0.05)

        # Essayer chaque pattern de libellé
        for pattern_libelle_str in patterns_libelle:
            pattern_libelle = pattern_libelle_str.upper()

            # Si le pattern est présent dans le libellé de la transaction
            if pattern_libelle and pattern_libelle in libelle_upper:
                # L'identifiant n'est plus utilisé pour le matching, seulement pour l'affichage
                # Vérifier le montant si un montant de référence est défini
                if montant_reference > 0:
                    montant_transaction = abs(transaction.get('montant', 0))
                    # Utiliser la tolérance personnalisée
                    if abs(montant_transaction - montant_reference) / montant_reference <= montant_tolerance:
                        # Le libellé correspond et le montant est dans la tolérance
                        return True, {
                            'nom': depense_fixe.get('identifiant', pattern_libelle_str) if identifiant else pattern_libelle_str,
                            'categorie': depense_fixe.get('categorie', 'Non classe')
                        }
                else:
                    # Pas de montant de référence, le libellé seul suffit
                    return True, {
                        'nom': depense_fixe.get('identifiant', pattern_libelle_str) if identifiant else pattern_libelle_str,
                        'categorie': depense_fixe.get('categorie', 'Non classe')
                    }

    # Méthode 2: Si le label contient 'Récurrent' (fallback)
    labels = transaction.get('labels', '')
    if labels and 'Récurrent' in labels:
        return True, {
            'nom': 'Depense recurrente (label)',
            'categorie': transaction.get('categorie', 'Non classe')
        }

    return False, None


def lire_csv_linxo(csv_path):
    """
    Lit le fichier CSV exporté de Linxo avec filtrage des exclusions

    Args:
        csv_path: Chemin vers le fichier CSV

    Returns:
        tuple: (transactions_valides, transactions_exclues)
    """
    transactions = []
    exclus = []

    print(f"\n[ANALYSE] Lecture du fichier CSV: {csv_path}")

    try:
        # Détecter l'encodage du fichier
        encodings_to_try = ['utf-8', 'utf-16', 'utf-16-le', 'utf-16-be', 'latin-1', 'cp1252']
        detected_encoding = None

        for encoding in encodings_to_try:
            try:
                with open(csv_path, 'r', encoding=encoding) as f:
                    f.read(1024)  # Essayer de lire
                    detected_encoding = encoding
                    break
            except (UnicodeDecodeError, UnicodeError):
                continue

        if not detected_encoding:
            print("[ERREUR] Impossible de detecter l'encodage du fichier CSV")
            return [], []

        print(f"[INFO] Encodage detecte: {detected_encoding}")

        with open(csv_path, 'r', encoding=detected_encoding) as f:
            # Détecter le délimiteur
            sample = f.read(1024)
            f.seek(0)

            delimiter = '\t' if '\t' in sample else ','
            if ';' in sample:
                delimiter = ';'

            print(f"[INFO] Delimiteur detecte: {repr(delimiter)}")

            reader = csv.DictReader(f, delimiter=delimiter)

            for row in reader:
                date_str = row.get('Date', '')
                libelle = row.get('Libellé', row.get('Libelle', ''))
                notes = row.get('Notes', '')
                montant_str = row.get('Montant', '0')
                categorie = row.get('Catégorie', row.get('Categorie', ''))
                compte = row.get('Nom du compte', '')
                labels = row.get('Labels', '')

                # Nettoyer le montant
                montant_str = montant_str.replace(',', '.').replace(' ', '').replace('€', '').replace('E', '')
                try:
                    montant = float(montant_str)
                except:
                    montant = 0.0

                # Parser la date
                try:
                    date = datetime.strptime(date_str, '%d/%m/%Y')
                except:
                    date = None

                libelle_complet = f"{libelle} {notes}".strip()

                # Vérifier si la transaction doit être exclue
                doit_exclure, raison = doit_exclure_transaction(
                    libelle_complet, categorie, notes, montant
                )

                transaction = {
                    'date': date,
                    'date_str': date_str,
                    'libelle': libelle,
                    'libelle_complet': libelle_complet,
                    'montant': montant,
                    'categorie': categorie,
                    'compte': compte,
                    'labels': labels,
                    'notes': notes
                }

                if doit_exclure:
                    transaction['raison_exclusion'] = raison
                    exclus.append(transaction)
                else:
                    transactions.append(transaction)

        print(f"[OK] {len(transactions)} transactions valides (+ {len(exclus)} exclues)")
        return transactions, exclus

    except Exception as e:
        print(f"[ERREUR] Erreur lecture CSV: {e}")
        import traceback
        traceback.print_exc()
        return [], []


def analyser_transactions(transactions, use_ml=True, enable_learning=True, enable_familles=True):
    """
    Analyse les transactions et les classe

    Args:
        transactions: Liste des transactions valides
        use_ml: Utiliser le classificateur ML si disponible (défaut: True)

    Returns:
        dict: Résultats de l'analyse
    """
    config = get_config()
    depenses_fixes_ref = config.depenses_data.get('depenses_fixes', [])
    depenses_recurrentes = depenses_fixes_ref
    all_transactions = transactions

    depenses_fixes = []
    depenses_variables = []

    total_fixes = 0
    total_variables = 0

    # Initialiser le classificateur ML si disponible et demandé
    classifier = None
    ml_classifications = 0
    if use_ml and SMART_CLASSIFIER_AVAILABLE:
        try:
            classifier = create_classifier()
            print(f"[ML] Classificateur intelligent activé")
            stats = classifier.get_statistics()
            if stats['training_examples'] > 0:
                print(f"[ML] {stats['training_examples']} exemples d'apprentissage")
        except Exception as e:  # pylint: disable=broad-except
            print(f"[WARNING] Erreur initialisation classificateur: {e}")

    print("\n[ANALYSE] Classification des transactions...")

    for transaction in transactions:
        montant = transaction['montant']

        # Ignorer les revenus (montants positifs)
        if montant >= 0:
            continue

        # Améliorer la catégorie avec le classificateur ML si disponible
        if classifier:
            current_category = transaction.get('categorie', '')
            # Classifier si catégorie vague ou manquante
            if not current_category or current_category in ['Non classé', 'Non classe', 'Autres']:
                description = transaction.get('libelle_complet', transaction.get('libelle', ''))
                new_category, confidence = classifier.classify(
                    description,
                    abs(montant),
                    existing_category=None
                )
                if confidence >= 0.5:  # Confiance minimum
                    transaction['categorie'] = new_category
                    transaction['ml_confidence'] = confidence
                    ml_classifications += 1

        # Vérifier si c'est une dépense récurrente
        est_recurrente, depense_match = est_depense_recurrente(transaction, depenses_fixes_ref)

        if est_recurrente:
            transaction['depense_recurrente'] = depense_match['nom']
            transaction['categorie_fixe'] = depense_match['categorie']
            depenses_fixes.append(transaction)
            total_fixes += abs(montant)
        else:
            depenses_variables.append(transaction)
            total_variables += abs(montant)

    print(f"[OK] Depenses fixes:     {len(depenses_fixes):3} transactions | {total_fixes:10.2f}E")
    print(f"[OK] Depenses variables: {len(depenses_variables):3} transactions | {total_variables:10.2f}E")
    if ml_classifications > 0:
        print(f"[ML] {ml_classifications} transactions améliorées par IA")

    # Lancer la détection automatique de patterns (Phase 2)
    if enable_learning:
        try:
            from pattern_learner import RecurringPatternLearner
            learner = RecurringPatternLearner(config)

            # Détecter nouvelles dépenses récurrentes
            new_recurring = learner.detect_new_recurring(all_transactions, months_to_analyze=6, min_occurrences=3)

            # Détecter variantes de libellés
            libelle_variants = learner.detect_libelle_variants(depenses_recurrentes, all_transactions, months_to_analyze=6)

            # Sauvegarder les suggestions (sera affiché dans le rapport)
            if new_recurring or libelle_variants:
                for suggestion in new_recurring:
                    learner.add_suggestion(suggestion)
                for suggestion in libelle_variants:
                    learner.add_suggestion(suggestion)

                print(f"[PATTERN LEARNER] {len(new_recurring)} nouvelles depenses recurrentes detectees")
                print(f"[PATTERN LEARNER] {len(libelle_variants)} variantes de libelles detectees")
        except Exception as e:
            print(f"[WARN] Erreur pattern learner: {e}")

    # Agréger les dépenses par famille (Phase 3)
    familles_aggregees = {}
    famille_alerts = []
    if enable_familles:
        try:
            from family_aggregator import ExpenseFamilyAggregator
            aggregator = ExpenseFamilyAggregator(config)

            # Agréger les transactions par famille
            familles_aggregees = aggregator.aggregate_by_family(depenses_fixes)

            # Obtenir les alertes
            famille_alerts = aggregator.get_alerts(familles_aggregees)

            # Afficher le résumé
            if familles_aggregees:
                print("\n" + aggregator.get_family_summary(familles_aggregees))

            if famille_alerts:
                print("\n[ALERTES FAMILLES]")
                for alert in famille_alerts:
                    print(f"  - {alert['message']}")
        except Exception as e:
            print(f"[WARN] Erreur family aggregator: {e}")

    return {
        'depenses_fixes': depenses_fixes,
        'depenses_variables': depenses_variables,
        'total_fixes': total_fixes,
        'total_variables': total_variables,
        'total': total_fixes + total_variables,
        'familles_aggregees': familles_aggregees,
        'famille_alerts': famille_alerts
    }


def generer_conseil_budget(total_depenses, budget_max):
    """
    Génère un conseil budget intelligent basé sur la situation

    Args:
        total_depenses: Total des dépenses variables
        budget_max: Budget maximum alloué

    Returns:
        str: Conseil formaté
    """
    now = datetime.now()
    jour_actuel = now.day
    dernier_jour = calendar.monthrange(now.year, now.month)[1]
    jours_restants = dernier_jour - jour_actuel

    reste = budget_max - total_depenses
    pourcentage = (total_depenses / budget_max * 100) if budget_max > 0 else 0
    budget_jour = reste / jours_restants if jours_restants > 0 else 0

    # Calcul de l'avancement théorique
    avancement_mois = (jour_actuel / dernier_jour * 100)
    depense_theorique = budget_max * (jour_actuel / dernier_jour)
    ecart = depense_theorique - total_depenses

    conseils = []

    # Déterminer le statut
    if reste < 0:
        # Budget dépassé
        depassement = abs(reste)
        conseils.append(f"ALERTE BUDGET DEPASSE DE {depassement:.2f}E !")
        conseils.append(f"Vous avez depense {pourcentage:.0f}% de votre budget.")
        conseils.append(f"Il reste {jours_restants} jours dans le mois.")
        conseils.append("")
        conseils.append("RECOMMANDATION : Limitez au maximum les depenses non essentielles !")

    elif pourcentage >= 80:
        # Attention
        conseils.append(f"Attention au rythme de depenses !")
        conseils.append(f"Vous avez depense {total_depenses:.2f}E sur {budget_max:.2f}E ({pourcentage:.0f}%).")
        conseils.append(f"Nous sommes au jour {jour_actuel}/{dernier_jour} du mois ({avancement_mois:.0f}%).")
        conseils.append("")

        if ecart > 0:
            conseils.append(f"Vous etes en avance de {abs(ecart):.2f}E par rapport au rythme normal.")

        conseils.append(f"CONSEIL : Limitez-vous a {budget_jour:.2f}E/jour pour les {jours_restants} jours restants.")

    else:
        # Budget OK
        conseils.append(f"Budget sous controle !")
        conseils.append(f"Depenses : {total_depenses:.2f}E / {budget_max:.2f}E ({pourcentage:.0f}%).")
        conseils.append(f"Il vous reste {reste:.2f}E pour {jours_restants} jours.")
        conseils.append(f"Vous pouvez depenser environ {budget_jour:.2f}E/jour.")
        conseils.append("")

        if ecart > 50:
            conseils.append(f"Excellent ! Vous etes en retard de {abs(ecart):.2f}E sur le budget prevu.")
            conseils.append("Vous gerez tres bien votre budget !")

    return "\n".join(conseils)


def generer_rapport(analyse, transactions_exclues, budget_max=None):
    """
    Génère un rapport détaillé de l'analyse

    Args:
        analyse: Résultat de l'analyse
        transactions_exclues: Transactions exclues
        budget_max: Budget maximum (optionnel, utilise config par défaut)

    Returns:
        str: Rapport formaté
    """
    config = get_config()

    if budget_max is None:
        budget_max = config.budget_variable

    rapport = []
    rapport.append("=" * 80)
    rapport.append("RAPPORT D'ANALYSE DES DEPENSES LINXO")
    rapport.append("=" * 80)
    rapport.append(f"Date: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    rapport.append("")

    # Section exclusions
    if transactions_exclues:
        rapport.append("TRANSACTIONS EXCLUES")
        rapport.append("-" * 80)
        total_exclu = 0
        for trans in transactions_exclues[:20]:  # Limiter à 20 pour la lisibilité
            rapport.append(f"  {trans['libelle_complet'][:50]:50} | {trans['montant']:8.2f}E | {trans['raison_exclusion']}")
            total_exclu += abs(trans['montant'])
        if len(transactions_exclues) > 20:
            rapport.append(f"  ... et {len(transactions_exclues) - 20} autres")
        rapport.append(f"\nTOTAL EXCLU: {total_exclu:8.2f}E")
        rapport.append("")

    # Dépenses fixes
    rapport.append("DEPENSES FIXES")
    rapport.append("-" * 80)
    for dep in analyse['depenses_fixes']:
        rapport.append(f"  {dep['libelle'][:50]:50} | {dep['montant']:8.2f}E | {dep['date_str']}")
    rapport.append(f"\nTOTAL FIXES: {analyse['total_fixes']:8.2f}E")
    rapport.append("")

    # Dépenses variables
    rapport.append("DEPENSES VARIABLES")
    rapport.append("-" * 80)
    for dep in analyse['depenses_variables']:
        rapport.append(f"  {dep['libelle'][:50]:50} | {dep['montant']:8.2f}E | {dep['date_str']}")
    rapport.append(f"\nTOTAL VARIABLES: {analyse['total_variables']:8.2f}E")
    rapport.append("")

    # Statut budget
    reste = budget_max - analyse['total_variables']
    pourcentage = (analyse['total_variables'] / budget_max * 100) if budget_max > 0 else 0

    # Déterminer le statut
    now = datetime.now()
    jour_actuel = now.day
    dernier_jour = calendar.monthrange(now.year, now.month)[1]

    if reste < 0:
        emoji = "[ROUGE]"
        statut = "ALERTE - BUDGET DEPASSE"
    elif pourcentage >= 80:
        emoji = "[ORANGE]"
        statut = "ATTENTION"
    else:
        emoji = "[VERT]"
        statut = "OK"

    rapport.append("BUDGET ET STATUT")
    rapport.append("-" * 80)
    rapport.append(f"Statut: {emoji} {statut}")
    rapport.append("")
    rapport.append(f"Budget variables alloue:  {budget_max:10.2f}E")
    rapport.append(f"Depenses variables:       {analyse['total_variables']:10.2f}E")

    if reste >= 0:
        rapport.append(f"Reste disponible:         {reste:10.2f}E")
    else:
        rapport.append(f"DEPASSEMENT:              {abs(reste):10.2f}E")

    rapport.append(f"\nJour {jour_actuel}/{dernier_jour} du mois")
    rapport.append("")

    # Ajouter les conseils budget
    conseil = generer_conseil_budget(analyse['total_variables'], budget_max)
    rapport.append("CONSEIL DE VOTRE AGENT BUDGET")
    rapport.append("-" * 80)
    rapport.append(conseil)
    rapport.append("")

    rapport.append("=" * 80)
    rapport.append(f"TOTAL GENERAL: {analyse['total']:10.2f}E")
    rapport.append("=" * 80)

    return "\n".join(rapport)


def analyser_csv(csv_path=None, budget_max=None):
    """
    Fonction principale d'analyse

    Args:
        csv_path: Chemin vers le fichier CSV (optionnel, utilise le dernier par défaut)
        budget_max: Budget maximum (optionnel, utilise config par défaut)

    Returns:
        dict: Résultats de l'analyse complète
    """
    config = get_config()

    # Utiliser le dernier CSV si non fourni
    if csv_path is None:
        csv_path = config.get_latest_csv()

    if not Path(csv_path).exists():
        print(f"[ERREUR] Fichier CSV introuvable: {csv_path}")
        return None

    # Lire le CSV
    transactions, exclus = lire_csv_linxo(csv_path)

    if not transactions:
        print("[ERREUR] Aucune transaction a analyser")
        return None

    # Analyser
    analyse = analyser_transactions(transactions)

    # Générer le rapport
    rapport = generer_rapport(analyse, exclus, budget_max)

    # Préparer le résultat complet
    if budget_max is None:
        budget_max = config.budget_variable

    reste = budget_max - analyse['total_variables']
    pourcentage = (analyse['total_variables'] / budget_max * 100) if budget_max > 0 else 0

    result = {
        'csv_path': str(csv_path),
        'total_transactions': len(transactions),
        'total_exclus': len(exclus),
        'depenses_fixes': analyse['depenses_fixes'],
        'depenses_variables': analyse['depenses_variables'],
        'total_fixes': analyse['total_fixes'],
        'total_variables': analyse['total_variables'],
        'total': analyse['total'],
        'budget_max': budget_max,
        'reste': reste,
        'pourcentage': pourcentage,
        'rapport': rapport
    }

    return result


# Fonction de test
if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("TEST DU MODULE D'ANALYSE")
    print("=" * 80)

    # Tester l'analyse
    result = analyser_csv()

    if result:
        print("\n" + result['rapport'])
        print("\n[SUCCESS] Analyse terminee!")
    else:
        print("\n[ERREUR] Echec de l'analyse")
