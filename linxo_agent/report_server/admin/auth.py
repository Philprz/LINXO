#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Système d'authentification pour l'interface d'administration
"""

import os
import secrets
from typing import Optional
from fastapi import HTTPException, Depends, Request
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from starlette.status import HTTP_401_UNAUTHORIZED

# Security
security = HTTPBasic()

# Configuration admin (distinct de l'auth des rapports)
ADMIN_USER = os.getenv('ADMIN_USER', 'admin')
ADMIN_PASS = os.getenv('ADMIN_PASS')


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


async def verify_admin_auth(
    credentials: HTTPBasicCredentials = Depends(security)
) -> bool:
    """
    Vérifie l'authentification admin via Basic Auth

    Args:
        credentials: Credentials HTTP Basic

    Returns:
        bool: True si authentifié

    Raises:
        HTTPException: Si authentification échouée ou ADMIN_PASS non configuré
    """
    # Vérifier que ADMIN_PASS est configuré
    if not ADMIN_PASS:
        raise HTTPException(
            status_code=500,
            detail="Interface admin non configurée (ADMIN_PASS manquant dans .env)"
        )

    # Vérifier les credentials
    correct_username = constant_time_compare(credentials.username, ADMIN_USER)
    correct_password = constant_time_compare(credentials.password, ADMIN_PASS)

    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="Accès admin refusé - identifiants incorrects",
            headers={"WWW-Authenticate": "Basic realm='Linxo Admin'"},
        )

    return True
