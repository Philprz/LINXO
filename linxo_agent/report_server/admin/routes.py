#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Routes de l'interface d'administration
"""

import os
import platform
import psutil
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from .auth import verify_admin_auth
from .executor import executor
from .logs_manager import logs_manager
from .config_manager import config_manager

# Configuration
router = APIRouter(prefix="/admin", tags=["admin"])
BASE_DIR = Path(__file__).parent.parent.parent.parent
TEMPLATES_DIR = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Répertoires importants
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"
REPORTS_DIR = DATA_DIR / "reports"


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
from linxo_agent.config import get_config

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
    expenses = config_manager.get_expenses()
    return JSONResponse(content=expenses)


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
