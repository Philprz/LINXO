#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
File Classification Script for LINXO Project
Classifies files into KEEP, REVIEW, and REMOVE_CANDIDATES categories
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Set


class FileClassifier:
    """Classify files based on usage and importance"""

    def __init__(self, root_dir: str, dependency_analysis: str):
        self.root_dir = Path(root_dir)
        self.dep_analysis_file = Path(dependency_analysis)

        # Categories
        self.keep_files: List[tuple] = []  # (path, reason)
        self.review_files: List[tuple] = []  # (path, reason)
        self.remove_candidates: List[tuple] = []  # (path, reason)

        # Parse dependency analysis
        self.entry_points: Set[str] = set()
        self.imported_modules: Set[str] = set()
        self.runtime_refs: Set[str] = set()

        self._parse_dependency_report()

    def _parse_dependency_report(self):
        """Parse dependency analysis report"""
        if not self.dep_analysis_file.exists():
            print(f"Warning: Dependency analysis file not found: {self.dep_analysis_file}")
            return

        with open(self.dep_analysis_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Extract entry points
        in_entry_section = False
        for line in content.split('\n'):
            if '## ENTRY POINTS' in line:
                in_entry_section = True
                continue
            elif line.startswith('##'):
                in_entry_section = False

            if in_entry_section and line.strip().startswith('-'):
                entry = line.strip()[2:].strip()
                self.entry_points.add(entry)

    def classify_all_files(self):
        """Classify all files in the project"""
        print("Classifying files...")

        # Walk through all files
        for root, dirs, files in os.walk(self.root_dir):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if d not in {'.venv', 'venv', '__pycache__', '.git', 'node_modules', '.eggs'}]

            for file in files:
                file_path = Path(root) / file
                rel_path = file_path.relative_to(self.root_dir)
                self._classify_file(rel_path, file_path)

    def _classify_file(self, rel_path: Path, full_path: Path):
        """Classify a single file"""

        # Convert to string with forward slashes for comparison
        rel_str = str(rel_path).replace('\\', '/')
        file_name = rel_path.name
        parent_dir = rel_path.parent.name if rel_path.parent != Path('.') else ''

        # ===== KEEP LIST - Critical files =====

        # Entry points
        if rel_str in self.entry_points:
            self.keep_files.append((rel_str, "Entry point script (has __main__)"))
            return

        # Core Python modules in linxo_agent/
        if rel_path.parts[0] == 'linxo_agent' and file_name.endswith('.py'):
            core_modules = {'config.py', 'analyzer.py', 'notifications.py', 'linxo_connexion.py',
                          'report_formatter_v2.py', 'agent_linxo_csv_v3_RELIABLE.py',
                          'run_linxo_e2e.py', 'run_analysis.py'}
            if file_name in core_modules:
                self.keep_files.append((rel_str, "Core application module"))
                return

        # Configuration files
        if file_name in {'requirements.txt', '.env.example', '.gitignore', 'pyproject.toml', 'setup.py', 'setup.cfg'}:
            self.keep_files.append((rel_str, "Configuration/dependency file"))
            return

        # JSON config files
        if file_name in {'config_linxo.json', 'depenses_recurrentes.json', 'api_secrets.json'}:
            self.keep_files.append((rel_str, "Runtime configuration file"))
            return

        # Example/template files
        if '.example' in file_name:
            self.keep_files.append((rel_str, "Template/example file for deployment"))
            return

        # Deploy scripts
        if parent_dir == 'deploy' and file_name.endswith('.sh'):
            self.keep_files.append((rel_str, "Deployment script"))
            return

        # Essential documentation
        essential_docs = {'README.md', '00_COMMENCER_ICI.md', 'START_HERE.md',
                         'LANCEMENT_RAPIDE.md', 'GUIDE_DEPLOIEMENT_VPS.md'}
        if file_name in essential_docs:
            self.keep_files.append((rel_str, "Essential documentation"))
            return

        # ===== REMOVE CANDIDATES - Likely unused =====

        # Cache directories content
        if '__pycache__' in rel_path.parts or '.pytest_cache' in rel_path.parts:
            self.remove_candidates.append((rel_str, "Python cache file (automatically generated)"))
            return

        # Compiled Python files
        if file_name.endswith(('.pyc', '.pyo')):
            self.remove_candidates.append((rel_str, "Compiled Python file (automatically regenerated)"))
            return

        # IDE files
        if parent_dir in {'.vscode', '.idea', '.claude'} or file_name in {'.DS_Store', 'Thumbs.db', 'desktop.ini'}:
            if parent_dir == '.claude' and file_name == 'settings.local.json':
                self.review_files.append((rel_str, "Claude IDE settings (user-specific, consider keeping)"))
            else:
                self.remove_candidates.append((rel_str, "IDE/OS-specific file (not needed in repo)"))
            return

        # Log files
        if parent_dir == 'logs' or file_name.endswith('.log'):
            self.remove_candidates.append((rel_str, "Log file (runtime artifact, regenerated)"))
            return

        # Report files (generated)
        if parent_dir == 'reports' or file_name.startswith('rapport_'):
            self.remove_candidates.append((rel_str, "Generated report (runtime artifact)"))
            return

        # Duplicate/old test files
        test_files = ['test_sms_only.py', 'test_sms_direct.py', 'test_sms_debug.py',
                     'test_preview_notifications.py']
        if file_name in test_files:
            self.remove_candidates.append((rel_str, "Old test file (likely superseded by main test suite)"))
            return

        # Old/backup documentation
        redundant_docs = ['QUICK_START.txt', 'QUICK_START_V2.md', 'README_V2.md',
                         'CHANGELOG_V2.md', 'SUMMARY_FINAL.txt', 'SUMMARY_REFACTORISATION.md',
                         'FICHIERS_CREES.md', 'NETTOYAGE_EFFECTUE.md', 'UPDATE_WORKFLOW_CSV.md',
                         'RESUME_PROJET.md']
        if file_name in redundant_docs:
            self.remove_candidates.append((rel_str, "Redundant/outdated documentation (info in README.md)"))
            return

        # Old report formatter (v1)
        if file_name == 'report_formatter.py':
            self.remove_candidates.append((rel_str, "Old version (report_formatter_v2.py is used)"))
            return

        # Old send_notifications (standalone, replaced by notifications.py)
        if file_name == 'send_notifications.py' and parent_dir == 'linxo_agent':
            self.remove_candidates.append((rel_str, "Standalone script (functionality in notifications.py)"))
            return

        # Generated preview files
        if file_name in {'apercu_rapport.html', 'apercu_sms.txt'}:
            self.remove_candidates.append((rel_str, "Generated preview (runtime artifact)"))
            return

        # Empty or placeholder directories
        if parent_dir in {'Downloads', 'Uploads', 'data'} and full_path.stat().st_size == 0:
            self.remove_candidates.append((rel_str, "Empty placeholder file in data directory"))
            return

        # ===== REVIEW LIST - Uncertain cases =====

        # Test files that might be useful
        if file_name.startswith('test_') and file_name.endswith('.py'):
            self.review_files.append((rel_str, "Test file - verify if still used"))
            return

        # Generate scripts
        if file_name.startswith('generate_') and file_name.endswith('.py'):
            self.review_files.append((rel_str, "Generation script - verify usage"))
            return

        # Data directories
        if parent_dir in {'data', 'Downloads', 'Uploads'}:
            self.review_files.append((rel_str, "Data directory file - check if needed for tests/demos"))
            return

        # Documentation files
        if file_name.endswith('.md') or file_name.endswith('.txt'):
            self.review_files.append((rel_str, "Documentation - verify relevance"))
            return

        # JSON files (not config)
        if file_name.endswith('.json') and file_name not in {'config_linxo.json', 'depenses_recurrentes.json'}:
            self.review_files.append((rel_str, "JSON data file - verify usage"))
            return

        # HTML/Text outputs
        if file_name.endswith(('.html', '.htm')) or (file_name.endswith('.txt') and parent_dir in {'reports', ''}):
            self.review_files.append((rel_str, "Output file - likely generated, verify"))
            return

        # Everything else -> REVIEW
        self.review_files.append((rel_str, "Uncategorized - needs manual review"))

    def write_classification_files(self):
        """Write classification results to files"""

        # KEEP_LIST.txt
        with open(self.root_dir / 'KEEP_LIST.txt', 'w', encoding='utf-8') as f:
            f.write("# KEEP LIST - Files to retain\n")
            f.write("# These files are essential for the application to function\n\n")
            for file_path, reason in sorted(self.keep_files):
                f.write(f"{file_path}\n  Reason: {reason}\n\n")

        # REVIEW_LIST.txt
        with open(self.root_dir / 'REVIEW_LIST.txt', 'w', encoding='utf-8') as f:
            f.write("# REVIEW LIST - Files needing manual verification\n")
            f.write("# These files require validation before deciding to keep or remove\n\n")
            for file_path, reason in sorted(self.review_files):
                f.write(f"{file_path}\n  Reason: {reason}\n\n")

        # REMOVE_CANDIDATES.txt
        with open(self.root_dir / 'REMOVE_CANDIDATES.txt', 'w', encoding='utf-8') as f:
            f.write("# REMOVE CANDIDATES - Files safe to delete\n")
            f.write("# These files can be safely removed (caches, logs, redundant docs, etc.)\n\n")
            for file_path, reason in sorted(self.remove_candidates):
                f.write(f"{file_path}\n  Reason: {reason}\n\n")

        print(f"\nClassification complete:")
        print(f"  KEEP: {len(self.keep_files)} files")
        print(f"  REVIEW: {len(self.review_files)} files")
        print(f"  REMOVE CANDIDATES: {len(self.remove_candidates)} files")
        print(f"\nFiles written:")
        print(f"  - KEEP_LIST.txt")
        print(f"  - REVIEW_LIST.txt")
        print(f"  - REMOVE_CANDIDATES.txt")


def main():
    """Main entry point"""
    import sys

    # Get root directory
    if len(sys.argv) > 1:
        root_dir = sys.argv[1]
    else:
        root_dir = Path(__file__).parent.parent

    dep_analysis = Path(root_dir) / 'DEPENDENCY_ANALYSIS.txt'

    print(f"Classifying files in: {root_dir}")
    print("=" * 80)

    classifier = FileClassifier(root_dir, dep_analysis)
    classifier.classify_all_files()
    classifier.write_classification_files()

    print("\n" + "=" * 80)
    print("Classification complete!")
    print("=" * 80)


if __name__ == '__main__':
    main()
