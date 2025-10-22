#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dependency Analyzer for LINXO Project
Analyzes Python imports, runtime file references, and build dependencies
"""

import ast
import os
import re
import json
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Set, Tuple


class DependencyAnalyzer:
    """Analyze project dependencies and file usage"""

    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir)
        self.python_files: List[Path] = []
        self.imports_graph: Dict[str, Set[str]] = defaultdict(set)
        self.runtime_refs: Dict[str, Set[str]] = defaultdict(set)
        self.defined_symbols: Dict[str, Set[str]] = defaultdict(set)
        self.used_symbols: Dict[str, Set[str]] = defaultdict(set)
        self.entry_points: List[Path] = []

    def scan_python_files(self) -> List[Path]:
        """Find all Python files in the project"""
        python_files = []
        exclude_dirs = {'.venv', 'venv', '__pycache__', '.git', 'build', 'dist', '.eggs', 'node_modules'}

        for path in self.root_dir.rglob('*.py'):
            # Skip excluded directories
            if any(excluded in path.parts for excluded in exclude_dirs):
                continue
            python_files.append(path)

        self.python_files = python_files
        return python_files

    def parse_imports(self, file_path: Path) -> Tuple[Set[str], Set[str]]:
        """Parse imports from a Python file"""
        imports = set()
        from_imports = set()

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read(), filename=str(file_path))

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.add(alias.name.split('.')[0])
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        from_imports.add(node.module.split('.')[0])
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")

        return imports, from_imports

    def find_runtime_references(self, file_path: Path) -> Set[str]:
        """Find runtime file references (open, Path, etc.)"""
        refs = set()
        patterns = [
            r'open\(["\']([^"\']+)["\']',
            r'Path\(["\']([^"\']+)["\']',
            r'glob\(["\']([^"\']+)["\']',
            r'read_csv\(["\']([^"\']+)["\']',
            r'load\(["\']([^"\']+)["\']',
            r'\.json|\.csv|\.txt|\.html|\.pdf|\.md'
        ]

        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            for pattern in patterns:
                matches = re.findall(pattern, content)
                refs.update(matches)
        except Exception as e:
            print(f"Error scanning {file_path}: {e}")

        return refs

    def identify_entry_points(self) -> List[Path]:
        """Identify entry points (files with if __name__ == '__main__')"""
        entry_points = []

        for py_file in self.python_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if 'if __name__' in content and '__main__' in content:
                        entry_points.append(py_file)
            except Exception as e:
                print(f"Error reading {py_file}: {e}")

        self.entry_points = entry_points
        return entry_points

    def build_dependency_graph(self):
        """Build complete dependency graph"""
        print("Scanning Python files...")
        self.scan_python_files()
        print(f"Found {len(self.python_files)} Python files")

        print("\nAnalyzing imports and dependencies...")
        for py_file in self.python_files:
            rel_path = py_file.relative_to(self.root_dir)

            # Parse imports
            imports, from_imports = self.parse_imports(py_file)
            all_imports = imports | from_imports
            self.imports_graph[str(rel_path)] = all_imports

            # Find runtime references
            refs = self.find_runtime_references(py_file)
            self.runtime_refs[str(rel_path)] = refs

        print("Identifying entry points...")
        self.identify_entry_points()
        print(f"Found {len(self.entry_points)} entry points")

    def get_imported_modules(self) -> Set[str]:
        """Get all imported modules (local and external)"""
        all_imports = set()
        for imports in self.imports_graph.values():
            all_imports.update(imports)
        return all_imports

    def get_unreferenced_files(self) -> List[Path]:
        """Find Python files that are never imported"""
        # Get all module names from file paths
        file_modules = {}
        for py_file in self.python_files:
            rel_path = py_file.relative_to(self.root_dir)
            module_name = str(rel_path.with_suffix('')).replace(os.sep, '.')
            file_modules[module_name] = py_file

        # Get all imported modules
        imported = self.get_imported_modules()

        # Find unreferenced files
        unreferenced = []
        for module_name, file_path in file_modules.items():
            # Check if this module or its parent is imported
            is_imported = False
            parts = module_name.split('.')

            for i in range(len(parts)):
                partial = '.'.join(parts[:i+1])
                if partial in imported or parts[i] in imported:
                    is_imported = True
                    break

            # Entry points are always referenced
            if file_path in self.entry_points:
                is_imported = True

            if not is_imported:
                unreferenced.append(file_path)

        return unreferenced

    def generate_report(self, output_file: str):
        """Generate detailed analysis report"""
        report = []
        report.append("# LINXO PROJECT DEPENDENCY ANALYSIS REPORT")
        report.append("=" * 80)
        report.append("")

        # Summary
        report.append("## SUMMARY")
        report.append(f"Total Python files: {len(self.python_files)}")
        report.append(f"Entry points: {len(self.entry_points)}")
        report.append(f"Unique imports: {len(self.get_imported_modules())}")
        report.append("")

        # Entry points
        report.append("## ENTRY POINTS (Main scripts)")
        for ep in sorted(self.entry_points):
            rel_path = ep.relative_to(self.root_dir)
            report.append(f"  - {rel_path}")
        report.append("")

        # Import graph
        report.append("## IMPORT GRAPH")
        for file_path in sorted(self.imports_graph.keys()):
            imports = self.imports_graph[file_path]
            if imports:
                report.append(f"\n{file_path}:")
                for imp in sorted(imports):
                    report.append(f"  -> {imp}")
        report.append("")

        # Runtime references
        report.append("## RUNTIME FILE REFERENCES")
        for file_path in sorted(self.runtime_refs.keys()):
            refs = self.runtime_refs[file_path]
            if refs:
                report.append(f"\n{file_path}:")
                for ref in sorted(refs):
                    report.append(f"  -> {ref}")
        report.append("")

        # Unreferenced files
        unreferenced = self.get_unreferenced_files()
        report.append("## POTENTIALLY UNREFERENCED FILES")
        report.append(f"Found {len(unreferenced)} potentially unreferenced Python files:")
        for file_path in sorted(unreferenced):
            rel_path = file_path.relative_to(self.root_dir)
            report.append(f"  - {rel_path}")
        report.append("")

        # External dependencies
        report.append("## EXTERNAL DEPENDENCIES (from imports)")
        external_deps = set()
        builtin_modules = {'os', 'sys', 'json', 'csv', 'datetime', 'pathlib', 'time',
                          'argparse', 'logging', 're', 'collections', 'typing', 'ast',
                          'traceback', 'email', 'smtplib', 'base64', 'hashlib', 'urllib'}

        for imports in self.imports_graph.values():
            for imp in imports:
                if imp not in builtin_modules:
                    external_deps.add(imp)

        for dep in sorted(external_deps):
            report.append(f"  - {dep}")
        report.append("")

        # Write report
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report))

        print(f"\nReport saved to: {output_file}")

        return '\n'.join(report)


def main():
    """Main entry point"""
    import sys

    # Get root directory
    if len(sys.argv) > 1:
        root_dir = sys.argv[1]
    else:
        root_dir = Path(__file__).parent.parent

    print(f"Analyzing project at: {root_dir}")
    print("=" * 80)

    analyzer = DependencyAnalyzer(root_dir)
    analyzer.build_dependency_graph()

    # Generate report
    report_file = Path(root_dir) / 'DEPENDENCY_ANALYSIS.txt'
    analyzer.generate_report(report_file)

    print("\n" + "=" * 80)
    print("Analysis complete!")
    print("=" * 80)


if __name__ == '__main__':
    main()
