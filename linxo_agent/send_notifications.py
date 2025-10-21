#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Send Linxo notifications via Brevo (SMS + Email)
"""

import json
import requests
from pathlib import Path

# Load API secrets
secrets_file = Path("/home/ubuntu/.api_secret_infos/api_secrets.json")
with open(secrets_file, 'r') as f:
    secrets = json.load(f)

BREVO_API_KEY = secrets['BREVO']['secrets']['API_KEY']

# Load reports
sms_report = Path("/home/ubuntu/reports/sms_report_20251013.txt").read_text(encoding='utf-8')
email_report = Path("/home/ubuntu/reports/email_report_20251013.html").read_text(encoding='utf-8')

# Recipients
phone_numbers = ["+33626267421", "+33611435899"]
email_addresses = ["phiperez@gmail.com", "caliemphi@gmail.com"]

print("📱 Sending SMS notifications via Brevo...")

# Send SMS
for phone in phone_numbers:
    try:
        response = requests.post(
            "https://api.brevo.com/v3/transactionalSMS/sms",
            headers={
                "api-key": BREVO_API_KEY,
                "Content-Type": "application/json"
            },
            json={
                "sender": "Linxo",
                "recipient": phone,
                "content": sms_report,
                "type": "transactional"
            }
        )
        
        if response.status_code in [200, 201]:
            print(f"✅ SMS sent to {phone}")
        else:
            print(f"❌ Failed to send SMS to {phone}: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Error sending SMS to {phone}: {e}")

print("\n📧 Sending email notifications via Brevo...")

# Send Email
for email in email_addresses:
    try:
        response = requests.post(
            "https://api.brevo.com/v3/smtp/email",
            headers={
                "api-key": BREVO_API_KEY,
                "Content-Type": "application/json"
            },
            json={
                "sender": {
                    "name": "Agent Linxo",
                    "email": "phiperez@gmail.com"
                },
                "to": [{"email": email}],
                "subject": "💰 Rapport Linxo - 13 octobre 2025",
                "htmlContent": email_report
            }
        )
        
        if response.status_code in [200, 201]:
            print(f"✅ Email sent to {email}")
        else:
            print(f"❌ Failed to send email to {email}: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Error sending email to {email}: {e}")

print("\n✅ Notification process completed!")
