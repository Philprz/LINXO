#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Linxo Analysis Runner - Uses V3.0 RELIABLE
Simple wrapper to run the reliable analysis system
"""

import sys
import os

# Add the linxo_agent directory to path
sys.path.insert(0, '/home/ubuntu/linxo_agent')

# Import the reliable version
import agent_linxo_csv_v3_RELIABLE as analyzer

def main():
    """Run the analysis with optional CSV file path"""
    if len(sys.argv) > 1:
        # Custom CSV file provided
        csv_file = sys.argv[1]
        if not os.path.exists(csv_file):
            print(f"❌ Erreur: Le fichier {csv_file} n'existe pas")
            sys.exit(1)
        
        print(f"📂 Utilisation du fichier: {csv_file}")
        analyzer.CSV_FILE = csv_file
    else:
        # Use default CSV file
        print(f"📂 Utilisation du fichier par défaut: {analyzer.CSV_FILE}")
    
    # Run the analysis
    analyzer.main()

if __name__ == "__main__":
    main()
