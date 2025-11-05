#!/bin/bash
# Script de correction des problèmes identifiés sur le VPS
# À exécuter DIRECTEMENT SUR LE VPS (après connexion SSH)

set -e

echo "=========================================="
echo "CORRECTION DES PROBLÈMES VPS"
echo "=========================================="
echo ""

# Vérifier qu'on est bien sur le VPS
if [ ! -d "/home/linxo/LINXO" ]; then
    echo "❌ Ce script doit être exécuté sur le VPS"
    echo "Connectez-vous d'abord avec: ssh linxo@152.228.218.1"
    exit 1
fi

cd /home/linxo/LINXO

# ÉTAPE 1: Installer rsync
echo "📋 ÉTAPE 1: Installation de rsync"
echo "=========================================="
if command -v rsync &> /dev/null; then
    echo "✅ rsync est déjà installé"
else
    echo "Installation de rsync..."
    sudo apt-get update
    sudo apt-get install -y rsync
    echo "✅ rsync installé"
fi
echo ""

# ÉTAPE 2: Vérifier l'environnement virtuel Python
echo "📋 ÉTAPE 2: Vérification de l'environnement virtuel Python"
echo "=========================================="

if [ -d ".venv" ]; then
    echo "✅ Répertoire .venv trouvé"

    # Tester l'activation
    if [ -f ".venv/bin/activate" ]; then
        echo "✅ Script d'activation présent"

        # Tester Python
        if .venv/bin/python3 --version &> /dev/null; then
            echo "✅ Python fonctionnel: $(.venv/bin/python3 --version)"
        else
            echo "❌ Python ne fonctionne pas dans .venv"
            echo "Recréation de l'environnement virtuel..."
            rm -rf .venv
            python3 -m venv .venv
            .venv/bin/pip install --upgrade pip
            .venv/bin/pip install -r requirements.txt
            echo "✅ Environnement virtuel recréé"
        fi
    else
        echo "❌ Script d'activation manquant, recréation..."
        rm -rf .venv
        python3 -m venv .venv
        .venv/bin/pip install --upgrade pip
        .venv/bin/pip install -r requirements.txt
        echo "✅ Environnement virtuel recréé"
    fi
else
    echo "❌ Répertoire .venv manquant, création..."
    python3 -m venv .venv
    .venv/bin/pip install --upgrade pip
    .venv/bin/pip install -r requirements.txt
    echo "✅ Environnement virtuel créé"
fi
echo ""

# ÉTAPE 3: Vérifier les dépendances Python
echo "📋 ÉTAPE 3: Vérification des dépendances Python"
echo "=========================================="
echo "Installation/mise à jour des dépendances..."
.venv/bin/pip install -q -r requirements.txt
echo "✅ Dépendances installées"
echo ""

# ÉTAPE 4: Vérifier la configuration .env
echo "📋 ÉTAPE 4: Vérification du fichier .env"
echo "=========================================="
if [ -f ".env" ]; then
    echo "✅ Fichier .env présent"

    # Vérifier les variables critiques (sans afficher les valeurs)
    missing_vars=()

    if ! grep -q "^SMTP_SERVER=" .env; then missing_vars+=("SMTP_SERVER"); fi
    if ! grep -q "^SMTP_PORT=" .env; then missing_vars+=("SMTP_PORT"); fi
    if ! grep -q "^SMTP_USER=" .env; then missing_vars+=("SMTP_USER"); fi
    if ! grep -q "^SMTP_PASSWORD=" .env; then missing_vars+=("SMTP_PASSWORD"); fi
    if ! grep -q "^OVH_SMS_ENDPOINT=" .env; then missing_vars+=("OVH_SMS_ENDPOINT"); fi
    if ! grep -q "^OVH_SMS_APPLICATION_KEY=" .env; then missing_vars+=("OVH_SMS_APPLICATION_KEY"); fi
    if ! grep -q "^OVH_SMS_APPLICATION_SECRET=" .env; then missing_vars+=("OVH_SMS_APPLICATION_SECRET"); fi
    if ! grep -q "^OVH_SMS_CONSUMER_KEY=" .env; then missing_vars+=("OVH_SMS_CONSUMER_KEY"); fi

    if [ ${#missing_vars[@]} -eq 0 ]; then
        echo "✅ Toutes les variables essentielles sont présentes"
    else
        echo "⚠️  Variables manquantes dans .env:"
        for var in "${missing_vars[@]}"; do
            echo "  - $var"
        done
        echo ""
        echo "Ajoutez ces variables dans le fichier .env"
    fi
else
    echo "❌ Fichier .env manquant!"
    echo "Copiez le fichier .env depuis votre machine locale"
    echo "Commande depuis votre PC: scp .env linxo@152.228.218.1:~/LINXO/"
fi
echo ""

# ÉTAPE 5: Vérifier les permissions des répertoires
echo "📋 ÉTAPE 5: Vérification des permissions"
echo "=========================================="

# Créer les répertoires nécessaires
mkdir -p logs data downloads reports

# Vérifier les permissions du répertoire web
if [ -d "/var/www/html/reports" ]; then
    if [ -w "/var/www/html/reports" ]; then
        echo "✅ Permissions OK pour /var/www/html/reports"
    else
        echo "⚠️  Pas de permission d'écriture sur /var/www/html/reports"
        echo "Correction des permissions..."
        sudo chown -R linxo:linxo /var/www/html/reports
        sudo chmod -R 755 /var/www/html/reports
        echo "✅ Permissions corrigées"
    fi
else
    echo "⚠️  Répertoire /var/www/html/reports manquant, création..."
    sudo mkdir -p /var/www/html/reports
    sudo chown -R linxo:linxo /var/www/html/reports
    sudo chmod -R 755 /var/www/html/reports
    echo "✅ Répertoire créé"
fi

if [ -d "/var/www/html/static" ]; then
    if [ -w "/var/www/html/static" ]; then
        echo "✅ Permissions OK pour /var/www/html/static"
    else
        echo "⚠️  Pas de permission d'écriture sur /var/www/html/static"
        echo "Correction des permissions..."
        sudo chown -R linxo:linxo /var/www/html/static
        sudo chmod -R 755 /var/www/html/static
        echo "✅ Permissions corrigées"
    fi
else
    echo "⚠️  Répertoire /var/www/html/static manquant, création..."
    sudo mkdir -p /var/www/html/static
    sudo chown -R linxo:linxo /var/www/html/static
    sudo chmod -R 755 /var/www/html/static
    echo "✅ Répertoire créé"
fi
echo ""

# ÉTAPE 6: Test du script run_daily_report.sh
echo "📋 ÉTAPE 6: Vérification du script run_daily_report.sh"
echo "=========================================="
if [ -f "run_daily_report.sh" ]; then
    if [ -x "run_daily_report.sh" ]; then
        echo "✅ Script exécutable"
    else
        echo "⚠️  Script non exécutable, correction..."
        chmod +x run_daily_report.sh
        echo "✅ Permissions corrigées"
    fi
else
    echo "❌ Script run_daily_report.sh manquant!"
fi
echo ""

# ÉTAPE 7: Afficher un résumé
echo "=========================================="
echo "📊 RÉSUMÉ DES CORRECTIONS"
echo "=========================================="
echo ""
echo "✅ Corrections appliquées:"
echo "  1. rsync installé"
echo "  2. Environnement virtuel Python vérifié"
echo "  3. Dépendances Python installées"
echo "  4. Fichier .env vérifié"
echo "  5. Permissions des répertoires corrigées"
echo "  6. Script run_daily_report.sh vérifié"
echo ""
echo "🧪 TEST RECOMMANDÉ"
echo "=========================================="
echo "Pour tester que tout fonctionne, exécutez:"
echo "  ./run_daily_report.sh"
echo ""
echo "Vérifiez que:"
echo "  - L'analyse s'exécute sans erreur"
echo "  - Un email est envoyé"
echo "  - Un SMS est envoyé"
echo "  - Les rapports HTML sont uploadés"
echo ""
echo "=========================================="
