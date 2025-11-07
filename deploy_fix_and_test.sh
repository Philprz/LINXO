#!/bin/bash
# Script de déploiement et test du fix de filtrage CSV
# Ce script déploie les changements sur le VPS et lance un test

set -e

echo "=========================================="
echo "DEPLOIEMENT ET TEST DU FIX FILTRAGE CSV"
echo "=========================================="

VPS_HOST="vps-6e2f6679.vps.ovh.net"
VPS_USER="linxo"
VPS_DIR="/home/linxo/LINXO"

echo ""
echo "[1/4] Push des changements vers Git..."
git push origin main

echo ""
echo "[2/4] Connexion au VPS et pull des changements..."
ssh ${VPS_USER}@${VPS_HOST} << 'ENDSSH'
cd /home/linxo/LINXO
echo "Git pull..."
git pull origin main

echo ""
echo "Vérification des fichiers modifiés..."
ls -lh linxo_agent/linxo_connexion.py
ls -lh linxo_agent/run_linxo_e2e.py
ls -lh linxo_agent/csv_filter.py
ENDSSH

echo ""
echo "[3/4] Lancement du test sur le VPS..."
ssh ${VPS_USER}@${VPS_HOST} << 'ENDSSH'
cd /home/linxo/LINXO

echo ""
echo "=========================================="
echo "EXECUTION DU TEST"
echo "=========================================="
source .venv/bin/activate
python linxo_agent.py --skip-notifications

echo ""
echo "=========================================="
echo "VERIFICATION DES RESULTATS"
echo "=========================================="
echo ""
echo "Le rapport devrait maintenant montrer uniquement les transactions de novembre 2025"
echo "et non plus les 679k€ de transactions historiques depuis 2016-2017."
echo ""
ENDSSH

echo ""
echo "[4/4] Test terminé!"
echo ""
echo "=========================================="
echo "INSTRUCTIONS DE VERIFICATION"
echo "=========================================="
echo "1. Vérifiez que le rapport affiche ~1500€ et non 679k€"
echo "2. Vérifiez les logs de filtrage CSV affichant:"
echo "   - [ETAPE 6] Filtrage du CSV pour le mois courant..."
echo "   - [INFO] Periode dans le CSV AVANT filtrage: XX/XX/XXXX -> XX/XX/XXXX"
echo "   - [SUCCESS] CSV filtre pour le mois courant"
echo "   - [INFO] Periode dans le CSV APRES filtrage: 01/11/2025 -> XX/11/2025"
echo ""
echo "Si le problème persiste, vérifiez le dernier rapport:"
echo "ssh ${VPS_USER}@${VPS_HOST} 'cat /home/linxo/LINXO/reports/rapport_linxo_*.txt | tail -100'"
