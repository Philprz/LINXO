#!/bin/bash
# Script de déploiement des corrections sur le VPS

VPS_USER="votre_user"  # À modifier
VPS_HOST="votre_vps"   # À modifier
VPS_PATH="/chemin/vers/LINXO"  # À modifier

echo "==================================="
echo "Déploiement des corrections"
echo "==================================="

# Fichiers à déployer
FILES=(
    "linxo_agent/reports.py"
    "templates/reports/depenses-variables.html.j2"
)

echo ""
echo "Fichiers à déployer :"
for file in "${FILES[@]}"; do
    echo "  - $file"
done

echo ""
read -p "Confirmez le déploiement (o/n) ? " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Oo]$ ]]; then
    echo "Déploiement annulé"
    exit 1
fi

# Copie des fichiers
for file in "${FILES[@]}"; do
    echo "Copie de $file..."
    scp "$file" "${VPS_USER}@${VPS_HOST}:${VPS_PATH}/$file"
    if [ $? -eq 0 ]; then
        echo "  ✓ OK"
    else
        echo "  ✗ ERREUR"
        exit 1
    fi
done

echo ""
echo "==================================="
echo "Déploiement terminé avec succès !"
echo "==================================="
echo ""
echo "N'oubliez pas de :"
echo "1. Relancer le service sur le VPS si nécessaire"
echo "2. Régénérer les rapports avec le nouveau code"
