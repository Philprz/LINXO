#!/bin/bash
# Script de diagnostic pour identifier pourquoi le filtrage CSV ne fonctionne pas sur le VPS

set -e

echo "=========================================="
echo "DIAGNOSTIC VPS - FILTRAGE CSV"
echo "=========================================="

VPS_HOST="vps-6e2f6679.vps.ovh.net"
VPS_USER="linxo"
VPS_DIR="/home/linxo/LINXO"

echo ""
echo "[1/5] Connexion au VPS et vérification de la version Git..."
ssh ${VPS_USER}@${VPS_HOST} << 'ENDSSH'
cd /home/linxo/LINXO

echo "Git status et dernier commit :"
git log -1 --oneline
git status --short

echo ""
echo "=========================================="
ENDSSH

echo ""
echo "[2/5] Vérification des fichiers modifiés..."
ssh ${VPS_USER}@${VPS_HOST} << 'ENDSSH'
cd /home/linxo/LINXO

echo "Contenu de linxo_agent/linxo_connexion.py (lignes 912-940) :"
sed -n '912,940p' linxo_agent/linxo_connexion.py

echo ""
echo "=========================================="
ENDSSH

echo ""
echo "[3/5] Test d'import du module csv_filter..."
ssh ${VPS_USER}@${VPS_HOST} << 'ENDSSH'
cd /home/linxo/LINXO
source .venv/bin/activate

echo "Test d'import Python :"
python3 << 'ENDPYTHON'
import sys
from pathlib import Path

# Ajouter le chemin du module
sys.path.insert(0, str(Path.cwd() / "linxo_agent"))

print("Tentative d'import de csv_filter...")
try:
    from csv_filter import filter_csv_by_month, get_csv_date_range
    print("✅ Import réussi !")
    print(f"   - filter_csv_by_month: {filter_csv_by_month}")
    print(f"   - get_csv_date_range: {get_csv_date_range}")
except ImportError as e:
    print(f"❌ Erreur d'import: {e}")
    import traceback
    traceback.print_exc()
except Exception as e:
    print(f"❌ Erreur: {e}")
    import traceback
    traceback.print_exc()
ENDPYTHON

echo ""
echo "=========================================="
ENDSSH

echo ""
echo "[4/5] Vérification du fichier csv_filter.py..."
ssh ${VPS_USER}@${VPS_HOST} << 'ENDSSH'
cd /home/linxo/LINXO

if [ -f "linxo_agent/csv_filter.py" ]; then
    echo "✅ linxo_agent/csv_filter.py existe"
    echo "   Taille: $(wc -l < linxo_agent/csv_filter.py) lignes"
    echo "   Dernière modification: $(stat -c '%y' linxo_agent/csv_filter.py)"
else
    echo "❌ linxo_agent/csv_filter.py N'EXISTE PAS !"
fi

echo ""
echo "=========================================="
ENDSSH

echo ""
echo "[5/5] Vérification des logs récents..."
ssh ${VPS_USER}@${VPS_HOST} << 'ENDSSH'
cd /home/linxo/LINXO

echo "Dernier rapport généré :"
LATEST_REPORT=$(ls -t reports/rapport_linxo_*.txt 2>/dev/null | head -1)

if [ -n "$LATEST_REPORT" ]; then
    echo "Fichier: $LATEST_REPORT"
    echo ""
    echo "Recherche de logs de filtrage dans le rapport :"
    grep -i "filtrage\|filter\|ETAPE 6" "$LATEST_REPORT" || echo "❌ Aucun log de filtrage trouvé"

    echo ""
    echo "Total affiché dans le rapport :"
    grep "TOTAL VARIABLES\|TOTAL GENERAL" "$LATEST_REPORT" || echo "Non trouvé"
else
    echo "❌ Aucun rapport trouvé"
fi

echo ""
echo "=========================================="
ENDSSH

echo ""
echo "=========================================="
echo "DIAGNOSTIC TERMINÉ"
echo "=========================================="
echo ""
echo "PROCHAINES ÉTAPES :"
echo "1. Si csv_filter.py n'existe pas → Vérifier que 'git pull' a bien récupéré tous les fichiers"
echo "2. Si l'import échoue → Problème de syntaxe dans csv_filter.py"
echo "3. Si les logs ne montrent pas [ETAPE 6] → Le code modifié ne s'exécute pas"
echo "4. Si le total est 679k€ → Le filtrage n'est pas appliqué"
