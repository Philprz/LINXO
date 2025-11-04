#!/usr/bin/env python3
"""Test de la fonctionnalité de prédiction de fin de mois."""

import sys
from pathlib import Path

# Ajouter le chemin du module linxo_agent
sys.path.insert(0, str(Path(__file__).parent / "linxo_agent"))

from datetime import datetime
from jinja2 import Environment, FileSystemLoader, select_autoescape
import calendar

def test_prediction():
    """Test le calcul de la prédiction."""
    print("="*80)
    print("TEST DE LA PREDICTION DE FIN DE MOIS")
    print("="*80)

    # Données de test
    now = datetime.now()
    jours_dans_mois = calendar.monthrange(now.year, now.month)[1]
    jour_actuel = now.day
    jours_restants = jours_dans_mois - jour_actuel

    # Simulations de dépenses
    scenarios = [
        {"nom": "Dépenses normales", "total": 800, "budget": 1500},
        {"nom": "Dépenses élevées", "total": 1200, "budget": 1500},
        {"nom": "Dépassement imminent", "total": 1400, "budget": 1500},
    ]

    print(f"\nDate actuelle: {now.strftime('%d/%m/%Y')}")
    print(f"Jour {jour_actuel}/{jours_dans_mois} du mois")
    print(f"Jours restants: {jours_restants}")
    print()

    for scenario in scenarios:
        print(f"\n--- {scenario['nom']} ---")
        total_depenses = scenario["total"]
        budget_max = scenario["budget"]

        # Calcul de la prédiction (même logique que dans notifications.py)
        if jour_actuel > 0:
            depense_quotidienne_moyenne = total_depenses / jour_actuel
            prediction_fin_mois = total_depenses + (depense_quotidienne_moyenne * jours_restants)
            prediction_depassement = prediction_fin_mois - budget_max
            prediction_pourcentage = (prediction_fin_mois / budget_max * 100) if budget_max > 0 else 0

            # Couleur de la prédiction
            if prediction_depassement > 0:
                couleur = "ROUGE"
                message = f"Vous risquez de depasser de {abs(prediction_depassement):.2f} €"
            elif prediction_pourcentage > 90:
                couleur = "ORANGE"
                message = f"Attention, vous serez a {prediction_pourcentage:.0f}% du budget"
            else:
                couleur = "VERT"
                message = f"Vous devriez rester sous budget ({prediction_pourcentage:.0f}%)"

            print(f"  Dépenses actuelles: {total_depenses:.2f} €")
            print(f"  Budget: {budget_max:.2f} €")
            print(f"  Dépense quotidienne moyenne: {depense_quotidienne_moyenne:.2f} €/jour")
            print(f"  Prédiction fin de mois: {prediction_fin_mois:.2f} €")
            print(f"  Écart prévu: {prediction_depassement:+.2f} €")
            print(f"  Pourcentage: {prediction_pourcentage:.0f}%")
            print(f"  Couleur: {couleur}")
            print(f"  Message: {message}")

    print("\n" + "="*80)
    print("Test de prediction termine !")
    print("="*80)

    # Test du template email
    print("\n\nTest du rendu du template email...")
    templates_dir = Path(__file__).parent / "templates" / "email"
    env = Environment(
        loader=FileSystemLoader(templates_dir),
        autoescape=select_autoescape(["html", "xml"]),
    )
    template = env.get_template("daily_summary.html.j2")

    # Données fictives pour le test
    avancement_mois = (jour_actuel / jours_dans_mois) * 100.0

    html = template.render(
        report_date=now.strftime("%Y-%m-%d"),
        total_variables=1200.0,
        total_fixes=2500.0,
        budget_max=1500,
        budget_fixes_prevu=3000,
        reste=300.0,
        pourcentage=80.0,
        pourcentage_fixes=83.3,
        couleur_barre_variables="#28a745",
        couleur_barre_fixes="#28a745",
        avancement_mois=avancement_mois,
        prediction_fin_mois=1450.0,
        prediction_depassement=-50.0,
        prediction_pourcentage=96.7,
        couleur_prediction="#fd7e14",
        message_prediction="⚡ Attention, vous serez à 97% du budget",
        jours_restants=jours_restants,
        families=[
            {"name": "Alimentation", "total": 400.0, "url": "#"},
            {"name": "Transport", "total": 200.0, "url": "#"},
        ],
        grand_total=600.0,
        index_url="#",
    )

    # Vérifier que la prédiction est bien dans le HTML
    if "prediction-box" in html and ("Prédiction fin de mois" in html or "prediction-value" in html):
        print("OK Le template email contient bien la section de prediction !")

        # Sauvegarder pour inspection
        output_file = Path(__file__).parent / "test_prediction_output.html"
        output_file.write_text(html, encoding="utf-8")
        print(f"OK HTML genere sauvegarde dans: {output_file}")
    else:
        print("ERREUR Le template email ne contient pas la section de prediction !")
        return False

    return True

if __name__ == "__main__":
    success = test_prediction()
    sys.exit(0 if success else 1)
