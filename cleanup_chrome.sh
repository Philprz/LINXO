#!/bin/bash
# Script de nettoyage des processus Chrome zombies et du cache
# A utiliser sur le VPS en cas de problème de lancement

echo "=================================="
echo "Nettoyage Chrome pour Linxo Agent"
echo "=================================="

# 1. Tuer tous les processus Chrome
echo ""
echo "[1/3] Arrêt des processus Chrome..."
pkill -f chrome
pkill -f chromedriver
sleep 2

# Forcer si nécessaire
pkill -9 -f chrome 2>/dev/null
pkill -9 -f chromedriver 2>/dev/null

echo "✓ Processus Chrome arrêtés"

# 2. Nettoyer le répertoire user-data
echo ""
echo "[2/3] Nettoyage du répertoire user-data..."
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
CHROME_DATA_DIR="$SCRIPT_DIR/.chrome_user_data"

if [ -d "$CHROME_DATA_DIR" ]; then
    # Supprimer les fichiers de lock
    find "$CHROME_DATA_DIR" -name "SingletonLock" -delete 2>/dev/null
    find "$CHROME_DATA_DIR" -name "*.lock" -delete 2>/dev/null

    # Optionnel : tout supprimer (décommenter si nécessaire)
    # rm -rf "$CHROME_DATA_DIR"

    echo "✓ Fichiers de lock supprimés"
else
    echo "✓ Répertoire user-data inexistant (OK)"
fi

# 3. Vérifier qu'aucun processus ne subsiste
echo ""
echo "[3/3] Vérification finale..."
CHROME_PROCS=$(pgrep -f chrome | wc -l)

if [ "$CHROME_PROCS" -eq 0 ]; then
    echo "✓ Aucun processus Chrome en cours"
else
    echo "⚠ Attention : $CHROME_PROCS processus Chrome encore actifs"
    echo "  Vous pouvez les lister avec : ps aux | grep chrome"
fi

echo ""
echo "=================================="
echo "Nettoyage terminé !"
echo "=================================="
echo ""
echo "Vous pouvez maintenant relancer : python linxo_agent.py"
