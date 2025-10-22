# LINXO PROJECT - DEPENDENCY GRAPH

**Generated:** 2025-10-22
**Purpose:** Visual representation of module dependencies

---

## 🎯 LEGEND

- **→** : imports/uses
- **✅** : Active module (in use)
- **❌** : Obsolete module (can be removed)
- **[EP]** : Entry Point (has `__main__`)

---

## 📊 CORE ARCHITECTURE

```
┌─────────────────────────────────────────────────────────┐
│                    ENTRY POINTS                         │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  [1] linxo_agent.py [EP] ✅                            │
│       Main orchestrator (v2 unified architecture)      │
│       ├─→ config                                       │
│       ├─→ analyzer                                     │
│       ├─→ linxo_connexion                             │
│       └─→ notifications                               │
│                                                         │
│  [2] linxo_agent/run_linxo_e2e.py [EP] ✅             │
│       E2E workflow runner (v3 standalone)              │
│       ├─→ selenium                                     │
│       ├─→ requests (OVH SMS)                          │
│       └─→ smtplib (Email)                             │
│                                                         │
│  [3] linxo_agent/run_analysis.py [EP] ✅              │
│       Simplified analysis runner                       │
│       └─→ agent_linxo_csv_v3_RELIABLE                │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## 🔧 CORE MODULES

### Configuration Layer

```
config.py ✅
  ├─ Purpose: Central configuration management
  ├─ Loads: config_linxo.json, depenses_recurrentes.json
  ├─ Dependencies: python-dotenv, pathlib, json
  └─ Used by: analyzer, notifications, linxo_connexion
```

### Data Processing Layer

```
analyzer.py ✅
  ├─ Purpose: CSV parsing, expense categorization, budget analysis
  ├─ Dependencies: config, csv, datetime, re
  ├─ Categorizes: Fixed expenses, Variable expenses, Excluded items
  └─ Used by: linxo_agent.py, notifications.py, test files
```

### Web Automation Layer

```
linxo_connexion.py ✅
  ├─ Purpose: Selenium-based Linxo web scraping
  ├─ Dependencies: selenium, config, time
  ├─ Functions: Login, CSV download, session management
  └─ Used by: linxo_agent.py, run_linxo_e2e.py
```

### Notification Layer

```
notifications.py ✅
  ├─ Purpose: Multi-channel notification manager
  ├─ Dependencies: analyzer, config, report_formatter_v2, smtplib, email
  ├─ Channels: Email (Gmail SMTP), SMS (OVH API)
  └─ Used by: linxo_agent.py, test files
```

### Report Generation Layer

```
report_formatter_v2.py ✅ (ACTIVE VERSION)
  ├─ Purpose: HTML and text report generation
  ├─ Dependencies: config, datetime, calendar
  ├─ Formats: Email HTML, SMS text, console output
  └─ Used by: notifications.py, generate_preview.py

report_formatter.py ❌ (OLD VERSION - REMOVE)
  ├─ Purpose: Original report formatter
  ├─ Status: UNREFERENCED - superseded by _v2
  └─ Action: Safe to delete
```

---

## 🔗 DEPENDENCY FLOW DIAGRAM

### Main Application Flow (linxo_agent.py)

```
┌────────────────┐
│ linxo_agent.py │ [Entry Point]
└────────┬───────┘
         │
         ├─→ config.py
         │    └─→ Load JSON configs
         │         ├─ config_linxo.json
         │         └─ depenses_recurrentes.json
         │
         ├─→ linxo_connexion.py
         │    ├─→ selenium (web automation)
         │    └─→ Download CSV from Linxo
         │
         ├─→ analyzer.py
         │    ├─→ Parse CSV
         │    ├─→ Categorize expenses
         │    └─→ Calculate budget
         │
         └─→ notifications.py
              ├─→ report_formatter_v2.py
              │    ├─→ Generate HTML report
              │    └─→ Generate SMS text
              ├─→ smtplib (Email)
              └─→ requests (OVH SMS API)
```

### E2E Flow (run_linxo_e2e.py)

```
┌──────────────────────┐
│ run_linxo_e2e.py     │ [Entry Point]
└──────────┬───────────┘
           │
           ├─→ Selenium automation (direct)
           │    └─→ Linxo login & download
           │
           ├─→ CSV analysis (inline)
           │    └─→ Custom logic (not using analyzer.py)
           │
           └─→ Notifications (inline)
                ├─→ Gmail SMTP (smtplib)
                └─→ OVH SMS API (requests)
```

### Simplified Analysis Flow (run_analysis.py)

```
┌──────────────────────┐
│ run_analysis.py      │ [Entry Point]
└──────────┬───────────┘
           │
           └─→ agent_linxo_csv_v3_RELIABLE.py
                ├─→ Legacy analyzer module
                ├─→ Self-contained (includes all logic)
                └─→ Direct CSV analysis (no dependencies)
```

---

## 🧪 TEST SUITE DEPENDENCIES

### Active Test Files

```
test_analyzer.py [EP] ✅
  └─→ analyzer.py

test_new_format.py [EP] ✅
  ├─→ analyzer.py
  ├─→ config.py
  └─→ report_formatter_v2.py

test_envoi_nouveaux_formats.py [EP] ✅
  ├─→ analyzer.py
  ├─→ config.py
  ├─→ notifications.py
  └─→ report_formatter_v2.py

test_preview_notifications.py [EP] ✅
  ├─→ analyzer.py
  ├─→ config.py
  └─→ datetime

test_send_notifications.py [EP] ✅
  ├─→ analyzer.py
  ├─→ config.py
  └─→ notifications.py

test_sms_only.py [EP] ✅
  ├─→ config.py
  ├─→ notifications.py
  └─→ email/smtplib

test_sms_direct.py [EP] ✅
  ├─→ config.py
  └─→ notifications.py

test_sms_debug.py [EP] ✅
  ├─→ config.py
  └─→ email/smtplib
```

---

## 📦 EXTERNAL DEPENDENCIES

From [requirements.txt](requirements.txt):

```
┌──────────────────────────────────────┐
│     EXTERNAL PYTHON PACKAGES         │
├──────────────────────────────────────┤
│                                      │
│  selenium==4.15.2                    │
│    └─→ Used by: linxo_connexion,     │
│                  run_linxo_e2e       │
│                                      │
│  webdriver-manager==4.0.1            │
│    └─→ Used by: linxo_connexion      │
│         (ChromeDriver management)    │
│                                      │
│  requests==2.31.0                    │
│    └─→ Used by: run_linxo_e2e        │
│         (OVH SMS API)                │
│                                      │
│  python-dotenv==1.0.0                │
│    └─→ Used by: config               │
│         (.env file loading)          │
│                                      │
│  Built-in modules:                   │
│    - smtplib (Email)                 │
│    - email (MIME)                    │
│    - json (Config)                   │
│    - csv (Data parsing)              │
│    - datetime (Timestamps)           │
│    - pathlib (File paths)            │
│    - re (Regex matching)             │
│                                      │
└──────────────────────────────────────┘
```

---

## 🗂️ RUNTIME CONFIGURATION FILES

```
┌─────────────────────────────────────────┐
│      CONFIGURATION FILES                │
│      (Loaded at Runtime)                │
├─────────────────────────────────────────┤
│                                         │
│  config_linxo.json ✅                   │
│    ├─ Linxo credentials                │
│    ├─ Budget settings                  │
│    ├─ Notification recipients          │
│    └─ Loaded by: config.py             │
│                                         │
│  depenses_recurrentes.json ✅           │
│    ├─ Fixed expense definitions        │
│    ├─ Category mappings                │
│    ├─ Matching rules                   │
│    └─ Loaded by: config.py, analyzer   │
│                                         │
│  api_secrets.json ✅                    │
│    ├─ Gmail credentials                │
│    ├─ OVH SMS API keys                 │
│    └─ Loaded by: notifications,        │
│                  run_linxo_e2e         │
│                                         │
│  .env (optional) ✅                     │
│    ├─ Environment overrides            │
│    └─ Loaded by: config.py             │
│                                         │
└─────────────────────────────────────────┘
```

---

## 🔍 UNREFERENCED FILES (Safe to Remove)

### Obsolete Code

```
linxo_agent/send_notifications.py ❌
  ├─ Status: UNREFERENCED
  ├─ Reason: Standalone script, integrated into notifications.py
  └─ Action: DELETE

linxo_agent/report_formatter.py ❌
  ├─ Status: UNREFERENCED
  ├─ Reason: Old version, superseded by report_formatter_v2.py
  └─ Action: DELETE
```

### Generated Artifacts (Should not be in Git)

```
apercu_rapport.html ❌
apercu_sms.txt ❌
reports/*.txt ❌
  └─ Reason: Runtime-generated, excluded by .gitignore
```

---

## 📈 MODULE USAGE MATRIX

| Module | Imported By | Entry Point | Status |
|--------|-------------|-------------|--------|
| config.py | analyzer, linxo_connexion, notifications, tests | No | ✅ KEEP |
| analyzer.py | linxo_agent, notifications, tests | Yes | ✅ KEEP |
| linxo_connexion.py | linxo_agent | Yes | ✅ KEEP |
| notifications.py | linxo_agent, tests | Yes | ✅ KEEP |
| report_formatter_v2.py | notifications, generate_preview, tests | No | ✅ KEEP |
| agent_linxo_csv_v3_RELIABLE.py | run_analysis | Yes | ✅ KEEP |
| run_linxo_e2e.py | - | Yes | ✅ KEEP |
| run_analysis.py | - | Yes | ✅ KEEP |
| report_formatter.py | **NONE** | Yes | ❌ REMOVE |
| send_notifications.py | **NONE** | Yes | ❌ REMOVE |

---

## 🎯 KEY INSIGHTS

### Critical Modules (Never Remove)

1. **config.py** - Central config manager, used everywhere
2. **analyzer.py** - Core business logic for expense analysis
3. **notifications.py** - Notification orchestrator
4. **linxo_connexion.py** - Web automation layer
5. **report_formatter_v2.py** - Active report generator

### Entry Points (3 ways to run the app)

1. **linxo_agent.py** - Recommended (unified architecture, modular)
2. **run_linxo_e2e.py** - Alternative (standalone, all-in-one)
3. **run_analysis.py** - Simplified (analysis only, no download)

### Obsolete Modules (Safe to Remove)

1. **report_formatter.py** - Never imported, old version
2. **send_notifications.py** - Never imported, functionality in notifications.py

---

## 🔄 REFACTORING HISTORY

### V1 → V2 → V3 Evolution

```
V1 (Legacy)
  └─ Monolithic scripts, no modules

V2 (Current Production - linxo_agent.py)
  ├─ Modular architecture
  ├─ Separate concerns (config, analyzer, notifications)
  └─ Recommended for new development

V3 (Alternative - run_linxo_e2e.py)
  ├─ Standalone E2E script
  ├─ Self-contained (minimal dependencies)
  └─ Used for specific deployments

RELIABLE (Fallback - agent_linxo_csv_v3_RELIABLE.py)
  ├─ Legacy analyzer
  ├─ Used by run_analysis.py
  └─ Kept for compatibility
```

---

## 📝 RECOMMENDATIONS

### For Development

- **Use:** `linxo_agent.py` (modular, testable, maintainable)
- **Test with:** `test_*.py` files
- **Configure via:** `config.py` + JSON files

### For Deployment

- **Production:** `linxo_agent.py` or `run_linxo_e2e.py`
- **Quick analysis:** `run_analysis.py`
- **Cron job:** Any of the above

### For Cleanup

- **Remove:** `report_formatter.py`, `send_notifications.py`
- **Keep:** All other modules
- **Archive:** Old documentation files

---

*Dependency graph generated from automated analysis*
*See DEPENDENCY_ANALYSIS.txt for raw data*
