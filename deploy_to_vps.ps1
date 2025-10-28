# Script PowerShell pour déployer vers le VPS
# Usage: .\deploy_to_vps.ps1

$VPS_HOST = "linxo@vps-6e2f6679"
$VPS_PATH = "~/LINXO"

Write-Host "=== DEPLOIEMENT VERS LE VPS ===" -ForegroundColor Green

# Transférer les fichiers Python
Write-Host "`nTransfert des fichiers Python..." -ForegroundColor Yellow
scp linxo_agent/*.py ${VPS_HOST}:${VPS_PATH}/linxo_agent/

# Transférer les scripts de test
Write-Host "Transfert des scripts de test..." -ForegroundColor Yellow
scp test_*.py ${VPS_HOST}:${VPS_PATH}/

# Transférer requirements.txt
Write-Host "Transfert de requirements.txt..." -ForegroundColor Yellow
scp requirements.txt ${VPS_HOST}:${VPS_PATH}/

# Transférer la documentation
Write-Host "Transfert de la documentation..." -ForegroundColor Yellow
scp *.md ${VPS_HOST}:${VPS_PATH}/ 2>$null

Write-Host "`n=== DEPLOIEMENT TERMINE ===" -ForegroundColor Green
Write-Host "`nPour installer les dependances sur le VPS, executez:" -ForegroundColor Cyan
Write-Host "  ssh $VPS_HOST" -ForegroundColor White
Write-Host "  cd $VPS_PATH" -ForegroundColor White
Write-Host "  source .venv/bin/activate" -ForegroundColor White
Write-Host "  pip install -r requirements.txt" -ForegroundColor White
