# Script PowerShell de vérification complète du VPS
# Usage: .\check_vps_status.ps1

$VPS_HOST = "linxo@152.228.218.1"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "VÉRIFICATION COMPLÈTE DU VPS LINXO" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 1. Vérifier la connexion SSH
Write-Host "1. Test de connexion SSH..." -ForegroundColor Yellow
try {
    $result = ssh $VPS_HOST "echo 'Connexion OK'" 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✓ Connexion SSH : OK" -ForegroundColor Green
    } else {
        Write-Host "   ✗ Connexion SSH : ÉCHEC" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "   ✗ Connexion SSH : ÉCHEC" -ForegroundColor Red
    exit 1
}
Write-Host ""

# 2. Vérifier le cron
Write-Host "2. Configuration du cron..." -ForegroundColor Yellow
ssh $VPS_HOST "crontab -l 2>/dev/null | grep -E '(linxo|LINXO|run_)'"
Write-Host ""

# 3. Vérifier le service cron
Write-Host "3. Service cron..." -ForegroundColor Yellow
$cronStatus = ssh $VPS_HOST "systemctl is-active cron"
if ($cronStatus -eq "active") {
    Write-Host "   ✓ Service cron : actif" -ForegroundColor Green
} else {
    Write-Host "   ✗ Service cron : inactif" -ForegroundColor Red
}
Write-Host ""

# 4. Vérifier la structure des dossiers
Write-Host "4. Structure des dossiers..." -ForegroundColor Yellow
$checks = @(
    @{Path="~/LINXO"; Name="Dossier ~/LINXO"},
    @{Path="~/LINXO/venv"; Name="Virtualenv"},
    @{Path="~/LINXO/logs"; Name="Dossier logs"},
    @{Path="/var/www/html/reports"; Name="Dossier rapports web"}
)

foreach ($check in $checks) {
    $exists = ssh $VPS_HOST "test -d $($check.Path) && echo 'OK' || echo 'KO'" 2>$null
    if ($exists -eq "OK") {
        Write-Host "   ✓ $($check.Name) : existe" -ForegroundColor Green
    } else {
        Write-Host "   ✗ $($check.Name) : manquant" -ForegroundColor Red
    }
}
Write-Host ""

# 5. Vérifier les fichiers CSV récents
Write-Host "5. Fichiers CSV récents..." -ForegroundColor Yellow
ssh $VPS_HOST "ls -lt ~/LINXO/data/*.csv 2>/dev/null | head -3 || echo '   Aucun fichier CSV dans data/'"
ssh $VPS_HOST "ls -lt ~/LINXO/downloads/*.csv 2>/dev/null | head -3 || echo '   Aucun fichier CSV dans downloads/'"
Write-Host ""

# 6. Vérifier les logs récents
Write-Host "6. Logs récents..." -ForegroundColor Yellow
ssh $VPS_HOST "ls -lt ~/LINXO/logs/*.log 2>/dev/null | head -5 || echo '   Aucun fichier log'"
Write-Host ""

# 7. Vérifier le dernier log cron
Write-Host "7. Contenu du dernier log cron (50 dernières lignes)..." -ForegroundColor Yellow
ssh $VPS_HOST "tail -50 ~/LINXO/logs/cron.log 2>/dev/null || echo '   Fichier cron.log introuvable'"
Write-Host ""

# 8. Vérifier Nginx
Write-Host "8. Service Nginx..." -ForegroundColor Yellow
$nginxStatus = ssh $VPS_HOST "systemctl is-active nginx"
if ($nginxStatus -eq "active") {
    Write-Host "   ✓ Nginx : actif" -ForegroundColor Green
} else {
    Write-Host "   ✗ Nginx : inactif" -ForegroundColor Red
}
Write-Host ""

# 9. Vérifier les rapports générés
Write-Host "9. Rapports HTML générés..." -ForegroundColor Yellow
ssh $VPS_HOST "ls -lt /var/www/html/reports/ 2>/dev/null | head -5 || echo '   Aucun rapport trouvé'"
Write-Host ""

# 10. Vérifier le fichier .env
Write-Host "10. Configuration .env..." -ForegroundColor Yellow
$envExists = ssh $VPS_HOST "test -f ~/LINXO/.env && echo 'OK' || echo 'KO'"
if ($envExists -eq "OK") {
    Write-Host "   ✓ Fichier .env : existe" -ForegroundColor Green
} else {
    Write-Host "   ✗ Fichier .env : manquant" -ForegroundColor Red
}
Write-Host ""

# 11. Test Python
Write-Host "11. Environnement Python..." -ForegroundColor Yellow
ssh $VPS_HOST "~/LINXO/venv/bin/python3 --version"
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "RÉSUMÉ DE LA VÉRIFICATION" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Pour tester manuellement l'exécution complète :" -ForegroundColor Yellow
Write-Host "  ssh $VPS_HOST 'cd ~/LINXO && ./venv/bin/python3 run_linxo_e2e.py'" -ForegroundColor White
Write-Host ""
Write-Host "Pour voir les logs en temps réel :" -ForegroundColor Yellow
Write-Host "  ssh $VPS_HOST 'tail -f ~/LINXO/logs/cron.log'" -ForegroundColor White
Write-Host ""
Write-Host "Pour corriger l'heure du cron :" -ForegroundColor Yellow
Write-Host "  .\fix_cron_hour.sh" -ForegroundColor White
