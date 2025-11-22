#!/bin/bash
# Script de déploiement de l'harmonisation Chrome/WhatsApp
# Corrige l'erreur "Binary Location Must be a String"
# en harmonisant la détection de Chrome entre tous les modules

set -e

VPS_HOST="linxo@152.228.218.1"
VPS_PATH="/home/linxo/LINXO"

echo "=========================================="
echo "DÉPLOIEMENT HARMONISATION CHROME/WHATSAPP"
echo "=========================================="
echo ""
echo "Ce script déploie 3 fichiers modifiés:"
echo "  1. chrome_detector.py (nouveau)"
echo "  2. linxo_connexion_undetected.py (modifié)"
echo "  3. whatsapp_sender.py (modifié)"
echo ""

# Liste des fichiers à déployer
FILES=(
    "linxo_agent/chrome_detector.py"
    "linxo_agent/linxo_connexion_undetected.py"
    "linxo_agent/whatsapp_sender.py"
)

# Vérifier que tous les fichiers existent localement
echo "🔍 Vérification des fichiers locaux..."
for file in "${FILES[@]}"; do
    if [ ! -f "$file" ]; then
        echo "❌ ERREUR: Le fichier $file n'existe pas localement"
        exit 1
    fi
    echo "  ✅ $file"
done
echo ""

# Créer des sauvegardes sur le VPS
echo "📦 Création des sauvegardes sur le VPS..."
BACKUP_SUFFIX=$(date +%Y%m%d_%H%M%S)
for file in "${FILES[@]}"; do
    ssh "$VPS_HOST" "if [ -f $VPS_PATH/$file ]; then cp $VPS_PATH/$file $VPS_PATH/$file.backup_$BACKUP_SUFFIX; echo '  ✅ Sauvegarde: $file.backup_$BACKUP_SUFFIX'; fi" || {
        echo "  ⚠️  $file n'existe pas sur le VPS (normal pour chrome_detector.py)"
    }
done
echo ""

# Déployer les fichiers
echo "📤 Déploiement des fichiers corrigés..."
for file in "${FILES[@]}"; do
    scp "$file" "$VPS_HOST:$VPS_PATH/$file" || {
        echo "❌ ERREUR: Échec du transfert de $file"
        exit 1
    }
    echo "  ✅ $file déployé"
done
echo ""

# Vérifier que Chrome est installé sur le VPS
echo "🔍 Vérification de l'installation de Chrome sur le VPS..."
ssh "$VPS_HOST" << 'EOF'
echo ""
echo "Test de détection avec chrome_detector.py:"
cd /home/linxo/LINXO
source .venv/bin/activate
python linxo_agent/chrome_detector.py
DETECT_RESULT=$?
echo ""

if [ $DETECT_RESULT -ne 0 ]; then
    echo "❌ ERREUR: Chrome non détecté sur le VPS!"
    echo ""
    echo "Pour installer Chrome:"
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
    echo "⚠️  ATTENTION: Chrome non installé sur le VPS!"
    echo "   Le script ne pourra pas fonctionner sans Chrome."
    exit 1
fi

# Tester l'import Python des modules modifiés
echo "🐍 Test de l'import Python des modules corrigés..."
ssh "$VPS_HOST" << 'EOF'
cd /home/linxo/LINXO
source .venv/bin/activate

echo "  - Test chrome_detector..."
python -c "from linxo_agent.chrome_detector import detect_chrome_binary; print('[OK] chrome_detector importé')" || {
    echo "❌ ERREUR: Impossible d'importer chrome_detector"
    exit 1
}

echo "  - Test linxo_connexion_undetected..."
python -c "from linxo_agent.linxo_connexion_undetected import initialiser_driver_linxo_undetected; print('[OK] linxo_connexion_undetected importé')" || {
    echo "❌ ERREUR: Impossible d'importer linxo_connexion_undetected"
    exit 1
}

echo "  - Test whatsapp_sender..."
python -c "from linxo_agent.whatsapp_sender import initialiser_driver_whatsapp; print('[OK] whatsapp_sender importé')" || {
    echo "❌ ERREUR: Impossible d'importer whatsapp_sender"
    exit 1
}
EOF

echo ""
echo "=========================================="
echo "✅ DÉPLOIEMENT RÉUSSI!"
echo "=========================================="
echo ""
echo "Les 3 modules ont été harmonisés avec succès:"
echo "  ✅ chrome_detector.py - Détection commune de Chrome"
echo "  ✅ linxo_connexion_undetected.py - Utilise chrome_detector"
echo "  ✅ whatsapp_sender.py - Utilise chrome_detector"
echo ""
echo "Configuration harmonisée:"
echo "  - browser_executable_path: Détecté automatiquement"
echo "  - use_subprocess: True (cohérent entre Linxo et WhatsApp)"
echo ""
echo "Pour tester immédiatement:"
echo "  ssh $VPS_HOST 'cd /home/linxo/LINXO && ./run_daily_report.sh'"
echo ""
echo "En cas de problème, les sauvegardes sont disponibles avec le suffixe:"
echo "  .backup_$BACKUP_SUFFIX"
echo ""
