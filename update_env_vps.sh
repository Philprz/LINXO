#!/bin/bash
# Script pour mettre à jour le fichier .env sur le VPS avec les variables correctes
# À exécuter sur le VPS

set -e

cd /home/linxo/LINXO

echo "=========================================="
echo "MISE À JOUR DU FICHIER .ENV"
echo "=========================================="
echo ""

# Backup du fichier .env actuel
if [ -f .env ]; then
    cp .env .env.backup.$(date +%Y%m%d_%H%M%S)
    echo "✅ Backup créé: .env.backup.$(date +%Y%m%d_%H%M%S)"
fi

# Créer/mettre à jour les variables nécessaires
echo "Mise à jour des variables pour les notifications..."

# Fonction pour ajouter ou mettre à jour une variable
update_env_var() {
    local key=$1
    local value=$2

    if grep -q "^${key}=" .env 2>/dev/null; then
        # Variable existe, la mettre à jour
        sed -i "s|^${key}=.*|${key}=${value}|" .env
    else
        # Variable n'existe pas, l'ajouter
        echo "${key}=${value}" >> .env
    fi
}

# SMTP Configuration (mapping depuis vos variables existantes)
# Votre fichier utilise SENDER_EMAIL, le code attend SMTP_HOST, SMTP_SENDER, etc.

# Récupérer les valeurs existantes
SENDER_EMAIL=$(grep "^SENDER_EMAIL=" .env 2>/dev/null | cut -d= -f2)
SENDER_PASSWORD=$(grep "^SENDER_PASSWORD=" .env 2>/dev/null | cut -d= -f2)
NOTIFICATION_EMAIL=$(grep "^NOTIFICATION_EMAIL=" .env 2>/dev/null | cut -d= -f2)

# Ajouter/mettre à jour les variables SMTP attendues par le code
if [ -n "$SENDER_EMAIL" ]; then
    update_env_var "SMTP_HOST" "smtp.gmail.com"
    update_env_var "SMTP_PORT" "465"
    update_env_var "SMTP_USER" "$SENDER_EMAIL"
    update_env_var "SMTP_PASSWORD" "$SENDER_PASSWORD"
    update_env_var "SMTP_SENDER" "$SENDER_EMAIL"
    update_env_var "NOTIFICATION_EMAILS" "$NOTIFICATION_EMAIL"
    echo "✅ Variables SMTP configurées"
else
    echo "⚠️  SENDER_EMAIL non trouvé dans .env"
fi

# OVH SMS Configuration (mapping depuis vos variables existantes)
OVH_SERVICE_NAME=$(grep "^OVH_SERVICE_NAME=" .env 2>/dev/null | cut -d= -f2)
OVH_APP_SECRET=$(grep "^OVH_APP_SECRET=" .env 2>/dev/null | cut -d= -f2)
SMS_SENDER=$(grep "^SMS_SENDER=" .env 2>/dev/null | cut -d= -f2)
SMS_RECIPIENT=$(grep "^SMS_RECIPIENT=" .env 2>/dev/null | cut -d= -f2)

# Ajouter/mettre à jour les variables OVH attendues par le code
if [ -n "$OVH_SERVICE_NAME" ]; then
    # Le code attend OVH_ENDPOINT, OVH_APP_KEY, OVH_APP_SECRET, OVH_CONSUMER_KEY
    # Il semble que votre config OVH soit différente (ancienne API email2sms)
    # Gardons les deux configurations pour compatibilité
    update_env_var "OVH_ENDPOINT" "ovh-eu"
    update_env_var "OVH_SMS_ACCOUNT" "$OVH_SERVICE_NAME"
    update_env_var "OVH_SMS_SENDER" "$SMS_SENDER"
    update_env_var "OVH_SMS_RECIPIENTS" "$SMS_RECIPIENT"
    echo "✅ Variables OVH SMS configurées"
else
    echo "⚠️  OVH_SERVICE_NAME non trouvé dans .env"
fi

echo ""
echo "=========================================="
echo "VÉRIFICATION DES VARIABLES"
echo "=========================================="

# Vérifier que les variables critiques sont présentes
echo ""
echo "Variables SMTP:"
grep -E "^SMTP_HOST=|^SMTP_PORT=|^SMTP_USER=|^SMTP_SENDER=|^NOTIFICATION_EMAILS=" .env | sed 's/SMTP_PASSWORD=.*/SMTP_PASSWORD=***/' || echo "⚠️  Certaines variables SMTP manquent"

echo ""
echo "Variables OVH SMS:"
grep -E "^OVH_ENDPOINT=|^OVH_SMS_ACCOUNT=|^OVH_SMS_SENDER=|^OVH_SMS_RECIPIENTS=" .env || echo "⚠️  Certaines variables OVH SMS manquent"

echo ""
echo "=========================================="
echo "✅ MISE À JOUR TERMINÉE"
echo "=========================================="
echo ""
echo "Un backup a été créé. En cas de problème:"
echo "  cp .env.backup.* .env"
echo ""
echo "Testez maintenant avec:"
echo "  ./run_daily_report.sh"
echo ""
