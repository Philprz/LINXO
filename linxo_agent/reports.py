#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module de génération de rapports HTML par famille de dépenses.

- Produit un index + une page HTML par famille
- URLs optionnellement signées (HMAC) avec expiration
"""

from __future__ import annotations

import hashlib
import hmac
import re
import time
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from jinja2 import Environment, FileSystemLoader, select_autoescape
    import pandas as pd
except ImportError as exc:
    raise ImportError(
        "Les dépendances requises ne sont pas installées. "
        "Installez jinja2 et pandas: pip install jinja2 pandas"
    ) from exc


@dataclass
class FamilyReport:
    """Représente un rapport de famille de dépenses."""
    name: str
    slug: str
    total: float
    count: int
    url: str
    file_path: Path


@dataclass
class ReportIndex:
    """Index des rapports générés pour une date donnée."""
    report_date: str
    base_dir: Path
    public_base_url: str
    families: List[Dict[str, Any]]
    grand_total: float
    total_transactions: int


def slugify(text: str) -> str:
    """
    Convertit un texte en slug URL-safe.
    """
    normalized = text.lower()
    normalized = re.sub(r"[àáâãäå]", "a", normalized)
    normalized = re.sub(r"[èéêë]", "e", normalized)
    normalized = re.sub(r"[ìíîï]", "i", normalized)
    normalized = re.sub(r"[òóôõö]", "o", normalized)
    normalized = re.sub(r"[ùúûü]", "u", normalized)
    normalized = re.sub(r"[ýÿ]", "y", normalized)
    normalized = re.sub(r"[ç]", "c", normalized)
    normalized = re.sub(r"[^a-z0-9]+", "-", normalized)
    normalized = normalized.strip("-")
    return normalized


def classify_famille(categorie: str, libelle: str) -> str:
    """
    Détermine la famille d'une dépense.
    """
    categorie_upper = categorie.upper()
    libelle_upper = libelle.upper()

    # Crédits & Emprunts
    credit_keywords = ("PRET", "CREDIT", "SOFINCO")
    credit_libelle = ("DIAC", "ONEY", "CONSUMER FINANCE", "ECHEANCE PRET")
    if any(k in categorie_upper for k in credit_keywords) or any(
        k in libelle_upper for k in credit_libelle
    ):
        return "Crédits & Emprunts"

    # Épargne & Investissements
    if (
        "EPARGNE" in categorie_upper
        or "GENERALI VIE" in libelle_upper
        or "BITCOIN" in categorie_upper
        or "BITSTACK" in libelle_upper
        or "CRYPTO" in categorie_upper
    ):
        return "Épargne & Investissements"

    # Animaux
    if (
        "ANIMAUX" in categorie_upper
        or "VETERINAIRE" in categorie_upper
        or "VETERI" in libelle_upper
        or "GAMM VERT" in libelle_upper
    ):
        return "Animaux de compagnie"

    # Énergie & Eau
    energie_keywords = ("ELECTRICITE", "GAZ", "CHAUFFAGE", "EAU")
    energie_libelle = ("ENGIE", "EDF", "SGC")
    if any(k in categorie_upper for k in energie_keywords) or any(
        k in libelle_upper for k in energie_libelle
    ):
        return "Énergie & Eau"

    # Télécommunications
    telecom_keywords = ("INTERNET", "TELECOM")
    telecom_libelle = ("FREE", "BOUYGUES", "ORANGE", "SFR", "DISNEY")
    if any(k in categorie_upper for k in telecom_keywords) or any(
        k in libelle_upper for k in telecom_libelle
    ):
        return "Télécommunications"

    # Impôts & Taxes
    if (
        "IMPOT" in categorie_upper
        or "TAXE" in categorie_upper
        or "DIRECTION GENERALE" in libelle_upper
        or "TRESOR PUBLIC" in libelle_upper
    ):
        return "Impôts & Taxes"

    # Beauté & Bien-être
    if (
        "COIFFEUR" in categorie_upper
        or "ESTHETIQUE" in categorie_upper
        or "COSMETIQUE" in categorie_upper
        or "SOINS" in categorie_upper
        or "BEAUTE" in categorie_upper
    ):
        return "Beauté & Bien-être"

    # Travaux & Jardin
    if (
        "TRAVAUX" in categorie_upper
        or "DECO" in categorie_upper
        or "JARDIN" in categorie_upper
        or "LEROY MERLIN" in libelle_upper
        or "BRICOLAGE" in categorie_upper
    ):
        return "Maison & Jardin"

    # Services & Tech
    if (
        "SERVICES" in categorie_upper
        or "OVH" in libelle_upper
        or "SENDINB" in libelle_upper
        or "UBER" in libelle_upper
        or "PAYPAL" in libelle_upper
    ):
        return "Services & Tech"

    # Parking & Péages
    if (
        "PARKING" in categorie_upper
        or "PEAGE" in categorie_upper
        or "APRR" in libelle_upper
        or "LPA" in libelle_upper
        or "GARAGE" in categorie_upper
    ):
        return "Parking & Péages"

    # Café & Snacks
    if (
        "SNACKS" in categorie_upper
        or "REPAS AU TRAVAIL" in categorie_upper
        or "MAXICOFFEE" in libelle_upper
    ):
        return "Café & Snacks"

    # Culture & High-tech
    culture_keywords = ("MUSIQUE", "LIVRES", "FILMS", "ELECTRONIQUE", "MULTIMEDIA")
    culture_libelle = ("FNAC", "CDISCOUNT")
    if any(k in categorie_upper for k in culture_keywords) or any(
        k in libelle_upper for k in culture_libelle
    ):
        return "Culture & High-tech"

    # Éducation & Enfants
    if (
        "RESTAURATION SCOLAIRE" in categorie_upper
        or "CANTINE" in categorie_upper
    ):
        return "Éducation & Enfants"

    # Juridique & Syndical
    if (
        "CONSEIL JURIDIQUE" in categorie_upper
        or "CFDT" in libelle_upper
        or "SYNDICAT" in categorie_upper
    ):
        return "Juridique & Syndical"

    # Frais bancaires
    if (
        "INTERET" in categorie_upper
        or "FRAIS" in categorie_upper
        or "BANQUE" in categorie_upper
        or "AGIOS" in categorie_upper
    ):
        return "Frais bancaires"

    # Alimentation
    if "ALIMENTATION" in categorie_upper or "SUPERMARCHE" in categorie_upper:
        return "Alimentation"

    # Restaurants & Cafés
    if "RESTAURANT" in categorie_upper or "CAFE" in categorie_upper:
        return "Restaurants & Cafés"

    # Transports
    if (
        "TRANSPORT" in categorie_upper
        or "CARBURANT" in categorie_upper
        or "ESSENCE" in categorie_upper
    ):
        return "Transports"

    # Logement (loyer)
    if "LOGEMENT" in categorie_upper or "LOYER" in categorie_upper:
        return "Logement"

    # Santé
    if (
        "SANTE" in categorie_upper
        or "PHARMACIE" in categorie_upper
        or "MEDECIN" in categorie_upper
    ):
        return "Santé"

    # Loisirs & Sports
    if (
        "LOISIR" in categorie_upper
        or "SPORT" in categorie_upper
        or "CINEMA" in categorie_upper
    ):
        return "Loisirs & Sports"

    # Shopping & Mode
    if (
        "SHOPPING" in categorie_upper
        or "VETEMENT" in categorie_upper
        or "HABILLEMENT" in categorie_upper
    ):
        return "Shopping & Mode"

    # Abonnements
    if (
        "ABONNEMENT" in categorie_upper
        or "NETFLIX" in libelle_upper
        or "SPOTIFY" in libelle_upper
    ):
        return "Abonnements"

    # Assurances
    if "ASSURANCE" in categorie_upper:
        return "Assurances"

    return "Autres dépenses"


def generate_token(url: str, signing_key: str, validity_hours: int = 24) -> str:
    """
    Génère un token HMAC signé pour une URL avec expiration.
    """
    expiry = int(time.time()) + (validity_hours * 3600)
    message = f"{url}:{expiry}"
    signature = hmac.new(
        signing_key.encode("utf-8"),
        message.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return f"{signature}:{expiry}"


def build_daily_report(
    df: "pd.DataFrame",
    report_date: Optional[date | str] = None,
    base_url: Optional[str] = None,
    signing_key: Optional[str] = None,
    budget_max: Optional[float] = None,
    conseil_llm: Optional[str] = None,
    analysis_result: Optional[Dict[str, Any]] = None,
) -> ReportIndex:
    """
    Construit un rapport journalier HTML avec pages par famille.
    """
    if not base_url:
        raise ValueError(
            "REPORTS_BASE_URL est requis pour générer les rapports. "
            "Définissez cette variable dans votre fichier .env."
        )

    # Colonnes requises
    required = {"montant", "libelle", "categorie"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Colonnes manquantes dans le DataFrame: {', '.join(sorted(missing))}")

    # Coercition numérique du montant
    df["montant"] = pd.to_numeric(df["montant"], errors="coerce").fillna(0.0)

    # Normaliser report_date
    if report_date is None:
        r_date = date.today()
    elif isinstance(report_date, str):
        r_date = datetime.strptime(report_date, "%Y-%m-%d").date()
    else:
        r_date = report_date

    report_date_str = r_date.strftime("%Y-%m-%d")

    # Répertoire de sortie
    project_root = Path(__file__).parent.parent
    base_dir = project_root / "data" / "reports" / report_date_str
    base_dir.mkdir(parents=True, exist_ok=True)

    # Classifier si absent
    if "famille" not in df.columns:
        df["famille"] = df.apply(
            lambda row: classify_famille(
                row.get("categorie", ""),
                row.get("libelle", ""),
            ),
            axis=1,
        )

    families_data: List[Dict[str, Any]] = []
    family_reports: List[FamilyReport] = []

    # Grouper par famille
    for famille_name, groupe in df.groupby("famille"):
        famille_label = str(famille_name)
        total_famille = float(groupe["montant"].apply(lambda x: abs(x) if x < 0 else 0.0).sum())
        count = int(len(groupe))
        slug = slugify(famille_label)

        # Fichier et URL
        file_name = f"family-{slug}.html"
        file_path = base_dir / file_name

        relative_url = f"/{report_date_str}/{file_name}"
        full_url = f"{base_url.rstrip('/')}{relative_url}"

        if signing_key:
            token = generate_token(relative_url, signing_key)
            full_url = f"{full_url}?t={token}"

        families_data.append(
            {"name": famille_label, "slug": slug,
              "total": total_famille, "count": count, "url": full_url}
        )

        family_reports.append(
            FamilyReport(
                name=famille_label, slug=slug,
                total=total_famille, count=count, url=full_url, file_path=file_path
            )
        )

    # Tri décroissant
    families_data.sort(key=lambda x: x["total"], reverse=True)
    family_reports.sort(key=lambda x: x.total, reverse=True)

    # Totaux globaux
    grand_total = float(sum(f["total"] for f in families_data))
    total_transactions = int(len(df))

    # Jinja2
    templates_dir = project_root / "templates" / "reports"
    env = Environment(
        loader=FileSystemLoader(templates_dir),
        autoescape=select_autoescape(["html", "xml"]),
    )

    # Générer les pages famille
    family_template = env.get_template("family.html.j2")

    # Fonction utilitaire pour parser les dates
    def _parse_date(s: str) -> datetime:
        if not s:
            return datetime.min
        for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
            try:
                return datetime.strptime(s, fmt)
            except (ValueError, TypeError):
                continue
        return datetime.min

    for family_report in family_reports:
        groupe = df[df["famille"] == family_report.name].copy()

        # Préparer transactions (normaliser date en str)
        transactions: List[Dict[str, Any]] = []
        for _, row in groupe.iterrows():
            montant = float(row["montant"])
            dval = row.get("date_str", row.get("date", ""))
            dval = "" if pd.isna(dval) else str(dval)
            transactions.append(
                {
                    "date": dval,
                    "libelle": row.get("libelle", ""),
                    "montant": abs(montant) if montant < 0 else 0.0,
                    "categorie": row.get("categorie", "Non classé"),
                }
            )

        # Tri par date décroissante (accepte 'dd/mm/YYYY' puis 'YYYY-MM-DD')
        transactions.sort(key=lambda x: _parse_date(x["date"]), reverse=True)

        # URL index
        index_relative_url = f"/{report_date_str}/index.html"
        index_url = f"{base_url.rstrip('/')}{index_relative_url}"
        if signing_key:
            token_idx = generate_token(index_relative_url, signing_key)
            index_url = f"{index_url}?t={token_idx}"

        # Contexte de rendu pour la page famille (sans calculs budgétaires)
        render_context = {
            "famille_name": family_report.name,
            "total": family_report.total,
            "count": family_report.count,
            "transactions": transactions,
            "report_date": report_date_str,
            "index_url": index_url,
        }

        # Ajouter le conseil LLM si disponible
        if conseil_llm:
            render_context["conseil_llm"] = conseil_llm

        html_content = family_template.render(**render_context)
        family_report.file_path.write_text(html_content, encoding="utf-8")

    # Générer la page index
    index_template = env.get_template("index.html.j2")
    index_relative_url = f"/{report_date_str}/index.html"
    index_url = f"{base_url.rstrip('/')}{index_relative_url}"
    if signing_key:
        token = generate_token(index_relative_url, signing_key)
        index_url = f"{index_url}?t={token}"

    # Préparer les données budgétaires pour l'index
    index_context = {
        "report_date": report_date_str,
        "families": families_data,
        "grand_total": grand_total,
        "total_transactions": total_transactions,
    }

    # Ajouter les familles de dépenses agrégées si disponibles
    if analysis_result and 'familles_aggregees' in analysis_result:
        familles_agg = analysis_result['familles_aggregees']
        famille_alerts = analysis_result.get('famille_alerts', [])

        # Formater les données pour le template
        familles_depenses_data = []
        for nom_famille, data in sorted(familles_agg.items(), key=lambda x: x[1]['total'], reverse=True):
            famille_item = {
                'nom': nom_famille,
                'description': data.get('description', ''),
                'total': data['total'],
                'budget': data.get('budget', 0),
                'pourcentage': data.get('pourcentage', 0),
                'statut': data.get('statut', ''),
                'mode_affichage': data.get('mode_affichage', 'detail'),
                'nb_transactions': data.get('nb_transactions', 0),
                'transactions': []
            }

            # Ajouter les transactions si mode détaillé
            if data['mode_affichage'] == 'detail':
                for trans in data.get('transactions', []):
                    famille_item['transactions'].append({
                        'libelle': trans.get('libelle_complet', trans.get('libelle', '')),
                        'montant': abs(trans.get('montant', 0)),
                        'date': trans.get('date', '')
                    })

            familles_depenses_data.append(famille_item)

        index_context['familles_depenses'] = familles_depenses_data
        index_context['famille_alerts'] = [alert['message'] for alert in famille_alerts]

    # Ajouter les données budgétaires si disponibles
    if analysis_result and budget_max:
        import calendar
        jour_actuel = r_date.day
        dernier_jour = calendar.monthrange(r_date.year, r_date.month)[1]
        avancement_mois = (jour_actuel / dernier_jour) * 100

        total_variables = analysis_result.get("total_variables", 0)
        total_fixes = analysis_result.get("total_fixes", 0)
        reste = budget_max - total_variables
        pourcentage = (total_variables / budget_max * 100) if budget_max > 0 else 0

        # Déterminer la couleur de la barre selon le statut
        if reste < 0:
            couleur_barre_variables = "#dc3545"  # Rouge - dépassement
        elif pourcentage > avancement_mois + 10:
            couleur_barre_variables = "#fd7e14"  # Orange - trop en avance
        else:
            couleur_barre_variables = "#28a745"  # Vert - dans les clous

        # Calcul de la prédiction de fin de mois
        jours_restants = dernier_jour - jour_actuel
        if jour_actuel > 0:
            depense_quotidienne_moyenne = total_variables / jour_actuel
            prediction_fin_mois = total_variables + (depense_quotidienne_moyenne * jours_restants)
            prediction_depassement = prediction_fin_mois - budget_max
            prediction_pourcentage = (prediction_fin_mois / budget_max * 100) if budget_max > 0 else 0

            # Couleur de la prédiction
            couleur_prediction = "#28a745"  # Vert = OK
            if prediction_depassement > 0:
                couleur_prediction = "#dc3545"  # Rouge = dépassement
            elif prediction_pourcentage > 90:
                couleur_prediction = "#fd7e14"  # Orange = attention

            # Message de prédiction
            if prediction_depassement > 0:
                message_prediction = f"⚠️ Vous risquez de dépasser de {abs(prediction_depassement):.2f} €"
            elif prediction_pourcentage > 90:
                message_prediction = f"⚡ Attention, vous serez à {prediction_pourcentage:.0f}% du budget"
            else:
                message_prediction = f"✅ Vous devriez rester sous budget ({prediction_pourcentage:.0f}%)"
        else:
            prediction_fin_mois = 0
            prediction_depassement = 0
            prediction_pourcentage = 0
            couleur_prediction = "#6c757d"
            message_prediction = "⏳ Prédiction disponible après le 1er jour"

        index_context.update({
            "budget_max": budget_max,
            "total_variables": total_variables,
            "total_fixes": total_fixes,
            "reste": reste,
            "pourcentage": pourcentage,
            "couleur_barre_variables": couleur_barre_variables,
            "avancement_mois": avancement_mois,
            "jour_actuel": jour_actuel,
            "dernier_jour": dernier_jour,
            "prediction_fin_mois": prediction_fin_mois,
            "prediction_depassement": prediction_depassement,
            "prediction_pourcentage": prediction_pourcentage,
            "couleur_prediction": couleur_prediction,
            "message_prediction": message_prediction,
            "jours_restants": jours_restants,
        })

    # Ajouter le conseil LLM si disponible
    if conseil_llm:
        index_context["conseil_llm"] = conseil_llm

    index_html = index_template.render(**index_context)
    (base_dir / "index.html").write_text(index_html, encoding="utf-8")

    # Générer les pages dédiées aux frais fixes et dépenses variables
    frais_fixes_url = None
    depenses_variables_url = None

    if analysis_result:
        # Page frais fixes
        try:
            frais_fixes_url = build_frais_fixes_page(
                base_dir=base_dir,
                report_date_str=report_date_str,
                base_url=base_url,
                signing_key=signing_key,
                analysis_result=analysis_result,
                env=env,
            )
            print(f"[OK] Page frais fixes générée: {frais_fixes_url}")
        except Exception as e:
            print(f"[WARN] Erreur génération page frais fixes: {e}")

        # Page dépenses variables
        if budget_max:
            try:
                depenses_variables_url = build_depenses_variables_page(
                    base_dir=base_dir,
                    report_date_str=report_date_str,
                    base_url=base_url,
                    signing_key=signing_key,
                    analysis_result=analysis_result,
                    env=env,
                    budget_max=budget_max,
                )
                print(f"[OK] Page dépenses variables générée: {depenses_variables_url}")
            except Exception as e:
                print(f"[WARN] Erreur génération page dépenses variables: {e}")

    return ReportIndex(
        report_date=report_date_str,
        base_dir=base_dir,
        public_base_url=base_url,
        families=families_data,
        grand_total=grand_total,
        total_transactions=total_transactions,
    )


def build_frais_fixes_page(
    base_dir: Path,
    report_date_str: str,
    base_url: str,
    signing_key: Optional[str],
    analysis_result: Dict[str, Any],
    env: Environment,
) -> Optional[str]:
    """
    Génère la page dédiée aux frais fixes.
    Retourne l'URL de la page générée.
    """
    from config import get_config
    import calendar

    config = get_config()
    depenses_fixes_ref = config.depenses_data.get('depenses_fixes', [])
    depenses_fixes_transactions = analysis_result.get('depenses_fixes', [])

    # Obtenir le mois en cours
    r_date = datetime.strptime(report_date_str, "%Y-%m-%d").date()
    mois_actuel = r_date.month
    jour_actuel = r_date.day

    # Classer les frais fixes
    preleves = []
    en_attente = []
    non_appliques = []

    # Créer un ensemble des identifiants prélevés
    identifiants_preleves = set()
    for trans in depenses_fixes_transactions:
        # Chercher la correspondance dans la config
        for frais_ref in depenses_fixes_ref:
            identifiant = frais_ref.get('identifiant', frais_ref.get('libelle', ''))
            if identifiant.upper() in trans.get('libelle', '').upper():
                identifiants_preleves.add(identifiant)
                preleves.append({
                    'date': trans.get('date_str', trans.get('date', '')),
                    'libelle': trans.get('libelle', ''),
                    'compte': trans.get('compte', ''),
                    'montant': abs(trans.get('montant', 0.0)),
                    'commentaire_config': frais_ref.get('commentaire', '')
                })
                break

    # Analyser les frais de référence
    for frais in depenses_fixes_ref:
        identifiant = frais.get('identifiant', frais.get('libelle', ''))
        mois_occurrence = frais.get('mois_occurrence', list(range(1, 13)))

        # Vérifier si applicable ce mois
        if mois_actuel in mois_occurrence:
            # Vérifier si déjà prélevé
            if identifiant not in identifiants_preleves:
                en_attente.append(frais)
        else:
            non_appliques.append(frais)

    # Calculs des totaux
    total_preleve = sum(f['montant'] for f in preleves)
    total_en_attente = sum(f.get('montant', 0.0) for f in en_attente)
    total_prevu = total_preleve + total_en_attente
    nb_preleves = len(preleves)
    nb_total = len(preleves) + len(en_attente)

    # URL de l'index
    index_relative_url = f"/{report_date_str}/index.html"
    index_url = f"{base_url.rstrip('/')}{index_relative_url}"
    if signing_key:
        token_idx = generate_token(index_relative_url, signing_key)
        index_url = f"{index_url}?t={token_idx}"

    # Générer la page
    template = env.get_template("frais-fixes.html.j2")
    context = {
        "report_date": report_date_str,
        "index_url": index_url,
        "preleves": preleves,
        "en_attente": en_attente,
        "non_appliques": non_appliques,
        "total_preleve": total_preleve,
        "total_en_attente": total_en_attente,
        "total_prevu": total_prevu,
        "nb_preleves": nb_preleves,
        "nb_total": nb_total,
    }

    html_content = template.render(**context)
    file_path = base_dir / "frais-fixes.html"
    file_path.write_text(html_content, encoding="utf-8")

    # Retourner l'URL
    relative_url = f"/{report_date_str}/frais-fixes.html"
    full_url = f"{base_url.rstrip('/')}{relative_url}"
    if signing_key:
        token = generate_token(relative_url, signing_key)
        full_url = f"{full_url}?t={token}"

    return full_url


def build_depenses_variables_page(
    base_dir: Path,
    report_date_str: str,
    base_url: str,
    signing_key: Optional[str],
    analysis_result: Dict[str, Any],
    env: Environment,
    budget_max: float,
) -> Optional[str]:
    """
    Génère la page dédiée aux dépenses variables avec filtrage par catégorie.
    Retourne l'URL de la page générée.
    """
    import calendar

    depenses_variables = analysis_result.get('depenses_variables', [])
    total_variables = analysis_result.get('total_variables', 0.0)

    # Obtenir le mois en cours
    r_date = datetime.strptime(report_date_str, "%Y-%m-%d").date()
    jour_actuel = r_date.day
    dernier_jour = calendar.monthrange(r_date.year, r_date.month)[1]
    avancement_mois = (jour_actuel / dernier_jour) * 100

    # Calculs budgétaires
    reste = budget_max - total_variables
    pourcentage = (total_variables / budget_max * 100) if budget_max > 0 else 0

    # Couleur de la barre
    if reste < 0:
        couleur_barre = "#dc3545"  # Rouge
    elif pourcentage > avancement_mois + 10:
        couleur_barre = "#fd7e14"  # Orange
    else:
        couleur_barre = "#28a745"  # Vert

    # Préparer les transactions
    transactions = []
    categories_count = {}

    for trans in depenses_variables:
        categorie = trans.get('categorie', 'Non classé')
        montant = abs(trans.get('montant', 0.0))

        transactions.append({
            'date': trans.get('date_str', trans.get('date', '')),
            'libelle': trans.get('libelle', ''),
            'categorie': categorie,
            'compte': trans.get('compte', ''),
            'montant': montant,
        })

        # Compter par catégorie
        if categorie not in categories_count:
            categories_count[categorie] = {'count': 0, 'total': 0.0}
        categories_count[categorie]['count'] += 1
        categories_count[categorie]['total'] += montant

    # Préparer les catégories pour les filtres
    categories = [
        {'name': cat, 'count': data['count'], 'total': data['total']}
        for cat, data in sorted(categories_count.items(), key=lambda x: x[1]['total'], reverse=True)
    ]

    # URL de l'index
    index_relative_url = f"/{report_date_str}/index.html"
    index_url = f"{base_url.rstrip('/')}{index_relative_url}"
    if signing_key:
        token_idx = generate_token(index_relative_url, signing_key)
        index_url = f"{index_url}?t={token_idx}"

    # Générer la page
    template = env.get_template("depenses-variables.html.j2")
    context = {
        "report_date": report_date_str,
        "index_url": index_url,
        "transactions": transactions,
        "categories": categories,
        "total_variables": total_variables,
        "budget_max": budget_max,
        "reste": reste,
        "pourcentage": pourcentage,
        "couleur_barre": couleur_barre,
        "avancement_mois": avancement_mois,
        "jour_actuel": jour_actuel,
        "dernier_jour": dernier_jour,
        "nb_transactions": len(transactions),
    }

    html_content = template.render(**context)
    file_path = base_dir / "depenses-variables.html"
    file_path.write_text(html_content, encoding="utf-8")

    # Retourner l'URL
    relative_url = f"/{report_date_str}/depenses-variables.html"
    full_url = f"{base_url.rstrip('/')}{relative_url}"
    if signing_key:
        token = generate_token(relative_url, signing_key)
        full_url = f"{full_url}?t={token}"

    return full_url


if __name__ == "__main__":
    print("Module de génération de rapports HTML par famille")
    print("Utilisez build_daily_report(df, base_url=...) pour générer un rapport.")
