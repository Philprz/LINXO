#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module de génération de rapports HTML par famille de dépenses
Génère des pages HTML cliquables pour consultation détaillée
"""

import re
from datetime import date, datetime
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Optional
import hashlib
import hmac
import time

try:
    from jinja2 import Environment, FileSystemLoader, select_autoescape
    import pandas as pd
except ImportError:
    raise ImportError(
        "Les dépendances requises ne sont pas installées. "
        "Installez jinja2 et pandas: pip install jinja2 pandas"
    )


@dataclass
class FamilyReport:
    """Représente un rapport de famille de dépenses"""
    name: str
    slug: str
    total: float
    count: int
    url: str
    file_path: Path


@dataclass
class ReportIndex:
    """Index des rapports générés pour une date donnée"""
    report_date: str
    base_dir: Path
    public_base_url: str
    families: List[Dict]
    grand_total: float
    total_transactions: int


def slugify(text: str) -> str:
    """
    Convertit un texte en slug URL-safe

    Args:
        text: Texte à slugifier

    Returns:
        str: Slug URL-safe
    """
    # Normaliser les accents
    text = text.lower()
    text = re.sub(r'[àáâãäå]', 'a', text)
    text = re.sub(r'[èéêë]', 'e', text)
    text = re.sub(r'[ìíîï]', 'i', text)
    text = re.sub(r'[òóôõö]', 'o', text)
    text = re.sub(r'[ùúûü]', 'u', text)
    text = re.sub(r'[ýÿ]', 'y', text)
    text = re.sub(r'[ç]', 'c', text)

    # Remplacer les caractères non alphanumériques par des tirets
    text = re.sub(r'[^a-z0-9]+', '-', text)

    # Supprimer les tirets en début et fin
    text = text.strip('-')

    return text


def classify_famille(categorie: str, libelle: str) -> str:
    """
    Détermine la famille d'une dépense basée sur sa catégorie et son libellé

    Args:
        categorie: Catégorie de la transaction
        libelle: Libellé de la transaction

    Returns:
        str: Nom de la famille
    """
    categorie_upper = categorie.upper()
    libelle_upper = libelle.upper()

    # Mapping des catégories vers les familles (ordre d'importance)

    # Crédits & Emprunts
    if ('PRET' in categorie_upper or 'CREDIT' in categorie_upper or
        'SOFINCO' in categorie_upper or 'DIAC' in libelle_upper or
        'ONEY' in libelle_upper or 'CONSUMER FINANCE' in libelle_upper or
        'ECHEANCE PRET' in libelle_upper):
        return 'Crédits & Emprunts'

    # Épargne & Investissements
    elif ('EPARGNE' in categorie_upper or 'GENERALI' in libelle_upper or
          'BITCOIN' in categorie_upper or 'BITSTACK' in libelle_upper or
          'CRYPTO' in categorie_upper):
        return 'Épargne & Investissements'

    # Animaux
    elif ('ANIMAUX' in categorie_upper or 'VETERINAIRE' in categorie_upper or
          'VETERI' in libelle_upper or 'GAMM VERT' in libelle_upper):
        return 'Animaux de compagnie'

    # Énergie & Eau (distinct de Logement)
    elif ('ELECTRICITE' in categorie_upper or 'GAZ' in categorie_upper or
          'CHAUFFAGE' in categorie_upper or 'EAU' in categorie_upper or
          'ENGIE' in libelle_upper or 'EDF' in libelle_upper or 'SGC' in libelle_upper):
        return 'Énergie & Eau'

    # Télécommunications
    elif ('INTERNET' in categorie_upper or 'TELECOM' in categorie_upper or
          'FREE' in libelle_upper or 'BOUYGUES' in libelle_upper or
          'ORANGE' in libelle_upper or 'SFR' in libelle_upper or
          'DISNEY' in libelle_upper):
        return 'Télécommunications'

    # Impôts & Taxes
    elif ('IMPOT' in categorie_upper or 'TAXE' in categorie_upper or
          'DIRECTION GENERALE' in libelle_upper or 'TRESOR PUBLIC' in libelle_upper):
        return 'Impôts & Taxes'

    # Beauté & Bien-être
    elif ('COIFFEUR' in categorie_upper or 'ESTHETIQUE' in categorie_upper or
          'COSMETIQUE' in categorie_upper or 'SOINS' in categorie_upper or
          'BEAUTE' in categorie_upper):
        return 'Beauté & Bien-être'

    # Travaux & Jardin
    elif ('TRAVAUX' in categorie_upper or 'DECO' in categorie_upper or
          'JARDIN' in categorie_upper or 'LEROY MERLIN' in libelle_upper or
          'BRICOLAGE' in categorie_upper):
        return 'Maison & Jardin'

    # Services (PayPal, OVH, etc.)
    elif ('SERVICES' in categorie_upper or 'OVH' in libelle_upper or
          'SENDINB' in libelle_upper or 'UBER' in libelle_upper):
        return 'Services & Tech'

    # Parking & Péages
    elif ('PARKING' in categorie_upper or 'PEAGE' in categorie_upper or
          'APRR' in libelle_upper or 'LPA' in libelle_upper or 'GARAGE' in categorie_upper):
        return 'Parking & Péages'

    # Snacks & Café au travail
    elif ('SNACKS' in categorie_upper or 'REPAS AU TRAVAIL' in categorie_upper or
          'MAXICOFFEE' in libelle_upper):
        return 'Café & Snacks'

    # Culture & Divertissement
    elif ('MUSIQUE' in categorie_upper or 'LIVRES' in categorie_upper or
          'FILMS' in categorie_upper or 'FNAC' in libelle_upper or
          'ELECTRONIQUE' in categorie_upper or 'MULTIMEDIA' in categorie_upper or
          'CDISCOUNT' in libelle_upper):
        return 'Culture & High-tech'

    # Restauration scolaire
    elif ('RESTAURATION SCOLAIRE' in categorie_upper or 'CANTINE' in categorie_upper):
        return 'Éducation & Enfants'

    # Frais juridiques & syndicaux
    elif ('CONSEIL JURIDIQUE' in categorie_upper or 'CFDT' in libelle_upper or
          'SYNDICAT' in categorie_upper):
        return 'Juridique & Syndical'

    # Intérêts & Frais bancaires
    elif ('INTERET' in categorie_upper or 'FRAIS' in categorie_upper or
          'BANQUE' in categorie_upper or 'AGIOS' in categorie_upper):
        return 'Frais bancaires'

    # Alimentation
    elif 'ALIMENTATION' in categorie_upper or 'SUPERMARCHE' in categorie_upper:
        return 'Alimentation'

    # Restaurants & Cafés
    elif 'RESTAURANT' in categorie_upper or 'CAFE' in categorie_upper:
        return 'Restaurants & Cafés'

    # Transports
    elif 'TRANSPORT' in categorie_upper or 'CARBURANT' in categorie_upper or 'ESSENCE' in categorie_upper:
        return 'Transports'

    # Logement (uniquement loyer maintenant)
    elif 'LOGEMENT' in categorie_upper or 'LOYER' in categorie_upper:
        return 'Logement'

    # Santé
    elif 'SANTE' in categorie_upper or 'PHARMACIE' in categorie_upper or 'MEDECIN' in categorie_upper:
        return 'Santé'

    # Loisirs & Sports
    elif 'LOISIR' in categorie_upper or 'SPORT' in categorie_upper or 'CINEMA' in categorie_upper:
        return 'Loisirs & Sports'

    # Shopping & Mode
    elif 'SHOPPING' in categorie_upper or 'VETEMENT' in categorie_upper or 'HABILLEMENT' in categorie_upper:
        return 'Shopping & Mode'

    # Abonnements
    elif 'ABONNEMENT' in categorie_upper or 'NETFLIX' in libelle_upper or 'SPOTIFY' in libelle_upper:
        return 'Abonnements'

    # Assurances
    elif 'ASSURANCE' in categorie_upper:
        return 'Assurances'

    # Tout le reste
    else:
        return 'Autres dépenses'


def generate_token(url: str, signing_key: str, validity_hours: int = 24) -> str:
    """
    Génère un token HMAC signé pour une URL avec expiration

    Args:
        url: URL à signer
        signing_key: Clé de signature
        validity_hours: Durée de validité en heures

    Returns:
        str: Token signé
    """
    expiry = int(time.time()) + (validity_hours * 3600)
    message = f"{url}:{expiry}"
    signature = hmac.new(
        signing_key.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    return f"{signature}:{expiry}"


def build_daily_report(
    df: pd.DataFrame,
    report_date: Optional[date] = None,
    base_url: Optional[str] = None,
    signing_key: Optional[str] = None
) -> ReportIndex:
    """
    Construit un rapport journalier HTML avec pages par famille

    Args:
        df: DataFrame avec colonnes: date, libelle, montant, categorie
        report_date: Date du rapport (défaut: aujourd'hui)
        base_url: URL publique de base (doit être fournie, ex: https://linxo.appliprz.ovh/reports)
        signing_key: Clé pour signer les URLs (optionnel)

    Returns:
        ReportIndex: Index du rapport généré

    Raises:
        ValueError: Si base_url est manquant ou invalide
    """
    # Validation stricte de base_url
    if not base_url:
        raise ValueError(
            "REPORTS_BASE_URL est requis pour générer les rapports. "
            "Définissez cette variable dans votre fichier .env"
        )

    if report_date is None:
        report_date = date.today()
    elif isinstance(report_date, str):
        report_date = datetime.strptime(report_date, '%Y-%m-%d').date()

    # Créer le répertoire de destination
    report_date_str = report_date.strftime('%Y-%m-%d')
    base_dir = Path(__file__).parent.parent / 'data' / 'reports' / report_date_str
    base_dir.mkdir(parents=True, exist_ok=True)

    # Classifier les dépenses par famille si la colonne famille n'existe pas
    if 'famille' not in df.columns:
        df['famille'] = df.apply(
            lambda row: classify_famille(
                row.get('categorie', ''),
                row.get('libelle', '')
            ),
            axis=1
        )

    # Grouper par famille
    families_data = []
    family_reports = []

    for famille_name, groupe in df.groupby('famille'):
        total_famille = groupe['montant'].apply(lambda x: abs(x) if x < 0 else 0).sum()
        count = len(groupe)
        slug = slugify(famille_name)

        # Générer la page famille
        file_name = f"family-{slug}.html"
        file_path = base_dir / file_name

        # URL relative
        relative_url = f"/reports/{report_date_str}/{file_name}"
        full_url = f"{base_url.rstrip('/')}{relative_url}"

        # Ajouter le token si signing_key fourni
        if signing_key:
            token = generate_token(relative_url, signing_key)
            full_url = f"{full_url}?t={token}"

        families_data.append({
            'name': famille_name,
            'slug': slug,
            'total': total_famille,
            'count': count,
            'url': full_url
        })

        family_reports.append(FamilyReport(
            name=famille_name,
            slug=slug,
            total=total_famille,
            count=count,
            url=full_url,
            file_path=file_path
        ))

    # Trier les familles par montant décroissant
    families_data.sort(key=lambda x: x['total'], reverse=True)
    family_reports.sort(key=lambda x: x.total, reverse=True)

    # Calculer le total général
    grand_total = sum(f['total'] for f in families_data)
    total_transactions = len(df)

    # Configurer Jinja2
    templates_dir = Path(__file__).parent.parent / 'templates' / 'reports'
    env = Environment(
        loader=FileSystemLoader(templates_dir),
        autoescape=select_autoescape(['html', 'xml'])
    )

    # Générer les pages famille
    family_template = env.get_template('family.html.j2')

    for family_report in family_reports:
        groupe = df[df['famille'] == family_report.name].copy()

        # Préparer les transactions (trier par date décroissante)
        transactions = []
        for _, row in groupe.iterrows():
            transactions.append({
                'date': row.get('date_str', row.get('date', '')),
                'libelle': row.get('libelle', ''),
                'montant': abs(row['montant']) if row['montant'] < 0 else 0,
                'categorie': row.get('categorie', 'Non classé')
            })

        # Trier par date décroissante (plus récent en premier)
        try:
            transactions.sort(
                key=lambda x: datetime.strptime(x['date'], '%d/%m/%Y') if x['date'] else datetime.min,
                reverse=True
            )
        except:
            # Fallback: ne pas trier si problème de format de date
            pass

        # URL de l'index
        index_relative_url = f"/reports/{report_date_str}/index.html"
        index_url = f"{base_url.rstrip('/')}{index_relative_url}"
        if signing_key:
            token = generate_token(index_relative_url, signing_key)
            index_url = f"{index_url}?t={token}"

        # Rendre la page famille
        html_content = family_template.render(
            famille_name=family_report.name,
            total=family_report.total,
            count=family_report.count,
            transactions=transactions,
            report_date=report_date_str,
            index_url=index_url
        )

        # Écrire le fichier
        with open(family_report.file_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

    # Générer la page index
    index_template = env.get_template('index.html.j2')
    index_relative_url = f"/reports/{report_date_str}/index.html"
    index_url = f"{base_url.rstrip('/')}{index_relative_url}"
    if signing_key:
        token = generate_token(index_relative_url, signing_key)
        index_url = f"{index_url}?t={token}"

    html_content = index_template.render(
        report_date=report_date_str,
        families=families_data,
        grand_total=grand_total,
        total_transactions=total_transactions
    )

    index_path = base_dir / 'index.html'
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

    # Créer l'index de retour
    return ReportIndex(
        report_date=report_date_str,
        base_dir=base_dir,
        public_base_url=base_url,
        families=families_data,
        grand_total=grand_total,
        total_transactions=total_transactions
    )


if __name__ == "__main__":
    print("Module de génération de rapports HTML par famille")
    print("Utilisez build_daily_report(df) pour générer un rapport")
