#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Factory pour créer le bon driver selon l'environnement (VPS ou Local)
Détecte automatiquement l'environnement et choisit la meilleure méthode
"""

import os
import platform


def is_server_environment():
    """
    Détecte si on est dans un environnement serveur (VPS/Linux headless).

    Returns:
        bool: True si environnement serveur, False sinon
    """
    # Vérifier la variable d'environnement
    if os.environ.get('IS_VPS', '').lower() == 'true':
        return True

    # Vérifier l'absence de DISPLAY (pas d'interface graphique)
    if os.environ.get('DISPLAY') is None:
        # Sous Linux/Unix, pas de DISPLAY = pas de GUI
        if platform.system() in ('Linux', 'Unix'):
            return True

    # Vérifier WSL (Windows Subsystem for Linux)
    if 'microsoft' in platform.uname().release.lower():
        return True

    return False


def get_driver_module():
    """
    Retourne le bon module de connexion selon l'environnement.

    Returns:
        module: Module de connexion approprié
    """
    if is_server_environment():
        print("[DRIVER] Environnement serveur détecté → utilisation de undetected-chromedriver")
        try:
            from . import linxo_connexion_undetected
            return linxo_connexion_undetected
        except ImportError:
            print("[WARN] undetected-chromedriver non disponible, utilisation du driver standard")
            print("[WARN] Installez-le avec: pip install undetected-chromedriver")
            from . import linxo_connexion
            return linxo_connexion
    else:
        print("[DRIVER] Environnement local détecté → utilisation du driver standard")
        from . import linxo_connexion
        return linxo_connexion


def initialiser_driver_linxo(download_dir=None, headless=None, cleanup=True, max_retries=3):
    """
    Initialise le driver Selenium approprié selon l'environnement.

    Args:
        download_dir: Dossier de téléchargement
        headless: Mode headless (None = auto-détection)
        cleanup: Nettoyer les processus zombies
        max_retries: Nombre de tentatives

    Returns:
        tuple: (driver, wait, user_data_dir)
    """
    module = get_driver_module()

    # Auto-détection du mode headless si non spécifié
    if headless is None:
        headless = is_server_environment()

    # Utiliser la bonne fonction d'initialisation
    if hasattr(module, 'initialiser_driver_linxo_undetected'):
        return module.initialiser_driver_linxo_undetected(
            download_dir=download_dir,
            headless=headless,
            cleanup=cleanup,
            max_retries=max_retries
        )
    else:
        return module.initialiser_driver_linxo(
            download_dir=download_dir,
            headless=headless,
            cleanup=cleanup,
            max_retries=max_retries
        )


def se_connecter_linxo(driver, wait, email=None, password=None):
    """
    Se connecte à Linxo (délègue au module approprié).

    Args:
        driver: Instance du WebDriver
        wait: Instance de WebDriverWait
        email: Email de connexion
        password: Mot de passe

    Returns:
        bool: True si connexion réussie
    """
    module = get_driver_module()
    return module.se_connecter_linxo(driver, wait, email, password)


def telecharger_csv_linxo(driver, wait):
    """
    Télécharge le CSV depuis Linxo (toujours depuis le module standard).

    Args:
        driver: Instance du WebDriver
        wait: Instance de WebDriverWait

    Returns:
        Path: Chemin du fichier téléchargé
    """
    from . import linxo_connexion
    return linxo_connexion.telecharger_csv_linxo(driver, wait)


# Pour la compatibilité, exposer les fonctions au niveau du module
__all__ = [
    'initialiser_driver_linxo',
    'se_connecter_linxo',
    'telecharger_csv_linxo',
    'is_server_environment',
    'get_driver_module'
]
