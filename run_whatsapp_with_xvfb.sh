#!/bin/bash
# Script pour lancer WhatsApp avec Xvfb (serveur X virtuel)
# Usage: ./run_whatsapp_with_xvfb.sh [test|run]

DISPLAY_NUM=99
XVFB_RUNNING=false

# Fonction pour démarrer Xvfb si nécessaire
start_xvfb() {
    if ! pgrep -x "Xvfb" > /dev/null; then
        echo "Demarrage de Xvfb sur :$DISPLAY_NUM..."
        Xvfb :$DISPLAY_NUM -screen 0 1920x1080x24 > /dev/null 2>&1 &
        XVFB_PID=$!
        XVFB_RUNNING=true
        sleep 2
        echo "Xvfb demarre (PID: $XVFB_PID)"
    else
        echo "Xvfb deja en cours d'execution"
    fi
}

# Fonction pour arrêter Xvfb si on l'a démarré
stop_xvfb() {
    if [ "$XVFB_RUNNING" = true ] && [ ! -z "$XVFB_PID" ]; then
        echo "Arret de Xvfb..."
        kill $XVFB_PID 2>/dev/null
    fi
}

# Trap pour nettoyer à la sortie
trap stop_xvfb EXIT INT TERM

# Démarrer Xvfb
start_xvfb

# Exporter DISPLAY pour Chrome
export DISPLAY=:$DISPLAY_NUM

# Lancer le script Python approprié
case "$1" in
    test)
        echo "Lancement du test WhatsApp..."
        python setup_whatsapp.py --test
        ;;
    setup)
        echo "Configuration initiale WhatsApp (scan QR code)..."
        python setup_whatsapp.py
        ;;
    *)
        echo "Usage: $0 {test|setup}"
        exit 1
        ;;
esac

exit_code=$?

# Xvfb sera arrêté automatiquement par le trap
exit $exit_code
