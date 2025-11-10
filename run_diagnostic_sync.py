#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Helper pour exécuter le diagnostic de manière synchrone
Retourne True si le diagnostic a réussi et corrigé le code
"""

import sys
from pathlib import Path

# Ajouter le dossier parent au path
sys.path.insert(0, str(Path(__file__).parent))

from diagnostic_linxo_html import LinxoHTMLDiagnostic


def run_diagnostic_and_fix() -> tuple[bool, str]:
    """
    Execute le diagnostic et retourne le résultat

    Returns:
        tuple: (success, result_message)
            - success: True si le diagnostic a réussi et corrigé le code
            - result_message: Message décrivant le résultat
    """
    try:
        diagnostic = LinxoHTMLDiagnostic()
        success = diagnostic.run_diagnostic()

        if not success:
            return False, "Le diagnostic a échoué (erreur durant l'exécution)"

        # Vérifier si des méthodes fonctionnelles ont été trouvées
        if not diagnostic.results.get('working_methods'):
            return False, "Aucun sélecteur fonctionnel trouvé"

        # Vérifier les recommandations pour voir si le code a été corrigé
        recommendations = diagnostic.results.get('recommendations', [])
        auto_correct_found = any('auto-corrige' in rec.lower() for rec in recommendations)

        if auto_correct_found:
            working_count = len(diagnostic.results['working_methods'])
            return True, f"Code auto-corrigé avec {working_count} nouveaux sélecteurs"
        else:
            return False, "Sélecteurs trouvés mais auto-correction non effectuée"

    except Exception as e:
        return False, f"Erreur durant le diagnostic: {str(e)}"


if __name__ == "__main__":
    success, message = run_diagnostic_and_fix()
    print(f"Résultat: {'SUCCESS' if success else 'FAILED'}")
    print(f"Message: {message}")
    sys.exit(0 if success else 1)
