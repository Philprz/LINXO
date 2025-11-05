#!/bin/bash
# Script d'installation des dépendances VPS pour Agent Linxo

echo "=================================="
echo "INSTALLATION DEPENDANCES VPS"
echo "=================================="

# Vérifier si on est sur le VPS
if [ ! -d "/home/linxo" ]; then
    echo "[ERREUR] Ce script doit être exécuté sur le VPS"
    exit 1
fi

# Mise à jour des paquets
echo ""
echo "[1/3] Mise à jour des paquets..."
sudo apt-get update

# Installation de rsync
echo ""
echo "[2/3] Installation de rsync..."
if ! command -v rsync &> /dev/null; then
    sudo apt-get install -y rsync
    echo "[OK] rsync installé"
else
    echo "[OK] rsync déjà installé"
fi

# Installation de scikit-learn (optionnel pour le ML)
echo ""
echo "[3/3] Installation de scikit-learn (optionnel)..."
if python3 -c "import sklearn" 2>/dev/null; then
    echo "[OK] scikit-learn déjà installé"
else
    echo "[INFO] Installation de scikit-learn..."
    pip3 install scikit-learn numpy
    echo "[OK] scikit-learn installé"
fi

# Vérification
echo ""
echo "=================================="
echo "VERIFICATION"
echo "=================================="
echo -n "rsync: "
if command -v rsync &> /dev/null; then
    echo "OK ($(rsync --version | head -1))"
else
    echo "MANQUANT"
fi

echo -n "scikit-learn: "
if python3 -c "import sklearn" 2>/dev/null; then
    python3 -c "import sklearn; print(f'OK (version {sklearn.__version__})')"
else
    echo "MANQUANT (classification ML désactivée)"
fi

echo ""
echo "=================================="
echo "INSTALLATION TERMINEE"
echo "=================================="
