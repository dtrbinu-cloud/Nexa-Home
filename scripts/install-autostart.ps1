<#
.SYNOPSIS
    Pemasang Auto-Start Layanan Windows 10 — Tahap 7.
.DESCRIPTION
    Mendaftarkan tugas otomatis pada Windows Task Scheduler agar seluruh sistem
    Nexa Home (FastAPI, Mosquitto, MediaMTX, Cloudflare Tunnel, dan Watchdog)
    otomatis hidup saat PC dinyalakan / login pengguna.
#>

[CmdletBinding()]
param ()

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot

Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "  NEXA HOME -- PEMASANGAN AUTO-START LAYANAN WINDOWS 10" -ForegroundColor Cyan
Write-Host "=================================================================" -ForegroundColor Cyan

$taskName = "NexaHome_AutoStart"
$scriptPath = Join-Path $projectRoot "scripts\start-all-services.ps1"

if (-not (Test-Path $scriptPath)) {
    throw "Skrip peluncur utama tidak ditemukan di: $scriptPath"
}

$actionCommand = "powershell.exe"
$actionArgs = "-ExecutionPolicy Bypass -WindowStyle Hidden -File `"$scriptPath`""

Write-Host "[*] Mendaftarkan tugas Windows Task Scheduler: '$taskName'..." -ForegroundColor Yellow

try {
    # Hapus task lama jika sudah ada
    schtasks.exe /Delete /TN $taskName /F 2>$null

    # Buat task baru yang berjalan saat pengguna login (ONLOGON)
    $createCmd = "schtasks.exe /Create /TN `"$taskName`" /TR `"$actionCommand $actionArgs`" /SC ONLOGON /RL HIGHEST /F"
    Invoke-Expression $createCmd

    Write-Host "`n[+] BERHASIL: Tugas '$taskName' telah terdaftar di Windows Task Scheduler!" -ForegroundColor Green
    Write-Host "  - Pemicu        : Saat Login Pengguna (ONLOGON)" -ForegroundColor White
    Write-Host "  - Skrip Sasaran : $scriptPath" -ForegroundColor White
    Write-Host "  - Hak Akses     : Highest Available (Administrator/User)" -ForegroundColor White
    Write-Host "`nSeluruh subsistem Nexa Home akan otomatis menyala di latar belakang setiap kali Windows dinyalakan." -ForegroundColor Green

} catch {
    Write-Warning "Pendaftaran Task Scheduler memerlukan izin Administrator. Membuat jalan pintas di folder Startup sebagai cadangan..."
    $startupFolder = [System.Environment]::GetFolderPath([System.Environment+SpecialFolder]::Startup)
    $shortcutPath = Join-Path $startupFolder "NexaHome_AutoStart.lnk"

    $wshShell = New-Object -ComObject WScript.Shell
    $shortcut = $wshShell.CreateShortcut($shortcutPath)
    $shortcut.TargetPath = "powershell.exe"
    $shortcut.Arguments = $actionArgs
    $shortcut.WorkingDirectory = $projectRoot
    $shortcut.WindowStyle = 7  # Minimized / Hidden
    $shortcut.Save()

    Write-Host "[+] BERHASIL: Shortcut auto-start telah dipasang di folder Startup:" -ForegroundColor Green
    Write-Host "    $shortcutPath" -ForegroundColor White
}

Write-Host "=================================================================`n" -ForegroundColor Cyan
