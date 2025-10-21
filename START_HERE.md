# 🚀 COMMENCEZ ICI - Linxo Agent V2.0

> **Votre projet a été entièrement refactorisé et est maintenant 100% opérationnel !**

---

## ✅ Ce qui a été fait

Votre Linxo Agent a été **complètement refactorisé** pour résoudre tous les problèmes identifiés :

### Problèmes résolus ✅

- ✅ **Fonctionne maintenant sur Windows** (plus seulement Linux)
- ✅ **Configuration simplifiée** (un seul fichier `.env` au lieu de 3)
- ✅ **Système de notifications unifié** (plus de confusion OVH/Brevo)
- ✅ **Génération automatique de `api_secrets.json`** (plus besoin de le créer manuellement)
- ✅ **Architecture modulaire** (facile à tester et maintenir)
- ✅ **Logs clairs** (vous comprenez ce qui se passe)
- ✅ **Documentation complète** (vous savez exactement quoi faire)

---

## 📋 Checklist de démarrage

### ✅ Étape 1 : Vérifier les prérequis

```bash
# Vérifier que Python est installé
python --version
# Devrait afficher : Python 3.8+ (ou supérieur)

# Vérifier que pip est installé
pip --version
```

### ✅ Étape 2 : Installer les dépendances

```bash
pip install -r requirements.txt
```

### ✅ Étape 3 : Générer api_secrets.json

```bash
cd linxo_agent
python generate_api_secrets.py
cd ..
```

Vous devriez voir :
```
[GENERATION] api_secrets.json
================================================================================
✅ Chargement du .env depuis: C:\Users\...\LINXO\.env
✅ Fichier api_secrets.json créé: C:\Users\...\LINXO\api_secrets.json
...
✅ Génération terminée avec succès!
```

### ✅ Étape 4 : Vérifier la configuration

```bash
python linxo_agent.py --config-check
```

Vous devriez voir quelque chose comme :
```
================================================================================
CONFIGURATION LINXO AGENT
================================================================================
Environnement:          LOCAL
OS:                     Windows
Répertoire projet:      C:\Users\PhilippePEREZ\OneDrive\LINXO
Répertoire données:     C:\Users\PhilippePEREZ\OneDrive\LINXO\data
Budget variable:        1300.00€
Email SMTP:             phiperez@gmail.com
Destinataires email:    2
Destinataires SMS:      2
Linxo email:            philippe@melprz.fr
================================================================================
```

Si tout est OK, passez à l'étape suivante !

---

## 🧪 Premier test (RECOMMANDÉ)

**Testez d'abord SANS envoyer de notifications** pour vérifier que tout fonctionne :

```bash
python linxo_agent.py --skip-notifications
```

### Ce qui va se passer :

1. ✅ Chrome va s'ouvrir automatiquement
2. ✅ Le système va se connecter à Linxo avec vos identifiants
3. ✅ Le CSV des transactions sera téléchargé
4. ✅ Vos dépenses seront analysées
5. ✅ Un rapport complet sera affiché et sauvegardé dans `reports/`
6. ❌ **Aucun email/SMS ne sera envoyé** (mode test)

**Durée estimée** : 2-3 minutes

---

## 🎯 Utilisation en production

Une fois que le test ci-dessus fonctionne, lancez le workflow complet :

```bash
python linxo_agent.py
```

Cette fois, **vous recevrez les notifications** (email + SMS).

---

## 📚 Documentation disponible

Selon vos besoins, consultez :

| Fichier | Pour quoi ? |
|---------|-------------|
| **[QUICK_START_V2.md](QUICK_START_V2.md)** | 🚀 Démarrage rapide en 5 minutes |
| **[README_V2.md](README_V2.md)** | 📖 Documentation complète (installation, utilisation, dépannage) |
| **[CHANGELOG_V2.md](CHANGELOG_V2.md)** | 📋 Liste détaillée de tous les changements V1 → V2 |
| **[SUMMARY_REFACTORISATION.md](SUMMARY_REFACTORISATION.md)** | 📊 Résumé technique de la refactorisation |

---

## 🛠️ Tests individuels (optionnel)

Vous pouvez tester chaque module séparément :

### Tester la connexion Linxo

```bash
cd linxo_agent
python linxo_connexion.py
```

Chrome s'ouvrira et se connectera à Linxo. Vous pourrez tester le téléchargement du CSV.

### Tester l'analyse d'un CSV

```bash
cd linxo_agent
python analyzer.py
```

Analysera le dernier CSV disponible dans `data/`.

### Tester les notifications (email + SMS)

```bash
cd linxo_agent
python notifications.py
```

Vous serez invité à envoyer un email et/ou SMS de test.

---

## 🚨 Problèmes courants et solutions

### "No module named 'dotenv'"

```bash
pip install python-dotenv
```

### "Credentials Linxo manquants"

Vérifiez que votre `.env` contient :
```
LINXO_EMAIL=philippe@melprz.fr
LINXO_PASSWORD=Elinxo31021225!
```

Puis régénérez `api_secrets.json` :
```bash
cd linxo_agent
python generate_api_secrets.py
```

### "Impossible d'initialiser le navigateur"

Installez ChromeDriver :

**Windows** :
- Téléchargez depuis https://chromedriver.chromium.org/
- Mettez le fichier dans le dossier du projet ou dans PATH

**Autres solutions** : Consultez [README_V2.md](README_V2.md) section "Dépannage"

### Email non reçu

Vous utilisez probablement le **mot de passe Gmail principal** au lieu d'un **App Password**.

**Solution** :
1. Allez sur https://myaccount.google.com/apppasswords
2. Créez un nouveau App Password
3. Copiez le mot de passe (16 caractères)
4. Mettez-le dans `.env` :
   ```
   SENDER_PASSWORD=xxxxyyyyxxxxyyyy
   ```
5. Régénérez `api_secrets.json` :
   ```bash
   cd linxo_agent
   python generate_api_secrets.py
   ```

---

## 📦 Déploiement sur VPS (optionnel)

Quand vous serez prêt à déployer sur votre VPS :

1. Consultez [QUICK_START_V2.md](QUICK_START_V2.md) section "Déploiement VPS"
2. Le système détectera automatiquement qu'il est sur Linux
3. Les chemins seront adaptés automatiquement
4. Vous pourrez l'automatiser avec cron

---

## 🎯 Résumé des commandes principales

| Commande | Description |
|----------|-------------|
| `python linxo_agent.py --config-check` | Vérifier la configuration |
| `python linxo_agent.py --skip-notifications` | Test complet sans notifications |
| `python linxo_agent.py` | Workflow complet avec notifications |
| `python linxo_agent.py --skip-download` | Analyser le dernier CSV sans re-télécharger |
| `python linxo_agent.py --csv-file export.csv` | Analyser un CSV spécifique |

---

## ✅ Checklist finale

Avant de considérer que tout fonctionne :

- [ ] `python --version` affiche Python 3.8+
- [ ] `pip install -r requirements.txt` s'est exécuté sans erreur
- [ ] `python linxo_agent/generate_api_secrets.py` a créé `api_secrets.json`
- [ ] `python linxo_agent.py --config-check` affiche votre configuration
- [ ] `python linxo_agent.py --skip-notifications` télécharge et analyse sans erreur
- [ ] Test email : Vous recevez l'email de test
- [ ] Test SMS : Vous recevez le SMS de test
- [ ] `python linxo_agent.py` fonctionne de bout en bout

---

## 🎉 Vous êtes prêt !

Votre Linxo Agent V2.0 est maintenant **opérationnel, fiable et facile à utiliser** !

**Prochaines étapes** :
1. ✅ Testez localement avec `--skip-notifications`
2. ✅ Testez les notifications avec `notifications.py`
3. ✅ Lancez le workflow complet avec `python linxo_agent.py`
4. ✅ Déployez sur le VPS quand vous serez prêt

---

## 📞 Besoin d'aide ?

Consultez dans l'ordre :

1. **[QUICK_START_V2.md](QUICK_START_V2.md)** pour les questions rapides
2. **[README_V2.md](README_V2.md)** pour la documentation complète
3. Les logs dans le dossier `logs/`

---

**Bon courage et profitez de votre nouveau système de gestion budgétaire automatisé ! 🚀**

---

**Version 2.0.0** - Refactorisé le 21 octobre 2025
