#!/bin/bash
# Script de déploiement du fix "Binary Location Must be a String"
# Ce script déploie la correction qui spécifie explicitement le chemin de Chrome

set -e

VPS_HOST="linxo@152.228.218.1"
VPS_PATH="/home/linxo/LINXO"
LOCAL_FILE="linxo_agent/linxo_connexion_undetected.py"

echo "=========================================="
echo "DÉPLOIEMENT DU FIX CHROME BINARY LOCATION"
echo "=========================================="
echo ""

# Vérifier que le fichier local existe
if [ ! -f "$LOCAL_FILE" ]; then
    echo "❌ ERREUR: Le fichier $LOCAL_FILE n'existe pas localement"
    exit 1
fi

echo "✅ Fichier local trouvé: $LOCAL_FILE"
echo ""

# Créer une sauvegarde sur le VPS
echo "📦 Création d'une sauvegarde sur le VPS..."
ssh "$VPS_HOST" "cp $VPS_PATH/$LOCAL_FILE $VPS_PATH/$LOCAL_FILE.backup_$(date +%Y%m%d_%H%M%S)" || {
    echo "⚠️  WARN: Impossible de créer la sauvegarde (fichier peut-être inexistant)"
}

# Déployer le fichier corrigé
echo "📤 Déploiement du fichier corrigé..."
scp "$LOCAL_FILE" "$VPS_HOST:$VPS_PATH/$LOCAL_FILE" || {
    echo "❌ ERREUR: Échec du transfert SCP"
    exit 1
}

echo ""
echo "✅ Fichier déployé avec succès!"
echo ""

# Vérifier que Chrome est installé sur le VPS
echo "🔍 Vérification de l'installation de Chrome sur le VPS..."
ssh "$VPS_HOST" << 'EOF'
echo "Recherche de Chrome dans les chemins standards..."

CHROME_FOUND=0
if [ -f /usr/bin/google-chrome ]; then
    echo "✅ Chrome trouvé: /usr/bin/google-chrome"
    /usr/bin/google-chrome --version
    CHROME_FOUND=1
elif [ -f /usr/bin/google-chrome-stable ]; then
    echo "✅ Chrome trouvé: /usr/bin/google-chrome-stable"
    /usr/bin/google-chrome-stable --version
    CHROME_FOUND=1
elif [ -f /usr/bin/chromium ]; then
    echo "✅ Chromium trouvé: /usr/bin/chromium"
    /usr/bin/chromium --version
    CHROME_FOUND=1
elif [ -f /usr/bin/chromium-browser ]; then
    echo "✅ Chromium trouvé: /usr/bin/chromium-browser"
    /usr/bin/chromium-browser --version
    CHROME_FOUND=1
fi

if [ $CHROME_FOUND -eq 0 ]; then
    echo "❌ ERREUR: Chrome/Chromium non trouvé!"
    echo ""
    echo "Pour installer Chrome sur le VPS, exécutez:"
    echo "  wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo apt-key add -"
    echo "  sudo sh -c 'echo \"deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main\" >> /etc/apt/sources.list.d/google-chrome.list'"
    echo "  sudo apt update"
    echo "  sudo apt install -y google-chrome-stable"
    exit 1
fi
EOF

CHROME_CHECK=$?
echo ""

if [ $CHROME_CHECK -ne 0 ]; then
    echo "⚠️  ATTENTION: Chrome n'est pas installé sur le VPS!"
    echo "   Le script ne pourra pas fonctionner sans Chrome."
    echo ""
    exit 1
fi

# Tester l'import Python
echo "🐍 Test de l'import Python du module corrigé..."
ssh "$VPS_HOST" << 'EOF'
cd /home/linxo/LINXO
source .venv/bin/activate
python -c "from linxo_agent.linxo_connexion_undetected import initialiser_driver_linxo_undetected; print('[OK] Import réussi')" || {
    echo "❌ ERREUR: Impossible d'importer le module"
    exit 1
}
EOF

echo ""
echo "=========================================="
echo "✅ DÉPLOIEMENT RÉUSSI!"
echo "=========================================="
echo ""
echo "Le fix a été déployé avec succès sur le VPS."
echo ""
echo "Pour tester immédiatement:"
echo "  ssh $VPS_HOST 'cd /home/linxo/LINXO && ./run_daily_report.sh'"
echo ""
