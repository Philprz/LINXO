# Différences entre configuration VPS et Local

## Configuration pour le VPS

### Fichier `linxo_agent.py` (ou votre script principal)

**Sur le VPS, utiliser ces imports :**

```python
from linxo_agent.linxo_connexion_undetected import (
    initialiser_driver_linxo_undetected as initialiser_driver_linxo,
    se_connecter_linxo
)
from linxo_agent.linxo_connexion import telecharger_csv_linxo
```

**Sur Windows (local), utiliser ces imports :**

```python
from linxo_agent.linxo_connexion import (
    initialiser_driver_linxo,
    se_connecter_linxo,
    telecharger_csv_linxo
)
```

## Pourquoi cette différence ?

- **VPS (Linux headless)** : Nécessite `undetected-chromedriver` pour contourner la détection anti-bot de Linxo
- **Windows (local)** : Fonctionne avec Selenium standard en mode visible

## Solution automatique : Détection de l'environnement

Pour éviter de modifier le code à chaque fois, vous pouvez utiliser une détection automatique :

```python
import os
import platform

# Détection automatique de l'environnement
IS_SERVER = (
    os.environ.get('DISPLAY') is None or
    'microsoft' in platform.uname().release.lower() or
    os.environ.get('IS_VPS', '').lower() == 'true'
)

if IS_SERVER:
    # VPS : utiliser undetected-chromedriver
    from linxo_agent.linxo_connexion_undetected import (
        initialiser_driver_linxo_undetected as initialiser_driver_linxo,
        se_connecter_linxo
    )
else:
    # Local : utiliser Selenium standard
    from linxo_agent.linxo_connexion import (
        initialiser_driver_linxo,
        se_connecter_linxo
    )

# Importer ce qui est commun
from linxo_agent.linxo_connexion import telecharger_csv_linxo
```

Puis dans le `.env` du VPS, ajoutez :
```
IS_VPS=true
```

## Fichiers spécifiques au VPS

Ces fichiers ne sont nécessaires que sur le VPS :
- `.env` (avec les credentials IMAP)
- `.chrome_user_data_*` (répertoires temporaires)

## Commandes de déploiement rapide

### Déployer depuis Windows vers VPS :

```powershell
# Transférer les fichiers Python
scp linxo_agent/*.py linxo@vps-6e2f6679:~/LINXO/linxo_agent/
scp *.py linxo@vps-6e2f6679:~/LINXO/

# Transférer requirements.txt
scp requirements.txt linxo@vps-6e2f6679:~/LINXO/
```

### Installer les dépendances sur le VPS :

```bash
cd ~/LINXO
source .venv/bin/activate
pip install -r requirements.txt
```

## Checklist avant déploiement

- [ ] Vérifier que `undetected-chromedriver` est dans `requirements.txt`
- [ ] Tester en local d'abord
- [ ] Transférer les fichiers vers le VPS
- [ ] Tester sur le VPS avec `test_undetected_chrome.py`
- [ ] Lancer le script principal
- [ ] Vérifier les logs

## Maintenance

### Mettre à jour uniquement linxo_connexion.py :

```powershell
# Windows
scp linxo_agent/linxo_connexion.py linxo@vps-6e2f6679:~/LINXO/linxo_agent/
```

### Mettre à jour tout le dossier linxo_agent :

```powershell
# Windows
scp linxo_agent/*.py linxo@vps-6e2f6679:~/LINXO/linxo_agent/
```
