#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Linxo Analysis Runner - Version moderne avec rapports HTML complets
Utilise le système d'analyse moderne avec génération de rapports HTML par famille
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd

# Add the linxo_agent directory to path
linxo_agent_dir = Path(__file__).parent
sys.path.insert(0, str(linxo_agent_dir))

# Import des modules modernes
from analyzer import analyser_csv, lire_csv_linxo
from notifications import NotificationManager
from config import get_config
from reports import build_daily_report


def should_send_notification(frequency='weekly', notification_file='.last_whatsapp_notification'):
    """
    Détermine si une notification doit être envoyée selon la fréquence configurée.

    Args:
        frequency: Fréquence d'envoi:
            - 'daily': tous les jours
            - 'weekly': tous les 7 jours
            - 'monthly': tous les 30 jours
            - 'monday', 'tuesday', ..., 'sunday': jour spécifique de la semaine
            - nombre (int ou str): tous les N jours
        notification_file: Fichier stockant la date de dernière notification

    Returns:
        bool: True si notification doit être envoyée, False sinon
    """
    # Déterminer le répertoire de base
    config = get_config()
    notification_path = config.base_dir / notification_file

    # Lire la dernière date d'envoi si disponible
    last_notification_date = None
    if notification_path.exists():
        try:
            with open(notification_path, 'r') as f:
                last_date_str = f.read().strip()
                last_notification_date = datetime.fromisoformat(last_date_str)
        except (ValueError, OSError) as e:
            print(f"[WARN] Erreur lecture {notification_file}: {e}")
            last_notification_date = None

    now = datetime.now()

    # Jours de la semaine (0=Lundi, 6=Dimanche)
    weekdays = {
        'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
        'friday': 4, 'saturday': 5, 'sunday': 6
    }

    # Vérifier si c'est un jour de semaine spécifique
    if isinstance(frequency, str) and frequency.lower() in weekdays:
        target_weekday = weekdays[frequency.lower()]
        current_weekday = now.weekday()

        # Si ce n'est pas le bon jour, skip
        if current_weekday != target_weekday:
            day_names = ['lundi', 'mardi', 'mercredi', 'jeudi', 'vendredi', 'samedi', 'dimanche']
            print(f"[INFO] Notification WhatsApp programmée pour {frequency} (aujourd'hui: {day_names[current_weekday]})")
            return False

        # C'est le bon jour, vérifier si pas déjà envoyé cette semaine
        if last_notification_date is not None:
            # Vérifier si dernier envoi était dans les 6 derniers jours (même semaine)
            delta = now - last_notification_date
            if delta < timedelta(days=6):
                print(f"[INFO] Notification WhatsApp déjà envoyée cette semaine (le {last_notification_date.strftime('%Y-%m-%d')})")
                return False

        print(f"[INFO] Notification WhatsApp due (jour: {frequency})")
        return True

    # Si jamais envoyé, envoyer maintenant
    if last_notification_date is None:
        return True

    # Calculer le délai selon la fréquence
    delta = now - last_notification_date

    if frequency == 'daily':
        threshold = timedelta(days=1)
    elif frequency == 'weekly':
        threshold = timedelta(days=7)
    elif frequency == 'monthly':
        threshold = timedelta(days=30)
    else:
        # Fréquence personnalisée en jours
        try:
            days = int(frequency)
            threshold = timedelta(days=days)
        except (ValueError, TypeError):
            print(f"[WARN] Fréquence invalide '{frequency}', utilisation de 'weekly' par défaut")
            threshold = timedelta(days=7)

    should_send = delta >= threshold

    if should_send:
        print(f"[INFO] Notification WhatsApp due (dernière: {last_notification_date.strftime('%Y-%m-%d')})")
    else:
        remaining = threshold - delta
        remaining_hours = int(remaining.total_seconds() / 3600)
        print(f"[INFO] Notification WhatsApp pas encore due ({remaining_hours}h restantes)")

    return should_send


def mark_notification_sent(notification_file='.last_whatsapp_notification'):
    """
    Enregistre la date d'envoi de la dernière notification.

    Args:
        notification_file: Fichier stockant la date de dernière notification
    """
    config = get_config()
    notification_path = config.base_dir / notification_file

    try:
        with open(notification_path, 'w') as f:
            f.write(datetime.now().isoformat())
        print(f"[INFO] Date notification WhatsApp enregistrée: {notification_path}")
    except OSError as e:
        print(f"[WARN] Erreur enregistrement date notification: {e}")


def main():
    """Exécute l'analyse avec génération de rapports HTML et notifications"""
    print("\n" + "=" * 80)
    print("LINXO AGENT - ANALYSE AVEC RAPPORTS HTML COMPLETS")
    print("=" * 80)
    print(f"Demarrage: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    # Charger la configuration
    config = get_config()

    # Determiner le fichier CSV a utiliser
    if len(sys.argv) > 1:
        # Custom CSV file provided
        csv_file = sys.argv[1]
        if not os.path.exists(csv_file):
            print(f"ERREUR: Le fichier {csv_file} n'existe pas")
            sys.exit(1)
        print(f"Utilisation du fichier: {csv_file}")
    else:
        # Use default CSV file with duplicate check
        csv_file = config.get_latest_csv(check_already_sent=True)

        if csv_file is None:
            print("\n" + "=" * 80)
            print("AUCUN NOUVEAU FICHIER A TRAITER")
            print("=" * 80)
            print("Le dernier fichier CSV a deja ete envoye aujourd'hui.")
            print("Aucune action necessaire.")
            print("=" * 80)
            sys.exit(0)

        if not csv_file or not Path(csv_file).exists():
            print("\n" + "=" * 80)
            print("ERREUR: AUCUN FICHIER CSV DISPONIBLE")
            print("=" * 80)
            print("Aucun fichier CSV n'a ete trouve dans les repertoires de donnees.")
            print("Le telechargement automatique a probablement echoue.")
            print("=" * 80)

            # Envoyer une alerte technique
            try:
                notification_manager = NotificationManager()
                error_msg = f"""Le système n'a trouvé aucun fichier CSV à traiter.

Répertoires vérifiés:
- {config.data_dir}
- {config.downloads_dir}

Causes possibles:
1. Le téléchargement automatique depuis Linxo a échoué
2. Problème de connexion au site Linxo
3. Changement de l'interface Linxo nécessitant une mise à jour du scraper
4. Problème d'authentification (identifiants expirés ou 2FA non géré)

Logs à consulter:
- Derniers logs cron: ~/LINXO/logs/daily_report_*.log
- Logs de téléchargement si disponibles

Action immédiate requise pour rétablir le service.
"""
                notification_manager.send_technical_alert(
                    error_type="Aucun fichier CSV disponible",
                    error_message=error_msg
                )
                print("\n[ALERTE] Email d'alerte technique envoye a phiperez@gmail.com")
            except Exception as e:
                print(f"\n[ERREUR] Impossible d'envoyer l'alerte technique: {e}")

            sys.exit(1)

        print(f"Utilisation du dernier CSV: {csv_file}")

        # Vérifier l'âge du fichier et envoyer une alerte si trop ancien
        import time
        file_age_seconds = time.time() - Path(csv_file).stat().st_mtime
        file_age_days = file_age_seconds / 86400

        if file_age_days > 2:
            print(f"\n[WARN] Le fichier CSV a {file_age_days:.1f} jours")
            print(f"[WARN] Le fichier est potentiellement obsolète")

            # Envoyer une alerte technique
            try:
                notification_manager = NotificationManager()
                file_mtime = datetime.fromtimestamp(Path(csv_file).stat().st_mtime)
                error_msg = f"""Le fichier CSV utilisé pour l'analyse est obsolète.

Fichier: {Path(csv_file).name}
Dernière modification: {file_mtime.strftime('%Y-%m-%d %H:%M:%S')}
Âge du fichier: {file_age_days:.1f} jours

Le fichier CSV devrait être mis à jour quotidiennement.
Un fichier de plus de 2 jours indique que le téléchargement automatique ne fonctionne plus.

Causes possibles:
1. Le téléchargement automatique depuis Linxo a échoué
2. Problème de connexion au site Linxo
3. Changement de l'interface Linxo nécessitant une mise à jour du scraper
4. Problème d'authentification (identifiants expirés ou 2FA non géré)

Logs à consulter:
- Derniers logs cron: ~/LINXO/logs/daily_report_*.log
- Logs de téléchargement si disponibles

Action requise pour rétablir le téléchargement automatique.
"""
                notification_manager.send_technical_alert(
                    error_type="Fichier CSV obsolète",
                    error_message=error_msg
                )
                print("\n[ALERTE] Email d'alerte technique envoyé à phiperez@gmail.com")
            except Exception as e:
                print(f"\n[ERREUR] Impossible d'envoyer l'alerte technique: {e}")

    # ETAPE 1: Analyse des depenses
    print("\n" + "=" * 80)
    print("ETAPE 1: ANALYSE DES DEPENSES")
    print("=" * 80)

    try:
        analysis_result = analyser_csv(csv_file)

        if not analysis_result:
            print("ERREUR: Echec de l'analyse")

            # Envoyer une alerte technique
            try:
                notification_manager = NotificationManager()
                error_msg = f"""L'analyse du fichier CSV a échoué.

Fichier analysé: {csv_file}

Causes possibles:
1. Format du fichier CSV invalide ou corrompu
2. Colonnes manquantes dans l'export Linxo
3. Encodage du fichier incorrect
4. Fichier vide ou incomplet

Logs à consulter:
- ~/LINXO/logs/daily_report_*.log

Vérifiez manuellement le contenu du fichier CSV.
"""
                notification_manager.send_technical_alert(
                    error_type="Échec d'analyse du CSV",
                    error_message=error_msg
                )
                print("\n[ALERTE] Email d'alerte technique envoye a phiperez@gmail.com")
            except Exception as alert_error:
                print(f"\n[ERREUR] Impossible d'envoyer l'alerte technique: {alert_error}")

            sys.exit(1)

        print("\nAnalyse terminee!")
        print(f"  Transactions: {analysis_result['total_transactions']}")
        print(f"  Depenses fixes: {analysis_result['total_fixes']:.2f}E")
        print(f"  Depenses variables: {analysis_result['total_variables']:.2f}E")
        print(f"  Budget: {analysis_result['budget_max']:.2f}E")
        print(f"  Reste: {analysis_result['reste']:.2f}E")

        # Afficher le rapport texte
        print("\n" + analysis_result['rapport'])

    except Exception as e:
        print(f"ERREUR durant l'analyse: {e}")
        import traceback
        error_traceback = traceback.format_exc()
        traceback.print_exc()

        # Envoyer une alerte technique avec la stacktrace
        try:
            notification_manager = NotificationManager()
            error_msg = f"""Une erreur inattendue s'est produite lors de l'analyse.

Fichier analysé: {csv_file}

Erreur: {str(e)}

Stacktrace complète:
{error_traceback}

Logs à consulter:
- ~/LINXO/logs/daily_report_*.log

Une intervention technique est nécessaire pour corriger ce problème.
"""
            notification_manager.send_technical_alert(
                error_type="Erreur inattendue lors de l'analyse",
                error_message=error_msg
            )
            print("\n[ALERTE] Email d'alerte technique envoye a phiperez@gmail.com")
        except Exception as alert_error:
            print(f"\n[ERREUR] Impossible d'envoyer l'alerte technique: {alert_error}")

        sys.exit(1)

    # ETAPE 2: Generation des rapports HTML par famille
    print("\n" + "=" * 80)
    print("ETAPE 2: GENERATION DES RAPPORTS HTML PAR FAMILLE")
    print("=" * 80)

    report_index = None
    try:
        # Lire le CSV avec la fonction qui ajoute la colonne 'famille'
        transactions, exclus = lire_csv_linxo(csv_file)

        # Convertir en DataFrame pour build_daily_report
        df_data = []
        for t in transactions:
            df_data.append({
                'date': t.get('date_str', ''),
                'date_str': t.get('date_str', ''),
                'libelle': t.get('libelle', ''),
                'montant': t.get('montant', 0.0),
                'categorie': t.get('categorie', 'Non classe'),
                'compte': t.get('compte', ''),
            })

        df = pd.DataFrame(df_data)

        # Récupérer les variables d'environnement pour les rapports
        base_url = os.getenv('REPORTS_BASE_URL') or "https://linxo.appliprz.ovh/reports"
        signing_key = os.getenv('REPORTS_SIGNING_KEY')

        if not os.getenv('REPORTS_BASE_URL'):
            print(f"[INFO] REPORTS_BASE_URL non defini, utilisation de {base_url}")

        # Générer le conseil du LLM
        from analyzer import generer_conseil_budget
        conseil_llm = generer_conseil_budget(
            analysis_result['total_variables'],
            analysis_result['budget_max']
        )

        # Générer les rapports HTML
        report_date = datetime.now().strftime('%Y-%m-%d')
        report_index = build_daily_report(
            df=df,
            report_date=report_date,
            base_url=base_url,
            signing_key=signing_key,
            budget_max=analysis_result['budget_max'],
            conseil_llm=conseil_llm,
            analysis_result=analysis_result
        )

        print(f"\nRapports HTML generes!")
        print(f"  Repertoire: {report_index.base_dir}")
        print(f"  Familles: {len(report_index.families)}")
        print(f"  Total depenses: {report_index.grand_total:.2f}E")
        print(f"  URL index: {base_url}/{report_date}/index.html")

        # Upload vers le VPS
        print("\n" + "=" * 80)
        print("UPLOAD DES RAPPORTS VERS LE VPS")
        print("=" * 80)

        try:
            from upload_reports import upload_reports_to_vps, upload_static_files

            # Upload des rapports HTML
            data_reports = Path(__file__).parent.parent / "data" / "reports"
            if data_reports.exists():
                success = upload_reports_to_vps(data_reports)
                if success:
                    print("\n[OK] Rapports synchronises avec le VPS!")
                else:
                    print("\n[WARN] Echec de la synchronisation des rapports")

            # Upload des fichiers statiques (CSS) si nécessaire
            static_dir = Path(__file__).parent.parent / "static"
            if static_dir.exists():
                upload_static_files(static_dir)

        except Exception as upload_error:
            print(f"\n[WARN] Erreur lors de l'upload vers le VPS: {upload_error}")
            print("Les rapports sont disponibles localement mais pas sur le VPS")

    except Exception as e:
        print(f"WARNING: Erreur lors de la generation des rapports HTML: {e}")
        import traceback
        traceback.print_exc()
        print("Poursuite avec les notifications...")

    # ETAPE 3: Envoi des notifications (email HTML + SMS + WhatsApp)
    print("\n" + "=" * 80)
    print("ETAPE 3: ENVOI DES NOTIFICATIONS (EMAIL HTML + SMS + WHATSAPP)")
    print("=" * 80)

    try:
        notification_manager = NotificationManager()
        notif_results = notification_manager.send_budget_notification(
            analysis_result,
            report_index=report_index
        )

        # Verifier les resultats
        sms_ok = notif_results.get('sms', False)
        email_ok = notif_results.get('email', False)

        # Envoi WhatsApp si activé et si fréquence OK
        whatsapp_ok = False
        if config.whatsapp_enabled:
            # Récupérer la fréquence depuis .env ou utiliser weekly par défaut
            notification_frequency = os.getenv('NOTIFICATION_FREQUENCY', 'weekly')

            if should_send_notification(frequency=notification_frequency):
                print("\n[INFO] Envoi notification WhatsApp...")

                # Préparer le message WhatsApp (résumé budget similaire au SMS)
                try:
                    from report_formatter_v2 import formater_sms_v2  # type: ignore
                    total_depenses = float(analysis_result.get('total_variables', 0) or 0)
                    budget_max = float(analysis_result.get('budget_max', 0) or 0)
                    reste = budget_max - total_depenses
                    pct = (total_depenses / budget_max * 100) if budget_max > 0 else 0.0
                    whatsapp_msg = formater_sms_v2(total_depenses, budget_max, reste, pct)
                except Exception:  # pylint: disable=broad-except
                    total_depenses = float(analysis_result.get('total_variables', 0) or 0)
                    budget_max = float(analysis_result.get('budget_max', 0) or 0)
                    reste = budget_max - total_depenses
                    pct = (total_depenses / budget_max * 100) if budget_max > 0 else 0.0
                    whatsapp_msg = (
                        f"Budget: {total_depenses:.0f}/{budget_max:.0f}€ "
                        f"({pct:.0f}%), reste {reste:.0f}€"
                    )

                # Envoyer via WhatsApp
                whatsapp_ok = notification_manager.send_whatsapp(whatsapp_msg)

                if whatsapp_ok:
                    print("[OK] Notification WhatsApp envoyée")
                    mark_notification_sent()
                else:
                    print("[WARN] Échec envoi WhatsApp")
            else:
                print("[INFO] Notification WhatsApp non due, skip")
        else:
            print("[INFO] WhatsApp désactivé, skip")

        if sms_ok or email_ok or whatsapp_ok:
            print("\nNotifications envoyees!")
            print(f"  Email HTML: {'OK' if email_ok else 'ECHEC'}")
            print(f"  SMS: {'OK' if sms_ok else 'ECHEC'}")
            print(f"  WhatsApp: {'OK' if whatsapp_ok else 'SKIP/ECHEC'}")

            # Marquer le fichier comme envoyé
            config.mark_csv_as_sent(Path(csv_file))
        else:
            print("WARNING: Aucune notification n'a pu etre envoyee")

            # Envoyer une alerte technique
            try:
                error_msg = f"""L'envoi des notifications a échoué (email ET SMS).

Fichier analysé: {csv_file}
Date du rapport: {datetime.now().strftime('%Y-%m-%d')}

Résultats de l'analyse:
- Dépenses variables: {analysis_result['total_variables']:.2f}€
- Budget: {analysis_result['budget_max']:.2f}€
- Reste: {analysis_result['reste']:.2f}€

Causes possibles:
1. Problème de configuration SMTP
2. Identifiants email expirés ou invalides
3. Problème de configuration OVH SMS
4. Problème de connectivité réseau

Logs à consulter:
- ~/LINXO/logs/daily_report_*.log

Action requise: Vérifier la configuration des emails et SMS.
"""
                notification_manager.send_technical_alert(
                    error_type="Échec d'envoi des notifications",
                    error_message=error_msg
                )
                print("\n[ALERTE] Email d'alerte technique envoye a phiperez@gmail.com")
            except Exception as alert_error:
                print(f"\n[ERREUR] Impossible d'envoyer l'alerte technique: {alert_error}")

    except Exception as e:
        print(f"ERREUR durant l'envoi des notifications: {e}")
        import traceback
        traceback.print_exc()
        # Ne pas quitter avec erreur, l'analyse a reussi

    # ETAPE 4: Sauvegarder le rapport texte
    print("\n" + "=" * 80)
    print("ETAPE 4: SAUVEGARDE DU RAPPORT TEXTE")
    print("=" * 80)

    try:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        rapport_file = config.reports_dir / f"rapport_linxo_{timestamp}.txt"

        with open(rapport_file, 'w', encoding='utf-8') as f:
            f.write(analysis_result['rapport'])

        print(f"Rapport sauvegarde: {rapport_file}")

    except Exception as e:
        print(f"WARNING: Erreur lors de la sauvegarde du rapport: {e}")

    # RESUME FINAL
    print("\n" + "=" * 80)
    print("ANALYSE TERMINEE AVEC SUCCES")
    print("=" * 80)
    print(f"Fin: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

if __name__ == "__main__":
    main()
