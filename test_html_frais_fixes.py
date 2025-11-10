#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test de l'affichage des frais fixes dans le rapport HTML
"""

import sys
from pathlib import Path

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent))

from jinja2 import Environment, FileSystemLoader, select_autoescape


def test_html_frais_fixes():
    """Test que le template HTML affiche correctement les frais fixes"""

    print("=" * 80)
    print("TEST AFFICHAGE FRAIS FIXES DANS HTML")
    print("=" * 80)

    # Configuration Jinja2
    project_root = Path(__file__).parent
    templates_dir = project_root / "templates" / "reports"

    if not templates_dir.exists():
        print(f"[ERREUR] Dossier templates non trouvé: {templates_dir}")
        return False

    print(f"[OK] Dossier templates: {templates_dir}")

    env = Environment(
        loader=FileSystemLoader(templates_dir),
        autoescape=select_autoescape(["html", "xml"]),
    )

    # Charger le template index
    try:
        index_template = env.get_template("index.html.j2")
        print("[OK] Template index.html.j2 chargé")
    except Exception as e:
        print(f"[ERREUR] Impossible de charger le template: {e}")
        return False

    # Données de test
    context = {
        "report_date": "2025-11-10",
        "grand_total": 5040.70,
        "total_transactions": 115,
        "total_fixes": 2478.48,  # NOUVEAU
        "total_variables": 2562.22,  # NOUVEAU
        "budget_max": 1500,
        "jour_actuel": 10,
        "dernier_jour": 30,
        "avancement_mois": 33.3,
        "pourcentage": 170.8,
        "couleur_barre_variables": "#dc3545",
        "reste": -1062.22,
        "prediction_fin_mois": 7686.66,
        "prediction_depassement": 6186.66,
        "prediction_pourcentage": 512.4,
        "couleur_prediction": "#dc3545",
        "message_prediction": "⚠️ Vous risquez de dépasser de 6186.66 €",
        "jours_restants": 20,
        "families": [
            {"name": "Alimentation", "count": 25, "total": 450.50, "url": "/2025-11-10/family-alimentation.html"},
            {"name": "Transports", "count": 15, "total": 250.30, "url": "/2025-11-10/family-transports.html"},
        ],
    }

    # Générer le HTML
    try:
        html_output = index_template.render(**context)
        print("[OK] Template rendu avec succès")
    except Exception as e:
        print(f"[ERREUR] Erreur lors du rendu: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Vérifier que les frais fixes sont présents
    print("\n" + "=" * 80)
    print("VERIFICATION DU CONTENU")
    print("=" * 80)

    checks = [
        ("Frais récurrents (fixes)", "💳 Frais récurrents (fixes)" in html_output),
        ("Montant frais fixes", "2478.48 €" in html_output),
        ("Dépenses variables", "🛒 Dépenses variables" in html_output),
        ("Montant dépenses variables", "2562.22 €" in html_output),
        ("Total des dépenses", "5040.70 €" in html_output),
    ]

    all_ok = True
    for check_name, check_result in checks:
        status = "OK" if check_result else "ECHEC"
        print(f"[{status}] {check_name}")
        if not check_result:
            all_ok = False

    # Sauvegarder le HTML de test
    if all_ok:
        output_file = Path("test_html_frais_fixes_output.html")
        output_file.write_text(html_output, encoding="utf-8")
        print(f"\n[OK] HTML de test sauvegardé: {output_file}")

    return all_ok


if __name__ == "__main__":
    success = test_html_frais_fixes()

    print("\n" + "=" * 80)
    print("RESULTAT FINAL")
    print("=" * 80)

    if success:
        print("OK - Le template affiche correctement les frais fixes")
        sys.exit(0)
    else:
        print("ERREUR - Le template ne fonctionne pas correctement")
        sys.exit(1)
