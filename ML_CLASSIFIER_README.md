# 🤖 Classificateur Intelligent par IA

## Vue d'ensemble

Le classificateur intelligent utilise le Machine Learning pour améliorer automatiquement la catégorisation de vos transactions bancaires. Il apprend de vos corrections et s'améliore au fil du temps.

## 📋 Fonctionnalités

### ✅ Classification automatique
- Catégorise automatiquement les transactions sans catégorie
- Utilise un modèle ML (Naive Bayes + TF-IDF) si scikit-learn est disponible
- Fallback sur des règles par défaut sinon

### 🧠 Apprentissage continu
- Enregistre chaque correction que vous faites
- Réentraîne le modèle automatiquement tous les 10 nouveaux exemples
- Améliore sa précision au fil du temps

### 📊 Score de confiance
- Chaque prédiction a un score de confiance (0-100%)
- Seules les prédictions avec >50% de confiance sont appliquées
- Vous savez quelles classifications sont sûres

## 🚀 Installation

### Prérequis (optionnel pour le ML)

```bash
pip install scikit-learn numpy
```

**Note**: Le système fonctionne même sans scikit-learn, mais avec des règles par défaut uniquement.

## 💻 Utilisation

### 1. Utilisation automatique dans l'analyzer

Le classificateur est **activé par défaut** dans l'analyzer. Il améliore automatiquement les transactions sans catégorie ou avec catégorie générique ("Non classé", "Autres").

```python
from analyzer import analyser_csv

# Le classificateur ML est activé par défaut
results = analyser_csv("data/latest.csv")

# Pour désactiver le ML:
results = analyser_csv("data/latest.csv", use_ml=False)
```

### 2. Entraînement et corrections avec l'outil CLI

```bash
python train_classifier.py
```

Menu disponible:
1. **Voir les statistiques** - Nombre d'exemples, état du modèle
2. **Entraîner avec le dernier CSV** - Utilise les catégories existantes
3. **Corriger des classifications** - Interface interactive
4. **Suggérer des améliorations** - Trouve les classifications douteuses
5. **Ajouter un exemple manuel** - Entraîner manuellement

### 3. Workflow recommandé

1. **Premier lancement**: Entraînez avec votre CSV existant
   ```bash
   python train_classifier.py
   # Choix 2: Entraîner avec le dernier CSV
   ```

2. **Utilisation quotidienne**: L'analyzer applique le ML automatiquement
   ```bash
   python run_analysis.py
   ```

3. **Corrections périodiques**: Corrigez les mauvaises classifications
   ```bash
   python train_classifier.py
   # Choix 3: Corriger des classifications
   ```

4. **Améliorations**: Revoyez les suggestions
   ```bash
   python train_classifier.py
   # Choix 4: Suggérer des améliorations
   ```

## 📁 Structure des données

Les données d'apprentissage sont stockées dans `data/ml/`:

```
data/ml/
├── training_data.json       # Exemples d'entraînement
├── user_corrections.json    # Corrections utilisateur
└── classifier_model.pkl     # Modèle ML entraîné
```

### Format des données

**training_data.json**:
```json
[
  {
    "description": "carrefour express paris 15",
    "category": "Alimentation",
    "montant": 45.20,
    "date": "2025-11-04T10:30:00"
  }
]
```

**user_corrections.json**:
```json
[
  {
    "description": "spotify premium",
    "old_category": "Autres",
    "new_category": "Abonnements",
    "montant": 9.99,
    "date": "2025-11-04T11:00:00"
  }
]
```

## 🎯 Catégories par défaut

Le système reconnaît ces catégories principales:
- Alimentation (supermarchés, restaurants)
- Transport (essence, SNCF, parking)
- Santé (pharmacie, médecin)
- Logement (loyer, EDF, internet)
- Loisirs (cinéma, Netflix, Spotify)
- Vêtements (Zara, H&M, Decathlon)
- Assurances (AXA, MAIF, etc.)
- Abonnements (prélèvements mensuels)
- Autres dépenses (par défaut)

**Vous pouvez ajouter vos propres catégories** en corrigeant manuellement les transactions.

## 🔧 Configuration avancée

### Seuil de confiance

Dans `analyzer.py`, ligne 360:
```python
if confidence >= 0.5:  # Confiance minimum
    transaction['categorie'] = new_category
```

Ajustez ce seuil (0.0 à 1.0) selon vos besoins:
- **0.3**: Plus de classifications, moins précises
- **0.5**: Équilibre recommandé
- **0.7**: Moins de classifications, plus précises

### Fréquence de réentraînement

Dans `smart_classifier.py`, ligne 174:
```python
if len(self.training_data) % 10 == 0:  # Tous les 10 exemples
    self._train_model()
```

Ajustez le nombre (10) pour changer la fréquence.

## 📈 Performance

### Métriques

Consultez les statistiques avec:
```bash
python train_classifier.py
# Choix 1: Voir les statistiques
```

Exemple de sortie:
```
Exemples d'entraînement : 250
Corrections utilisateur : 45
Modèle ML entraîné      : Oui
Scikit-learn disponible : Oui

Catégories reconnues (15):
  1. Abonnements
  2. Alimentation
  3. Assurances
  ...
```

### Amélioration au fil du temps

Le modèle s'améliore avec plus de données:
- **< 50 exemples**: Précision ~60-70%
- **50-200 exemples**: Précision ~75-85%
- **> 200 exemples**: Précision ~85-95%

## 🐛 Dépannage

### Le ML ne fonctionne pas

**Problème**: Message "Classificateur ML non disponible"

**Solution**:
```bash
pip install scikit-learn numpy
```

### Mauvaises classifications

**Problème**: Le modèle classifie mal certaines transactions

**Solution**:
1. Corrigez les erreurs via `train_classifier.py` (choix 3)
2. Le modèle apprendra de vos corrections
3. Plus vous corrigez, plus il s'améliore

### Réinitialiser le modèle

**Problème**: Le modèle est complètement à côté

**Solution**:
```bash
# Supprimez les fichiers de données
rm data/ml/training_data.json
rm data/ml/user_corrections.json
rm data/ml/classifier_model.pkl

# Réentraînez depuis zéro
python train_classifier.py
```

## 🎓 Exemples d'utilisation

### Exemple 1: Entraînement initial

```bash
$ python train_classifier.py

OUTIL D'ENTRAINEMENT DU CLASSIFICATEUR INTELLIGENT
================================================================================

1. Voir les statistiques du classificateur
2. Entraîner avec le dernier CSV
...

Votre choix: 2

[1/2] Lecture du dernier CSV...
CSV: data/latest.csv

[2/2] Extraction des exemples d'entraînement...
Trouvé 115 transactions avec catégorie

Ajouter ces 115 exemples ? (o/N): o

[OK] 115 exemples ajoutés avec succès !
[INFO] Le modèle sera réentraîné automatiquement
```

### Exemple 2: Correction interactive

```bash
$ python train_classifier.py

Votre choix: 3

[1/2] Lecture du dernier CSV...
[2/2] 23 transactions sans catégorie trouvées

--- Transaction 1/20 ---
Description : CARREFOUR EXPRESS PARIS 15
Montant     : 45.20 €
Suggestion  : Alimentation (confiance: 85%)

Options:
  [Entrée]  Accepter la suggestion
  [texte]   Entrer une catégorie différente
  [skip]    Passer
  [quit]    Terminer

Votre choix: [Entrée]

[OK] Catégorie 'Alimentation' acceptée
```

## 🔮 Évolutions futures

- ✅ Classification de base avec ML
- ✅ Apprentissage continu
- ✅ Interface CLI de correction
- 🔲 API REST pour intégrations
- 🔲 Dashboard web de visualisation
- 🔲 Export/import de modèles pré-entraînés
- 🔲 Détection d'anomalies (dépenses inhabituelles)
- 🔲 Prédiction de catégorie avant transaction

## 📞 Support

En cas de problème, consultez les logs ou créez une issue avec:
- Le message d'erreur complet
- Le contenu de `data/ml/training_data.json` (anonymisé)
- La version de Python et scikit-learn

---

**Auteur**: Agent Linxo
**Version**: 1.0
**Date**: Novembre 2025
