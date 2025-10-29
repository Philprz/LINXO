#!/bin/bash
# Script de smoke test pour le développement
# Teste la génération de rapports et le serveur

set -e

# Couleurs
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "═══════════════════════════════════════════════════════════════"
echo "  SMOKE TEST - LINXO REPORTS"
echo "═══════════════════════════════════════════════════════════════"
echo

# Configuration
TEST_PORT=8899
TEST_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FIXTURE_CSV="$TEST_DIR/tests/fixtures/expenses_sample.csv"

echo -e "${YELLOW}[INFO]${NC} Répertoire de test: $TEST_DIR"
echo

# Vérifier que le venv est activé
if [ -z "$VIRTUAL_ENV" ]; then
    echo -e "${RED}[ERREUR]${NC} Virtualenv non activé"
    echo "Activez-le avec: source .venv/bin/activate"
    exit 1
fi

# Étape 1: Créer un CSV de test si nécessaire
echo -e "${GREEN}[1/5]${NC} Préparation des données de test..."

mkdir -p "$TEST_DIR/tests/fixtures"

if [ ! -f "$FIXTURE_CSV" ]; then
    echo "Création d'un CSV de test..."
    cat > "$FIXTURE_CSV" << 'EOF'
Date;Libellé;Montant;Catégorie;Notes;Nom du compte;Labels
15/01/2025;CARREFOUR MARKET;-45.50;Alimentation;;Compte Courant;
14/01/2025;STATION TOTAL;-60.00;Transport;;Compte Courant;
13/01/2025;RESTAURANT LE PARIS;-35.00;Restaurants;;Compte Courant;
12/01/2025;EDF FACTURE;-85.00;Logement;;Compte Courant;Récurrent
11/01/2025;SNCF BILLET;-25.00;Transport;;Compte Courant;
10/01/2025;AUCHAN SUPERMARCHE;-78.30;Alimentation;;Compte Courant;
09/01/2025;NETFLIX ABONNEMENT;-13.49;Abonnements;;Compte Courant;Récurrent
08/01/2025;PHARMACIE CENTRALE;-22.50;Santé;;Compte Courant;
EOF
    echo -e "${GREEN}✓${NC} CSV de test créé"
else
    echo -e "${GREEN}✓${NC} CSV de test existant"
fi

echo

# Étape 2: Générer les rapports
echo -e "${GREEN}[2/5]${NC} Génération des rapports HTML..."

cd "$TEST_DIR"

python << 'PYTHON_EOF'
import pandas as pd
import os
import sys
from pathlib import Path
from datetime import date

sys.path.insert(0, str(Path.cwd()))

try:
    from linxo_agent.reports import build_daily_report

    # Lire le CSV de test
    df = pd.read_csv('tests/fixtures/expenses_sample.csv', sep=';', encoding='utf-8')

    # Générer les rapports
    os.environ['REPORTS_BASE_URL'] = 'http://localhost:8899/reports'
    os.environ['REPORTS_SIGNING_KEY'] = 'test_key_for_smoke_test'

    report_index = build_daily_report(
        df,
        report_date=date.today(),
        base_url='http://localhost:8899/reports',
        signing_key='test_key_for_smoke_test'
    )

    print(f"✓ Rapports générés: {report_index.base_dir}")
    print(f"  - {len(report_index.families)} familles")
    print(f"  - {report_index.total_transactions} transactions")
    print(f"  - Total: {report_index.grand_total:.2f}€")

    # Sauvegarder les infos pour le test
    with open('/tmp/linxo_smoke_test.txt', 'w') as f:
        f.write(f"{report_index.base_dir}\n")
        f.write(f"{len(report_index.families)}\n")
        f.write(f"{report_index.grand_total:.2f}\n")
        for family in report_index.families[:3]:
            f.write(f"{family['name']}\t{family['total']:.2f}€\n")

except Exception as e:
    print(f"[ERREUR] {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
PYTHON_EOF

if [ $? -ne 0 ]; then
    echo -e "${RED}[ERREUR]${NC} Échec de la génération des rapports"
    exit 1
fi

echo

# Étape 3: Démarrer le serveur en arrière-plan
echo -e "${GREEN}[3/5]${NC} Démarrage du serveur de test..."

export REPORTS_BASE_URL="http://localhost:$TEST_PORT/reports"
export REPORTS_BASIC_USER="test"
export REPORTS_BASIC_PASS="testpass"
export REPORTS_SIGNING_KEY="test_key_for_smoke_test"
export REPORTS_PORT="$TEST_PORT"

# Démarrer uvicorn en arrière-plan
python -m uvicorn linxo_agent.report_server.app:app --host 127.0.0.1 --port $TEST_PORT > /tmp/linxo_server_test.log 2>&1 &
SERVER_PID=$!

echo -e "${GREEN}✓${NC} Serveur démarré (PID: $SERVER_PID)"

# Attendre que le serveur soit prêt
echo -n "Attente du serveur..."
for i in {1..10}; do
    if curl -s "http://127.0.0.1:$TEST_PORT/healthz" > /dev/null 2>&1; then
        echo -e " ${GREEN}OK${NC}"
        break
    fi
    sleep 1
    echo -n "."
    if [ $i -eq 10 ]; then
        echo -e " ${RED}TIMEOUT${NC}"
        kill $SERVER_PID 2>/dev/null
        cat /tmp/linxo_server_test.log
        exit 1
    fi
done

echo

# Étape 4: Tester les endpoints
echo -e "${GREEN}[4/5]${NC} Tests des endpoints..."

# Test health check
echo -n "  - Health check... "
if curl -s "http://127.0.0.1:$TEST_PORT/healthz" | grep -q '"status":"ok"'; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC}"
    kill $SERVER_PID 2>/dev/null
    exit 1
fi

# Test page d'accueil avec auth
echo -n "  - Page d'accueil (avec auth)... "
if curl -s -u test:testpass "http://127.0.0.1:$TEST_PORT/" | grep -q "Linxo Report Server"; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC}"
    kill $SERVER_PID 2>/dev/null
    exit 1
fi

# Test sans auth (doit échouer)
echo -n "  - Protection sans auth... "
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:$TEST_PORT/")
if [ "$HTTP_CODE" == "401" ]; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗ (code: $HTTP_CODE)${NC}"
    kill $SERVER_PID 2>/dev/null
    exit 1
fi

# Test rapport index
REPORT_DATE=$(date +%Y-%m-%d)
echo -n "  - Rapport index... "
if curl -s -u test:testpass "http://127.0.0.1:$TEST_PORT/reports/$REPORT_DATE/index.html" | grep -q "Rapport Budget"; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC}"
    kill $SERVER_PID 2>/dev/null
    exit 1
fi

echo

# Étape 5: Afficher le résumé
echo -e "${GREEN}[5/5]${NC} Résumé du test..."

if [ -f /tmp/linxo_smoke_test.txt ]; then
    echo
    echo "Rapports générés:"
    tail -n 3 /tmp/linxo_smoke_test.txt | while read line; do
        echo "  - $line"
    done
fi

echo
echo "URLs de test (serveur actif):"
echo "  - Health:  http://127.0.0.1:$TEST_PORT/healthz"
echo "  - Index:   http://127.0.0.1:$TEST_PORT/reports/$REPORT_DATE/index.html"
echo "  - Auth:    test / testpass"
echo

# Arrêter le serveur
echo -n "Arrêt du serveur... "
kill $SERVER_PID 2>/dev/null
wait $SERVER_PID 2>/dev/null
echo -e "${GREEN}✓${NC}"

# Nettoyage
rm -f /tmp/linxo_smoke_test.txt /tmp/linxo_server_test.log

echo
echo "═══════════════════════════════════════════════════════════════"
echo -e "${GREEN}  SMOKE TEST RÉUSSI ✓${NC}"
echo "═══════════════════════════════════════════════════════════════"
echo
