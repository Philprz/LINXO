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
        or "GENERALI" in libelle_upper
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

    # Calcul de l'avancement dans le temps (pour toutes les familles)
    import calendar
    jour_actuel = r_date.day
    dernier_jour = calendar.monthrange(r_date.year, r_date.month)[1]
    avancement_mois = (jour_actuel / dernier_jour) * 100

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

        # Calcul des données de progression (si budget_max fourni)
        render_context = {
            "famille_name": family_report.name,
            "total": family_report.total,
            "count": family_report.count,
            "transactions": transactions,
            "report_date": report_date_str,
            "index_url": index_url,
            "jour_actuel": jour_actuel,
            "dernier_jour": dernier_jour,
            "avancement_mois": avancement_mois,
        }

        # Ajouter les informations de budget si disponibles
        if budget_max is not None and budget_max > 0:
            pourcentage_utilise = (family_report.total / budget_max) * 100
            reste = budget_max - family_report.total

            # Déterminer la couleur de la barre selon le statut
            if reste < 0:
                couleur_barre = "#dc3545"  # Rouge - dépassement
            elif pourcentage_utilise > avancement_mois + 10:
                couleur_barre = "#fd7e14"  # Orange - trop en avance
            else:
                couleur_barre = "#28a745"  # Vert - dans les clous

            # Calcul de la prédiction de fin de mois
            jours_restants = dernier_jour - jour_actuel
            if jour_actuel > 0:
                depense_quotidienne_moyenne = family_report.total / jour_actuel
                prediction_fin_mois = family_report.total + (depense_quotidienne_moyenne * jours_restants)
                prediction_depassement = prediction_fin_mois - budget_max
                prediction_pourcentage = (prediction_fin_mois / budget_max * 100)

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

            render_context.update({
                "budget_max": budget_max,
                "pourcentage_utilise": pourcentage_utilise,
                "couleur_barre": couleur_barre,
                "prediction_fin_mois": prediction_fin_mois,
                "prediction_depassement": prediction_depassement,
                "prediction_pourcentage": prediction_pourcentage,
                "couleur_prediction": couleur_prediction,
                "message_prediction": message_prediction,
                "jours_restants": jours_restants,
            })

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

    index_html = index_template.render(
        report_date=report_date_str,
        families=families_data,
        grand_total=grand_total,
        total_transactions=total_transactions,
    )
    (base_dir / "index.html").write_text(index_html, encoding="utf-8")

    return ReportIndex(
        report_date=report_date_str,
        base_dir=base_dir,
        public_base_url=base_url,
        families=families_data,
        grand_total=grand_total,
        total_transactions=total_transactions,
    )


if __name__ == "__main__":
    print("Module de génération de rapports HTML par famille")
    print("Utilisez build_daily_report(df, base_url=...) pour générer un rapport.")
