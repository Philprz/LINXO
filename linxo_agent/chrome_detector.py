#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module commun pour détecter l'emplacement de Chrome/Chromium.
Utilisé par tous les modules nécessitant undetected-chromedriver.
"""

import os
from pathlib import Path


def detect_chrome_binary():
    """
    Détecte automatiquement l'emplacement de Chrome/Chromium sur le système.

    Returns:
        str ou None: Chemin vers l'exécutable Chrome, ou None si non trouvé
    """
    # Chemins standards à tester (ordre de préférence)
    chrome_paths = [
        # Linux - Google Chrome
        '/usr/bin/google-chrome',
        '/usr/bin/google-chrome-stable',
        '/usr/bin/google-chrome-beta',
        '/usr/bin/google-chrome-dev',

        # Linux - Chromium
        '/usr/bin/chromium',
        '/usr/bin/chromium-browser',
        '/snap/bin/chromium',

        # macOS
        '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
        '/Applications/Chromium.app/Contents/MacOS/Chromium',

        # Windows
        r'C:\Program Files\Google\Chrome\Application\chrome.exe',
        r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe',
        os.path.expandvars(r'%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe'),
    ]

    for path in chrome_paths:
        if os.path.exists(path):
            return path

    return None


def get_chrome_binary_or_raise():
    """
    Détecte Chrome et lève une exception si non trouvé.

    Returns:
        str: Chemin vers l'exécutable Chrome

    Raises:
        RuntimeError: Si Chrome n'est pas trouvé
    """
    chrome_binary = detect_chrome_binary()

    if chrome_binary is None:
        raise RuntimeError(
            "Chrome/Chromium non trouvé sur le système.\n"
            "Veuillez installer Google Chrome ou Chromium:\n"
            "  - Ubuntu/Debian: sudo apt install google-chrome-stable\n"
            "  - Windows: https://www.google.com/chrome/\n"
            "  - macOS: brew install --cask google-chrome"
        )

    return chrome_binary


if __name__ == "__main__":
    # Test du module
    print("Détection de Chrome/Chromium...")

    chrome = detect_chrome_binary()
    if chrome:
        print(f"✅ Chrome trouvé: {chrome}")
    else:
        print("❌ Chrome non trouvé")
        print("\nChemins testés:")
        print("  - /usr/bin/google-chrome")
        print("  - /usr/bin/chromium")
        print("  - C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe")
        print("  - ...")
