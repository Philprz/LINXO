#!/bin/bash
# Script pour créer et configurer les répertoires de rapports sur le VPS

VPS_HOST="linxo@152.228.218.1"

echo "========================================="
echo "CONFIGURATION DES RÉPERTOIRES VPS"
echo "========================================="
echo ""

echo "Création des répertoires sur le VPS..."

ssh $VPS_HOST << 'EOF'
# Créer les répertoires avec sudo
sudo mkdir -p /var/www/html/reports
sudo mkdir -p /var/www/html/static/reports

# Changer le propriétaire pour l'utilisateur linxo
sudo chown -R linxo:www-data /var/www/html/reports
sudo chown -R linxo:www-data /var/www/html/static

# Définir les permissions
sudo chmod -R 755 /var/www/html/reports
sudo chmod -R 755 /var/www/html/static

# Vérifier que tout est ok
echo ""
echo "Répertoires créés :"
ls -la /var/www/html/ | grep -E "(reports|static)"
echo ""
echo "Permissions :"
ls -ld /var/www/html/reports
ls -ld /var/www/html/static
EOF

echo ""
echo "========================================="
echo "✓ CONFIGURATION TERMINÉE"
echo "========================================="
echo ""
echo "Vous pouvez maintenant uploader les rapports avec :"
echo "  python linxo_agent/upload_reports.py"
echo ""
echo "Ou manuellement :"
echo "  rsync -avz data/reports/ $VPS_HOST:/var/www/html/reports/"
echo "  rsync -avz static/reports/ $VPS_HOST:/var/www/html/static/reports/"
