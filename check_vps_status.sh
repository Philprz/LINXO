#!/bin/bash
# Script de vérification complète du VPS

VPS_HOST="linxo@152.228.218.1"

echo "========================================"
echo "VÉRIFICATION COMPLÈTE DU VPS LINXO"
echo "========================================"
echo ""

# 1. Vérifier la connexion SSH
echo "1. Test de connexion SSH..."
if ssh -o ConnectTimeout=10 $VPS_HOST "echo 'Connexion OK'" 2>/dev/null; then
    echo "   ✓ Connexion SSH : OK"
else
    echo "   ✗ Connexion SSH : ÉCHEC"
    exit 1
fi
echo ""

# 2. Vérifier le cron
echo "2. Configuration du cron..."
ssh $VPS_HOST "crontab -l 2>/dev/null | grep -E '(linxo|LINXO|run_)' || echo 'Aucun cron trouvé'"
echo ""

# 3. Vérifier le service cron
echo "3. Service cron..."
ssh $VPS_HOST "systemctl is-active cron" | grep -q "active" && echo "   ✓ Service cron : actif" || echo "   ✗ Service cron : inactif"
echo ""

# 4. Vérifier la structure des dossiers
echo "4. Structure des dossiers..."
ssh $VPS_HOST "ls -ld ~/LINXO" 2>/dev/null && echo "   ✓ Dossier ~/LINXO : existe" || echo "   ✗ Dossier ~/LINXO : manquant"
ssh $VPS_HOST "ls -ld ~/LINXO/venv" 2>/dev/null && echo "   ✓ Virtualenv : existe" || echo "   ✗ Virtualenv : manquant"
ssh $VPS_HOST "ls -ld ~/LINXO/logs" 2>/dev/null && echo "   ✓ Dossier logs : existe" || echo "   ✗ Dossier logs : manquant"
ssh $VPS_HOST "ls -ld /var/www/html/reports" 2>/dev/null && echo "   ✓ Dossier rapports web : existe" || echo "   ✗ Dossier rapports web : manquant"
echo ""

# 5. Vérifier les fichiers récents
echo "5. Fichiers CSV récents..."
ssh $VPS_HOST "ls -lt ~/LINXO/data/*.csv 2>/dev/null | head -3 || echo '   Aucun fichier CSV dans data/'"
ssh $VPS_HOST "ls -lt ~/LINXO/downloads/*.csv 2>/dev/null | head -3 || echo '   Aucun fichier CSV dans downloads/'"
echo ""

# 6. Vérifier les logs récents
echo "6. Logs récents..."
ssh $VPS_HOST "ls -lt ~/LINXO/logs/*.log 2>/dev/null | head -5 || echo '   Aucun fichier log'"
echo ""

# 7. Vérifier le dernier log cron
echo "7. Contenu du dernier log cron (50 dernières lignes)..."
ssh $VPS_HOST "tail -50 ~/LINXO/logs/cron.log 2>/dev/null || echo '   Fichier cron.log introuvable'"
echo ""

# 8. Vérifier les logs système du cron
echo "8. Logs système cron (dernières exécutions)..."
ssh $VPS_HOST "grep CRON /var/log/syslog 2>/dev/null | grep linxo -i | tail -10 || echo '   Aucune trace dans syslog'"
echo ""

# 9. Vérifier Nginx
echo "9. Service Nginx..."
ssh $VPS_HOST "systemctl is-active nginx" | grep -q "active" && echo "   ✓ Nginx : actif" || echo "   ✗ Nginx : inactif"
echo ""

# 10. Vérifier les rapports générés
echo "10. Rapports HTML générés..."
ssh $VPS_HOST "ls -lt /var/www/html/reports/ 2>/dev/null | head -5 || echo '   Aucun rapport trouvé'"
echo ""

# 11. Vérifier le fichier .env
echo "11. Configuration .env..."
ssh $VPS_HOST "test -f ~/LINXO/.env && echo '   ✓ Fichier .env : existe' || echo '   ✗ Fichier .env : manquant'"
echo ""

# 12. Test Python et dépendances
echo "12. Environnement Python..."
ssh $VPS_HOST "~/LINXO/venv/bin/python3 --version" && echo "   ✓ Python : OK"
ssh $VPS_HOST "~/LINXO/venv/bin/pip list | grep -E '(selenium|pandas|jinja2)' | head -5" || echo "   Vérifier les dépendances"
echo ""

echo "========================================"
echo "RÉSUMÉ DE LA VÉRIFICATION"
echo "========================================"
echo ""
echo "Pour tester manuellement l'exécution complète :"
echo "  ssh $VPS_HOST 'cd ~/LINXO && ./venv/bin/python3 run_linxo_e2e.py'"
echo ""
echo "Pour voir les logs en temps réel :"
echo "  ssh $VPS_HOST 'tail -f ~/LINXO/logs/cron.log'"
echo ""
echo "Pour vérifier demain après 10h :"
echo "  ssh $VPS_HOST 'tail -100 ~/LINXO/logs/cron.log'"
