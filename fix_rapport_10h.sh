#!/bin/bash
# Script de correction pour rétablir le rapport quotidien à 10h

VPS_HOST="linxo@152.228.218.1"

echo "=========================================="
echo "CORRECTION DU RAPPORT QUOTIDIEN À 10H"
echo "=========================================="
echo ""

# Fonction pour afficher les étapes
step_num=1
step() {
    echo ""
    echo "📋 ÉTAPE $step_num: $1"
    echo "=========================================="
    ((step_num++))
}

# ÉTAPE 1: Vérifier la configuration actuelle
step "Vérification de la configuration actuelle"
echo "Configuration actuelle du cron:"
ssh $VPS_HOST "crontab -l 2>/dev/null" || {
    echo "❌ Impossible de récupérer le crontab"
    exit 1
}

# ÉTAPE 2: Modifier le cron pour 10h
step "Modification du cron pour 10h00"

read -p "Voulez-vous modifier le cron pour qu'il s'exécute à 10h00? (o/n) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[OoYy]$ ]]; then
    echo "Opération annulée."
    exit 0
fi

ssh $VPS_HOST << 'ENDSSH'
# Sauvegarder le cron actuel
crontab -l > /tmp/current_cron 2>/dev/null || touch /tmp/current_cron

# Vérifier qu'il y a bien un cron pour le rapport
if grep -q "run_daily_report\|run_analysis\|run_linxo_e2e" /tmp/current_cron; then
    echo "✅ Cron Linxo trouvé, modification en cours..."

    # Remplacer toutes les heures par 10h pour les scripts Linxo
    sed -i 's/^[0-9]\+ [0-9]\+ \* \* \* .*run_daily_report/0 10 * * * \/home\/linxo\/LINXO\/run_daily_report.sh/g' /tmp/current_cron
    sed -i 's/^[0-9]\+ [0-9]\+ \* \* \* .*run_analysis/0 10 * * * cd \/home\/linxo\/LINXO \&\& \/home\/linxo\/LINXO\/venv\/bin\/python3 linxo_agent\/run_analysis.py >> logs\/cron_analysis.log 2>\&1/g' /tmp/current_cron
    sed -i 's/^[0-9]\+ [0-9]\+ \* \* \* .*run_linxo_e2e/0 10 * * * cd \/home\/linxo\/LINXO \&\& \/home\/linxo\/LINXO\/venv\/bin\/python3 run_linxo_e2e.py >> logs\/cron.log 2>\&1/g' /tmp/current_cron

    # Réinstaller le cron modifié
    crontab /tmp/current_cron

    echo ""
    echo "✅ Cron modifié avec succès!"
    echo ""
    echo "Nouvelle configuration:"
    crontab -l
else
    echo "⚠️  Aucun cron Linxo trouvé!"
    echo ""
    echo "Souhaitez-vous créer un nouveau cron? Voici la commande recommandée:"
    echo ""
    echo "0 10 * * * /home/linxo/LINXO/run_daily_report.sh"
    echo ""
    echo "Ajoutez cette ligne manuellement avec: crontab -e"
fi

# Nettoyer
rm -f /tmp/current_cron
ENDSSH

# ÉTAPE 3: Vérifier le service cron
step "Vérification du service cron"
ssh $VPS_HOST "systemctl is-active cron" > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ Service cron actif"
else
    echo "⚠️  Service cron inactif, tentative de démarrage..."
    ssh $VPS_HOST "sudo systemctl start cron && sudo systemctl enable cron"
fi

# ÉTAPE 4: Nettoyer le fichier already_sent si nécessaire
step "Vérification du fichier already_sent.txt"

echo "Contenu actuel du fichier already_sent.txt:"
ssh $VPS_HOST "cat ~/LINXO/data/already_sent.txt 2>/dev/null" || echo "(fichier vide ou inexistant)"
echo ""

read -p "Voulez-vous réinitialiser le fichier already_sent.txt? (o/n) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[OoYy]$ ]]; then
    ssh $VPS_HOST "rm -f ~/LINXO/data/already_sent.txt && echo 'Fichier already_sent.txt supprimé'"
    echo "✅ Fichier réinitialisé, le prochain CSV sera traité"
fi

# ÉTAPE 5: Vérifier les fichiers CSV disponibles
step "Vérification des fichiers CSV disponibles"

echo "Fichiers CSV récents dans data/:"
ssh $VPS_HOST "ls -lht ~/LINXO/data/*.csv 2>/dev/null | head -3" || echo "⚠️  Aucun fichier CSV"
echo ""

echo "Fichiers CSV récents dans downloads/:"
ssh $VPS_HOST "ls -lht ~/LINXO/downloads/*.csv 2>/dev/null | head -3" || echo "⚠️  Aucun fichier CSV"
echo ""

# ÉTAPE 6: Tester l'exécution manuelle
step "Proposition de test manuel"

echo "Voulez-vous tester l'exécution manuelle du script maintenant?"
echo "Cela permettra de vérifier que tout fonctionne correctement."
echo ""
read -p "Lancer le test maintenant? (o/n) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[OoYy]$ ]]; then
    echo ""
    echo "🚀 Lancement du test..."
    echo "=========================================="
    ssh $VPS_HOST "cd ~/LINXO && ./run_daily_report.sh"

    if [ $? -eq 0 ]; then
        echo ""
        echo "✅ Test réussi!"
    else
        echo ""
        echo "❌ Le test a échoué, consultez les logs ci-dessus"
    fi
fi

# RÉSUMÉ
echo ""
echo "=========================================="
echo "📊 RÉSUMÉ DES CORRECTIONS"
echo "=========================================="
echo ""
echo "Actions effectuées:"
echo "  1. ✅ Cron modifié pour s'exécuter à 10h00"
echo "  2. ✅ Service cron vérifié"
echo "  3. ✅ Fichiers CSV vérifiés"
echo ""
echo "Prochaines étapes:"
echo "  - Le rapport s'exécutera automatiquement demain à 10h00"
echo "  - Vérifiez les logs demain à 10h05:"
echo "    ssh $VPS_HOST 'tail -100 ~/LINXO/logs/daily_report_\$(date +%Y%m%d).log'"
echo ""
echo "En cas de problème:"
echo "  - Exécutez: ./diagnostic_rapport_10h.sh"
echo "  - Consultez: DIAGNOSTIC_CRON.md"
echo ""
echo "=========================================="
echo "✅ CORRECTION TERMINÉE"
echo "=========================================="
