#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# pylint: disable=invalid-name
"""
Agent Linxo - Analyse des dépenses à partir d'un export CSV
Version 3.0 - RELIABLE - Corrigé selon l'analyse utilisateur d'octobre 2025
"""

import json
import csv
import re
import sys
import os
import io
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import calendar
from pathlib import Path
from difflib import SequenceMatcher
# Détection automatique de l'environnement
def _detect_base_dir():
    """Détecte le répertoire de base selon l'environnement"""
    if sys.platform.startswith('linux'):
        # VPS Linux
        if os.path.exists('/home/linxo/LINXO'):
            return Path('/home/linxo/LINXO')
        if os.path.exists('/home/ubuntu'):
            return Path('/home/ubuntu')
    # Local (Windows ou autre)
    return Path(__file__).parent.parent

_BASE_DIR = _detect_base_dir()
_LINXO_AGENT_DIR = _BASE_DIR / 'linxo_agent' if _BASE_DIR.name != 'linxo_agent' else _BASE_DIR

# Configuration avec chemins dynamiques
CONFIG_FILE = str(_LINXO_AGENT_DIR / 'config_linxo.json')
DEPENSES_FILE = str(_LINXO_AGENT_DIR / 'depenses_recurrentes.json')
CSV_FILE = str(_BASE_DIR / 'data' / 'latest.csv')

# API Secrets selon l'environnement
if sys.platform.startswith('linux') and os.path.exists('/home/linxo/.api_secret_infos'):
    API_SECRETS_FILE = '/home/linxo/.api_secret_infos/api_secrets.json'
elif sys.platform.startswith('linux') and os.path.exists('/home/ubuntu/.api_secret_infos'):
    API_SECRETS_FILE = '/home/ubuntu/.api_secret_infos/api_secrets.json'
else:
    API_SECRETS_FILE = str(_BASE_DIR / 'api_secrets.json')

# Seuils de tolérance
SEUIL_SIMILARITE = 0.6  # 60% de similarité minimum pour matcher
TOLERANCE_MONTANT = 0.05  # 5% de tolérance sur les montants

# Patterns à exclure (relevés différés et virements internes)
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
        r'VIR\.PERMANENT.*INTERNE',  # Matches "VIREMENT PERMANENT ... Interne"
        r'VIR\s+SEPA.*INTERNE',  # Matches "VIR SEPA ... Interne"
        r'VIR\s+INST.*INTERNE',  # Matches "VIR INST ... Interne"
        r'VIREMENT.*INTERNE',  # General catch-all for any virement with "Interne"
    ],
    # NOUVEAU: Catégories à exclure directement
    'categories_exclues': [
        'Prél. carte débit différé',  # Relevés différés de carte
        'Virements internes',  # Virements internes
    ]
}

# NOUVEAU: Exceptions pour les dépenses récurrentes qui doivent rester variables
EXCEPTIONS_VARIABLES = [
    'OPENAI',
    'CLAUDE',
    'CHATGPT',
    'BITSTACK',  # Crypto - variable par nature
]

def charger_api_secrets():
    """Charge les credentials depuis le fichier sécurisé"""
    with open(API_SECRETS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def charger_config():
    """Charge la configuration"""
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def charger_depenses_recurrentes():
    """Charge les dépenses récurrentes"""
    with open(DEPENSES_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def doit_exclure_transaction(libelle, categorie="", notes=""):
    """
    Vérifie si une transaction doit être exclue de l'analyse
    Retourne (True, raison) si à exclure, (False, None) sinon

    VERSION 3.0: Amélioration basée sur l'analyse utilisateur
    """
    libelle_upper = libelle.upper()
    categorie_upper = categorie.upper()
    notes_upper = notes.upper() if notes else ""

    # PRIORITÉ 1: Vérifier la catégorie directement
    for cat_exclue in EXCLUSIONS['categories_exclues']:
        if cat_exclue.upper() in categorie_upper:
            return True, f"Catégorie exclue: {cat_exclue}"

    # PRIORITÉ 2: Vérifier les relevés différés
    for pattern in EXCLUSIONS['releves_differes']:
        if re.search(pattern, libelle_upper, re.IGNORECASE):
            return True, "Relevé différé (déjà comptabilisé)"

    # PRIORITÉ 3: Vérifier les virements internes par catégorie
    if "VIREMENT" in categorie_upper and "INTERNE" in categorie_upper:
        return True, "Virement interne (transfert de compte)"

    # PRIORITÉ 4: Vérifier les virements internes par libellé
    for pattern in EXCLUSIONS['virements_internes']:
        if re.search(pattern, libelle_upper, re.IGNORECASE):
            return True, "Virement interne (transfert de compte)"

    # PRIORITÉ 5: Vérifier les virements internes dans les notes
    if "INTERNE" in notes_upper and ("VIR" in notes_upper or "VIREMENT" in notes_upper):
        return True, "Virement interne (détecté dans notes)"

    return False, None

def est_exception_variable(libelle):
    """
    Vérifie si une transaction doit rester variable même si elle a le label 'Récurrent'
    """
    libelle_upper = libelle.upper()
    for exception in EXCEPTIONS_VARIABLES:
        if exception in libelle_upper:
            return True
    return False

def normaliser_texte(texte):
    """Normalise un texte pour la comparaison"""
    if not texte:
        return ""
    texte = str(texte).upper()
    texte = texte.replace('É', 'E').replace('È', 'E').replace('Ê', 'E')
    texte = texte.replace('À', 'A').replace('Â', 'A')
    texte = texte.replace('Ù', 'U').replace('Û', 'U')
    texte = texte.replace('Ô', 'O').replace('Ö', 'O')
    texte = texte.replace('Ç', 'C')
    texte = re.sub(r'[^\w\s]', ' ', texte)
    texte = re.sub(r'\s+', ' ', texte)
    return texte.strip()

def calculer_similarite(texte1, texte2):
    """Calcule la similarité entre deux textes (0 à 1)"""
    texte1_norm = normaliser_texte(texte1)
    texte2_norm = normaliser_texte(texte2)

    ratio = SequenceMatcher(None, texte1_norm, texte2_norm).ratio()

    if texte2_norm in texte1_norm or texte1_norm in texte2_norm:
        ratio = max(ratio, 0.8)

    return ratio

def montants_similaires(montant1, montant2, tolerance=TOLERANCE_MONTANT):
    """Vérifie si deux montants sont similaires (avec tolérance)"""
    montant1 = abs(float(montant1))
    montant2 = abs(float(montant2))

    tolerance_absolue = 1.0
    tolerance_relative = montant2 * tolerance

    diff = abs(montant1 - montant2)
    return diff <= max(tolerance_absolue, tolerance_relative)

def lire_csv_linxo(fichier_csv):
    """Lit le fichier CSV exporté de Linxo avec filtrage des exclusions"""
    transactions = []
    exclus = []

    # Détecter l'encodage du fichier
    encodings_to_try = ['utf-8-sig', 'utf-16', 'utf-8', 'latin-1', 'cp1252']
    content = None
    used_encoding = None

    for encoding in encodings_to_try:
        try:
            with open(fichier_csv, 'r', encoding=encoding) as f:
                content = f.read()
                used_encoding = encoding
                break
        except (UnicodeDecodeError, UnicodeError):
            continue

    if content is None:
        print(f"❌ Impossible de lire le fichier avec les encodages testés: {encodings_to_try}")
        return [], []

    print(f"✓ Fichier CSV lu avec l'encodage: {used_encoding}")

    try:
        # Détecter le délimiteur
        sample = content[:1024]
        delimiter = '\t' if '\t' in sample else ','
        if ';' in sample:
            delimiter = ';'

        # Lire le CSV depuis le contenu en mémoire
        f = io.StringIO(content)
        reader = csv.DictReader(f, delimiter=delimiter)

        for row in reader:
            date_str = row.get('Date', '')
            libelle = row.get('Libellé', '')
            notes = row.get('Notes', '')
            montant_str = row.get('Montant', '0')
            categorie = row.get('Catégorie', '')
            compte = row.get('Nom du compte', '')
            labels = row.get('Labels', '')

            montant_str = montant_str.replace(',', '.').replace(' ', '').replace('€', '')
            try:
                montant = float(montant_str)
            except (ValueError, TypeError):
                montant = 0.0

            try:
                date = datetime.strptime(date_str, '%d/%m/%Y')
            except (ValueError, TypeError):
                date = None

            libelle_complet = f"{libelle} {notes}".strip()

            # Vérifier si la transaction doit être exclue
            doit_exclure, raison = doit_exclure_transaction(libelle_complet, categorie, notes)

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
                print(f"⊘  EXCLU: {libelle_complet[:50]:50} | {montant:8.2f}€ | {raison}")
            else:
                transactions.append(transaction)

        print(f"\n✅ {len(transactions)} transactions valides (+ {len(exclus)} exclues)")
        return transactions, exclus

    except (FileNotFoundError, PermissionError, OSError) as e:
        print(f"❌ Erreur lecture CSV: {str(e)}")
        return [], []

def identifier_depense_recurrente(transaction, depenses_recurrentes, depenses_deja_utilisees=None):
    """
    Identifie si une transaction correspond à une dépense récurrente
    VERSION 3.0: Utilise le label 'Récurrent' comme indicateur principal
    """
    if depenses_deja_utilisees is None:
        depenses_deja_utilisees = {}

    libelle_transaction = transaction['libelle_complet']
    montant_transaction = abs(transaction['montant'])
    labels = transaction.get('labels', '')

    # NOUVELLE LOGIQUE: Si le label contient 'Récurrent' ET ce n'est pas une exception
    if labels and 'Récurrent' in labels:
        if not est_exception_variable(libelle_transaction):
            # C'est une dépense fixe basée sur le label
            return {
                'libelle': libelle_transaction,
                'commentaire': 'Dépense récurrente (label)',
                'categorie': transaction['categorie'] or 'Non classé',
                'montant': montant_transaction
            }, 0.95, None

    # AMÉLIORATION V3.0: Utiliser l'ancienne méthode de matching UNIQUEMENT pour les dépenses
    # qui sont dans la config ET qui ont un bon score de similarité (>= 0.85)
    # Cela évite les faux positifs comme "CLI. RADIO CHARC" qui match avec "FRAIS BOURSO"
    meilleur_match = None
    meilleur_score = 0

    for i, depense in enumerate(depenses_recurrentes):
        libelle_ref = depense.get('libelle', depense.get('libelle_linxo', ''))
        montant_ref = depense.get('montant', depense.get('montant_attendu', 0))

        score_libelle = calculer_similarite(libelle_transaction, libelle_ref)
        montants_ok = montants_similaires(montant_transaction, montant_ref)

        score_final = score_libelle
        if montants_ok:
            score_final = min(1.0, score_final + 0.3)
        else:
            score_final = score_final * 0.7

        if i in depenses_deja_utilisees:
            score_final = score_final * 0.5

        # SEUIL AUGMENTÉ: Exiger un score >= 0.85 pour éviter les faux positifs
        if score_final > meilleur_score and score_final >= 0.85:
            meilleur_score = score_final
            meilleur_match = (depense, i)

    if meilleur_match:
        return meilleur_match[0], meilleur_score, meilleur_match[1]
    return None, 0, None

def analyser_transactions(transactions, data_depenses):
    """Analyse les transactions et les classe"""
    depenses_recurrentes = data_depenses.get('depenses_fixes',
                                             data_depenses.get('depenses_recurrentes', []))

    depenses_fixes_identifiees = []
    depenses_variables = []
    depenses_deja_utilisees = {}

    total_depenses_fixes = 0
    total_depenses_variables = 0

    print("\n" + "="*80)
    print("🔍 ANALYSE DES TRANSACTIONS (VERSION 3.0 - RELIABLE)")
    print("="*80)

    for transaction in transactions:
        montant = transaction['montant']

        if montant >= 0:
            continue

        depense_match, score, depense_id = identifier_depense_recurrente(
            transaction, depenses_recurrentes, depenses_deja_utilisees
        )

        if depense_match:
            nom_depense = depense_match.get('commentaire',
                depense_match.get('nom', depense_match.get('libelle', 'Inconnu')))
            transaction['depense_recurrente'] = nom_depense
            transaction['categorie_fixe'] = depense_match.get('categorie', 'Non classé')
            transaction['score_match'] = score
            depenses_fixes_identifiees.append(transaction)
            total_depenses_fixes += abs(montant)

            if depense_id is not None:
                depenses_deja_utilisees[depense_id] = depenses_deja_utilisees.get(depense_id, 0) + 1

            print(f"✅ FIXE: {transaction['libelle'][:40]:40} | {montant:8.2f}€ | "
                f"Match: {nom_depense[:30]} ({score:.0%})")

        else:
            depenses_variables.append(transaction)
            total_depenses_variables += abs(montant)

            print(f"💰 VAR:  {transaction['libelle'][:40]:40} | "
                  f"Match: {montant:8.2f}€ | {transaction['categorie'][:20]}")

    print("="*80)
    print("\n📊 RÉSUMÉ:")
    print(f"   Dépenses fixes:     {len(depenses_fixes_identifiees):3} transactions | "
        f"{total_depenses_fixes:10.2f}€")
    print(f"   Dépenses variables: {len(depenses_variables):3} transactions | "
        f"{total_depenses_variables:10.2f}€")
    print(f"   TOTAL DÉPENSES:                              "
        f"{total_depenses_fixes + total_depenses_variables:10.2f}€")

    return {
        'depenses_fixes': depenses_fixes_identifiees,
        'depenses_variables': depenses_variables,
        'total_fixes': total_depenses_fixes,
        'total_variables': total_depenses_variables,
        'total': total_depenses_fixes + total_depenses_variables
    }

def calculer_avancement_mois():
    """Calcule le pourcentage d'avancement dans le mois"""
    maintenant = datetime.now()
    jour_actuel = maintenant.day
    dernier_jour = calendar.monthrange(maintenant.year, maintenant.month)[1]
    pourcentage = (jour_actuel / dernier_jour) * 100
    return pourcentage, jour_actuel, dernier_jour

def determiner_statut_budget(depenses_variables, budget_max):
    """Détermine le statut du budget avec système de feux tricolores"""
    pourcentage_depense = (depenses_variables / budget_max) * 100 if budget_max > 0 else 0
    avancement_mois, jour_actuel, dernier_jour = calculer_avancement_mois()

    budget_theorique = (budget_max * avancement_mois) / 100
    ecart = depenses_variables - budget_theorique
    ecart_pourcentage = (ecart / budget_theorique) * 100 if budget_theorique > 0 else 0

    if depenses_variables > budget_max:
        statut = "🔴 ROUGE - BUDGET DÉPASSÉ"
        emoji = "🔴"
        alerte = True
    elif pourcentage_depense > 90:
        statut = "🟠 ORANGE - ATTENTION"
        emoji = "🟠"
        alerte = False
    elif ecart_pourcentage > 20:
        statut = "🟠 ORANGE - RYTHME ÉLEVÉ"
        emoji = "🟠"
        alerte = False
    else:
        statut = "🟢 VERT - SOUS CONTRÔLE"
        emoji = "🟢"
        alerte = False

    return {
        'statut': statut,
        'emoji': emoji,
        'alerte': alerte,
        'pourcentage_depense': pourcentage_depense,
        'avancement_mois': avancement_mois,
        'jour_actuel': jour_actuel,
        'dernier_jour': dernier_jour,
        'budget_theorique': budget_theorique,
        'ecart': ecart,
        'ecart_pourcentage': ecart_pourcentage
    }

def generer_conseil_budget(statut_info, depenses_variables, budget_max):
    """Génère un conseil budget intelligent basé sur la situation"""
    reste = budget_max - depenses_variables
    jours_restants = statut_info['dernier_jour'] - statut_info['jour_actuel']
    budget_jour = reste / jours_restants if jours_restants > 0 else 0

    conseils = []

    if statut_info['alerte']:
        depassement = depenses_variables - budget_max
        conseils.append(f"⚠️ ALERTE BUDGET DÉPASSÉ DE {depassement:.2f}€ !")
        conseils.append(
            f"Vous avez dépensé {statut_info['pourcentage_depense']:.0f}% "
            f"de votre budget."
        )
        conseils.append(f"Il reste {jours_restants} jours dans le mois.")
        conseils.append("🚨 RECOMMANDATION : Limitez au maximum les dépenses non essentielles !")

    elif statut_info['emoji'] == "🟠":
        conseils.append("⚠️ Attention au rythme de dépenses !")
        conseils.append(
            f"Vous avez dépensé {depenses_variables:.2f}€ sur {budget_max:.2f}€ "
            f"({statut_info['pourcentage_depense']:.0f}%).")
        conseils.append(f"Nous sommes au jour {statut_info['jour_actuel']}/ "
            f"{statut_info['dernier_jour']} du mois ({statut_info['avancement_mois']:.0f}%).")

        if statut_info['ecart'] > 0:
            conseils.append(
                f"Vous êtes en avance de {abs(statut_info['ecart']):.2f}€ "
                f"par rapport au rythme normal.")

        conseils.append(
            f"💡 CONSEIL : Limitez-vous à {budget_jour:.2f}€/jour "
            f"pour les {jours_restants} jours restants.")

    else:
        conseils.append("✅ Budget sous contrôle !")
        conseils.append(f"Dépenses : {depenses_variables:.2f}€ / "
            f"{budget_max:.2f}€ ({statut_info['pourcentage_depense']:.0f}%).")
        conseils.append(f"Il vous reste {reste:.2f}€ pour {jours_restants} jours.")
        conseils.append(f"💡 Vous pouvez dépenser environ {budget_jour:.2f}€/jour.")

        if statut_info['ecart'] < -50:
            conseils.append(
                f"👍 Excellent ! Vous êtes en avance de {abs(statut_info['ecart']):.2f}€ "
                f"sur le budget prévu.")

    return "\n".join(conseils)

def generer_rapport(analyse, data_depenses, transactions_exclues):
    """Génère un rapport détaillé"""
    budget_max = data_depenses.get('totaux', {}).get('budget_variable_max',
                 data_depenses.get('budget', {}).get('depenses_variables_max', 2000))

    rapport = []
    rapport.append("="*80)
    rapport.append("📊 RAPPORT D'ANALYSE DES DÉPENSES LINXO - VERSION 3.0 RELIABLE")
    rapport.append("="*80)
    rapport.append(f"Date d'analyse: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    rapport.append("")

    # Section exclusions
    if transactions_exclues:
        rapport.append("⊘ TRANSACTIONS EXCLUES DE L'ANALYSE")
        rapport.append("-"*80)
        total_exclu = 0
        for trans in transactions_exclues:
            rapport.append(f"   • {trans['libelle_complet'][:50]:50} | "
                f"{trans['montant']:8.2f}€ | {trans['raison_exclusion']}")
            total_exclu += abs(trans['montant'])
        rapport.append(f"\n{'TOTAL EXCLU':50} | {total_exclu:8.2f}€")
        rapport.append("")

    # Dépenses fixes
    rapport.append("🔒 DÉPENSES FIXES IDENTIFIÉES")
    rapport.append("-"*80)

    par_categorie = {}
    for dep in analyse['depenses_fixes']:
        cat = dep['categorie_fixe']
        if cat not in par_categorie:
            par_categorie[cat] = []
        par_categorie[cat].append(dep)

    for categorie in sorted(par_categorie.keys()):
        rapport.append(f"\n📁 {categorie}")
        total_cat = 0
        for dep in par_categorie[categorie]:
            rapport.append(
                f"   • {dep['depense_recurrente']:35} | {dep['montant']:8.2f}€ | "
                f"{dep['date_str']}")
            total_cat += abs(dep['montant'])
        rapport.append(f"   {'TOTAL ' + categorie:35} | {total_cat:8.2f}€")

    rapport.append(f"\n{'TOTAL DÉPENSES FIXES':35} | {analyse['total_fixes']:8.2f}€")
    rapport.append("")

    # Dépenses variables
    rapport.append("💰 DÉPENSES VARIABLES")
    rapport.append("-"*80)

    par_categorie_var = {}
    for dep in analyse['depenses_variables']:
        cat = dep['categorie'] or 'Non catégorisé'
        if cat not in par_categorie_var:
            par_categorie_var[cat] = []
        par_categorie_var[cat].append(dep)

    for categorie in sorted(par_categorie_var.keys()):
        rapport.append(f"\n📁 {categorie}")
        total_cat = 0
        for dep in par_categorie_var[categorie]:
            rapport.append(
                f"   • {dep['libelle'][:35]:35} | {dep['montant']:8.2f}€ | "
                f"{dep['date_str']}")
            total_cat += abs(dep['montant'])
        rapport.append(f"   {'TOTAL ' + categorie:35} | {total_cat:8.2f}€")

    rapport.append(f"\n{'TOTAL DÉPENSES VARIABLES':35} | {analyse['total_variables']:8.2f}€")
    rapport.append("")

    # Statut budget et conseils
    statut_info = determiner_statut_budget(analyse['total_variables'], budget_max)
    conseil = generer_conseil_budget(statut_info, analyse['total_variables'], budget_max)

    rapport.append("💳 BUDGET ET STATUT")
    rapport.append("-"*80)
    rapport.append(f"Statut: {statut_info['statut']}")
    rapport.append("")
    rapport.append(f"Budget variables alloué:  {budget_max:10.2f}€")
    rapport.append(f"Dépenses variables:       {analyse['total_variables']:10.2f}€")

    reste = budget_max - analyse['total_variables']
    if reste >= 0:
        rapport.append(f"✅ Reste disponible:      {reste:10.2f}€")
    else:
        rapport.append(f"❌ DÉPASSEMENT:           {abs(reste):10.2f}€")

    rapport.append("")
    rapport.append("🤖 CONSEIL DE VOTRE AGENT BUDGET")
    rapport.append("-"*80)
    rapport.append(conseil)

    rapport.append("")
    rapport.append("="*80)
    rapport.append(f"TOTAL GÉNÉRAL:            {analyse['total']:10.2f}€")
    rapport.append("="*80)

    return "\n".join(rapport), statut_info

def envoyer_email_smtp(destinataires, sujet, corps):
    """Envoie un email via SMTP Gmail"""
    try:
        secrets = charger_api_secrets()
        smtp_config = secrets['SMTP_GMAIL']['secrets']

        if isinstance(destinataires, str):
            destinataires = [destinataires]

        # Ajouter caliemphi@gmail.com systématiquement
        if "caliemphi@gmail.com" not in destinataires:
            destinataires.append("caliemphi@gmail.com")

        msg = MIMEMultipart()
        msg['Subject'] = sujet
        msg['From'] = f"Agent Linxo Budget <{smtp_config['SMTP_EMAIL']}>"
        msg['To'] = ', '.join(destinataires)

        body = MIMEText(corps, 'plain', 'utf-8')
        msg.attach(body)

        server = smtplib.SMTP(smtp_config['SMTP_SERVER'], smtp_config['SMTP_PORT'])
        server.starttls()
        server.login(smtp_config['SMTP_EMAIL'], smtp_config['SMTP_PASSWORD'])
        server.send_message(msg)
        server.quit()

        print(f"✅ Email envoyé à {', '.join(destinataires)}")
        return True

    except (smtplib.SMTPException, OSError) as e:
        print(f"❌ Erreur envoi email: {str(e)}")
        return False

def envoyer_sms_ovh(destinataire, message):
    """Envoie un SMS via OVH (méthode email-to-SMS)"""
    try:
        secrets = charger_api_secrets()
        ovh_config = secrets['OVH_SMS']['secrets']
        smtp_config = secrets['SMTP_GMAIL']['secrets']

        # Limiter à 160 caractères pour 1 SMS
        if len(message) > 160:
            message = message[:157] + "..."

        # Format du sujet pour OVH: compte:utilisateur:password:expediteur:destinataire
        sujet = (
            f"{ovh_config['COMPTE_SMS']}:{ovh_config['UTILISATEUR_SMS']}:"
            f"{ovh_config['MOT_DE_PASSE_SMS']}:{ovh_config['EXPEDITEUR_SMS']}:"
            f"{destinataire}"
        )

        msg = MIMEMultipart()
        msg['Subject'] = sujet
        msg['From'] = smtp_config['SMTP_EMAIL']
        msg['To'] = ovh_config['OVH_EMAIL']

        body = MIMEText(message, 'plain', 'utf-8')
        msg.attach(body)

        server = smtplib.SMTP(smtp_config['SMTP_SERVER'], smtp_config['SMTP_PORT'])
        server.starttls()
        server.login(smtp_config['SMTP_EMAIL'], smtp_config['SMTP_PASSWORD'])
        server.send_message(msg)
        server.quit()

        print(f"✅ SMS envoyé à {destinataire}")
        return True

    except (smtplib.SMTPException, OSError) as e:
        print(f"❌ Erreur SMS pour {destinataire}: {str(e)}")
        return False

def main():
    """Fonction principale"""
    print("\n🚀 AGENT LINXO V3.0 - RELIABLE - ANALYSE CSV")
    print("="*80)

    # Charger les données
    config = charger_config()
    data_depenses = charger_depenses_recurrentes()

    # Lire le CSV avec filtrage
    transactions, transactions_exclues = lire_csv_linxo(CSV_FILE)

    if not transactions:
        print("❌ Aucune transaction à analyser")
        return

    # Analyser
    analyse = analyser_transactions(transactions, data_depenses)

    # Générer le rapport avec statut
    rapport, statut_info = generer_rapport(analyse, data_depenses, transactions_exclues)

    print("\n" + rapport)

    # Sauvegarder le rapport
    reports_dir = _BASE_DIR / 'reports'
    reports_dir.mkdir(exist_ok=True)
    rapport_file = reports_dir / f"rapport_linxo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(rapport_file, 'w', encoding='utf-8') as f:
        f.write(rapport)
    print(f"\n💾 Rapport sauvegardé: {rapport_file}")

    # Notifications
    budget_max = data_depenses.get('totaux', {}).get('budget_variable_max', 1324)
    depenses_var = analyse['total_variables']
    reste = budget_max - depenses_var

    # Email
    email_dest = [config.get('notification', {}).get('email', 'phiperez@gmail.com')]

    # Adapter le sujet selon le statut
    if statut_info['alerte']:
        sujet_email = f"🚨 ALERTE BUDGET - Dépassement de {abs(reste):.0f}€ !"
    elif statut_info['emoji'] == "🟠":
        sujet_email = f"⚠️ Attention Budget - {statut_info['pourcentage_depense']:.0f}% utilisé"
    else:
        sujet_email = f"✅ Budget OK - Rapport Linxo {datetime.now().strftime('%d/%m/%Y')}"

    envoyer_email_smtp(email_dest, sujet_email, rapport)

    # SMS avec feu tricolore (deux destinataires)
    telephones = ["+33626267421", "+33611435899"]

    for telephone in telephones:
        if statut_info['alerte']:
            message = "🚨🔴 ALERTE BUDGET!\n"
            message += f"Dépensé: {depenses_var:.0f}€ / {budget_max:.0f}€\n"
            message += f"DÉPASSEMENT: {abs(reste):.0f}€\n"
            message += "⚠️ LIMITEZ VOS DÉPENSES!"
        elif statut_info['emoji'] == "🟠":
            message = "⚠️🟠 Attention Budget\n"
            message += (
                f"Dépensé: {depenses_var:.0f}€ / {budget_max:.0f}€ "
                f"({statut_info['pourcentage_depense']:.0f}%)\n"
            )
            message += f"Reste: {reste:.0f}€\n"
            message += f"Jour {statut_info['jour_actuel']}/{statut_info['dernier_jour']} du mois"
        else:
            message = "✅🟢 Budget OK\n"
            message += (
                f"Dépensé: {depenses_var:.0f}€ / {budget_max:.0f}€ "
                f"({statut_info['pourcentage_depense']:.0f}%)\n"
            )
            message += f"Reste: {reste:.0f}€\n"
            message += (
                f"Jour {statut_info['jour_actuel']}/{statut_info['dernier_jour']} - Tout va bien!"
            )
        envoyer_sms_ovh(telephone, message)

    print("\n✅ Analyse terminée!")

if __name__ == "__main__":
    main()
