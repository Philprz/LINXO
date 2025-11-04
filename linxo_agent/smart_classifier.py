#!/usr/bin/env python3
"""
Classification intelligente des transactions avec Machine Learning.

Ce module utilise un modèle ML simple mais efficace pour classifier automatiquement
les transactions bancaires en différentes catégories, avec apprentissage continu.
"""

import json
import pickle
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import re

# Tentative d'import de scikit-learn (optionnel)
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.naive_bayes import MultinomialNB
    from sklearn.pipeline import Pipeline
    import numpy as np
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    print("[WARNING] scikit-learn non disponible. Classification basique activée.")


class SmartClassifier:
    """Classificateur intelligent de transactions avec apprentissage continu."""

    def __init__(self, data_dir: Path):
        """
        Initialise le classificateur.

        Args:
            data_dir: Répertoire pour stocker les données d'apprentissage et le modèle
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.training_data_file = self.data_dir / "training_data.json"
        self.model_file = self.data_dir / "classifier_model.pkl"
        self.corrections_file = self.data_dir / "user_corrections.json"

        # Charger les données d'entraînement
        self.training_data: List[Dict] = self._load_training_data()
        self.corrections: List[Dict] = self._load_corrections()

        # Charger ou créer le modèle
        self.model: Optional[Pipeline] = None
        self.categories: List[str] = []
        if SKLEARN_AVAILABLE:
            self._load_or_create_model()

        # Règles de classification par défaut (fallback)
        self.default_rules = self._load_default_rules()

    def _load_training_data(self) -> List[Dict]:
        """Charge les données d'entraînement depuis le fichier JSON."""
        if self.training_data_file.exists():
            with open(self.training_data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []

    def _save_training_data(self):
        """Sauvegarde les données d'entraînement."""
        with open(self.training_data_file, 'w', encoding='utf-8') as f:
            json.dump(self.training_data, f, indent=2, ensure_ascii=False)

    def _load_corrections(self) -> List[Dict]:
        """Charge les corrections utilisateur."""
        if self.corrections_file.exists():
            with open(self.corrections_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []

    def _save_corrections(self):
        """Sauvegarde les corrections utilisateur."""
        with open(self.corrections_file, 'w', encoding='utf-8') as f:
            json.dump(self.corrections, f, indent=2, ensure_ascii=False)

    def _load_or_create_model(self):
        """Charge le modèle existant ou en crée un nouveau."""
        if self.model_file.exists() and len(self.training_data) > 0:
            try:
                with open(self.model_file, 'rb') as f:
                    data = pickle.load(f)
                    self.model = data['model']
                    self.categories = data['categories']
                print(f"[OK] Modèle ML chargé ({len(self.categories)} catégories)")
            except Exception as e:  # pylint: disable=broad-except
                print(f"[WARNING] Erreur chargement modèle: {e}")
                self._train_model()
        elif len(self.training_data) > 10:  # Besoin d'au moins 10 exemples
            self._train_model()

    def _train_model(self):
        """Entraîne le modèle ML avec les données disponibles."""
        if not SKLEARN_AVAILABLE or len(self.training_data) < 10:
            return

        try:
            # Préparer les données
            texts = [item['description'] for item in self.training_data]
            labels = [item['category'] for item in self.training_data]

            # Créer et entraîner le pipeline
            self.model = Pipeline([
                ('tfidf', TfidfVectorizer(
                    max_features=500,
                    ngram_range=(1, 2),
                    strip_accents='unicode'
                )),
                ('clf', MultinomialNB(alpha=0.1))
            ])

            self.model.fit(texts, labels)
            self.categories = list(set(labels))

            # Sauvegarder le modèle
            with open(self.model_file, 'wb') as f:
                pickle.dump({
                    'model': self.model,
                    'categories': self.categories
                }, f)

            print(f"[OK] Modèle ML entraîné avec {len(texts)} exemples")

        except Exception as e:  # pylint: disable=broad-except
            print(f"[ERROR] Erreur entraînement modèle: {e}")
            self.model = None

    def _load_default_rules(self) -> Dict[str, List[str]]:
        """
        Charge les règles de classification par défaut.

        Returns:
            Dictionnaire {catégorie: [mots-clés]}
        """
        return {
            "Alimentation": [
                "carrefour", "auchan", "leclerc", "casino", "monoprix",
                "lidl", "aldi", "intermarche", "picard", "franprix",
                "supermarche", "hypermarche", "epicerie", "boulangerie",
                "restaurant", "mcdo", "burger king", "kfc", "subway"
            ],
            "Transport": [
                "essence", "carburant", "total", "esso", "bp", "shell",
                "station service", "parking", "autoroute", "peage",
                "sncf", "ratp", "metro", "bus", "navigo", "uber", "taxi"
            ],
            "Santé": [
                "pharmacie", "medecin", "docteur", "hopital", "clinique",
                "dentiste", "opticien", "laboratoire", "mutuelle", "secu"
            ],
            "Logement": [
                "loyer", "edf", "engie", "gaz", "electricite", "eau",
                "veolia", "suez", "internet", "orange", "free", "sfr", "bouygues"
            ],
            "Loisirs": [
                "cinema", "theatre", "concert", "spotify", "netflix",
                "deezer", "amazon prime", "disney", "fnac", "cultura",
                "sport", "salle de sport", "piscine", "tennis"
            ],
            "Vêtements": [
                "zara", "h&m", "kiabi", "uniqlo", "mango", "celio",
                "decathlon", "nike", "adidas", "chaussures", "vetement"
            ],
            "Assurances": [
                "assurance", "axa", "maif", "macif", "matmut", "maaf",
                "allianz", "generali", "mutuelle"
            ],
            "Abonnements": [
                "abonnement", "mensualite", "prelevement", "souscription"
            ]
        }

    def classify(
        self,
        description: str,
        montant: float,
        existing_category: Optional[str] = None
    ) -> Tuple[str, float]:
        """
        Classifie une transaction.

        Args:
            description: Description de la transaction
            montant: Montant de la transaction
            existing_category: Catégorie déjà attribuée (si disponible)

        Returns:
            Tuple (catégorie, score_de_confiance)
        """
        description_clean = description.lower().strip()

        # Si une catégorie existe déjà, on la garde (peut être manuelle)
        if existing_category and existing_category.strip():
            return existing_category, 1.0

        # 1. Essayer le modèle ML si disponible
        if self.model is not None and SKLEARN_AVAILABLE:
            try:
                # Prédiction
                probas = self.model.predict_proba([description_clean])[0]
                best_idx = probas.argmax()
                confidence = float(probas[best_idx])
                category = self.categories[best_idx]

                # Si confiance élevée, on utilise la prédiction ML
                if confidence >= 0.6:
                    return category, confidence

            except Exception:  # pylint: disable=broad-except
                pass

        # 2. Fallback : règles par défaut
        best_match = None
        best_score = 0.0

        for category, keywords in self.default_rules.items():
            score = 0.0
            for keyword in keywords:
                if keyword in description_clean:
                    score += 1.0 / len(keywords)  # Score normalisé

            if score > best_score:
                best_score = score
                best_match = category

        if best_match and best_score > 0:
            return best_match, min(best_score * 0.8, 0.95)  # Max 95% pour règles

        # 3. Catégorie par défaut
        return "Autres dépenses", 0.3

    def add_training_example(
        self,
        description: str,
        category: str,
        montant: float = 0.0
    ):
        """
        Ajoute un exemple d'entraînement.

        Args:
            description: Description de la transaction
            category: Catégorie correcte
            montant: Montant (optionnel)
        """
        example = {
            "description": description.lower().strip(),
            "category": category,
            "montant": montant,
            "date": datetime.now().isoformat()
        }

        # Éviter les doublons
        for item in self.training_data:
            if (item['description'] == example['description'] and
                item['category'] == example['category']):
                return  # Déjà présent

        self.training_data.append(example)
        self._save_training_data()

        # Ré-entraîner le modèle si assez de nouvelles données
        if len(self.training_data) % 10 == 0:  # Tous les 10 exemples
            self._train_model()

    def record_correction(
        self,
        description: str,
        old_category: str,
        new_category: str,
        montant: float = 0.0
    ):
        """
        Enregistre une correction utilisateur.

        Args:
            description: Description de la transaction
            old_category: Catégorie initialement attribuée
            new_category: Catégorie corrigée par l'utilisateur
            montant: Montant
        """
        correction = {
            "description": description,
            "old_category": old_category,
            "new_category": new_category,
            "montant": montant,
            "date": datetime.now().isoformat()
        }

        self.corrections.append(correction)
        self._save_corrections()

        # Ajouter aux données d'entraînement
        self.add_training_example(description, new_category, montant)

        print(f"[LEARNING] Correction enregistrée: '{description}' → {new_category}")

    def get_statistics(self) -> Dict:
        """
        Retourne des statistiques sur le classificateur.

        Returns:
            Dictionnaire de statistiques
        """
        return {
            "training_examples": len(self.training_data),
            "user_corrections": len(self.corrections),
            "ml_model_trained": self.model is not None,
            "categories": self.categories if self.model else list(self.default_rules.keys()),
            "sklearn_available": SKLEARN_AVAILABLE
        }

    def suggest_improvements(self, transactions: List[Dict]) -> List[Dict]:
        """
        Suggère des améliorations de classification pour les transactions.

        Args:
            transactions: Liste de transactions

        Returns:
            Liste de suggestions {transaction, old_category, suggested_category, confidence}
        """
        suggestions = []

        for trans in transactions:
            description = trans.get('description', '')
            current_category = trans.get('categorie', '')
            montant = trans.get('montant', 0.0)

            # Reclassifier
            suggested_category, confidence = self.classify(
                description,
                montant,
                existing_category=None  # Ignorer catégorie actuelle
            )

            # Si différent et confiance élevée, suggérer
            if (suggested_category != current_category and
                confidence >= 0.7 and
                current_category != "Non classé"):
                suggestions.append({
                    "transaction": trans,
                    "old_category": current_category,
                    "suggested_category": suggested_category,
                    "confidence": confidence
                })

        return suggestions


def create_classifier(config_dir: Path = None) -> SmartClassifier:
    """
    Factory pour créer un classificateur.

    Args:
        config_dir: Répertoire de configuration (défaut: ./data/ml)

    Returns:
        Instance de SmartClassifier
    """
    if config_dir is None:
        config_dir = Path(__file__).parent.parent / "data" / "ml"

    return SmartClassifier(config_dir)
