#!/usr/bin/env python3
"""Script de vérification du calcul des frais fixes"""

import sys
from pathlib import Path
from datetime import datetime

# Ajouter le répertoire linxo_agent au PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent / 'linxo_agent'))

def main():
    print("=" * 70)
    print("Vérification du calcul du Total Prévu pour les Frais Fixes")
    print("=" * 70)

    try:
        from config import get_config

        config = get_config()
        depenses_fixes_ref = config.depenses_data.get('depenses_fixes', [])

        print(f"\nNombre de frais fixes configurés : {len(depenses_fixes_ref)}")

        # Mois actuel
        mois_actuel = datetime.now().month
        print(f"Mois actuel : {mois_actuel}")

        # Calculer le total prévu avec la NOUVELLE logique
        print("\n" + "=" * 70)
        print("Calcul du Total Prévu (nouvelle logique - basé sur config)")
        print("=" * 70)

        total_prevu_config = 0.0
        frais_applicables = []

        for frais in depenses_fixes_ref:
            mois_occurrence = frais.get('mois_occurrence', list(range(1, 13)))
            montant = frais.get('montant', 0.0)
            libelle = frais.get('libelle', 'Sans nom')

            if mois_actuel in mois_occurrence:
                total_prevu_config += montant
                frais_applicables.append({
                    'libelle': libelle,
                    'montant': montant
                })
                print(f"  + {montant:8.2f}€  {libelle[:50]}")

        print("-" * 70)
        print(f"TOTAL PRÉVU (config) : {total_prevu_config:.2f}€")
        print(f"Nombre de frais applicables ce mois : {len(frais_applicables)}")

        # Vérifier que le code dans reports.py utilise bien cette logique
        print("\n" + "=" * 70)
        print("Vérification du code dans reports.py")
        print("=" * 70)

        reports_file = Path(__file__).parent / 'linxo_agent' / 'reports.py'
        with open(reports_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Vérifier la présence de la nouvelle logique
        if 'total_prevu_config' in content:
            print("✓ Variable 'total_prevu_config' trouvée dans reports.py")
        else:
            print("✗ Variable 'total_prevu_config' NON trouvée dans reports.py")
            print("  => Le code n'a pas été mis à jour !")
            return 1

        if 'total_prevu = total_prevu_config' in content:
            print("✓ Affectation 'total_prevu = total_prevu_config' trouvée")
        else:
            print("✗ Affectation correcte NON trouvée")
            print("  => Le code n'utilise pas la nouvelle logique !")
            return 1

        # Vérifier l'ancienne logique (ne devrait plus exister)
        if 'total_prevu = total_preleve + total_en_attente' in content:
            print("⚠️  ATTENTION : Ancienne logique toujours présente !")
            print("  => Le code contient encore l'ancienne formule !")
            return 1
        else:
            print("✓ Ancienne logique absente (bon signe)")

        print("\n" + "=" * 70)
        print("RÉSULTAT")
        print("=" * 70)
        print(f"Le Total Prévu devrait être : {total_prevu_config:.2f}€")
        print("\nSi le rapport HTML affiche un montant différent :")
        print("  1. Le rapport n'a pas été régénéré avec le nouveau code")
        print("  2. Exécutez : python linxo_agent/run_analysis.py <chemin_csv>")
        print("=" * 70)

        return 0

    except Exception as e:
        print(f"\n✗ ERREUR : {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())
