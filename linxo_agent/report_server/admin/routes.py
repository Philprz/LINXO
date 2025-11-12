#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Routes de l'interface d'administration
"""

import calendar
import hashlib
import os
import platform
import psutil
import subprocess
from pathlib import Path
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from .auth import verify_admin_auth
from .executor import executor
from .logs_manager import logs_manager
from .config_manager import config_manager
from .feedback_manager import feedback_manager
from linxo_agent.analyzer import lire_csv_linxo, analyser_transactions
from linxo_agent.config import get_config

# Configuration
router = APIRouter(prefix="/admin", tags=["admin"])
BASE_DIR = Path(__file__).parent.parent.parent.parent
TEMPLATES_DIR = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Répertoires importants
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"
REPORTS_DIR = DATA_DIR / "reports"

PERIODICITY_MONTHS = {
    'mensuel': list(range(1, 13)),
    'bimestriel': [1, 3, 5, 7, 9, 11],
    'trimestriel': [1, 4, 7, 10],
    'semestriel': [1, 7],
    'annuel': [1],
}
DEFAULT_OCCURRENCE_DAY = 5


def _parse_date(value: Optional[str]) -> Optional[date]:
    """Parse divers formats de date simples."""
    if not value:
        return None
    for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(value, fmt).date()
        except (ValueError, TypeError):
            continue
    return None


def _normalize_months(entry: Dict[str, Any]) -> List[int]:
    """Retourne la liste des mois sélectionnés pour une entrée finance."""
    raw_months = entry.get('mois_occurrence')
    if not raw_months:
        periodicite = str(entry.get('periodicite', 'mensuel')).lower()
        raw_months = PERIODICITY_MONTHS.get(periodicite, list(range(1, 13)))

    normalized: List[int] = []
    for value in raw_months:
        try:
            month_value = int(value)
        except (TypeError, ValueError):
            continue
        if 1 <= month_value <= 12:
            normalized.append(month_value)

    if not normalized:
        normalized = list(range(1, 13))

    normalized = sorted(set(normalized))
    entry['mois_occurrence'] = normalized
    return normalized


def _sanitize_day(value: Any) -> int:
    """Normalise le jour de prélèvement."""
    try:
        day_value = int(value)
    except (TypeError, ValueError):
        day_value = DEFAULT_OCCURRENCE_DAY
    return max(1, min(day_value, 31))


def _compute_occurrences(entry: Dict[str, Any], count: int = 12) -> List[Dict[str, Any]]:
    """Calcule les prochaines occurrences d'une dépense ou d'un revenu."""
    months = _normalize_months(entry)
    day = _sanitize_day(entry.get('jour_prelevement'))
    entry['jour_prelevement'] = day

    today = date.today()
    occurrences: List[Dict[str, Any]] = []
    pointer = 0
    horizon_months = 48  # sécurité

    while len(occurrences) < count and pointer < horizon_months:
        target_month = ((today.month - 1 + pointer) % 12) + 1
        target_year = today.year + ((today.month - 1 + pointer) // 12)
        pointer += 1

        if target_month not in months:
            continue

        day_in_month = min(day, calendar.monthrange(target_year, target_month)[1])
        occurrence_date = date(target_year, target_month, day_in_month)
        if occurrence_date < today:
            continue

        occurrences.append({
            'date': occurrence_date.isoformat(),
            'montant': float(entry.get('montant', 0) or 0),
            'mois': target_month,
            'annee': occurrence_date.year
        })

    return occurrences


def _apply_finance_metadata(finance_data: Dict[str, Any]) -> Dict[str, Any]:
    """Enrichit les données financières avec les occurrences futures."""
    for key in ('depenses_fixes', 'revenus'):
        for item in finance_data.get(key, []):
            occurrences = _compute_occurrences(item)
            item['occurrences'] = occurrences
            item['prochaine_occurrence'] = occurrences[0]['date'] if occurrences else None
    return finance_data


def _active_adjustments(adjustments: List[Dict[str, Any]]) -> float:
    """Retourne la somme des ajustements actifs aujourd'hui."""
    today = date.today()
    total = 0.0
    for adj in adjustments:
        try:
            montant = float(adj.get('montant', 0) or 0)
        except (TypeError, ValueError):
            montant = 0.0

        start = _parse_date(adj.get('date_debut')) or date.min
        end = _parse_date(adj.get('date_fin')) or date.max
        if start <= today <= end:
            total += montant
    return total


def _compute_budget_preview(finance_data: Dict[str, Any]) -> Dict[str, float]:
    """Calcule les totaux revenus/dépenses pour l'interface."""
    current_month = datetime.now().month
    total_revenus = sum(
        float(r.get('montant', 0) or 0)
        for r in finance_data.get('revenus', [])
    )

    total_depenses = 0.0
    for depense in finance_data.get('depenses_fixes', []):
        months = depense.get('mois_occurrence') or _normalize_months(depense)
        if current_month in months:
            try:
                total_depenses += float(depense.get('montant', 0) or 0)
            except (TypeError, ValueError):
                continue

    ajustements_actifs = _active_adjustments(finance_data.get('ajustements_budget', []))
    budget_estime = total_revenus - total_depenses + ajustements_actifs

    return {
        'revenus_total': round(total_revenus, 2),
        'depenses_fixes_mois': round(total_depenses, 2),
        'ajustements_actifs': round(ajustements_actifs, 2),
        'budget_estime': round(budget_estime, 2),
    }


def _hash_transaction(transaction: Dict[str, Any]) -> str:
    """Construit un identifiant stable pour une transaction."""
    raw = "|".join([
        str(transaction.get('date_str', '')).strip(),
        str(transaction.get('libelle', '')).strip(),
        str(transaction.get('montant', '')).strip(),
        str(transaction.get('compte', '')).strip(),
    ])
    return hashlib.sha1(raw.encode('utf-8', errors='ignore')).hexdigest()


def _serialize_transaction(transaction: Dict[str, Any]) -> Dict[str, Any]:
    """Formate une transaction pour l'API de reclassification."""
    montant = float(transaction.get('montant', 0) or 0)
    return {
        'id': _hash_transaction(transaction),
        'date': transaction.get('date_str'),
        'libelle': transaction.get('libelle'),
        'montant': abs(montant),
        'categorie': transaction.get('categorie', 'Non classé'),
        'compte': transaction.get('compte', ''),
        'notes': transaction.get('notes', ''),
        'labels': transaction.get('labels', ''),
        'ml_confidence': transaction.get('ml_confidence'),
        'depense_recurrente': transaction.get('depense_recurrente'),
        'categorie_fixe': transaction.get('categorie_fixe'),
    }


def get_system_status() -> Dict[str, Any]:
    """
    Récupère le statut système complet

    Returns:
        dict: Informations système
    """
    # Espace disque
    disk_usage = psutil.disk_usage(str(BASE_DIR))

    # Processus Chrome
    chrome_processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info']):
        try:
            if 'chrome' in proc.info['name'].lower():
                chrome_processes.append({
                    'pid': proc.info['pid'],
                    'name': proc.info['name'],
                    'cpu': proc.info['cpu_percent'],
                    'memory_mb': proc.info['memory_info'].rss / (1024 * 1024)
                })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    # Dernier log cron
    last_cron_status = get_last_cron_status()

    return {
        'system': {
            'platform': platform.system(),
            'hostname': platform.node(),
            'python_version': platform.python_version(),
        },
        'disk': {
            'total_gb': round(disk_usage.total / (1024**3), 2),
            'used_gb': round(disk_usage.used / (1024**3), 2),
            'free_gb': round(disk_usage.free / (1024**3), 2),
            'percent': disk_usage.percent
        },
        'chrome': {
            'process_count': len(chrome_processes),
            'processes': chrome_processes
        },
        'cron': last_cron_status,
        'directories': {
            'data_exists': DATA_DIR.exists(),
            'logs_exists': LOGS_DIR.exists(),
            'reports_exists': REPORTS_DIR.exists(),
            'logs_size_mb': get_directory_size(LOGS_DIR) if LOGS_DIR.exists() else 0
        }
    }


def get_last_cron_status() -> Dict[str, Any]:
    """
    Récupère le statut de la dernière exécution cron

    Returns:
        dict: Statut du dernier cron
    """
    if not LOGS_DIR.exists():
        return {'status': 'unknown', 'message': 'Répertoire logs introuvable'}

    # Chercher le dernier fichier log
    log_files = sorted(LOGS_DIR.glob('daily_report_*.log'), reverse=True)

    if not log_files:
        return {'status': 'unknown', 'message': 'Aucun log trouvé'}

    last_log = log_files[0]

    try:
        # Lire les dernières lignes du log
        with open(last_log, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # Analyser le contenu pour détecter succès/erreur
        has_success = any('[SUCCESS]' in line for line in lines[-20:])
        has_error = any('[ERROR]' in line for line in lines[-20:])

        # Extraire la date de modification du fichier
        mtime = datetime.fromtimestamp(last_log.stat().st_mtime)

        # Déterminer le statut
        if has_error:
            status = 'error'
            message = 'Erreurs détectées'
        elif has_success:
            status = 'success'
            message = 'Exécution réussie'
        else:
            status = 'warning'
            message = 'Statut incertain'

        return {
            'status': status,
            'message': message,
            'timestamp': mtime.isoformat(),
            'log_file': last_log.name,
            'lines_count': len(lines)
        }

    except Exception as e:
        return {
            'status': 'error',
            'message': f'Erreur lecture log: {str(e)}',
            'log_file': last_log.name
        }


def get_directory_size(directory: Path) -> float:
    """
    Calcule la taille d'un répertoire en Mo

    Args:
        directory: Chemin du répertoire

    Returns:
        float: Taille en Mo
    """
    total_size = 0
    try:
        for file in directory.rglob('*'):
            if file.is_file():
                total_size += file.stat().st_size
    except Exception:
        pass

    return round(total_size / (1024 * 1024), 2)


@router.get("/", response_class=HTMLResponse)
async def admin_dashboard(
    request: Request,
    authenticated: bool = Depends(verify_admin_auth)
):
    """
    Dashboard principal de l'interface d'administration

    Args:
        request: Requête FastAPI
        authenticated: Dépendance d'authentification

    Returns:
        HTMLResponse: Page HTML du dashboard
    """
    system_status = get_system_status()

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "status": system_status,
            "page_title": "Dashboard",
            "active_page": "dashboard"
        }
    )


@router.get("/api/status")
async def api_system_status(
    authenticated: bool = Depends(verify_admin_auth)
):
    """
    API endpoint pour récupérer le statut système (pour auto-refresh)

    Args:
        authenticated: Dépendance d'authentification

    Returns:
        JSONResponse: Statut système en JSON
    """
    return JSONResponse(content=get_system_status())


@router.post("/api/cleanup-chrome")
async def api_cleanup_chrome(
    authenticated: bool = Depends(verify_admin_auth)
):
    """
    Nettoie les processus Chrome zombies

    Args:
        authenticated: Dépendance d'authentification

    Returns:
        JSONResponse: Résultat de l'opération
    """
    killed_count = 0
    errors = []

    for proc in psutil.process_iter(['pid', 'name']):
        try:
            if 'chrome' in proc.info['name'].lower():
                proc.kill()
                killed_count += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            errors.append(str(e))

    return JSONResponse(content={
        'success': True,
        'killed_count': killed_count,
        'errors': errors
    })


@router.get("/logs", response_class=HTMLResponse)
async def admin_logs(
    request: Request,
    authenticated: bool = Depends(verify_admin_auth)
):
    """
    Page de visualisation des logs

    Args:
        request: Requête FastAPI
        authenticated: Dépendance d'authentification

    Returns:
        HTMLResponse: Page HTML des logs
    """
    return templates.TemplateResponse(
        "logs.html",
        {
            "request": request,
            "page_title": "Logs",
            "active_page": "logs"
        }
    )


@router.get("/config", response_class=HTMLResponse)
async def admin_config(
    request: Request,
    authenticated: bool = Depends(verify_admin_auth)
):
    """
    Page de gestion de la configuration

    Args:
        request: Requête FastAPI
        authenticated: Dépendance d'authentification

    Returns:
        HTMLResponse: Page HTML de configuration
    """
    return templates.TemplateResponse(
        "config.html",
        {
            "request": request,
            "page_title": "Configuration",
            "active_page": "config"
        }
    )


@router.get("/classification", response_class=HTMLResponse)
async def admin_classification(
    request: Request,
    authenticated: bool = Depends(verify_admin_auth)
):
    """
    Page de gestion des corrections de classification
    """
    return templates.TemplateResponse(
        "classification.html",
        {
            "request": request,
            "page_title": "Corrections",
            "active_page": "classification"
        }
    )


# ============================================================================
# ENDPOINTS D'ACTIONS MANUELLES (Phase 3)
# ============================================================================

@router.post("/api/execute")
async def api_execute_full(
    authenticated: bool = Depends(verify_admin_auth)
):
    """
    Lance une exécution complète (téléchargement + analyse + notifications)

    Args:
        authenticated: Dépendance d'authentification

    Returns:
        JSONResponse: ID de la tâche lancée
    """
    import sys
    python_exe = sys.executable

    command = [
        python_exe,
        str(BASE_DIR / "linxo_agent.py")
    ]

    task_id = await executor.execute_task("Exécution complète", command)

    return JSONResponse(content={
        'success': True,
        'task_id': task_id,
        'message': 'Exécution complète lancée en arrière-plan'
    })


@router.post("/api/download-csv")
async def api_download_csv(
    authenticated: bool = Depends(verify_admin_auth)
):
    """
    Lance le téléchargement du CSV seulement (sans notifications)

    Args:
        authenticated: Dépendance d'authentification

    Returns:
        JSONResponse: ID de la tâche lancée
    """
    import sys
    python_exe = sys.executable

    command = [
        python_exe,
        str(BASE_DIR / "linxo_agent.py"),
        "--skip-notifications"
    ]

    task_id = await executor.execute_task("Téléchargement CSV", command)

    return JSONResponse(content={
        'success': True,
        'task_id': task_id,
        'message': 'Téléchargement CSV lancé en arrière-plan'
    })


@router.post("/api/analyze")
async def api_analyze_only(
    authenticated: bool = Depends(verify_admin_auth)
):
    """
    Lance l'analyse du dernier CSV (sans téléchargement)

    Args:
        authenticated: Dépendance d'authentification

    Returns:
        JSONResponse: ID de la tâche lancée
    """
    import sys
    python_exe = sys.executable

    # Vérifier que le CSV existe
    latest_csv = BASE_DIR / "data" / "latest.csv"
    if not latest_csv.exists():
        return JSONResponse(
            status_code=400,
            content={
                'success': False,
                'error': 'Aucun fichier CSV trouvé. Téléchargez d\'abord le CSV.'
            }
        )

    command = [
        python_exe,
        str(BASE_DIR / "linxo_agent.py"),
        "--skip-download"
    ]

    task_id = await executor.execute_task("Analyse du CSV", command)

    return JSONResponse(content={
        'success': True,
        'task_id': task_id,
        'message': 'Analyse lancée en arrière-plan'
    })


@router.post("/api/diagnostic")
async def api_diagnostic(
    authenticated: bool = Depends(verify_admin_auth)
):
    """
    Lance le diagnostic avec auto-réparation

    Args:
        authenticated: Dépendance d'authentification

    Returns:
        JSONResponse: ID de la tâche lancée
    """
    import sys
    python_exe = sys.executable

    command = [
        python_exe,
        str(BASE_DIR / "diagnostic_linxo_html.py")
    ]

    task_id = await executor.execute_task("Diagnostic auto-réparation", command)

    return JSONResponse(content={
        'success': True,
        'task_id': task_id,
        'message': 'Diagnostic lancé en arrière-plan'
    })


@router.post("/api/test-email")
async def api_test_email(
    authenticated: bool = Depends(verify_admin_auth)
):
    """
    Envoie un email de test

    Args:
        authenticated: Dépendance d'authentification

    Returns:
        JSONResponse: ID de la tâche lancée
    """
    import sys
    python_exe = sys.executable

    command = [
        python_exe,
        "-c",
        """
import sys
sys.path.insert(0, '.')
from linxo_agent.notifications import send_email_notification
config = get_config()
result = send_email_notification(
    subject='[TEST] Email de test depuis interface admin',
    body='<h2>Test réussi !</h2><p>Cet email de test a été envoyé depuis l\\'interface d\\'administration.</p>',
    is_html=True
)
print(f'Email envoyé avec succès' if result else 'Échec envoi email')
"""
    ]

    task_id = await executor.execute_task("Test email", command)

    return JSONResponse(content={
        'success': True,
        'task_id': task_id,
        'message': 'Test email lancé'
    })


@router.post("/api/test-sms")
async def api_test_sms(
    authenticated: bool = Depends(verify_admin_auth)
):
    """
    Envoie un SMS de test

    Args:
        authenticated: Dépendance d'authentification

    Returns:
        JSONResponse: ID de la tâche lancée
    """
    import sys
    python_exe = sys.executable

    command = [
        python_exe,
        "-c",
        """
import sys
sys.path.insert(0, '.')
from linxo_agent.notifications import send_sms_notification

result = send_sms_notification('[TEST] SMS de test depuis interface admin')
print(f'SMS envoyé avec succès' if result else 'Échec envoi SMS')
"""
    ]

    task_id = await executor.execute_task("Test SMS", command)

    return JSONResponse(content={
        'success': True,
        'task_id': task_id,
        'message': 'Test SMS lancé'
    })


@router.get("/api/task/{task_id}")
async def api_get_task_status(
    task_id: str,
    authenticated: bool = Depends(verify_admin_auth)
):
    """
    Récupère le statut d'une tâche

    Args:
        task_id: ID de la tâche
        authenticated: Dépendance d'authentification

    Returns:
        JSONResponse: Statut de la tâche
    """
    task_status = await executor.get_task_status(task_id)

    if not task_status:
        return JSONResponse(
            status_code=404,
            content={'error': 'Tâche non trouvée'}
        )

    return JSONResponse(content=task_status)


@router.get("/api/tasks")
async def api_list_tasks(
    authenticated: bool = Depends(verify_admin_auth),
    limit: int = 50
):
    """
    Liste les tâches récentes

    Args:
        authenticated: Dépendance d'authentification
        limit: Nombre maximum de tâches

    Returns:
        JSONResponse: Liste des tâches
    """
    tasks = await executor.list_tasks(limit=limit)

    return JSONResponse(content={
        'tasks': tasks,
        'count': len(tasks)
    })


# ============================================================================
# ENDPOINTS DE GESTION DES LOGS (Phase 4)
# ============================================================================

@router.get("/api/logs/files")
async def api_list_log_files(
    authenticated: bool = Depends(verify_admin_auth)
):
    """
    Liste tous les fichiers de logs disponibles

    Args:
        authenticated: Dépendance d'authentification

    Returns:
        JSONResponse: Liste des fichiers de logs
    """
    files = logs_manager.list_log_files()

    return JSONResponse(content={
        'files': files,
        'count': len(files)
    })


@router.get("/api/logs/content")
async def api_get_log_content(
    file_name: str,
    offset: int = 0,
    limit: int = 100,
    level: Optional[str] = None,
    search: Optional[str] = None,
    authenticated: bool = Depends(verify_admin_auth)
):
    """
    Récupère le contenu d'un fichier de log avec pagination et filtres

    Args:
        file_name: Nom du fichier de log
        offset: Ligne de départ (pagination)
        limit: Nombre de lignes à retourner
        level: Filtrer par niveau (SUCCESS, ERROR, WARNING, INFO)
        search: Recherche dans le contenu
        authenticated: Dépendance d'authentification

    Returns:
        JSONResponse: Contenu du log
    """
    lines, total, has_more = logs_manager.read_log_file(
        file_name=file_name,
        offset=offset,
        limit=limit,
        level_filter=level,
        search_query=search
    )

    return JSONResponse(content={
        'lines': lines,
        'total': total,
        'offset': offset,
        'limit': limit,
        'has_more': has_more,
        'file_name': file_name
    })


@router.get("/api/logs/tail")
async def api_tail_log(
    file_name: str,
    lines: int = 50,
    authenticated: bool = Depends(verify_admin_auth)
):
    """
    Récupère les dernières lignes d'un fichier de log (tail -f like)

    Args:
        file_name: Nom du fichier de log
        lines: Nombre de lignes à retourner
        authenticated: Dépendance d'authentification

    Returns:
        JSONResponse: Dernières lignes du log
    """
    log_lines = logs_manager.tail_log_file(file_name, lines)

    return JSONResponse(content={
        'lines': log_lines,
        'count': len(log_lines),
        'file_name': file_name
    })


# ============================================================================
# ENDPOINTS DE GESTION DE CONFIGURATION (Phase 5)
# ============================================================================

@router.get("/api/config/budget")
async def api_get_budget(
    authenticated: bool = Depends(verify_admin_auth)
):
    """Récupère la configuration du budget"""
    budget = config_manager.get_budget()
    return JSONResponse(content=budget)


@router.put("/api/config/budget")
async def api_update_budget(
    request: Request,
    authenticated: bool = Depends(verify_admin_auth)
):
    """Met à jour le budget"""
    data = await request.json()
    new_budget = data.get('budget_variable')

    if new_budget is None:
        return JSONResponse(
            status_code=400,
            content={'success': False, 'error': 'budget_variable requis'}
        )

    try:
        new_budget = int(new_budget)
    except ValueError:
        return JSONResponse(
            status_code=400,
            content={'success': False, 'error': 'budget_variable doit être un entier'}
        )

    success = config_manager.update_budget(new_budget)

    return JSONResponse(content={
        'success': success,
        'message': 'Budget mis à jour' if success else 'Échec mise à jour'
    })


@router.get("/api/config/reports-url")
async def api_get_reports_url(
    authenticated: bool = Depends(verify_admin_auth)
):
    """Retourne l'URL publique configurée pour les rapports."""
    return JSONResponse(content=config_manager.get_reports_base_url())


@router.put("/api/config/reports-url")
async def api_update_reports_url(
    request: Request,
    authenticated: bool = Depends(verify_admin_auth)
):
    """Met à jour l'URL publique des rapports."""
    data = await request.json()
    base_url = data.get('reports_base_url')
    if not base_url:
        return JSONResponse(
            status_code=400,
            content={'success': False, 'error': 'reports_base_url requis'}
        )

    success = config_manager.update_reports_base_url(base_url)
    return JSONResponse(content={
        'success': success,
        'message': 'URL mise à jour' if success else 'Échec mise à jour'
    })


@router.get("/api/config/recipients")
async def api_get_recipients(
    authenticated: bool = Depends(verify_admin_auth)
):
    """Récupère les destinataires des notifications"""
    recipients = config_manager.get_notification_recipients()
    return JSONResponse(content=recipients)


@router.put("/api/config/recipients")
async def api_update_recipients(
    request: Request,
    authenticated: bool = Depends(verify_admin_auth)
):
    """Met à jour les destinataires des notifications"""
    data = await request.json()

    success = config_manager.update_notification_recipients(
        emails=data.get('email'),
        sms=data.get('sms')
    )

    return JSONResponse(content={
        'success': success,
        'message': 'Destinataires mis à jour' if success else 'Échec mise à jour'
    })


@router.get("/api/config/expenses")
async def api_get_expenses(
    authenticated: bool = Depends(verify_admin_auth)
):
    """Récupère toutes les dépenses récurrentes"""
    finance_data = config_manager.get_expenses()
    _apply_finance_metadata(finance_data)
    finance_data['budget_preview'] = _compute_budget_preview(finance_data)
    return JSONResponse(content=finance_data)


@router.post("/api/config/expenses")
async def api_add_expense(
    request: Request,
    authenticated: bool = Depends(verify_admin_auth)
):
    """Ajoute une nouvelle dépense récurrente"""
    expense = await request.json()

    # Validation basique
    required_fields = ['libelle', 'montant', 'categorie', 'identifiant']
    for field in required_fields:
        if field not in expense:
            return JSONResponse(
                status_code=400,
                content={'success': False, 'error': f'Champ {field} requis'}
            )

    success = config_manager.add_expense(expense)

    return JSONResponse(content={
        'success': success,
        'message': 'Dépense ajoutée' if success else 'Échec ajout'
    })


@router.put("/api/config/expenses/{expense_id}")
async def api_update_expense(
    expense_id: int,
    request: Request,
    authenticated: bool = Depends(verify_admin_auth)
):
    """Met à jour une dépense récurrente"""
    expense = await request.json()

    success = config_manager.update_expense(expense_id, expense)

    return JSONResponse(content={
        'success': success,
        'message': 'Dépense mise à jour' if success else 'Échec mise à jour'
    })


@router.delete("/api/config/expenses/{expense_id}")
async def api_delete_expense(
    expense_id: int,
    authenticated: bool = Depends(verify_admin_auth)
):
    """Supprime une dépense récurrente"""
    success = config_manager.delete_expense(expense_id)

    return JSONResponse(content={
        'success': success,
        'message': 'Dépense supprimée' if success else 'Échec suppression'
    })


# ---------------------------------------------------------------------------
# Revenus
# ---------------------------------------------------------------------------


@router.post("/api/config/revenues")
async def api_add_income(
    request: Request,
    authenticated: bool = Depends(verify_admin_auth)
):
    """Ajoute un revenu."""
    income = await request.json()
    required_fields = ['libelle', 'montant', 'categorie', 'identifiant']
    for field in required_fields:
        if not income.get(field):
            return JSONResponse(
                status_code=400,
                content={'success': False, 'error': f'Champ {field} requis'}
            )

    try:
        income['montant'] = float(income.get('montant', 0))
    except (TypeError, ValueError):
        return JSONResponse(
            status_code=400,
            content={'success': False, 'error': 'Montant invalide'}
        )

    success = config_manager.add_income(income)
    return JSONResponse(content={
        'success': success,
        'message': 'Revenu ajouté' if success else 'Échec ajout'
    })


@router.put("/api/config/revenues/{income_id}")
async def api_update_income(
    income_id: int,
    request: Request,
    authenticated: bool = Depends(verify_admin_auth)
):
    """Met à jour un revenu."""
    income = await request.json()
    try:
        income['montant'] = float(income.get('montant', 0))
    except (TypeError, ValueError):
        return JSONResponse(
            status_code=400,
            content={'success': False, 'error': 'Montant invalide'}
        )

    success = config_manager.update_income(income_id, income)
    return JSONResponse(content={
        'success': success,
        'message': 'Revenu mis à jour' if success else 'Échec mise à jour'
    })


@router.delete("/api/config/revenues/{income_id}")
async def api_delete_income(
    income_id: int,
    authenticated: bool = Depends(verify_admin_auth)
):
    """Supprime un revenu."""
    success = config_manager.delete_income(income_id)
    return JSONResponse(content={
        'success': success,
        'message': 'Revenu supprimé' if success else 'Échec suppression'
    })


# ---------------------------------------------------------------------------
# Ajustements budget
# ---------------------------------------------------------------------------


@router.post("/api/config/adjustments")
async def api_add_adjustment(
    request: Request,
    authenticated: bool = Depends(verify_admin_auth)
):
    """Ajoute un ajustement manuel."""
    adjustment = await request.json()
    required_fields = ['nom', 'montant', 'date_debut', 'date_fin']
    for field in required_fields:
        if not adjustment.get(field):
            return JSONResponse(
                status_code=400,
                content={'success': False, 'error': f'Champ {field} requis'}
            )

    try:
        adjustment['montant'] = float(adjustment.get('montant', 0))
    except (TypeError, ValueError):
        return JSONResponse(
            status_code=400,
            content={'success': False, 'error': 'Montant invalide'}
        )

    success = config_manager.add_budget_adjustment(adjustment)
    return JSONResponse(content={
        'success': success,
        'message': 'Ajustement ajouté' if success else 'Échec ajout'
    })


@router.put("/api/config/adjustments/{adjustment_id}")
async def api_update_adjustment(
    adjustment_id: int,
    request: Request,
    authenticated: bool = Depends(verify_admin_auth)
):
    """Met à jour un ajustement."""
    adjustment = await request.json()
    try:
        adjustment['montant'] = float(adjustment.get('montant', 0))
    except (TypeError, ValueError):
        return JSONResponse(
            status_code=400,
            content={'success': False, 'error': 'Montant invalide'}
        )

    success = config_manager.update_budget_adjustment(adjustment_id, adjustment)
    return JSONResponse(content={
        'success': success,
        'message': 'Ajustement mis à jour' if success else 'Échec mise à jour'
    })


@router.delete("/api/config/adjustments/{adjustment_id}")
async def api_delete_adjustment(
    adjustment_id: int,
    authenticated: bool = Depends(verify_admin_auth)
):
    """Supprime un ajustement."""
    success = config_manager.delete_budget_adjustment(adjustment_id)
    return JSONResponse(content={
        'success': success,
        'message': 'Ajustement supprimé' if success else 'Échec suppression'
    })


# ---------------------------------------------------------------------------
# Reclassification & feedback ML
# ---------------------------------------------------------------------------


def _load_latest_variable_transactions() -> Dict[str, Any]:
    """Lit le CSV le plus récent et renvoie les transactions variables."""
    latest_csv = DATA_DIR / "latest.csv"
    if not latest_csv.exists():
        raise FileNotFoundError("Aucun fichier latest.csv trouvé")

    transactions, _ = lire_csv_linxo(str(latest_csv))
    if not transactions:
        return {'csv': latest_csv, 'transactions': []}

    analysis = analyser_transactions(
        transactions,
        use_ml=True,
        enable_learning=False,
        enable_familles=False
    )
    return {
        'csv': latest_csv,
        'transactions': analysis.get('depenses_variables', [])
    }


@router.get("/api/classification/transactions")
async def api_get_classification_transactions(
    limit: int = 100,
    authenticated: bool = Depends(verify_admin_auth)
):
    """Retourne les dernières transactions variables pour validation."""
    limit = max(1, min(limit, 500))
    try:
        payload = _load_latest_variable_transactions()
    except FileNotFoundError:
        return JSONResponse(
            status_code=404,
            content={'success': False, 'error': 'Aucun CSV disponible'}
        )
    except Exception as exc:
        return JSONResponse(
            status_code=500,
            content={'success': False, 'error': f'Analyse impossible: {exc}'}
        )

    serialized = [_serialize_transaction(tx) for tx in payload['transactions']]
    serialized.sort(key=lambda item: _parse_date(item.get('date')) or date.min, reverse=True)
    limited = serialized[:limit]

    return JSONResponse(content={
        'success': True,
        'transactions': limited,
        'total': len(serialized),
        'source_csv': str(payload['csv']),
        'generated_at': datetime.utcnow().isoformat()
    })


@router.post("/api/classification/feedback")
async def api_post_classification_feedback(
    request: Request,
    authenticated: bool = Depends(verify_admin_auth)
):
    """Enregistre un feedback utilisateur (correction ou validation)."""
    data = await request.json()
    statut = str(data.get('statut', 'corrige')).lower()
    if statut not in {'corrige', 'correct'}:
        return JSONResponse(
            status_code=400,
            content={'success': False, 'error': 'Statut invalide'}
        )

    if not data.get('transaction_id'):
        return JSONResponse(
            status_code=400,
            content={'success': False, 'error': 'transaction_id requis'}
        )

    if statut == 'corrige' and not data.get('categorie_corrigee'):
        return JSONResponse(
            status_code=400,
            content={'success': False, 'error': 'Nouvelle catégorie requise'}
        )

    try:
        montant = float(data.get('montant', 0) or 0)
    except (TypeError, ValueError):
        montant = 0.0

    feedback_payload = {
        'transaction_id': data.get('transaction_id'),
        'libelle': data.get('libelle', ''),
        'categorie_initiale': data.get('categorie_initiale'),
        'categorie_corrigee': data.get('categorie_corrigee') if statut == 'corrige' else data.get('categorie_initiale'),
        'statut': statut,
        'commentaire': data.get('commentaire'),
        'montant': montant,
        'compte': data.get('compte'),
        'date_transaction': data.get('date_transaction', data.get('date')),
        'confiance': data.get('ml_confidence'),
    }

    feedback_id = feedback_manager.add_feedback(feedback_payload)

    ml_updated = False
    if statut == 'corrige' and feedback_payload['categorie_corrigee'] and (
        feedback_payload['categorie_corrigee'] != feedback_payload['categorie_initiale']
    ):
        try:
            from linxo_agent.smart_classifier import create_classifier
            classifier = create_classifier()
            classifier.record_correction(
                description=feedback_payload['libelle'] or '',
                old_category=feedback_payload['categorie_initiale'] or 'Non classé',
                new_category=feedback_payload['categorie_corrigee'],
                montant=montant
            )
            ml_updated = True
        except Exception:
            ml_updated = False

    return JSONResponse(content={
        'success': True,
        'feedback_id': feedback_id,
        'ml_updated': ml_updated
    })


@router.get("/api/classification/feedback")
async def api_get_feedback_history(
    limit: int = 50,
    authenticated: bool = Depends(verify_admin_auth)
):
    """Retourne l'historique des corrections."""
    limit = max(1, min(limit, 200))
    history = feedback_manager.list_feedback(limit)
    return JSONResponse(content={
        'success': True,
        'history': history
    })
