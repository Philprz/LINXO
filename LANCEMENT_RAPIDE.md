# 🚀 Lancement Rapide - Linxo Agent V2.0

> **Tout est prêt ! Suivez ces 4 étapes pour lancer votre système.**

---

## ⚡ Installation (1 minute)

```bash
# 1. Installer les dépendances
pip install -r requirements.txt

# 2. Générer api_secrets.json
cd linxo_agent
python generate_api_secrets.py
cd ..
```

✅ **Terminé !** Le système est configuré.

---

## 🧪 Premier Test (3 minutes)

```bash
# Test sans envoyer d'email/SMS
python linxo_agent.py --skip-notifications
```

**Ce qui va se passer :**
1. Chrome s'ouvre automatiquement
2. Connexion à Linxo avec vos identifiants
3. Navigation : Historique → Recherche avancée → "Ce mois-ci" → CSV
4. Téléchargement du CSV
5. Analyse des dépenses
6. Affichage du rapport

⏱️ **Durée** : ~2-3 minutes

---

## 🎯 Utilisation Production

```bash
# Workflow complet avec notifications
python linxo_agent.py
```

Cette fois, vous recevrez :
- 📧 Un email détaillé avec le rapport
- 📱 Un SMS avec le résumé budgétaire

---

## 🧰 Commandes Utiles

| Commande | Description |
|----------|-------------|
| `python linxo_agent.py --config-check` | Vérifier la configuration |
| `python linxo_agent.py --skip-download` | Analyser le dernier CSV |
| `python linxo_agent.py --csv-file export.csv` | Analyser un CSV spécifique |
| `cd linxo_agent && python linxo_connexion.py` | Tester la connexion seule |
| `cd linxo_agent && python notifications.py` | Tester les notifications |

---

## 🆘 Problèmes ?

### Email non reçu

**Cause** : Vous utilisez le mot de passe Gmail au lieu de l'App Password

**Solution** :
1. Allez sur https://myaccount.google.com/apppasswords
2. Créez un App Password (16 caractères)
3. Mettez-le dans `.env` :
   ```
   SENDER_PASSWORD=xxxxyyyyxxxxyyyy
   ```
4. Régénérez :
   ```bash
   cd linxo_agent
   python generate_api_secrets.py
   ```

### "Module dotenv not found"

```bash
pip install python-dotenv
```

### Chrome ne se lance pas

**Windows** : Téléchargez ChromeDriver depuis https://chromedriver.chromium.org/

**Linux** :
```bash
sudo apt install chromium-chromedriver
```

---

## 📚 Documentation Complète

Pour aller plus loin :
- **[START_HERE.md](START_HERE.md)** → Guide complet de démarrage
- **[QUICK_START_V2.md](QUICK_START_V2.md)** → Guide détaillé
- **[README_V2.md](README_V2.md)** → Documentation complète
- **[UPDATE_WORKFLOW_CSV.md](UPDATE_WORKFLOW_CSV.md)** → Détails du workflow de téléchargement

---

## ✅ Checklist

Avant de lancer en production :

- [ ] `pip install -r requirements.txt` ✅
- [ ] `python linxo_agent/generate_api_secrets.py` ✅
- [ ] `python linxo_agent.py --config-check` affiche la bonne config ✅
- [ ] `python linxo_agent.py --skip-notifications` fonctionne ✅
- [ ] Test email : `cd linxo_agent && python notifications.py` ✅
- [ ] Workflow complet : `python linxo_agent.py` ✅

---

**C'est parti ! 🎉**
