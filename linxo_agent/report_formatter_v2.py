#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module de formatage des rapports budgétaires - Version 2
Style épuré et moderne inspiré de l'exemple fourni
"""

from datetime import datetime
import calendar


def formater_sms_v2(total_depenses, budget_max, reste, pourcentage):
    """
    Formate un SMS court et visuel avec emojis et conseil

    Args:
        total_depenses: Total dépensé
        budget_max: Budget maximum
        reste: Reste disponible
        pourcentage: Pourcentage utilisé

    Returns:
        str: Message SMS formaté
    """
    now = datetime.now()
    jour_actuel = now.day
    dernier_jour = calendar.monthrange(now.year, now.month)[1]
    jours_restants = dernier_jour - jour_actuel

    # Emoji selon le statut
    if reste < 0:
        emoji = "🔴"
    elif pourcentage >= 80:
        emoji = "🟠"
    else:
        emoji = "🟢"

    # Construction du message compact avec conseil
    if reste < 0:
        message = f"{emoji} BUDGET DÉPASSÉ!\n"
        message += f"💰 {total_depenses:.0f}€ / {budget_max:.0f}€\n"
        message += f"⚠️ +{abs(reste):.0f}€ de dépassement\n"
        message += f"📅 J{jour_actuel}/{dernier_jour}\n"
        message += f"💡 Limiter au strict nécessaire"
    elif pourcentage >= 80:
        budget_jour = reste / jours_restants if jours_restants > 0 else 0
        message = f"{emoji} Budget : {total_depenses:.0f}€/{budget_max:.0f}€\n"
        message += f"💵 Reste: {reste:.0f}€ ({100-pourcentage:.0f}%)\n"
        message += f"📅 J{jour_actuel}/{dernier_jour}\n"
        message += f"💡 Max {budget_jour:.0f}€/j les {jours_restants}j restants"
    else:
        budget_jour = reste / jours_restants if jours_restants > 0 else 0
        message = f"{emoji} Budget : {total_depenses:.0f}€/{budget_max:.0f}€\n"
        message += f"💵 Reste: {reste:.0f}€ ({100-pourcentage:.0f}%)\n"
        message += f"📅 J{jour_actuel}/{dernier_jour}\n"
        message += f"💡 ~{budget_jour:.0f}€/jour disponible"

    return message


def formater_email_html_v2(analyse, budget_max, conseil, budget_fixes_prevu=None):
    """
    Génère un email HTML épuré style moderne avec barres de progression améliorées

    Args:
        analyse: Résultat de l'analyse
        budget_max: Budget maximum pour variables
        conseil: Conseil généré
        budget_fixes_prevu: Budget prévu pour les frais fixes (calculé depuis depenses_fixes si None)

    Returns:
        str: HTML formaté
    """
    now = datetime.now()
    jour_actuel = now.day
    dernier_jour = calendar.monthrange(now.year, now.month)[1]

    total_fixes = analyse['total_fixes']
    total_depenses = analyse['total_variables']
    reste = budget_max - total_depenses
    pourcentage = (total_depenses / budget_max * 100) if budget_max > 0 else 0

    # Calculer le budget fixes prévu depuis les dépenses fixes référence si non fourni
    if budget_fixes_prevu is None:
        # Lire depuis la config
        try:
            from config import get_config
            config = get_config()
            depenses_fixes_ref = config.depenses_data.get('depenses_fixes', [])
            budget_fixes_prevu = sum(d.get('montant', 0) for d in depenses_fixes_ref)
        except:
            budget_fixes_prevu = 3422  # Fallback

    pourcentage_fixes = (total_fixes / budget_fixes_prevu * 100) if budget_fixes_prevu > 0 else 0

    # Calcul de l'avancement théorique du mois
    avancement_mois = (jour_actuel / dernier_jour * 100)
    depense_theorique_pct = avancement_mois  # On devrait avoir dépensé X% du budget

    # Couleur pour les dépenses variables selon le statut
    if reste < 0:
        # Dépassement = Rouge
        couleur_reste = "#dc3545"
        couleur_barre_variables = "#dc3545"
    elif pourcentage > depense_theorique_pct + 10:
        # Trop en avance (plus de 10% d'avance) = Orange
        couleur_reste = "#fd7e14"
        couleur_barre_variables = "#fd7e14"
    else:
        # Dans les clous = Vert
        couleur_reste = "#28a745"
        couleur_barre_variables = "#28a745"

    # Couleur pour les frais fixes selon le pourcentage
    if pourcentage_fixes > 100:
        # Dépassement = Rouge
        couleur_barre_fixes = "#dc3545"
    elif pourcentage_fixes > 90:
        # Proche de 100% = Orange
        couleur_barre_fixes = "#fd7e14"
    else:
        # Dans les clous = Vert
        couleur_barre_fixes = "#28a745"

    html = f"""
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;
            background-color: #f5f5f5;
            color: #333;
            line-height: 1.4;
        }}
        .container {{
            max-width: 650px;
            margin: 0 auto;
            background-color: white;
        }}
        .header {{
            background: linear-gradient(135deg, #7c69ef 0%, #a78bfa 100%);
            color: white;
            padding: 35px 30px;
            text-align: center;
        }}
        .header h1 {{
            font-size: 26px;
            font-weight: 600;
            margin-bottom: 6px;
        }}
        .header .date {{
            font-size: 15px;
            opacity: 0.95;
        }}
        .content {{
            padding: 25px 30px;
        }}
        .metric {{
            margin-bottom: 12px;
            font-size: 16px;
        }}
        .metric-label {{
            color: #333;
            margin-right: 8px;
        }}
        .metric-value {{
            font-weight: 700;
            font-size: 18px;
        }}
        .value-red {{ color: #dc3545; }}
        .value-green {{ color: {couleur_reste}; }}
        .value-default {{ color: #333; }}

        .progress-section {{
            margin: 15px 0;
        }}
        .progress-bar-container {{
            background-color: #e9ecef;
            border-radius: 6px;
            height: 28px;
            position: relative;
            width: 100%;
            border: 1px solid #ddd;
            overflow: visible;
        }}
        .progress-bar-fill {{
            height: 100%;
            display: flex;
            align-items: center;
            justify-content: flex-start;
            padding-left: 10px;
            color: white;
            font-weight: 600;
            font-size: 13px;
            transition: width 0.3s ease;
            border-radius: 5px 0 0 5px;
        }}
        .progress-marker-100 {{
            position: absolute;
            right: -2px;
            top: 0;
            bottom: 0;
            width: 3px;
            background-color: #333;
            z-index: 10;
        }}
        .progress-marker-100::before {{
            content: '100%';
            position: absolute;
            right: -22px;
            top: -24px;
            font-size: 11px;
            font-weight: 700;
            color: #333;
            white-space: nowrap;
        }}

        .conseil-box {{
            background-color: #fff9e6;
            border-left: 4px solid #ffc107;
            padding: 15px;
            margin: 20px 0;
            border-radius: 4px;
        }}
        .conseil-box h3 {{
            font-size: 15px;
            color: #856404;
            margin-bottom: 8px;
        }}
        .conseil-box p {{
            font-size: 13px;
            color: #856404;
            line-height: 1.5;
            margin: 4px 0;
        }}
        .section {{
            margin-top: 25px;
        }}
        .section-title {{
            font-size: 17px;
            font-weight: 600;
            margin-bottom: 15px;
            padding-bottom: 6px;
            border-bottom: 2px solid #7c69ef;
            color: #333;
        }}
        .section-title-icon {{
            margin-right: 6px;
        }}
        .transactions-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
        }}
        .transactions-table th {{
            background-color: #f8f9fa;
            padding: 10px 8px;
            text-align: left;
            font-size: 13px;
            font-weight: 600;
            color: #495057;
            border-bottom: 2px solid #dee2e6;
        }}
        .transactions-table td {{
            padding: 8px;
            font-size: 13px;
            border-bottom: 1px solid #f0f0f0;
        }}
        .transactions-table tr:last-child td {{
            border-bottom: none;
        }}
        .transactions-table tr:hover {{
            background-color: #f8f9fa;
        }}
        .td-date {{
            width: 85px;
            color: #6c757d;
            font-size: 12px;
            white-space: nowrap;
        }}
        .td-category {{
            width: 140px;
            color: #495057;
            font-size: 12px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}
        .td-label {{
            color: #333;
            font-size: 13px;
        }}
        .td-amount {{
            width: 90px;
            text-align: right;
            color: #dc3545;
            font-weight: 700;
            white-space: nowrap;
        }}
        .footer {{
            text-align: center;
            padding: 20px;
            background-color: #f8f9fa;
            font-size: 12px;
            color: #6c757d;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>💰 Rapport Linxo - Budget</h1>
            <div class="date">{now.strftime('%d/%m/%Y')}</div>
        </div>

        <div class="content">
            <div class="metric">
                <span class="metric-label">Frais fixes</span>
                <span class="metric-value value-red">{total_fixes:.2f} €</span>
                <span class="metric-label">/ {budget_fixes_prevu:.0f} €</span>
            </div>

            <div class="progress-section">
                <div class="progress-bar-container">
                    <div class="progress-bar-fill" style="width: {pourcentage_fixes:.1f}%; background: linear-gradient(90deg, {couleur_barre_fixes} 0%, {couleur_barre_fixes}dd 100%);">
                        {pourcentage_fixes:.0f}%
                    </div>
                    <div class="progress-marker-100"></div>
                </div>
            </div>

            <div class="metric">
                <span class="metric-label">Dépenses variables</span>
                <span class="metric-value value-red">{total_depenses:.2f} €</span>
                <span class="metric-label">/ {budget_max:.0f} €</span>
            </div>

            <div class="progress-section">
                <div class="progress-bar-container">
                    <div class="progress-bar-fill" style="width: {pourcentage:.1f}%; background: linear-gradient(90deg, {couleur_barre_variables} 0%, {couleur_barre_variables}dd 100%);">
                        {pourcentage:.0f}%
                    </div>
                    <div class="progress-marker-100"></div>
                </div>
            </div>

            <div class="metric" style="margin-top: 15px;">
                <span class="metric-label">{"Dépassement" if reste < 0 else "Reste disponible"}</span>
                <span class="metric-value value-green">{abs(reste):.2f} €</span>
            </div>

            <div class="conseil-box">
                <h3>💡 Conseil de votre Agent Budget</h3>
"""

    # Ajouter les lignes du conseil
    for ligne in conseil.split('\n'):
        if ligne.strip():
            html += f"                <p>{ligne}</p>\n"

    html += """
            </div>

            <div class="section">
                <div class="section-title">
                    <span class="section-title-icon">🔒</span>
                    Dépenses fixes ({} transactions)
                </div>
                <table class="transactions-table">
                    <thead>
                        <tr>
                            <th class="td-date">Date</th>
                            <th class="td-category">Catégorie</th>
                            <th class="td-label">Libellé</th>
                            <th class="td-amount">Montant</th>
                        </tr>
                    </thead>
                    <tbody>
""".format(len(analyse['depenses_fixes']))

    # Trier les dépenses fixes par montant décroissant
    depenses_fixes_triees = sorted(analyse['depenses_fixes'], key=lambda x: abs(x['montant']), reverse=True)

    # Ajouter toutes les dépenses fixes triées dans le tableau
    for dep in depenses_fixes_triees:
        libelle = dep['libelle']
        montant = abs(dep['montant'])
        date = dep.get('date_str', '')
        categorie = dep.get('categorie_fixe', dep.get('categorie', 'Non classé'))

        html += f"""
                        <tr>
                            <td class="td-date">{date}</td>
                            <td class="td-category">{categorie}</td>
                            <td class="td-label">{libelle}</td>
                            <td class="td-amount">-{montant:.2f} €</td>
                        </tr>
"""

    html += """
                    </tbody>
                </table>
            </div>

            <div class="section">
                <div class="section-title">
                    <span class="section-title-icon">📋</span>
                    Dépenses variables détaillées ({} transactions)
                </div>
                <table class="transactions-table">
                    <thead>
                        <tr>
                            <th class="td-date">Date</th>
                            <th class="td-category">Catégorie</th>
                            <th class="td-label">Libellé</th>
                            <th class="td-amount">Montant</th>
                        </tr>
                    </thead>
                    <tbody>
""".format(len(analyse['depenses_variables']))

    # Trier les dépenses variables par montant décroissant (plus important en premier)
    depenses_triees = sorted(analyse['depenses_variables'], key=lambda x: abs(x['montant']), reverse=True)

    # Ajouter toutes les transactions variables triées dans le tableau
    for dep in depenses_triees:
        libelle = dep['libelle']
        montant = abs(dep['montant'])
        date = dep.get('date_str', '')
        categorie = dep.get('categorie', 'Non classé')

        html += f"""
                        <tr>
                            <td class="td-date">{date}</td>
                            <td class="td-category">{categorie}</td>
                            <td class="td-label">{libelle}</td>
                            <td class="td-amount">-{montant:.2f} €</td>
                        </tr>
"""

    html += """
                    </tbody>
                </table>
"""

    html += """
            </div>
        </div>

        <div class="footer">
            🤖 Rapport généré automatiquement par votre Agent Linxo
        </div>
    </div>
</body>
</html>
"""

    return html
