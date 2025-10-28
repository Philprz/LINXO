# Diagnostic et résolution du problème de connexion VPS

## Problème identifié

La connexion à Linxo **fonctionne en local (Windows)** mais **échoue sur le VPS (Linux headless)**.

### Cause probable

Linxo détecte l'automatisation en mode headless sur Linux via :
- User-Agent headless
- Propriétés `navigator.webdriver`
- Absence de plugins/GPU
- Comportement non-humain (saisie instantanée)

## Solutions implémentées

### 1. **Anti-détection d'automatisation** (linxo_connexion.py:570-596)

```python
# Désactivation des indicateurs d'automatisation
options.add_argument('--disable-blink-features=AutomationControlled')
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option('useAutomationExtension', False)

# User-Agent réaliste
user_agent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36..."
options.add_argument(f'user-agent={user_agent}')

# Options headless améliorées
options.add_argument('--disable-infobars')
options.add_argument('--disable-browser-side-navigation')
options.add_argument('--disable-features=VizDisplayCompositor')

# Langue française
options.add_argument('--lang=fr-FR')
prefs = {"intl.accept_languages": "fr-FR,fr"}
```

### 2. **Masquage des propriétés webdriver** (linxo_connexion.py:627-643)

```python
driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
    'source': '''
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
        Object.defineProperty(navigator, 'plugins', {
            get: () => [1, 2, 3, 4, 5]
        });
        Object.defineProperty(navigator, 'languages', {
            get: () => ['fr-FR', 'fr', 'en-US', 'en']
        });
        window.chrome = { runtime: {} };
    '''
})
```

### 3. **Comportement humain** (linxo_connexion.py:400-418)

```python
# Saisie caractère par caractère (100ms entre chaque)
for char in email:
    username_field.send_keys(char)
    time.sleep(0.1)

# Pauses réalistes
time.sleep(0.5)  # Après clear
time.sleep(1)    # Entre username et password
time.sleep(2)    # Avant clic sur "Je me connecte"
```

### 4. **Diagnostic amélioré** (linxo_connexion.py:431-459)

- Screenshot avant/après clic sur "Je me connecte"
- Sauvegarde du HTML complet en cas d'échec
- Détection de messages d'erreur dans la page

## Comment tester

### Test 1 : En local (mode headless)

```bash
# Windows
python test_vps_connexion.py
```

Ce test simule exactement les conditions du VPS sur votre machine locale.

### Test 2 : Sur le VPS

```bash
# SSH vers le VPS
ssh linxo@vps-6e2f6679

# Activer l'environnement virtuel
cd ~/LINXO
source .venv/bin/activate

# Lancer le test
python test_vps_connexion.py
```

### Récupérer les fichiers de diagnostic

Si le test échoue sur le VPS :

```bash
# Depuis Windows
scp linxo@vps-6e2f6679:/tmp/before_login_click.png .
scp linxo@vps-6e2f6679:/tmp/after_login_click.png .
scp linxo@vps-6e2f6679:/tmp/login_failed_page.html .
```

## Solutions alternatives si ça ne marche toujours pas

### Solution A : undetected-chromedriver

Installer une bibliothèque spécialisée pour contourner la détection :

```bash
pip install undetected-chromedriver
```

Modifier `linxo_connexion.py` :
```python
import undetected_chromedriver as uc
driver = uc.Chrome(options=options)
```

### Solution B : Xvfb (mode non-headless sur serveur)

Utiliser un serveur X virtuel pour exécuter Chrome en mode graphique :

```bash
# Sur le VPS
sudo apt-get install xvfb

# Lancer avec Xvfb
xvfb-run --server-args="-screen 0 1920x1080x24" python linxo_agent.py
```

### Solution C : Playwright au lieu de Selenium

Playwright a une meilleure détection anti-bot :

```bash
pip install playwright
playwright install chromium
```

### Solution D : Session persistante

Utiliser un `user-data-dir` permanent pour garder la session entre exécutions :

```python
# Dans config.py
user_data_dir = "/home/linxo/LINXO/.chrome_persistent"
```

## Checklist de vérification

- [x] User-Agent réaliste
- [x] Propriétés webdriver masquées
- [x] Options anti-détection
- [x] Comportement de saisie humain
- [x] Langue française configurée
- [x] Screenshots de debug
- [ ] Test en local (mode headless) réussi
- [ ] Test sur VPS réussi

## Fichiers modifiés

- `linxo_agent/linxo_connexion.py` : Améliorations anti-détection
- `test_connexion_diagnostic.py` : Test en local (mode visible)
- `test_vps_connexion.py` : Test en mode headless (simule VPS)
- `DIAGNOSTIC_VPS.md` : Ce fichier

## Prochaines étapes

1. **Tester en local** en mode headless : `python test_vps_connexion.py`
2. **Si ça marche en local headless** : Transférer sur le VPS et tester
3. **Si ça ne marche toujours pas** : Essayer undetected-chromedriver ou Xvfb
4. **Si rien ne marche** : Envisager une solution cloud avec interface graphique (AWS EC2 avec VNC)
