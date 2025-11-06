#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module d'apprentissage automatique de patterns récurrents
Détecte les nouvelles dépenses récurrentes et les variantes de libellés
"""

import json
from datetime import datetime, timedelta
from collections import defaultdict
from pathlib import Path


class RecurringPatternLearner:
    """Apprend automatiquement les patterns de dépenses récurrentes"""

    def __init__(self, config):
        """
        Initialise le learner

        Args:
            config: Instance de Config avec les chemins et données
        """
        self.config = config
        self.suggestions_file = config.data_dir / 'ml' / 'pattern_suggestions.json'
        self.blacklist_file = config.data_dir / 'ml' / 'pattern_blacklist.json'

        # Créer le répertoire ml s'il n'existe pas
        self.suggestions_file.parent.mkdir(parents=True, exist_ok=True)

        # Charger les suggestions existantes et la blacklist
        self.suggestions = self._load_suggestions()
        self.blacklist = self._load_blacklist()

    def _load_suggestions(self):
        """Charge les suggestions sauvegardées"""
        if self.suggestions_file.exists():
            try:
                with open(self.suggestions_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                return []
        return []

    def _load_blacklist(self):
        """Charge la liste noire des patterns rejetés"""
        if self.blacklist_file.exists():
            try:
                with open(self.blacklist_file, 'r', encoding='utf-8') as f:
                    return set(json.load(f))
            except (json.JSONDecodeError, OSError):
                return set()
        return set()

    def _save_suggestions(self):
        """Sauvegarde les suggestions"""
        with open(self.suggestions_file, 'w', encoding='utf-8') as f:
            json.dump(self.suggestions, f, indent=2, ensure_ascii=False)

    def _save_blacklist(self):
        """Sauvegarde la liste noire"""
        with open(self.blacklist_file, 'w', encoding='utf-8') as f:
            json.dump(list(self.blacklist), f, indent=2, ensure_ascii=False)

    def _normalize_libelle(self, libelle):
        """Normalise un libellé pour comparaison"""
        return libelle.upper().strip()

    def _extract_merchant_name(self, libelle):
        """Extrait le nom du marchand depuis un libellé de transaction"""
        # Patterns communs : "MERCHANT NAME\CITY\" ou "MERCHANT NAME 123"
        libelle_clean = libelle.split('\\')[0]  # Enlever la ville
        libelle_clean = libelle_clean.split(' - ')[0]  # Enlever les détails après tiret
        return libelle_clean.strip()

    def _calculate_amount_variance(self, amounts):
        """Calcule la variance relative des montants"""
        if not amounts or len(amounts) < 2:
            return 0.0

        avg = sum(amounts) / len(amounts)
        if avg == 0:
            return 0.0

        variance = sum((abs(a - avg) / avg) ** 2 for a in amounts) / len(amounts)
        return variance ** 0.5  # Écart-type relatif

    def detect_new_recurring(self, transactions, months_to_analyze=6, min_occurrences=3):
        """
        Détecte les nouvelles dépenses récurrentes dans l'historique

        Args:
            transactions: Liste des transactions à analyser
            months_to_analyze: Nombre de mois à analyser
            min_occurrences: Nombre minimum d'occurrences pour considérer comme récurrent

        Returns:
            Liste de suggestions de nouvelles dépenses récurrentes
        """
        # Filtrer les transactions des N derniers mois
        cutoff_date = datetime.now() - timedelta(days=30 * months_to_analyze)

        # Grouper par merchant (libellé normalisé)
        merchant_transactions = defaultdict(list)

        for transaction in transactions:
            # Ignorer les crédits (revenus)
            montant = transaction.get('montant', 0)
            if montant >= 0:
                continue

            # Parse la date
            date_str = transaction.get('date', '')
            try:
                if '/' in date_str:
                    transaction_date = datetime.strptime(date_str, '%d/%m/%Y')
                else:
                    transaction_date = datetime.strptime(date_str, '%Y-%m-%d')
            except (ValueError, TypeError):
                continue

            # Ignorer si trop vieux
            if transaction_date < cutoff_date:
                continue

            # Extraire le merchant
            libelle = transaction.get('libelle_complet', transaction.get('libelle', ''))
            merchant = self._extract_merchant_name(libelle)
            merchant_norm = self._normalize_libelle(merchant)

            # Ignorer si dans la blacklist
            if merchant_norm in self.blacklist:
                continue

            merchant_transactions[merchant_norm].append({
                'libelle': libelle,
                'montant': abs(montant),
                'date': transaction_date,
                'categorie': transaction.get('categorie', 'Non classe')
            })

        # Analyser chaque merchant pour détecter récurrence
        new_suggestions = []
        depenses_fixes_existantes = self.config.depenses_data.get('depenses_fixes', [])
        existing_patterns = set()

        # Construire la liste des patterns existants
        for depense in depenses_fixes_existantes:
            libelle_raw = depense.get('libelle', '')
            if isinstance(libelle_raw, list):
                for lib in libelle_raw:
                    existing_patterns.add(self._normalize_libelle(lib))
            else:
                existing_patterns.add(self._normalize_libelle(libelle_raw))

        for merchant_norm, txns in merchant_transactions.items():
            # Vérifier si déjà une dépense fixe connue
            if merchant_norm in existing_patterns:
                continue

            # Vérifier le nombre d'occurrences
            if len(txns) < min_occurrences:
                continue

            # Calculer les statistiques
            amounts = [t['montant'] for t in txns]
            avg_amount = sum(amounts) / len(amounts)
            amount_variance = self._calculate_amount_variance(amounts)

            # Calculer la fréquence (jours entre transactions)
            dates = sorted([t['date'] for t in txns])
            intervals = [(dates[i+1] - dates[i]).days for i in range(len(dates) - 1)]
            avg_interval = sum(intervals) / len(intervals) if intervals else 0

            # Déterminer la périodicité
            if 25 <= avg_interval <= 35:
                periodicite = 'mensuel'
                confidence = 0.9 if amount_variance < 0.1 else 0.7
            elif 85 <= avg_interval <= 95:
                periodicite = 'trimestriel'
                confidence = 0.8 if amount_variance < 0.1 else 0.6
            elif 350 <= avg_interval <= 380:
                periodicite = 'annuel'
                confidence = 0.8 if amount_variance < 0.1 else 0.6
            else:
                # Fréquence irrégulière
                continue

            # Déterminer la tolérance recommandée selon la variance
            if amount_variance < 0.05:
                recommended_tolerance = 0.05
            elif amount_variance < 0.15:
                recommended_tolerance = 0.20
            elif amount_variance < 0.40:
                recommended_tolerance = 0.30
            else:
                recommended_tolerance = 0.50

            # Créer la suggestion
            suggestion = {
                'libelle': txns[0]['libelle'],  # Prendre le premier libellé comme exemple
                'identifiant': merchant_norm.title(),  # Nom lisible
                'montant': round(avg_amount, 2),
                'montant_tolerance': recommended_tolerance,
                'categorie': txns[0]['categorie'],
                'periodicite': periodicite,
                'commentaire': f"Auto-detecte: {len(txns)} occurrences sur {months_to_analyze} mois",
                'confidence': round(confidence, 2),
                'occurrences': len(txns),
                'amount_variance': round(amount_variance, 3),
                'suggestion_date': datetime.now().isoformat()
            }

            new_suggestions.append(suggestion)

        return new_suggestions

    def detect_libelle_variants(self, depenses_fixes, transactions, months_to_analyze=6):
        """
        Détecte les variantes de libellés pour les dépenses fixes existantes

        Args:
            depenses_fixes: Liste des dépenses fixes configurées
            transactions: Liste des transactions récentes
            months_to_analyze: Nombre de mois à analyser

        Returns:
            Liste de suggestions de nouveaux libellés à ajouter
        """
        cutoff_date = datetime.now() - timedelta(days=30 * months_to_analyze)

        suggestions = []

        for depense in depenses_fixes:
            libelle_raw = depense.get('libelle', '')
            patterns_existants = []

            if isinstance(libelle_raw, list):
                patterns_existants = [self._normalize_libelle(lib) for lib in libelle_raw]
            else:
                patterns_existants = [self._normalize_libelle(libelle_raw)]

            montant_ref = depense.get('montant', 0)
            tolerance = depense.get('montant_tolerance', 0.05)

            # Chercher des transactions similaires avec libellé différent
            similar_transactions = []

            for transaction in transactions:
                montant = abs(transaction.get('montant', 0))

                # Vérifier si le montant correspond (avec tolérance)
                if montant_ref > 0:
                    if abs(montant - montant_ref) / montant_ref > tolerance:
                        continue

                # Vérifier la date
                date_str = transaction.get('date', '')
                try:
                    if '/' in date_str:
                        transaction_date = datetime.strptime(date_str, '%d/%m/%Y')
                    else:
                        transaction_date = datetime.strptime(date_str, '%Y-%m-%d')
                except (ValueError, TypeError):
                    continue

                if transaction_date < cutoff_date:
                    continue

                # Vérifier si le libellé est différent des patterns existants
                libelle = transaction.get('libelle_complet', transaction.get('libelle', ''))
                libelle_norm = self._normalize_libelle(libelle)

                # Si le libellé contient déjà un pattern existant, passer
                if any(pattern in libelle_norm for pattern in patterns_existants):
                    continue

                # Transaction potentiellement similaire
                similar_transactions.append({
                    'libelle': libelle,
                    'libelle_norm': libelle_norm,
                    'montant': montant,
                    'date': transaction_date
                })

            # Si on a trouvé des transactions similaires, suggérer d'ajouter le libellé
            if similar_transactions:
                # Grouper par libellé normalisé
                grouped = defaultdict(list)
                for txn in similar_transactions:
                    grouped[txn['libelle_norm']].append(txn)

                for libelle_norm, txns in grouped.items():
                    if len(txns) >= 2:  # Au moins 2 occurrences
                        suggestion = {
                            'action': 'add_libelle_variant',
                            'depense_existante': depense.get('identifiant', depense.get('libelle', '')),
                            'nouveau_libelle': txns[0]['libelle'],
                            'occurrences': len(txns),
                            'montant_moyen': round(sum(t['montant'] for t in txns) / len(txns), 2),
                            'confidence': 0.8 if len(txns) >= 3 else 0.6,
                            'suggestion_date': datetime.now().isoformat()
                        }
                        suggestions.append(suggestion)

        return suggestions

    def detect_missing_recurring(self, depenses_fixes, transactions_this_month):
        """
        Détecte les dépenses fixes attendues mais absentes ce mois

        Args:
            depenses_fixes: Liste des dépenses fixes configurées
            transactions_this_month: Transactions du mois en cours

        Returns:
            Liste des dépenses manquantes avec suggestions
        """
        # Construire la liste des libellés détectés ce mois
        detected_patterns = set()

        for transaction in transactions_this_month:
            libelle = transaction.get('libelle_complet', transaction.get('libelle', ''))
            detected_patterns.add(self._normalize_libelle(libelle))

        # Vérifier chaque dépense fixe
        missing = []

        for depense in depenses_fixes:
            # Vérifier la périodicité
            periodicite = depense.get('periodicite', 'mensuel').lower()
            if periodicite != 'mensuel':
                # Pour l'instant, on ne gère que les mensuelles
                continue

            # Vérifier si détectée
            libelle_raw = depense.get('libelle', '')
            patterns = []

            if isinstance(libelle_raw, list):
                patterns = [self._normalize_libelle(lib) for lib in libelle_raw]
            else:
                patterns = [self._normalize_libelle(libelle_raw)]

            # Vérifier si au moins un pattern a été détecté
            found = any(
                any(pattern in detected_lib for pattern in patterns)
                for detected_lib in detected_patterns
            )

            if not found:
                missing.append({
                    'depense': depense,
                    'libelles_attendus': patterns,
                    'montant_attendu': depense.get('montant', 0)
                })

        return missing

    def add_suggestion(self, suggestion):
        """Ajoute une suggestion à la liste"""
        self.suggestions.append(suggestion)
        self._save_suggestions()

    def remove_suggestion(self, index):
        """Supprime une suggestion par index"""
        if 0 <= index < len(self.suggestions):
            self.suggestions.pop(index)
            self._save_suggestions()

    def blacklist_pattern(self, pattern):
        """Ajoute un pattern à la blacklist"""
        self.blacklist.add(self._normalize_libelle(pattern))
        self._save_blacklist()

    def get_suggestions(self):
        """Retourne toutes les suggestions actives"""
        return self.suggestions

    def clear_suggestions(self):
        """Efface toutes les suggestions"""
        self.suggestions = []
        self._save_suggestions()
