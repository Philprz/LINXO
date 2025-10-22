#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module de formatage des rapports budgétaires
Génère des rapports visuels et engageants
"""

from datetime import datetime
import calendar


def generer_barre_progression(pourcentage, largeur=20):
    """
    Génère une barre de progression visuelle

    Args:
        pourcentage: Pourcentage (0-100)
        largeur: Largeur de la barre en caractères

    Returns:
        str: Barre de progression formatée
    """
    rempli = int((pourcentage / 100) * largeur)
    vide = largeur - rempli

    if pourcentage >= 100:
        symbole = '█'
    elif pourcentage >= 80:
        symbole = '▓'
    else:
        symbole = '▒'

    barre = symbole * rempli + '░' * vide
    return f"[{barre}] {pourcentage:.0f}%"


def formater_sms(total_depenses, budget_max, reste, pourcentage):
    """
    Formate un SMS court et visuel

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

    # Emoji selon le statut
    if reste < 0:
        emoji = "🔴"
        statut = "ALERTE"
    elif pourcentage >= 80:
        emoji = "🟠"
        statut = "ATTENTION"
    else:
        emoji = "🟢"
        statut = "OK"

    # Construction du message
    if reste < 0:
        message = f"{emoji} {statut} Budget\n"
        message += f"{total_depenses:.0f}€/{budget_max:.0f}€\n"
        message += f"Depassement: {abs(reste):.0f}€\n"
        message += f"J{jour_actuel}/{dernier_jour}"
    else:
        message = f"{emoji} Budget {statut}\n"
        message += f"{total_depenses:.0f}€/{budget_max:.0f}€ ({pourcentage:.0f}%)\n"
        message += f"Reste: {reste:.0f}€\n"
        message += f"J{jour_actuel}/{dernier_jour}"

    return message


def formater_email_html(analyse, budget_max, conseil):
    """
    Génère un email HTML moderne et responsive (style épuré)

    Args:
        analyse: Résultat de l'analyse
        budget_max: Budget maximum
        conseil: Conseil généré

    Returns:
        str: HTML formaté
    """
    now = datetime.now()
    jour_actuel = now.day
    dernier_jour = calendar.monthrange(now.year, now.month)[1]

    total_depenses = analyse['total_variables']
    reste = budget_max - total_depenses
    pourcentage = (total_depenses / budget_max * 100) if budget_max > 0 else 0

    # Couleur selon le statut
    if reste < 0:
        couleur_reste = "#dc3545"  # Rouge
        couleur_barre = "#dc3545"
    elif pourcentage >= 80:
        couleur_reste = "#fd7e14"  # Orange
        couleur_barre = "#fd7e14"
    else:
        couleur_reste = "#28a745"  # Vert
        couleur_barre = "#7c69ef"  # Bleu/violet

    # Calcul du budget par jour restant
    jours_restants = dernier_jour - jour_actuel
    budget_jour = reste / jours_restants if jours_restants > 0 else 0

    html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;
            line-height: 1.5;
            color: #333;
            margin: 0;
            padding: 0;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 600px;
            margin: 0 auto;
            background-color: white;
        }}
        .header {{
            background: linear-gradient(135deg, #7c69ef 0%, #a78bfa 100%);
            color: white;
            padding: 40px 30px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 26px;
            font-weight: 600;
        }}
        .header .date {{
            margin-top: 8px;
            font-size: 15px;
            opacity: 0.95;
        }}
        .content {{
            padding: 30px 20px;
        }}
        .status-card {{
            background-color: {couleur_statut};
            color: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            margin-bottom: 25px;
        }}
        .status-card h2 {{
            margin: 0 0 10px 0;
            font-size: 22px;
        }}
        .status-card .emoji {{
            font-size: 40px;
            display: block;
            margin-bottom: 10px;
        }}
        .metric-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
            margin-bottom: 25px;
        }}
        .metric-card {{
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }}
        .metric-card .label {{
            font-size: 12px;
            color: #6c757d;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 5px;
        }}
        .metric-card .value {{
            font-size: 24px;
            font-weight: 700;
            color: #333;
        }}
        .metric-card .subvalue {{
            font-size: 14px;
            color: #6c757d;
            margin-top: 3px;
        }}
        .progress-section {{
            margin-bottom: 25px;
        }}
        .progress-label {{
            display: flex;
            justify-content: space-between;
            margin-bottom: 8px;
            font-size: 14px;
            font-weight: 500;
        }}
        .progress-bar {{
            height: 30px;
            background-color: #e9ecef;
            border-radius: 15px;
            overflow: hidden;
            position: relative;
        }}
        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, {couleur_statut} 0%, {couleur_statut}dd 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: 600;
            font-size: 14px;
            transition: width 0.3s ease;
        }}
        .conseil-box {{
            background-color: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 25px;
        }}
        .conseil-box h3 {{
            margin: 0 0 10px 0;
            color: #856404;
            font-size: 16px;
        }}
        .conseil-box p {{
            margin: 5px 0;
            color: #856404;
            line-height: 1.5;
        }}
        .section {{
            margin-bottom: 25px;
        }}
        .section h3 {{
            font-size: 18px;
            margin-bottom: 15px;
            color: #333;
            border-bottom: 2px solid #667eea;
            padding-bottom: 8px;
        }}
        .transaction-item {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px 0;
            border-bottom: 1px solid #e9ecef;
        }}
        .transaction-item:last-child {{
            border-bottom: none;
        }}
        .transaction-label {{
            flex: 1;
            font-size: 14px;
        }}
        .transaction-amount {{
            font-weight: 600;
            color: #dc3545;
        }}
        .footer {{
            background-color: #f8f9fa;
            padding: 20px;
            text-align: center;
            font-size: 12px;
            color: #6c757d;
        }}
        .highlight {{
            background-color: #fff3cd;
            padding: 2px 6px;
            border-radius: 4px;
            font-weight: 600;
        }}
        @media (max-width: 600px) {{
            .metric-grid {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>💰 Rapport Budget Linxo</h1>
            <div class="date">{now.strftime('%d %B %Y à %H:%M')}</div>
        </div>

        <div class="content">
            <div class="status-card">
                <span class="emoji">{emoji}</span>
                <h2>{statut}</h2>
            </div>

            <div class="metric-grid">
                <div class="metric-card">
                    <div class="label">Budget mensuel</div>
                    <div class="value">{budget_max:.0f}€</div>
                </div>
                <div class="metric-card">
                    <div class="label">Dépensé</div>
                    <div class="value">{total_depenses:.0f}€</div>
                    <div class="subvalue">{pourcentage:.1f}% utilisé</div>
                </div>
                <div class="metric-card">
                    <div class="label">{"Dépassement" if reste < 0 else "Reste"}</div>
                    <div class="value">{abs(reste):.0f}€</div>
                </div>
                <div class="metric-card">
                    <div class="label">Budget/jour</div>
                    <div class="value">{budget_jour:.0f}€</div>
                    <div class="subvalue">{jours_restants} jours restants</div>
                </div>
            </div>

            <div class="progress-section">
                <div class="progress-label">
                    <span>Progression du mois</span>
                    <span>Jour {jour_actuel}/{dernier_jour}</span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: {min(pourcentage, 100):.1f}%">
                        {pourcentage:.0f}%
                    </div>
                </div>
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
                <h3>📊 Répartition des dépenses</h3>
"""

    # Top 5 des dépenses variables
    depenses_triees = sorted(analyse['depenses_variables'], key=lambda x: abs(x['montant']), reverse=True)[:5]
    for dep in depenses_triees:
        html += f"""
                <div class="transaction-item">
                    <div class="transaction-label">{dep['libelle'][:40]}</div>
                    <div class="transaction-amount">{dep['montant']:.2f}€</div>
                </div>
"""

    html += f"""
            </div>

            <div class="section">
                <h3>📈 Résumé</h3>
                <p style="line-height: 1.8;">
                    • <strong>Dépenses fixes:</strong> {analyse['total_fixes']:.2f}€ ({len(analyse['depenses_fixes'])} transactions)<br>
                    • <strong>Dépenses variables:</strong> {analyse['total_variables']:.2f}€ ({len(analyse['depenses_variables'])} transactions)<br>
                    • <strong>Total général:</strong> {analyse['total']:.2f}€
                </p>
            </div>
        </div>

        <div class="footer">
            🤖 Rapport généré automatiquement par votre Agent Linxo<br>
            {now.strftime('%d/%m/%Y à %H:%M')}
        </div>
    </div>
</body>
</html>
"""

    return html


def formater_email_texte(analyse, budget_max, conseil):
    """
    Génère un email texte lisible (fallback si HTML non supporté)

    Args:
        analyse: Résultat de l'analyse
        budget_max: Budget maximum
        conseil: Conseil généré

    Returns:
        str: Texte formaté
    """
    now = datetime.now()
    jour_actuel = now.day
    dernier_jour = calendar.monthrange(now.year, now.month)[1]

    total_depenses = analyse['total_variables']
    reste = budget_max - total_depenses
    pourcentage = (total_depenses / budget_max * 100) if budget_max > 0 else 0

    # Emoji selon le statut
    if reste < 0:
        emoji = "🔴"
        statut = "ALERTE"
    elif pourcentage >= 80:
        emoji = "🟠"
        statut = "ATTENTION"
    else:
        emoji = "🟢"
        statut = "OK"

    jours_restants = dernier_jour - jour_actuel
    budget_jour = reste / jours_restants if jours_restants > 0 else 0

    barre = generer_barre_progression(pourcentage)

    texte = f"""
╔════════════════════════════════════════════════════════════════╗
║             💰 RAPPORT BUDGET LINXO                            ║
║             {now.strftime('%d %B %Y à %H:%M')}                              ║
╚════════════════════════════════════════════════════════════════╝

{emoji} STATUT: {statut}

┌────────────────────────────────────────────────────────────────┐
│ BUDGET DU MOIS                                                 │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  Budget mensuel:         {budget_max:>10.2f}€                        │
│  Dépensé:                {total_depenses:>10.2f}€                        │
│  {"Dépassement:" if reste < 0 else "Reste:"}              {abs(reste):>10.2f}€                        │
│                                                                │
│  {barre}                 │
│                                                                │
│  Budget par jour:        {budget_jour:>10.2f}€                        │
│  Jours restants:         {jours_restants:>10} jours                     │
│  Jour {jour_actuel}/{dernier_jour} du mois                                          │
│                                                                │
└────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────┐
│ 💡 CONSEIL DE VOTRE AGENT BUDGET                               │
├────────────────────────────────────────────────────────────────┤
│                                                                │
"""

    for ligne in conseil.split('\n'):
        if ligne.strip():
            texte += f"│  {ligne:<60} │\n"

    texte += """│                                                                │
└────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────┐
│ 📊 TOP 5 DÉPENSES VARIABLES                                    │
├────────────────────────────────────────────────────────────────┤
"""

    # Top 5 des dépenses variables
    depenses_triees = sorted(analyse['depenses_variables'], key=lambda x: abs(x['montant']), reverse=True)[:5]
    for i, dep in enumerate(depenses_triees, 1):
        libelle = dep['libelle'][:35]
        montant = dep['montant']
        texte += f"│  {i}. {libelle:<35} {montant:>10.2f}€         │\n"

    texte += f"""└────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────┐
│ 📈 RÉSUMÉ                                                      │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  Dépenses fixes:         {analyse['total_fixes']:>10.2f}€  ({len(analyse['depenses_fixes'])} transactions)   │
│  Dépenses variables:     {analyse['total_variables']:>10.2f}€  ({len(analyse['depenses_variables'])} transactions)   │
│  ────────────────────────────────────────────────────────     │
│  TOTAL GÉNÉRAL:          {analyse['total']:>10.2f}€                        │
│                                                                │
└────────────────────────────────────────────────────────────────┘

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🤖 Rapport généré automatiquement par votre Agent Linxo
   {now.strftime('%d/%m/%Y à %H:%M')}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

    return texte
