<#
.SYNOPSIS
    Pencabut Auto-Start Layanan Windows 10 — Tahap 7.
.DESCRIPTION
    Menghapus tugas NexaHome_AutoStart dari Windows Task Scheduler dan shortcut Startup.
#>

$ErrorActionPreference = "Continue"

Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "  NEXA HOME -- PENCABUTAN AUTO-START LAYANAN WINDOWS 10" -ForegroundColor Cyan
Write-Host "=================================================================" -ForegroundColor Cyan

$taskName = "NexaHome_AutoStart"
Write-Host "[*] Menghapus tugas '$taskName' dari Task Scheduler..." -ForegroundColor Yellow
schtasks.exe /Delete /TN $taskName /F 2>$null

$startupFolder = [System.Environment]::GetFolderPath([System.Environment+SpecialFolder]::Startup)
$shortcutPath = Join-Path $startupFolder "NexaHome_AutoStart.lnk"
if (Test-Path $shortcutPath) {
    Remove-Item -Path $shortcutPath -Force
    Write-Host "[*] Menghapus jalan pintas dari folder Startup: $shortcutPath" -ForegroundColor Yellow
}

Write-Host "`n[+] BERHASIL: Auto-start Nexa Home telah dicabut." -ForegroundColor Green
Write-Host "=================================================================`n" -ForegroundColor Cyan
