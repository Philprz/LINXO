#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module de gestion et agrégation des familles de dépenses
Regroupe les dépenses fixes liées et calcule les totaux par famille
"""


class ExpenseFamilyAggregator:
    """Agrège les dépenses par famille et gère les budgets associés"""

    def __init__(self, config):
        """
        Initialise l'aggregator

        Args:
            config: Instance de Config avec les données
        """
        self.config = config
        self.familles_config = config.depenses_data.get('familles_depenses', [])

    def _normalize_libelle(self, libelle):
        """Normalise un libellé pour comparaison"""
        return libelle.upper().strip()

    def _match_libelle(self, libelle_transaction, ref_libelle):
        """
        Vérifie si un libellé de transaction correspond à une référence

        Args:
            libelle_transaction: Libellé de la transaction
            ref_libelle: Libellé de référence (peut être partiel)

        Returns:
            bool: True si match
        """
        trans_norm = self._normalize_libelle(libelle_transaction)
        ref_norm = self._normalize_libelle(ref_libelle)

        # Matching par substring (comme dans analyzer.py)
        return ref_norm in trans_norm

    def aggregate_by_family(self, depenses_fixes_transactions):
        """
        Regroupe les transactions de dépenses fixes par famille

        Args:
            depenses_fixes_transactions: Liste des transactions identifiées comme fixes

        Returns:
            dict: Agrégation par famille avec totaux et détails
        """
        families_aggregated = {}

        for famille_config in self.familles_config:
            nom_famille = famille_config['nom']
            membres_config = famille_config.get('membres', [])
            mode_affichage = famille_config.get('mode_affichage', 'detail')
            budget_mensuel = famille_config.get('budget_mensuel', 0)
            alerte_si_depasse = famille_config.get('alerte_si_depasse', False)

            # Collecter les transactions appartenant à cette famille
            transactions_famille = []

            for transaction in depenses_fixes_transactions:
                libelle_trans = transaction.get('libelle_complet', transaction.get('libelle', ''))

                # Vérifier si cette transaction correspond à un membre de la famille
                for membre in membres_config:
                    ref_libelle = membre.get('ref_libelle', '')

                    if self._match_libelle(libelle_trans, ref_libelle):
                        transactions_famille.append(transaction)
                        break  # Ne compter qu'une fois

            # Calculer le total
            total_famille = sum(abs(t.get('montant', 0)) for t in transactions_famille)

            # Déterminer le statut du budget
            if budget_mensuel > 0:
                pourcentage = (total_famille / budget_mensuel * 100) if budget_mensuel > 0 else 0

                if total_famille > budget_mensuel:
                    statut = 'depasse'
                elif pourcentage >= 90:
                    statut = 'attention'
                else:
                    statut = 'ok'
            else:
                statut = 'pas_de_budget'
                pourcentage = 0

            families_aggregated[nom_famille] = {
                'nom': nom_famille,
                'description': famille_config.get('description', ''),
                'total': total_famille,
                'budget': budget_mensuel,
                'pourcentage': pourcentage,
                'statut': statut,
                'alerte': alerte_si_depasse and statut == 'depasse',
                'mode_affichage': mode_affichage,
                'transactions': transactions_famille,
                'categorie': famille_config.get('categorie', ''),
                'nb_transactions': len(transactions_famille)
            }

        return families_aggregated

    def detect_missing_family_members(self, familles_aggregees, current_month_number):
        """
        Détecte les membres de famille attendus mais absents ce mois

        Args:
            familles_aggregees: Résultat de aggregate_by_family()
            current_month_number: Numéro du mois (1-12)

        Returns:
            list: Liste des membres manquants avec alertes
        """
        missing_members = []

        for nom_famille, data in familles_aggregees.items():
            famille_config = next(
                (f for f in self.familles_config if f['nom'] == nom_famille),
                None
            )

            if not famille_config:
                continue

            membres_config = famille_config.get('membres', [])
            transactions_trouvees = data['transactions']

            # Identifier les membres trouvés
            membres_trouves_refs = set()
            for transaction in transactions_trouvees:
                libelle_trans = transaction.get('libelle_complet', transaction.get('libelle', ''))
                for membre in membres_config:
                    ref_libelle = membre.get('ref_libelle', '')
                    if self._match_libelle(libelle_trans, ref_libelle):
                        membres_trouves_refs.add(ref_libelle)

            # Vérifier les membres manquants
            for membre in membres_config:
                ref_libelle = membre.get('ref_libelle', '')

                if ref_libelle not in membres_trouves_refs:
                    missing_members.append({
                        'famille': nom_famille,
                        'membre_manquant': ref_libelle,
                        'description': f"Transaction attendue '{ref_libelle}' non trouvee dans famille '{nom_famille}'"
                    })

        return missing_members

    def get_family_summary(self, familles_aggregees):
        """
        Génère un résumé textuel des familles de dépenses

        Args:
            familles_aggregees: Résultat de aggregate_by_family()

        Returns:
            str: Résumé formaté
        """
        if not familles_aggregees:
            return "Aucune famille de depenses configuree"

        lines = []
        lines.append("="*80)
        lines.append("FAMILLES DE DEPENSES")
        lines.append("="*80)

        for nom_famille, data in sorted(familles_aggregees.items()):
            lines.append("")
            lines.append(f"{nom_famille:<50} | {data['total']:>10.2f} EUR")

            if data['budget'] > 0:
                budget_info = f"{data['total']:.2f} / {data['budget']:.2f} EUR ({data['pourcentage']:.0f}%)"
                lines.append(f"  Budget: {budget_info}")

            # Statut
            if data['statut'] == 'depasse':
                depassement = data['total'] - data['budget']
                lines.append(f"  [!] ALERTE : Budget depasse de {depassement:.2f} EUR")
            elif data['statut'] == 'attention':
                lines.append(f"  [!] Attention : {data['pourcentage']:.0f}% du budget utilise")
            elif data['statut'] == 'ok':
                reste = data['budget'] - data['total']
                lines.append(f"  [OK] Dans le budget (reste {reste:.2f} EUR)")

            # Détails si mode_affichage == 'detail'
            if data['mode_affichage'] == 'detail' and data['transactions']:
                lines.append(f"  Details ({data['nb_transactions']} transaction(s)):")
                for trans in data['transactions']:
                    libelle = trans.get('libelle_complet', trans.get('libelle', ''))[:40]
                    montant = abs(trans.get('montant', 0))
                    lines.append(f"    - {libelle:<40} | {montant:>10.2f} EUR")

        lines.append("="*80)
        return "\n".join(lines)

    def get_alerts(self, familles_aggregees):
        """
        Récupère toutes les alertes de budgets dépassés

        Args:
            familles_aggregees: Résultat de aggregate_by_family()

        Returns:
            list: Liste des alertes
        """
        alerts = []

        for nom_famille, data in familles_aggregees.items():
            if data.get('alerte', False):
                depassement = data['total'] - data['budget']
                alerts.append({
                    'famille': nom_famille,
                    'total': data['total'],
                    'budget': data['budget'],
                    'depassement': depassement,
                    'message': f"ALERTE : Famille '{nom_famille}' depasse le budget de {depassement:.2f} EUR"
                })

        return alerts
