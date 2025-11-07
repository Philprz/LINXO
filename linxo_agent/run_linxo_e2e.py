#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Linxo End-to-End Test Orchestrator
Executes complete workflow: Connect → Download → Analyze → SMS → Email
"""

import json
import os
import sys
import time
import csv
import re
import smtplib
import requests
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path

# Selenium imports
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

# Configuration paths
BASE_DIR = Path("/home/ubuntu/linxo_agent")
CONFIG_FILE = BASE_DIR / "config_linxo.json"
DEPENSES_FILE = BASE_DIR / "depenses_recurrentes.json"
API_SECRETS_FILE = Path("/home/ubuntu/.api_secret_infos/api_secrets.json")
LOG_DIR = Path("/home/ubuntu/logs")
DATA_DIR = Path("/home/ubuntu/data")
DOWNLOAD_DIR = Path("/home/ubuntu/downloads")

# Create directories
LOG_DIR.mkdir(exist_ok=True)
DATA_DIR.mkdir(exist_ok=True)
DOWNLOAD_DIR.mkdir(exist_ok=True)

# Log file
TIMESTAMP = datetime.now().strftime('%Y%m%d_%H%M%S')
LOG_FILE = LOG_DIR / f"e2e_{TIMESTAMP}.log"

# Exclusion patterns
EXCLUSIONS = {
    'releves_differes': [
        r'RELEVE\s+DIFFERE.*CARTE\s+\d{4}\*+\d{4}',
        r'CARTE\s+\d{4}\*+\d{4}.*RELEVE',
        r'RELEVE.*DIFFERE',
    ],
    'virements_internes': [
        r'VIREMENT\s+(INTERNE|ENTRE\s+COMPTES)',
        r'VIREMENT\s+DE\s+COMPTE\s+A\s+COMPTE',
        r'TRANSFERT\s+(INTERNE|ENTRE\s+COMPTES)',
    ]
}

def log(message):
    """Log to both console and file"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_msg = f"[{timestamp}] {message}"
    print(log_msg)
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(log_msg + '\n')

def load_json(filepath):
    """Load JSON file"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def doit_exclure_transaction(libelle):
    """Check if transaction should be excluded"""
    libelle_upper = libelle.upper()
    
    for pattern in EXCLUSIONS['releves_differes']:
        if re.search(pattern, libelle_upper, re.IGNORECASE):
            return True, "Relevé différé"
    
    for pattern in EXCLUSIONS['virements_internes']:
        if re.search(pattern, libelle_upper, re.IGNORECASE):
            return True, "Virement interne"
    
    return False, None

def download_linxo_csv():
    """Download CSV from Linxo using Selenium"""
    log("=" * 80)
    log("STEP 1: DOWNLOAD CSV FROM LINXO")
    log("=" * 80)
    
    try:
        config = load_json(CONFIG_FILE)
        linxo_config = config['linxo']
        
        # Setup Chrome driver
        log("Initializing Chrome driver...")
        options = Options()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--window-size=1920,1080')
        
        prefs = {
            "download.default_directory": str(DOWNLOAD_DIR.absolute()),
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True
        }
        options.add_experimental_option("prefs", prefs)
        
        driver = webdriver.Chrome(options=options)
        wait = WebDriverWait(driver, 30)
        
        # Login to Linxo
        log(f"Navigating to Linxo login page...")
        driver.get('https://wwws.linxo.com/auth.page#Login')
        time.sleep(3)
        
        log("Filling login credentials...")
        username_field = wait.until(EC.presence_of_element_located((By.NAME, "username")))
        password_field = driver.find_element(By.NAME, "password")
        
        username_field.clear()
        username_field.send_keys(linxo_config['email'])
        time.sleep(1)
        
        password_field.clear()
        password_field.send_keys(linxo_config['password'])
        time.sleep(1)
        
        log("Clicking login button...")
        submit_button = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Je me connecte')]"))
        )
        submit_button.click()
        time.sleep(8)
        
        if 'login' in driver.current_url.lower() or 'auth' in driver.current_url.lower():
            raise Exception("Login failed - still on auth page")
        
        log("✅ Login successful!")
        
        # Navigate to history/export page
        log("Navigating to history page...")
        driver.get('https://wwws.linxo.com/historique.page')
        time.sleep(5)
        
        # Look for export/download button
        log("Looking for export button...")
        try:
            # Try multiple selectors for export button
            export_button = None
            selectors = [
                "//button[contains(text(), 'Exporter')]",
                "//a[contains(text(), 'Exporter')]",
                "//button[contains(@class, 'export')]",
                "//a[contains(@class, 'export')]",
                "//button[contains(text(), 'CSV')]",
                "//a[contains(text(), 'CSV')]"
            ]
            
            for selector in selectors:
                try:
                    export_button = driver.find_element(By.XPATH, selector)
                    log(f"Found export button with selector: {selector}")
                    break
                except:
                    continue
            
            if export_button:
                export_button.click()
                log("Clicked export button, waiting for download...")
                time.sleep(10)
            else:
                log("⚠️ Export button not found, trying alternative method...")
                # Try to find download link in page
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
        
        except Exception as e:
            log(f"⚠️ Could not find export button: {e}")
        
        # Check for downloaded file
        log("Checking for downloaded CSV file...")
        time.sleep(5)
        
        csv_files = list(DOWNLOAD_DIR.glob("*.csv"))
        if csv_files:
            # Get most recent CSV
            latest_csv = max(csv_files, key=lambda p: p.stat().st_mtime)
            target_csv = DATA_DIR / "latest.csv"
            
            # Copy to data directory
            import shutil
            shutil.copy2(latest_csv, target_csv)

            log(f"✅ CSV downloaded successfully: {target_csv}")
            log(f"   File size: {target_csv.stat().st_size} bytes")

            # IMPORTANT: Filter CSV by current month
            log("\n[FILTER] Applying month filter to CSV...")
            try:
                # Import the CSV filter module
                import sys
                sys.path.insert(0, str(BASE_DIR.parent / "linxo_agent"))
                from csv_filter import filter_csv_by_month

                # Filter for current month
                filtered_path = filter_csv_by_month(target_csv)

                if filtered_path:
                    log(f"✅ CSV filtered for current month")
                    log(f"   Filtered file: {filtered_path}")
                else:
                    log(f"⚠️ CSV filtering returned None, using unfiltered CSV")
            except Exception as filter_error:
                log(f"⚠️ CSV filtering failed: {filter_error}")
                log(f"   Continuing with unfiltered CSV")

            driver.quit()
            return True, str(target_csv)
        else:
            log("❌ No CSV file found in downloads")
            driver.quit()
            return False, "No CSV file downloaded"
            
    except Exception as e:
        log(f"❌ Error downloading CSV: {e}")
        import traceback
        log(traceback.format_exc())
        try:
            driver.quit()
        except:
            pass
        return False, str(e)

def analyze_expenses(csv_path):
    """Analyze expenses from CSV with exclusions"""
    log("=" * 80)
    log("STEP 2: ANALYZE EXPENSES")
    log("=" * 80)
    
    try:
        depenses_data = load_json(DEPENSES_FILE)
        
        transactions = []
        exclus = []
        
        log(f"Reading CSV: {csv_path}")
        
        with open(csv_path, 'r', encoding='utf-8') as f:
            sample = f.read(1024)
            f.seek(0)
            delimiter = '\t' if '\t' in sample else ','
            
            reader = csv.DictReader(f, delimiter=delimiter)
            
            for row in reader:
                date_str = row.get('Date', '')
                libelle = row.get('Libellé', '')
                notes = row.get('Notes', '')
                montant_str = row.get('Montant', '0')
                categorie = row.get('Catégorie', '')
                compte = row.get('Nom du compte', '')
                
                montant_str = montant_str.replace(',', '.').replace(' ', '').replace('€', '')
                try:
                    montant = float(montant_str)
                except:
                    montant = 0.0
                
                try:
                    date = datetime.strptime(date_str, '%d/%m/%Y')
                except:
                    date = None
                
                libelle_complet = f"{libelle} {notes}".strip()
                
                doit_exclure, raison = doit_exclure_transaction(libelle_complet)
                
                transaction = {
                    'date': date,
                    'date_str': date_str,
                    'libelle': libelle,
                    'libelle_complet': libelle_complet,
                    'montant': montant,
                    'categorie': categorie,
                    'compte': compte
                }
                
                if doit_exclure:
                    transaction['raison_exclusion'] = raison
                    exclus.append(transaction)
                    log(f"  ⊘ EXCLU: {libelle_complet[:40]:40} | {montant:8.2f}€ | {raison}")
                else:
                    transactions.append(transaction)
        
        log(f"\n✅ Loaded {len(transactions)} valid transactions ({len(exclus)} excluded)")
        
        # Calculate totals
        total_depenses = sum(abs(t['montant']) for t in transactions if t['montant'] < 0)
        total_revenus = sum(t['montant'] for t in transactions if t['montant'] > 0)
        
        # Get budget info
        budget_max = depenses_data.get('totaux', {}).get('budget_variable_max', 1324)
        reste = budget_max - total_depenses
        pourcentage = (total_depenses / budget_max * 100) if budget_max > 0 else 0
        
        # Determine status
        now = datetime.now()
        jour_actuel = now.day
        import calendar
        dernier_jour = calendar.monthrange(now.year, now.month)[1]
        
        alerte = reste < 0
        if alerte:
            emoji = "🔴"
        elif pourcentage >= 80:
            emoji = "🟠"
        else:
            emoji = "🟢"
        
        analysis = {
            'total_transactions': len(transactions),
            'total_exclus': len(exclus),
            'total_depenses': total_depenses,
            'total_revenus': total_revenus,
            'budget_max': budget_max,
            'reste': reste,
            'pourcentage': pourcentage,
            'alerte': alerte,
            'emoji': emoji,
            'jour_actuel': jour_actuel,
            'dernier_jour': dernier_jour,
            'csv_path': csv_path,
            'transactions': transactions,
            'exclus': exclus
        }
        
        log(f"\n📊 ANALYSIS RESULTS:")
        log(f"   Total expenses: {total_depenses:.2f}€")
        log(f"   Budget: {budget_max:.2f}€")
        log(f"   Remaining: {reste:.2f}€")
        log(f"   Usage: {pourcentage:.1f}%")
        log(f"   Status: {emoji}")
        
        return True, analysis
        
    except Exception as e:
        log(f"❌ Error analyzing expenses: {e}")
        import traceback
        log(traceback.format_exc())
        return False, str(e)

def send_sms_ovh(phone, message):
    """Send SMS via OVH API"""
    try:
        api_secrets = load_json(API_SECRETS_FILE)
        ovh_config = api_secrets['OVH_SMS']['secrets']
        smtp_config = api_secrets['SMTP_GMAIL']['secrets']
        
        # Truncate message if too long
        if len(message) > 160:
            message = message[:157] + "..."
        
        # Format subject for OVH
        sujet = f"{ovh_config['COMPTE_SMS']}:{ovh_config['UTILISATEUR_SMS']}:{ovh_config['MOT_DE_PASSE_SMS']}:{ovh_config['EXPEDITEUR_SMS']}:{phone}"
        
        msg = MIMEMultipart()
        msg['Subject'] = sujet
        msg['From'] = smtp_config['SMTP_EMAIL']
        msg['To'] = ovh_config['OVH_EMAIL']
        
        body = MIMEText(message, 'plain', 'utf-8')
        msg.attach(body)
        
        server = smtplib.SMTP(smtp_config['SMTP_SERVER'], int(smtp_config['SMTP_PORT']))
        server.starttls()
        server.login(smtp_config['SMTP_EMAIL'], smtp_config['SMTP_PASSWORD'])
        server.send_message(msg)
        server.quit()
        
        log(f"✅ SMS sent to {phone}")
        return True
        
    except Exception as e:
        log(f"❌ Error sending SMS to {phone}: {e}")
        return False

def send_email_smtp(recipients, subject, body_text, csv_path=None):
    """Send email via SMTP with optional CSV attachment"""
    try:
        api_secrets = load_json(API_SECRETS_FILE)
        smtp_config = api_secrets['SMTP_GMAIL']['secrets']
        
        msg = MIMEMultipart()
        msg['Subject'] = subject
        msg['From'] = smtp_config['SMTP_EMAIL']
        msg['To'] = ', '.join(recipients)
        
        body = MIMEText(body_text, 'plain', 'utf-8')
        msg.attach(body)
        
        # Attach CSV if provided
        if csv_path and os.path.exists(csv_path):
            with open(csv_path, 'rb') as f:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(f.read())
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', f'attachment; filename=linxo_export_{TIMESTAMP}.csv')
                msg.attach(part)
        
        server = smtplib.SMTP(smtp_config['SMTP_SERVER'], int(smtp_config['SMTP_PORT']))
        server.starttls()
        server.login(smtp_config['SMTP_EMAIL'], smtp_config['SMTP_PASSWORD'])
        server.send_message(msg)
        server.quit()
        
        log(f"✅ Email sent to {', '.join(recipients)}")
        return True
        
    except Exception as e:
        log(f"❌ Error sending email: {e}")
        return False

def send_notifications(analysis):
    """Send SMS and email notifications"""
    log("=" * 80)
    log("STEP 3: SEND NOTIFICATIONS")
    log("=" * 80)
    
    sms_results = []
    email_results = []
    
    try:
        # Prepare SMS message
        if analysis['alerte']:
            sms_msg = f"🚨🔴 ALERTE BUDGET!\n"
            sms_msg += f"Dépensé: {analysis['total_depenses']:.0f}€ / {analysis['budget_max']:.0f}€\n"
            sms_msg += f"DÉPASSEMENT: {abs(analysis['reste']):.0f}€"
        elif analysis['emoji'] == "🟠":
            sms_msg = f"⚠️🟠 Attention Budget\n"
            sms_msg += f"Dépensé: {analysis['total_depenses']:.0f}€ / {analysis['budget_max']:.0f}€ ({analysis['pourcentage']:.0f}%)\n"
            sms_msg += f"Reste: {analysis['reste']:.0f}€"
        else:
            sms_msg = f"✅🟢 Budget OK\n"
            sms_msg += f"Dépensé: {analysis['total_depenses']:.0f}€ / {analysis['budget_max']:.0f}€ ({analysis['pourcentage']:.0f}%)\n"
            sms_msg += f"Reste: {analysis['reste']:.0f}€"
        
        # Send SMS to both recipients
        log("\n📱 Sending SMS notifications...")
        phones = ["+33626267421", "+33611435899"]
        for phone in phones:
            result = send_sms_ovh(phone, sms_msg)
            sms_results.append({'phone': phone, 'success': result})
        
        # Prepare email body
        email_body = f"""RAPPORT LINXO - {datetime.now().strftime('%d/%m/%Y %H:%M')}
{'=' * 80}

📊 RÉSUMÉ DES DÉPENSES
{'=' * 80}

Budget mensuel: {analysis['budget_max']:.2f}€
Dépenses totales: {analysis['total_depenses']:.2f}€
Reste disponible: {analysis['reste']:.2f}€
Pourcentage utilisé: {analysis['pourcentage']:.1f}%

Statut: {analysis['emoji']} {'ALERTE - DÉPASSEMENT!' if analysis['alerte'] else 'OK'}

Jour {analysis['jour_actuel']}/{analysis['dernier_jour']} du mois

📈 DÉTAILS
{'=' * 80}

Transactions valides: {analysis['total_transactions']}
Transactions exclues: {analysis['total_exclus']}
Revenus: {analysis['total_revenus']:.2f}€

{'⚠️ ATTENTION: Budget dépassé de ' + f"{abs(analysis['reste']):.2f}€" if analysis['alerte'] else ''}

Fichier CSV: {analysis['csv_path']}

---
Rapport généré automatiquement par l'Agent Linxo
"""
        
        # Send emails
        log("\n📧 Sending email notifications...")
        emails = ["phiperez@gmail.com", "caliemphi@gmail.com"]
        
        if analysis['alerte']:
            subject = f"🚨 ALERTE BUDGET - Dépassement de {abs(analysis['reste']):.0f}€ !"
        elif analysis['emoji'] == "🟠":
            subject = f"⚠️ Attention Budget - {analysis['pourcentage']:.0f}% utilisé"
        else:
            subject = f"✅ Budget OK - Rapport Linxo {datetime.now().strftime('%d/%m/%Y')}"
        
        result = send_email_smtp(emails, subject, email_body, analysis['csv_path'])
        email_results.append({'recipients': emails, 'success': result})
        
        return True, {'sms': sms_results, 'email': email_results}
        
    except Exception as e:
        log(f"❌ Error sending notifications: {e}")
        import traceback
        log(traceback.format_exc())
        return False, str(e)

def main():
    """Main orchestrator"""
    log("=" * 80)
    log("LINXO END-TO-END TEST")
    log(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log("=" * 80)
    
    results = {
        'csv_ok': False,
        'analysis_ok': False,
        'sms_ok': False,
        'email_ok': False,
        'details': {}
    }
    
    # Step 1: Download CSV
    csv_ok, csv_result = download_linxo_csv()
    results['csv_ok'] = csv_ok
    
    if not csv_ok:
        results['details']['error'] = f"CSV download failed: {csv_result}"
        log("\n❌ FAILED: Could not download CSV")
        save_results(results)
        return results
    
    csv_path = csv_result
    results['details']['csv_path'] = csv_path
    
    # Step 2: Analyze expenses
    analysis_ok, analysis_result = analyze_expenses(csv_path)
    results['analysis_ok'] = analysis_ok
    
    if not analysis_ok:
        results['details']['error'] = f"Analysis failed: {analysis_result}"
        log("\n❌ FAILED: Could not analyze expenses")
        save_results(results)
        return results
    
    results['details']['analysis'] = {
        'total_transactions': analysis_result['total_transactions'],
        'total_exclus': analysis_result['total_exclus'],
        'total_depenses': analysis_result['total_depenses'],
        'budget_max': analysis_result['budget_max'],
        'reste': analysis_result['reste'],
        'pourcentage': analysis_result['pourcentage'],
        'status': analysis_result['emoji']
    }
    
    # Step 3: Send notifications
    notif_ok, notif_result = send_notifications(analysis_result)
    
    if notif_ok:
        results['sms_ok'] = all(r['success'] for r in notif_result['sms'])
        results['email_ok'] = all(r['success'] for r in notif_result['email'])
        results['details']['notifications'] = notif_result
    else:
        results['details']['notification_error'] = str(notif_result)
    
    # Final summary
    log("\n" + "=" * 80)
    log("FINAL RESULTS")
    log("=" * 80)
    log(f"✅ CSV Download: {'SUCCESS' if results['csv_ok'] else 'FAILED'}")
    log(f"✅ Analysis: {'SUCCESS' if results['analysis_ok'] else 'FAILED'}")
    log(f"✅ SMS: {'SUCCESS' if results['sms_ok'] else 'FAILED'}")
    log(f"✅ Email: {'SUCCESS' if results['email_ok'] else 'FAILED'}")
    log("=" * 80)
    
    save_results(results)
    return results

def save_results(results):
    """Save results to JSON file"""
    results_file = DATA_DIR / f"e2e_results_{TIMESTAMP}.json"
    
    # Convert non-serializable objects
    def serialize(obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return obj
    
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, default=serialize)
    
    log(f"\n💾 Results saved to: {results_file}")

if __name__ == "__main__":
    try:
        results = main()
        
        # Print final JSON for easy parsing
        print("\n" + "=" * 80)
        print("JSON_RESULTS_START")
        print(json.dumps(results, indent=2, default=str))
        print("JSON_RESULTS_END")
        print("=" * 80)
        
        sys.exit(0 if all([results['csv_ok'], results['analysis_ok']]) else 1)
        
    except Exception as e:
        log(f"\n❌ FATAL ERROR: {e}")
        import traceback
        log(traceback.format_exc())
        sys.exit(1)
