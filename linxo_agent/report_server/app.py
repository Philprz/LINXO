#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Serveur FastAPI pour servir les rapports HTML de manière sécurisée
- Basic Auth pour protection globale
- Token HMAC optionnel pour bypass auth depuis les emails
- Serving statique des rapports générés
"""

import os
import hmac
import hashlib
import time
import secrets
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from starlette.status import HTTP_401_UNAUTHORIZED
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Configuration
REPORTS_BASE_DIR = Path(__file__).parent.parent.parent / 'data' / 'reports'
STATIC_DIR = Path(__file__).parent.parent.parent / 'static'

REPORTS_BASIC_USER = os.getenv('REPORTS_BASIC_USER', 'linxo')
REPORTS_BASIC_PASS = os.getenv('REPORTS_BASIC_PASS')
REPORTS_SIGNING_KEY = os.getenv('REPORTS_SIGNING_KEY')

if not REPORTS_BASIC_PASS:
    raise ValueError(
        "REPORTS_BASIC_PASS doit être défini dans le fichier .env pour sécuriser le serveur"
    )

# Initialiser FastAPI
app = FastAPI(
    title="Linxo Report Server",
    description="Serveur sécurisé pour les rapports Linxo",
    version="1.0.0"
)

# Security
security = HTTPBasic()


def constant_time_compare(a: str, b: str) -> bool:
    """
    Compare deux chaînes en temps constant pour éviter les timing attacks

    Args:
        a: Première chaîne
        b: Deuxième chaîne

    Returns:
        bool: True si identiques
    """
    return secrets.compare_digest(a.encode('utf-8'), b.encode('utf-8'))


def verify_token(url_path: str, token: str) -> bool:
    """
    Vérifie un token HMAC signé

    Args:
        url_path: Chemin de l'URL (ex: /reports/2025-01-15/index.html)
        token: Token au format "signature:expiry"

    Returns:
        bool: True si token valide
    """
    if not REPORTS_SIGNING_KEY:
        return False

    try:
        signature, expiry_str = token.split(':')
        expiry = int(expiry_str)

        # Vérifier l'expiration
        if time.time() > expiry:
            return False

        # Recalculer la signature
        message = f"{url_path}:{expiry}"
        expected_signature = hmac.new(
            REPORTS_SIGNING_KEY.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

        # Comparaison en temps constant
        return constant_time_compare(signature, expected_signature)

    except (ValueError, AttributeError):
        return False


async def verify_auth(
    request: Request,
    credentials: HTTPBasicCredentials = Depends(security)
) -> bool:
    """
    Vérifie l'authentification (Basic Auth ou Token)

    Args:
        request: Requête FastAPI
        credentials: Credentials HTTP Basic

    Returns:
        bool: True si authentifié

    Raises:
        HTTPException: Si authentification échouée
    """
    # Vérifier d'abord si un token valide est présent
    token = request.query_params.get('t')
    if token:
        url_path = request.url.path
        if verify_token(url_path, token):
            return True

    # Sinon, vérifier Basic Auth
    correct_username = constant_time_compare(credentials.username, REPORTS_BASIC_USER)
    correct_password = constant_time_compare(credentials.password, REPORTS_BASIC_PASS)

    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="Identifiants incorrects",
            headers={"WWW-Authenticate": "Basic"},
        )

    return True


# Middleware pour ajouter des en-têtes de sécurité
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Ajoute des en-têtes de sécurité à toutes les réponses"""
    response = await call_next(request)

    # En-têtes de sécurité
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

    return response


@app.get("/healthz")
async def health_check():
    """
    Health check endpoint (non authentifié)

    Returns:
        dict: Status du serveur
    """
    return {
        "status": "ok",
        "service": "linxo-report-server",
        "reports_dir_exists": REPORTS_BASE_DIR.exists()
    }


@app.get("/")
async def root(authenticated: bool = Depends(verify_auth)):
    """
    Page d'accueil du serveur de rapports

    Args:
        authenticated: Dépendance d'authentification

    Returns:
        HTMLResponse: Page HTML
    """
    html_content = """
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Linxo Report Server</title>
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;
                background: linear-gradient(135deg, #7c69ef 0%, #a78bfa 100%);
                color: white;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                margin: 0;
            }
            .container {
                text-align: center;
            }
            h1 {
                font-size: 48px;
                margin-bottom: 20px;
            }
            p {
                font-size: 18px;
                opacity: 0.9;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>💰 Linxo Report Server</h1>
            <p>Serveur de rapports sécurisé</p>
            <p>Accédez à vos rapports via les liens envoyés par email</p>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@app.get("/reports/{date_path}/{file_path:path}")
async def get_report(
    date_path: str,
    file_path: str,
    authenticated: bool = Depends(verify_auth)
):
    """
    Sert un fichier de rapport HTML ou une ressource statique

    Args:
        date_path: Date du rapport (YYYY-MM-DD)
        file_path: Chemin du fichier dans le répertoire de la date
        authenticated: Dépendance d'authentification

    Returns:
        FileResponse: Fichier demandé

    Raises:
        HTTPException: Si fichier non trouvé
    """
    # Construire le chemin complet
    full_path = REPORTS_BASE_DIR / date_path / file_path

    # Vérifier que le fichier existe et est dans le bon répertoire (sécurité)
    if not full_path.exists() or not full_path.is_file():
        raise HTTPException(status_code=404, detail="Rapport non trouvé")

    # Vérifier que le chemin résolu est bien dans REPORTS_BASE_DIR (éviter path traversal)
    try:
        full_path.resolve().relative_to(REPORTS_BASE_DIR.resolve())
    except ValueError:
        raise HTTPException(status_code=403, detail="Accès interdit")

    # Déterminer le type MIME
    if file_path.endswith('.html'):
        media_type = 'text/html'
    elif file_path.endswith('.css'):
        media_type = 'text/css'
    elif file_path.endswith('.js'):
        media_type = 'application/javascript'
    else:
        media_type = 'application/octet-stream'

    return FileResponse(
        full_path,
        media_type=media_type,
        headers={
            "Cache-Control": "private, max-age=3600"
        }
    )


# Monter les fichiers statiques (CSS, JS)
app.mount(
    "/static",
    StaticFiles(directory=str(STATIC_DIR)),
    name="static"
)


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv('REPORTS_PORT', 8810))

    print(f"""
╔══════════════════════════════════════════════════════════════╗
║                 LINXO REPORT SERVER                          ║
╚══════════════════════════════════════════════════════════════╝

Serveur démarré sur http://0.0.0.0:{port}

Configuration:
  - Basic Auth User: {REPORTS_BASIC_USER}
  - Token signing: {'Activé' if REPORTS_SIGNING_KEY else 'Désactivé'}
  - Reports directory: {REPORTS_BASE_DIR}

Endpoints:
  - GET /healthz          : Health check (non authentifié)
  - GET /                 : Page d'accueil
  - GET /reports/...      : Rapports HTML (authentifié)

Appuyez sur Ctrl+C pour arrêter le serveur
    """)

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
