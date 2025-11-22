#!/bin/bash
# Script de déploiement de la correction Xvfb
# Corrige l'erreur "cannot connect to chrome" en utilisant Xvfb au lieu du mode headless

set -e

VPS_HOST="linxo@152.228.218.1"
VPS_PATH="/home/linxo/LINXO"

echo "=========================================="
echo "DÉPLOIEMENT CORRECTION XVFB"
echo "=========================================="
echo ""
echo "Cette correction permet d'utiliser Xvfb (DISPLAY=:99)"
echo "au lieu du mode headless qui échoue avec 'chrome not reachable'"
echo ""

# Fichiers à déployer
FILES=(
    "linxo_agent/chrome_detector.py"
    "linxo_agent/linxo_connexion_undetected.py"
    "linxo_agent/whatsapp_sender.py"
)

# Vérifier les fichiers locaux
echo "🔍 Vérification des fichiers locaux..."
for file in "${FILES[@]}"; do
    if [ ! -f "$file" ]; then
        echo "❌ ERREUR: $file n'existe pas"
        exit 1
    fi
    echo "  ✅ $file"
done
echo ""

# Créer sauvegardes
echo "📦 Création des sauvegardes sur le VPS..."
BACKUP_SUFFIX=$(date +%Y%m%d_%H%M%S)
for file in "${FILES[@]}"; do
    ssh "$VPS_HOST" "if [ -f $VPS_PATH/$file ]; then cp $VPS_PATH/$file $VPS_PATH/$file.backup_$BACKUP_SUFFIX; fi"
done
echo ""

# Déployer
echo "📤 Déploiement des fichiers..."
for file in "${FILES[@]}"; do
    scp "$file" "$VPS_HOST:$VPS_PATH/$file" || {
        echo "❌ ERREUR: Échec du transfert de $file"
        exit 1
    }
    echo "  ✅ $file déployé"
done
echo ""

# Vérifier Xvfb
echo "🔍 Vérification de Xvfb sur le VPS..."
ssh "$VPS_HOST" << 'EOF'
if pgrep -x Xvfb > /dev/null; then
    echo "  ✅ Xvfb est actif (PID: $(pgrep -x Xvfb))"
    echo "  ✅ DISPLAY devrait être :99"
else
    echo "  ❌ ERREUR: Xvfb n'est PAS actif!"
    echo ""
    echo "  Pour démarrer Xvfb:"
    echo "    Xvfb :99 -screen 0 1920x1080x24 -nolisten tcp -nolisten unix &"
    echo ""
    echo "  Ou créer un service systemd (recommandé):"
    echo "    sudo systemctl start xvfb"
    exit 1
fi
EOF

if [ $? -ne 0 ]; then
    echo ""
    echo "⚠️  Xvfb n'est pas actif. Démarrez-le avant de continuer."
    exit 1
fi
echo ""

# Tester l'import
echo "🐍 Test de l'import Python..."
ssh "$VPS_HOST" << 'EOF'
cd /home/linxo/LINXO
source .venv/bin/activate

python -c "from linxo_agent.chrome_detector import detect_chrome_binary; print('[OK] chrome_detector')" || exit 1
python -c "from linxo_agent.linxo_connexion_undetected import initialiser_driver_linxo_undetected; print('[OK] linxo_connexion_undetected')" || exit 1
python -c "from linxo_agent.whatsapp_sender import initialiser_driver_whatsapp; print('[OK] whatsapp_sender')" || exit 1
EOF

echo ""
echo "=========================================="
echo "✅ DÉPLOIEMENT RÉUSSI!"
echo "=========================================="
echo ""
echo "Modifications déployées:"
echo "  1. chrome_detector.py - Détection commune de Chrome"
echo "  2. linxo_connexion_undetected.py - Utilise Xvfb au lieu de headless"
echo "  3. whatsapp_sender.py - Harmonisé avec Linxo"
echo ""
echo "Comportement attendu:"
echo "  - Si DISPLAY=:99 est défini → Utilise Xvfb (PAS headless)"
echo "  - Chrome démarre normalement avec Xvfb"
echo ""
echo "Pour tester immédiatement:"
echo "  ssh $VPS_HOST 'cd /home/linxo/LINXO && ./run_daily_report.sh'"
echo ""
echo "Vous devriez voir dans les logs:"
echo "  [INFO] DISPLAY détecté: :99 (utilisation de Xvfb, pas headless)"
echo "  [INFO] Chrome trouvé: /usr/bin/google-chrome"
echo "  [OK] Driver créé avec succès!"
echo ""
