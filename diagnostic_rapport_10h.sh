#!/bin/bash
# Script de diagnostic pour comprendre pourquoi le rapport n'a pas été envoyé à 10h

VPS_HOST="linxo@152.228.218.1"
TODAY=$(date +%Y%m%d)

echo "=========================================="
echo "DIAGNOSTIC RAPPORT QUOTIDIEN - $(date '+%Y-%m-%d %H:%M:%S')"
echo "=========================================="
echo ""

echo "📋 ÉTAPE 1: Configuration du cron"
echo "=========================================="
ssh $VPS_HOST "crontab -l" 2>&1 || echo "❌ Erreur: Impossible de récupérer le crontab"
echo ""

echo "📋 ÉTAPE 2: Statut du service cron"
echo "=========================================="
ssh $VPS_HOST "systemctl status cron --no-pager" 2>&1 || echo "❌ Erreur: Service cron non accessible"
echo ""

echo "📋 ÉTAPE 3: Logs système du cron (dernières exécutions)"
echo "=========================================="
ssh $VPS_HOST "grep CRON /var/log/syslog | grep -E '(linxo|daily_report|run_analysis)' | tail -20" 2>&1 || echo "⚠️  Aucun log système trouvé"
echo ""

echo "📋 ÉTAPE 4: Logs de l'application (aujourd'hui)"
echo "=========================================="
echo "Fichiers de logs présents aujourd'hui:"
ssh $VPS_HOST "ls -lh ~/LINXO/logs/daily_report_${TODAY}*.log 2>/dev/null" 2>&1 || echo "⚠️  Aucun fichier de log pour aujourd'hui"
echo ""

echo "📋 ÉTAPE 5: Dernier log d'exécution disponible"
echo "=========================================="
ssh $VPS_HOST "ls -lt ~/LINXO/logs/daily_report_*.log 2>/dev/null | head -1" 2>&1 || echo "⚠️  Aucun log disponible"
echo ""
echo "Contenu du dernier log (50 dernières lignes):"
ssh $VPS_HOST "tail -50 \$(ls -t ~/LINXO/logs/daily_report_*.log 2>/dev/null | head -1) 2>&1" || echo "⚠️  Impossible de lire les logs"
echo ""

echo "📋 ÉTAPE 6: Fichiers CSV disponibles"
echo "=========================================="
echo "Fichiers CSV dans data/:"
ssh $VPS_HOST "ls -lht ~/LINXO/data/*.csv 2>/dev/null | head -3" 2>&1 || echo "⚠️  Aucun fichier CSV dans data/"
echo ""
echo "Fichiers CSV dans downloads/:"
ssh $VPS_HOST "ls -lht ~/LINXO/downloads/*.csv 2>/dev/null | head -3" 2>&1 || echo "⚠️  Aucun fichier CSV dans downloads/"
echo ""

echo "📋 ÉTAPE 7: Vérification du fichier de suivi (already_sent)"
echo "=========================================="
ssh $VPS_HOST "cat ~/LINXO/data/already_sent.txt 2>/dev/null" 2>&1 || echo "⚠️  Fichier already_sent.txt inexistant"
echo ""

echo "📋 ÉTAPE 8: Variables d'environnement"
echo "=========================================="
echo "Vérification que .env existe:"
ssh $VPS_HOST "test -f ~/LINXO/.env && echo '✅ Fichier .env présent' || echo '❌ Fichier .env manquant'" 2>&1
echo ""

echo "📋 ÉTAPE 9: Environnement Python"
echo "=========================================="
ssh $VPS_HOST "~/LINXO/venv/bin/python3 --version 2>&1" || echo "❌ Environnement virtuel Python non fonctionnel"
echo ""

echo "📋 ÉTAPE 10: Test manuel du script (simulation)"
echo "=========================================="
echo "Vous pouvez tester manuellement avec:"
echo "  ssh $VPS_HOST 'cd ~/LINXO && ./run_daily_report.sh'"
echo ""

echo "=========================================="
echo "📊 RÉSUMÉ DU DIAGNOSTIC"
echo "=========================================="
echo ""
echo "Points à vérifier:"
echo "1. ⏰ Le cron est-il configuré pour 10h (0 10 * * *)?"
echo "2. ✅ Le service cron est-il actif?"
echo "3. 📁 Y a-t-il un fichier CSV disponible pour aujourd'hui?"
echo "4. 📝 Le fichier already_sent.txt empêche-t-il l'envoi?"
echo "5. 🔧 L'environnement Python est-il fonctionnel?"
echo "6. 📧 Le script s'est-il exécuté mais a échoué lors de l'envoi?"
echo ""
echo "=========================================="
echo "Pour plus d'informations, consultez:"
echo "  - DIAGNOSTIC_CRON.md"
echo "  - VPS_CONFIG.md"
echo "=========================================="
