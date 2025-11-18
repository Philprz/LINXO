#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gestionnaire d'exécution asynchrone pour les actions administratives
"""

import asyncio
import subprocess
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, List
from enum import Enum

BASE_DIR = Path(__file__).parent.parent.parent.parent


class TaskStatus(str, Enum):
    """Statut d'une tâche"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    ERROR = "error"


class Task:
    """Représente une tâche en cours d'exécution"""

    def __init__(self, task_id: str, name: str, command: List[str]):
        self.id = task_id
        self.name = name
        self.command = command
        self.status = TaskStatus.PENDING
        self.output: List[str] = []
        self.error: Optional[str] = None
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.exit_code: Optional[int] = None

    def to_dict(self) -> dict:
        """Convertit la tâche en dictionnaire"""
        return {
            "id": self.id,
            "name": self.name,
            "status": self.status.value,
            "output": self.output,
            "error": self.error,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "exit_code": self.exit_code,
            "duration_seconds": (
                (self.end_time - self.start_time).total_seconds()
                if self.start_time and self.end_time
                else None
            )
        }


class TaskExecutor:
    """Gestionnaire de tâches asynchrones"""

    def __init__(self):
        self.tasks: Dict[str, Task] = {}
        self._lock = asyncio.Lock()

    async def execute_task(self, name: str, command: List[str]) -> str:
        """
        Lance l'exécution d'une tâche en arrière-plan

        Args:
            name: Nom de la tâche
            command: Commande à exécuter (liste)

        Returns:
            str: ID de la tâche
        """
        task_id = str(uuid.uuid4())
        task = Task(task_id, name, command)

        async with self._lock:
            self.tasks[task_id] = task

        # Lancer l'exécution en arrière-plan
        asyncio.create_task(self._run_task(task))

        return task_id

    async def _run_task(self, task: Task):
        """
        Exécute une tâche (méthode interne)

        Args:
            task: Tâche à exécuter
        """
        task.status = TaskStatus.RUNNING
        task.start_time = datetime.now()

        try:
            # Préparer l'environnement : utiliser le venv si disponible
            import os
            env = os.environ.copy()

            # Chercher le venv dans le projet
            venv_paths = [
                BASE_DIR / '.venv' / 'bin',  # Linux/Mac
                BASE_DIR / 'venv' / 'bin',
                BASE_DIR / '.venv' / 'Scripts',  # Windows
                BASE_DIR / 'venv' / 'Scripts',
            ]

            for venv_path in venv_paths:
                if venv_path.exists():
                    # Ajouter le venv au PATH
                    env['PATH'] = f"{venv_path}:{env.get('PATH', '')}"
                    env['VIRTUAL_ENV'] = str(venv_path.parent)
                    task.output.append(f"[INFO] Utilisation du venv: {venv_path}")
                    break

            # Exécuter la commande
            process = await asyncio.create_subprocess_exec(
                *task.command,
                stdin=asyncio.subprocess.DEVNULL,  # Fermer stdin pour éviter les blocages
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(BASE_DIR),
                env=env
            )

            # Lire la sortie en temps réel
            stdout_task = asyncio.create_task(
                self._read_stream(process.stdout, task.output)
            )
            stderr_task = asyncio.create_task(
                self._read_stream(process.stderr, task.output)
            )

            # Attendre la fin de l'exécution
            await asyncio.gather(stdout_task, stderr_task)
            await process.wait()

            task.exit_code = process.returncode

            if process.returncode == 0:
                task.status = TaskStatus.SUCCESS
            else:
                task.status = TaskStatus.ERROR
                task.error = f"Exit code: {process.returncode}"

        except Exception as e:
            task.status = TaskStatus.ERROR
            task.error = str(e)
            task.output.append(f"[ERROR] {str(e)}")

        finally:
            task.end_time = datetime.now()

    async def _read_stream(self, stream, output_list: List[str]):
        """
        Lit un flux (stdout/stderr) ligne par ligne

        Args:
            stream: Flux à lire
            output_list: Liste où stocker les lignes
        """
        while True:
            line = await stream.readline()
            if not line:
                break

            try:
                decoded = line.decode('utf-8').rstrip()
            except UnicodeDecodeError:
                try:
                    decoded = line.decode('latin-1').rstrip()
                except:
                    decoded = str(line)

            output_list.append(decoded)

    async def get_task_status(self, task_id: str) -> Optional[dict]:
        """
        Récupère le statut d'une tâche

        Args:
            task_id: ID de la tâche

        Returns:
            dict: Statut de la tâche ou None si non trouvée
        """
        async with self._lock:
            task = self.tasks.get(task_id)
            if task:
                return task.to_dict()
            return None

    async def list_tasks(self, limit: int = 50) -> List[dict]:
        """
        Liste les tâches récentes

        Args:
            limit: Nombre maximum de tâches à retourner

        Returns:
            List[dict]: Liste des tâches
        """
        async with self._lock:
            tasks = sorted(
                self.tasks.values(),
                key=lambda t: t.start_time or datetime.min,
                reverse=True
            )
            return [t.to_dict() for t in tasks[:limit]]

    async def cleanup_old_tasks(self, max_age_hours: int = 24):
        """
        Nettoie les vieilles tâches terminées

        Args:
            max_age_hours: Age maximum en heures
        """
        now = datetime.now()
        async with self._lock:
            to_remove = []
            for task_id, task in self.tasks.items():
                if task.end_time:
                    age = (now - task.end_time).total_seconds() / 3600
                    if age > max_age_hours:
                        to_remove.append(task_id)

            for task_id in to_remove:
                del self.tasks[task_id]


# Instance globale du gestionnaire de tâches
executor = TaskExecutor()
