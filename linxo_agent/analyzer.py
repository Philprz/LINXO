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
    ]
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
        pattern_libelle = depense_fixe.get('libelle', '').upper()
        identifiant = depense_fixe.get('identifiant', '').upper()
        montant_reference = depense_fixe.get('montant', 0)

        # Si le pattern est présent dans le libellé de la transaction
        if pattern_libelle and pattern_libelle in libelle_upper:
            # Vérification supplémentaire avec identifiant si fourni ET présent dans le libellé
            if identifiant and identifiant in libelle_upper:
                # Le libellé ET l'identifiant correspondent : c'est un match parfait
                return True, {
                    'nom': depense_fixe.get('libelle', 'Depense fixe'),
                    'categorie': depense_fixe.get('categorie', 'Non classe')
                }

            # Si pas d'identifiant dans le libellé, vérifier le montant pour différencier
            if identifiant and identifiant not in libelle_upper:
                montant_transaction = abs(transaction.get('montant', 0))
                # Tolérance de 5% sur le montant pour gérer les variations
                if montant_reference > 0 and abs(montant_transaction - montant_reference) / montant_reference <= 0.05:
                    # Le libellé correspond et le montant est proche : c'est un match
                    return True, {
                        'nom': depense_fixe.get('libelle', 'Depense fixe'),
                        'categorie': depense_fixe.get('categorie', 'Non classe')
                    }
                # Sinon, continuer la recherche (peut-être une autre règle correspondra mieux)
                continue

            # Si pas d'identifiant défini, le libellé seul suffit
            if not identifiant:
                return True, {
                    'nom': depense_fixe.get('libelle', 'Depense fixe'),
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


def analyser_transactions(transactions):
    """
    Analyse les transactions et les classe

    Args:
        transactions: Liste des transactions valides

    Returns:
        dict: Résultats de l'analyse
    """
    config = get_config()
    depenses_fixes_ref = config.depenses_data.get('depenses_fixes', [])

    depenses_fixes = []
    depenses_variables = []

    total_fixes = 0
    total_variables = 0

    print("\n[ANALYSE] Classification des transactions...")

    for transaction in transactions:
        montant = transaction['montant']

        # Ignorer les revenus (montants positifs)
        if montant >= 0:
            continue

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

    return {
        'depenses_fixes': depenses_fixes,
        'depenses_variables': depenses_variables,
        'total_fixes': total_fixes,
        'total_variables': total_variables,
        'total': total_fixes + total_variables
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

        if ecart < -50:
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
