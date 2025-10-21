# Mise à jour du workflow de téléchargement CSV

**Date** : 21 octobre 2025
**Modification** : Workflow précis pour le téléchargement du CSV depuis Linxo

---

## 🎯 Workflow implémenté

Le module `linxo_connexion.py` a été mis à jour pour suivre **exactement** le processus suivant :

### Étape 1 : Navigation vers l'Historique

```
URL: https://wwws.linxo.com/secured/history.page
```

Correspond au lien :
```html
<a href="/secured/history.page">Historique</a>
```

### Étape 2 : Clic sur "Recherche avancée"

Élément ciblé :
```html
<a class="GJALL4ABIGC">Recherche avancée</a>
```

Code Selenium :
```python
recherche_avancee = wait.until(
    EC.element_to_be_clickable((By.CLASS_NAME, "GJALL4ABIGC"))
)
recherche_avancee.click()
```

### Étape 3 : Sélection de "Ce mois-ci"

Élément ciblé :
```html
<select class="GJALL4ABIY">
  <option value="0">Tout</option>
  <option value="1">6 derniers mois</option>
  <option value="2">Le mois dernier</option>
  <option value="3">Ce mois-ci</option>      <!-- Sélectionner celle-ci -->
  <option value="4">Sélection personnalisée</option>
</select>
```

Code Selenium :
```python
from selenium.webdriver.support.ui import Select

select_element = wait.until(
    EC.presence_of_element_located((By.CLASS_NAME, "GJALL4ABIY"))
)
select = Select(select_element)
select.select_by_value("3")  # "Ce mois-ci"
```

### Étape 4 : Clic sur le bouton CSV

Élément ciblé :
```html
<button type="button" class="GJALL4ABCV GJALL4ABLW">CSV</button>
```

Code Selenium (3 méthodes de fallback) :
```python
# Méthode 1: Par les classes exactes
csv_button = wait.until(
    EC.element_to_be_clickable((By.CSS_SELECTOR, "button.GJALL4ABCV.GJALL4ABLW"))
)
csv_button.click()

# Méthode 2: Par le texte (fallback)
csv_button = driver.find_element(By.XPATH, "//button[contains(text(), 'CSV')]")
csv_button.click()

# Méthode 3: Par classe partielle (fallback)
csv_button = driver.find_element(By.CSS_SELECTOR, "button.GJALL4ABCV")
csv_button.click()
```

### Étape 5 : Vérification du téléchargement

Le système :
1. Attend 10 secondes pour le téléchargement
2. Cherche les fichiers `.csv` dans le dossier `Downloads/`
3. Prend le plus récent
4. Le copie dans `data/latest.csv`

---

## 📝 Logs attendus

Lors de l'exécution, vous devriez voir :

```
[DOWNLOAD] Telechargement du CSV...
[ETAPE 1] Navigation vers la page Historique...
[OK] URL actuelle: https://wwws.linxo.com/secured/history.page
[ETAPE 2] Clic sur 'Recherche avancee'...
[OK] Clic sur 'Recherche avancee' reussi
[ETAPE 3] Selection de 'Ce mois-ci' dans le menu deroulant...
[OK] 'Ce mois-ci' selectionne
[ETAPE 4] Clic sur le bouton CSV...
[OK] Clic sur bouton CSV reussi
[ETAPE 5] Verification du telechargement...
[SUCCESS] CSV telecharge: C:\Users\...\LINXO\data\latest.csv
[INFO] Taille: 45678 octets
```

---

## 🔧 Gestion des erreurs

Le code inclut plusieurs **fallbacks** pour chaque étape :

### Étape 2 : Recherche avancée
- Si le clic échoue → Continue (peut-être déjà ouvert)

### Étape 3 : Sélection période
- Méthode 1 : `select_by_value("3")`
- Méthode 2 (fallback) : `select_by_index(3)`
- Si échec → Continue avec période par défaut

### Étape 4 : Bouton CSV
- Méthode 1 : Classes exactes `button.GJALL4ABCV.GJALL4ABLW`
- Méthode 2 (fallback) : Texte "CSV"
- Méthode 3 (fallback) : Classe partielle `button.GJALL4ABCV`
- Si toutes échouent → Retourne `None`

---

## ✅ Test du nouveau workflow

### Test simple (sans notifications)

```bash
python linxo_agent.py --skip-notifications
```

### Test du module de connexion seul

```bash
cd linxo_agent
python linxo_connexion.py
```

Lors de l'exécution, Chrome s'ouvrira et vous pourrez :
1. Voir la connexion automatique
2. Observer chaque étape du téléchargement
3. Confirmer ou non le téléchargement du CSV (prompt)

---

## 📌 Points importants

### Période sélectionnée : "Ce mois-ci"

Le système télécharge **uniquement les transactions du mois en cours**.

**Avantage** : Fichier plus petit, analyse plus rapide
**Note** : Si vous voulez analyser une période différente, modifiez dans `linxo_connexion.py` :

```python
# Ligne 241
select.select_by_value("3")  # 3 = "Ce mois-ci"

# Pour changer :
# "0" = Tout
# "1" = 6 derniers mois
# "2" = Le mois dernier
# "3" = Ce mois-ci (actuel)
# "4" = Sélection personnalisée
```

### Classes CSS dynamiques

⚠️ **ATTENTION** : Les classes comme `GJALL4ABIGC`, `GJALL4ABIY`, `GJALL4ABCV` sont générées par GWT (Google Web Toolkit) et **peuvent changer** lors de mises à jour du site Linxo.

**Si le téléchargement échoue à l'avenir** :
1. Inspectez les éléments dans Chrome (F12)
2. Mettez à jour les classes dans `linxo_connexion.py`
3. Ou utilisez les méthodes de fallback (texte, XPath)

---

## 🔄 Fichier modifié

**Fichier** : [linxo_agent/linxo_connexion.py](c:\Users\PhilippePEREZ\OneDrive\LINXO\linxo_agent\linxo_connexion.py)

**Fonction** : `telecharger_csv_linxo(driver, wait)`

**Lignes** : 185-316

---

## 🎯 Prochaines étapes

1. **Tester le workflow** :
   ```bash
   cd linxo_agent
   python linxo_connexion.py
   ```

2. **Vérifier le CSV téléchargé** :
   - Dossier : `data/latest.csv`
   - Vérifier qu'il contient bien les transactions du mois

3. **Tester le workflow complet** :
   ```bash
   python linxo_agent.py --skip-notifications
   ```

4. **Si tout fonctionne, lancer en production** :
   ```bash
   python linxo_agent.py
   ```

---

## ✅ Statut

✅ Workflow de téléchargement mis à jour
✅ Suit exactement le processus décrit
✅ Multiples fallbacks pour robustesse
✅ Logs détaillés pour debug
✅ Prêt pour tests

---

**Le système est maintenant configuré pour télécharger les transactions du mois en cours en suivant le workflow exact de Linxo.**
