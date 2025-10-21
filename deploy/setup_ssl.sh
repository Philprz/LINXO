#!/bin/bash
###############################################################################
# Configuration SSL avec Let's Encrypt pour le domaine
# Ce script configure un certificat SSL gratuit et son renouvellement automatique
###############################################################################

set -e

echo "==========================================================================="
echo "  Configuration SSL avec Let's Encrypt"
echo "==========================================================================="
echo ""

# Couleurs
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

###############################################################################
# Vérification des prérequis
###############################################################################

# Vérifier si le script est exécuté en tant que root
if [ "$EUID" -ne 0 ]; then
    log_error "Ce script doit être exécuté avec sudo"
    exit 1
fi

# Demander le nom de domaine
echo ""
read -p "Entrez votre nom de domaine (ex: linxo.votredomaine.com) : " DOMAIN_NAME
read -p "Entrez votre email pour les notifications (ex: admin@votredomaine.com) : " ADMIN_EMAIL

# Vérifier que les variables ne sont pas vides
if [ -z "$DOMAIN_NAME" ] || [ -z "$ADMIN_EMAIL" ]; then
    log_error "Le nom de domaine et l'email sont obligatoires"
    exit 1
fi

log_info "Domaine : $DOMAIN_NAME"
log_info "Email : $ADMIN_EMAIL"

###############################################################################
# Installation de Certbot
###############################################################################

log_info "Installation de Certbot..."

apt update
apt install -y certbot

log_info "Certbot installé"

###############################################################################
# Configuration du pare-feu
###############################################################################

log_info "Configuration du pare-feu..."

# Vérifier si UFW est installé
if command -v ufw &> /dev/null; then
    log_info "Configuration d'UFW..."
    ufw allow 80/tcp
    ufw allow 443/tcp
    ufw allow 22/tcp
    ufw --force enable
    log_info "Pare-feu configuré (ports 80, 443, 22 ouverts)"
else
    log_warn "UFW n'est pas installé. Assurez-vous que les ports 80 et 443 sont ouverts"
fi

###############################################################################
# Vérification DNS
###############################################################################

log_warn "IMPORTANT : Vérifiez que votre domaine pointe vers ce serveur"
echo ""
echo "IP de ce serveur :"
curl -s ifconfig.me
echo ""
echo ""
read -p "Le DNS est-il configuré et propagé ? (y/n) : " DNS_OK

if [ "$DNS_OK" != "y" ] && [ "$DNS_OK" != "Y" ]; then
    log_error "Configurez d'abord votre DNS puis relancez ce script"
    exit 1
fi

###############################################################################
# Choix du mode de validation
###############################################################################

echo ""
log_info "Choisissez la méthode de validation :"
echo "1. Standalone (arrête temporairement les services web sur le port 80)"
echo "2. Webroot (nécessite un serveur web configuré)"
echo "3. DNS (validation manuelle via enregistrement TXT)"
echo ""
read -p "Votre choix (1/2/3) : " VALIDATION_METHOD

case $VALIDATION_METHOD in
    1)
        log_info "Méthode : Standalone"

        # Vérifier si un service utilise le port 80
        if netstat -tuln | grep ':80 ' > /dev/null; then
            log_warn "Un service utilise déjà le port 80"
            read -p "Voulez-vous arrêter nginx/apache temporairement ? (y/n) : " STOP_WEB
            if [ "$STOP_WEB" = "y" ] || [ "$STOP_WEB" = "Y" ]; then
                systemctl stop nginx 2>/dev/null || true
                systemctl stop apache2 2>/dev/null || true
            fi
        fi

        certbot certonly --standalone \
            -d "$DOMAIN_NAME" \
            --email "$ADMIN_EMAIL" \
            --agree-tos \
            --no-eff-email \
            --non-interactive
        ;;

    2)
        log_info "Méthode : Webroot"

        WEBROOT_PATH="/var/www/html"
        read -p "Chemin du webroot [$WEBROOT_PATH] : " CUSTOM_WEBROOT
        if [ ! -z "$CUSTOM_WEBROOT" ]; then
            WEBROOT_PATH="$CUSTOM_WEBROOT"
        fi

        mkdir -p "$WEBROOT_PATH"

        certbot certonly --webroot \
            -w "$WEBROOT_PATH" \
            -d "$DOMAIN_NAME" \
            --email "$ADMIN_EMAIL" \
            --agree-tos \
            --no-eff-email \
            --non-interactive
        ;;

    3)
        log_info "Méthode : DNS (manuelle)"

        certbot certonly --manual \
            --preferred-challenges dns \
            -d "$DOMAIN_NAME" \
            --email "$ADMIN_EMAIL" \
            --agree-tos \
            --no-eff-email
        ;;

    *)
        log_error "Choix invalide"
        exit 1
        ;;
esac

###############################################################################
# Vérification du certificat
###############################################################################

if [ -d "/etc/letsencrypt/live/$DOMAIN_NAME" ]; then
    log_info "Certificat SSL créé avec succès !"

    echo ""
    echo "Emplacement des certificats :"
    echo "  - Certificat : /etc/letsencrypt/live/$DOMAIN_NAME/fullchain.pem"
    echo "  - Clé privée : /etc/letsencrypt/live/$DOMAIN_NAME/privkey.pem"
    echo ""

    # Afficher les détails du certificat
    log_info "Détails du certificat :"
    openssl x509 -in "/etc/letsencrypt/live/$DOMAIN_NAME/fullchain.pem" -noout -dates

else
    log_error "Échec de la création du certificat"
    exit 1
fi

###############################################################################
# Configuration du renouvellement automatique
###############################################################################

log_info "Configuration du renouvellement automatique..."

# Test du renouvellement
certbot renew --dry-run

# Le cron est normalement configuré automatiquement par certbot
# Vérification
if [ -f "/etc/cron.d/certbot" ]; then
    log_info "Renouvellement automatique configuré via /etc/cron.d/certbot"
else
    log_warn "Configuration manuelle du cron pour le renouvellement..."

    # Ajouter un cron job pour le renouvellement
    CRON_CMD="0 3 * * * certbot renew --quiet --post-hook 'systemctl reload nginx 2>/dev/null || systemctl reload apache2 2>/dev/null || true'"

    if ! crontab -l 2>/dev/null | grep -q "certbot renew"; then
        (crontab -l 2>/dev/null; echo "$CRON_CMD") | crontab -
        log_info "Cron job de renouvellement ajouté (tous les jours à 3h)"
    fi
fi

###############################################################################
# Configuration optionnelle de Nginx
###############################################################################

echo ""
read -p "Voulez-vous configurer Nginx avec SSL ? (y/n) : " SETUP_NGINX

if [ "$SETUP_NGINX" = "y" ] || [ "$SETUP_NGINX" = "Y" ]; then
    log_info "Installation et configuration de Nginx..."

    apt install -y nginx

    # Créer la configuration Nginx
    cat > "/etc/nginx/sites-available/$DOMAIN_NAME" <<EOF
server {
    listen 80;
    server_name $DOMAIN_NAME;

    # Redirection HTTP vers HTTPS
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name $DOMAIN_NAME;

    # Certificats SSL
    ssl_certificate /etc/letsencrypt/live/$DOMAIN_NAME/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$DOMAIN_NAME/privkey.pem;

    # Configuration SSL recommandée
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Headers de sécurité
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;

    # Logs
    access_log /var/log/nginx/${DOMAIN_NAME}_access.log;
    error_log /var/log/nginx/${DOMAIN_NAME}_error.log;

    # Root directory
    root /var/www/html;
    index index.html index.htm;

    location / {
        try_files \$uri \$uri/ =404;
    }

    # Let's Encrypt challenge
    location ~ /.well-known {
        allow all;
    }
}
EOF

    # Activer le site
    ln -sf "/etc/nginx/sites-available/$DOMAIN_NAME" "/etc/nginx/sites-enabled/"

    # Supprimer la config par défaut si elle existe
    rm -f /etc/nginx/sites-enabled/default

    # Tester la configuration
    nginx -t

    # Redémarrer Nginx
    systemctl restart nginx
    systemctl enable nginx

    log_info "Nginx configuré avec SSL"
fi

###############################################################################
# Résumé
###############################################################################

echo ""
echo "==========================================================================="
echo -e "${GREEN}  Configuration SSL terminée avec succès !${NC}"
echo "==========================================================================="
echo ""
echo "Informations :"
echo "  - Domaine : $DOMAIN_NAME"
echo "  - Certificat : /etc/letsencrypt/live/$DOMAIN_NAME/fullchain.pem"
echo "  - Clé privée : /etc/letsencrypt/live/$DOMAIN_NAME/privkey.pem"
echo "  - Renouvellement : Automatique tous les jours à 3h"
echo ""
echo "Commandes utiles :"
echo "  - Lister les certificats : certbot certificates"
echo "  - Renouveler manuellement : certbot renew"
echo "  - Tester le renouvellement : certbot renew --dry-run"
echo "  - Révoquer un certificat : certbot revoke --cert-path /etc/letsencrypt/live/$DOMAIN_NAME/cert.pem"
echo ""
echo "Testez votre certificat sur : https://www.ssllabs.com/ssltest/"
echo ""
echo "==========================================================================="
echo ""
