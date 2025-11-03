#!/bin/bash
# Script pour corriger l'heure du cron sur le VPS (passer de 20h à 10h)

set -e

VPS_HOST="linxo@152.228.218.1"
NEW_HOUR="10"

echo "========================================="
echo "CORRECTION DE L'HEURE DU CRON SUR LE VPS"
echo "========================================="
echo ""
echo "Configuration actuelle :"
ssh $VPS_HOST "crontab -l 2>/dev/null || echo 'Aucun cron configuré'"
echo ""

read -p "Voulez-vous changer l'heure d'exécution à ${NEW_HOUR}h00 ? (o/n) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[OoYy]$ ]]; then
    echo "Opération annulée."
    exit 0
fi

echo ""
echo "Modification du cron en cours..."

# Se connecter au VPS et modifier le cron
ssh $VPS_HOST << EOF
# Sauvegarder le cron actuel
crontab -l > /tmp/current_cron 2>/dev/null || touch /tmp/current_cron

# Vérifier qu'il y a bien un cron Linxo
if grep -q "run_linxo_e2e.py" /tmp/current_cron || grep -q "run_daily_report" /tmp/current_cron; then
    echo "Cron Linxo trouvé, modification en cours..."

    # Remplacer l'heure dans le cron (change "0 XX" en "0 10")
    sed -i 's/^0 [0-9]\+ \* \* \* .*LINXO/0 ${NEW_HOUR} * * * cd \/home\/linxo\/LINXO \&\& \/home\/linxo\/LINXO\/venv\/bin\/python3 run_linxo_e2e.py >> logs\/cron.log 2>\&1/g' /tmp/current_cron
    sed -i 's/^0 [0-9]\+ \* \* \* .*run_daily_report/0 ${NEW_HOUR} * * * \/home\/linxo\/LINXO\/run_daily_report.sh/g' /tmp/current_cron

    # Réinstaller le cron modifié
    crontab /tmp/current_cron

    echo ""
    echo "✓ Cron modifié avec succès!"
    echo ""
    echo "Nouvelle configuration :"
    crontab -l
else
    echo "ERREUR: Aucun cron Linxo trouvé!"
    echo "Contenu actuel du crontab :"
    cat /tmp/current_cron
    exit 1
fi

# Nettoyer
rm /tmp/current_cron
EOF

echo ""
echo "========================================="
echo "✓ OPÉRATION TERMINÉE"
echo "========================================="
echo ""
echo "Le script s'exécutera maintenant tous les jours à ${NEW_HOUR}h00."
echo ""
echo "Pour vérifier demain :"
echo "  ssh $VPS_HOST 'tail -100 ~/LINXO/logs/cron.log'"
