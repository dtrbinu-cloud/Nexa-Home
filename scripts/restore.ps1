[CmdletBinding()]
param (
    [string]$BackupFile = "",
    [switch]$RestoreEnv = $false,
    [switch]$Force = $false,
    [string]$PythonExe = "server\.venv\Scripts\python.exe"
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot

Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "  NEXA HOME -- PEMULIHAN SISTEM DARI CADANGAN (TAHAP 7 RESTORE)" -ForegroundColor Cyan
Write-Host "=================================================================" -ForegroundColor Cyan

if (-not (Test-Path $PythonExe)) {
    $PythonExe = "python.exe"
}

# 1. Cari file backup jika tidak ditentukan
if ([string]::IsNullOrWhiteSpace($BackupFile)) {
    $latestBackup = Get-ChildItem -Path "backups" -Filter "nexa_backup_*.zip" -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 1

    if ($null -eq $latestBackup) {
        throw "Tidak ditemukan file arsip backup di direktori 'backups/'."
    }
    $BackupFile = $latestBackup.FullName
    Write-Host "[*] Menggunakan arsip backup terbaru: $BackupFile" -ForegroundColor Yellow
} else {
    if (-not (Test-Path $BackupFile)) {
        throw "File backup tidak ditemukan di: $BackupFile"
    }
}

# 2. Verifikasi Checksum SHA-256 jika ada
$shaFile = "$BackupFile.sha256"
if (Test-Path $shaFile) {
    Write-Host "[*] Memverifikasi integritas checksum SHA-256..." -ForegroundColor Yellow
    $expectedHash = (Get-Content $shaFile).Trim().Split(" ")[0]
    $actualHash = (Get-FileHash -Path $BackupFile -Algorithm SHA256).Hash
    if ($expectedHash.ToUpper() -ne $actualHash.ToUpper()) {
        throw "Checksum SHA-256 tidak cocok! Arsip backup mungkin korup. Ekspektasi: $expectedHash, Aktual: $actualHash"
    }
    Write-Host "[+] Checksum SHA-256 terverifikasi cocok ($actualHash)." -ForegroundColor Green
}

# 3. Konfirmasi (jika bukan mode -Force)
if (-not $Force) {
    Write-Host ""
    Write-Host "[PERINGATAN] Proses pemulihan akan menimpa data database aktif." -ForegroundColor Yellow
    $ans = Read-Host "Ketik 'YA' untuk melanjutkan proses pemulihan"
    if ($ans -ne "YA") {
        Write-Host "[-] Pemulihan dibatalkan oleh pengguna." -ForegroundColor Red
        exit 0
    }
}

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$stagingDir = Join-Path "backups" "restore_staging_$timestamp"
$rollbackDir = "server\data\rollback_before_restore"

try {
    # 4. Amankan snapshot darurat data aktif saat ini (Rollback Safety)
    Write-Host "[*] Membuat salinan darurat data aktif saat ini ke $rollbackDir..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Path $rollbackDir -Force | Out-Null
    if (Test-Path "server\data\rumah.db") {
        Copy-Item -Path "server\data\rumah.db" -Destination (Join-Path $rollbackDir "rumah.db.pre_restore_$timestamp") -Force
    }
    if (Test-Path ".env") {
        Copy-Item -Path ".env" -Destination (Join-Path $rollbackDir ".env.pre_restore_$timestamp") -Force
    }

    # 5. Ekstrak arsip ke staging
    Write-Host "[*] Mengekstrak arsip backup ke area verifikasi staging..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Path $stagingDir -Force | Out-Null
    Expand-Archive -Path $BackupFile -DestinationPath $stagingDir -Force

    $stagedDb = Join-Path $stagingDir "rumah.db"
    if (Test-Path $stagedDb) {
        # 6. Validasi integritas SQLite
        Write-Host "[*] Memeriksa integritas berkas database yang diekstrak..." -ForegroundColor Yellow
        & $PythonExe "scripts\sqlite_backup_helper.py" --source $stagedDb --target $stagedDb --verify-only
        if ($LASTEXITCODE -ne 0) {
            throw "Database hasil ekstraksi gagal validasi integritas!"
        }

        # 7. Terapkan database menggunakan SQLite Online Backup API (aman bahkan jika backend sedang berjalan)
        Write-Host "[*] Menerapkan database utama ke server\data\rumah.db (via Online Backup API)..." -ForegroundColor Yellow
        & $PythonExe "scripts\sqlite_backup_helper.py" --source $stagedDb --target "server\data\rumah.db"
        if ($LASTEXITCODE -ne 0) {
            # Fallback jika server sedang offline
            Copy-Item -Path $stagedDb -Destination "server\data\rumah.db" -Force
        }
    }

    # 8. Terapkan klip rekaman jika ada
    $stagedClips = Join-Path $stagingDir "clips"
    if (Test-Path $stagedClips) {
        Write-Host "[*] Memulihkan klip rekaman kamera terenkripsi..." -ForegroundColor Yellow
        New-Item -ItemType Directory -Path "server\data\clips" -Force | Out-Null
        Copy-Item -Path "$stagedClips\*" -Destination "server\data\clips" -Recurse -Force
    }

    # 9. Terapkan file konfigurasi jika diminta
    if ($RestoreEnv) {
        $stagedEnv = Join-Path $stagingDir "config\.env"
        if (Test-Path $stagedEnv) {
            Write-Host "[*] Memulihkan file .env dari cadangan..." -ForegroundColor Yellow
            Copy-Item -Path $stagedEnv -Destination ".env" -Force
        }
    }

    Write-Host ""
    Write-Host "=================================================================" -ForegroundColor Green
    Write-Host "  [SUKSES] PEMULIHAN SISTEM BERHASIL DILAKUKAN!" -ForegroundColor Green
    Write-Host "  - Arsip Sumber  : $BackupFile" -ForegroundColor White
    Write-Host "  - Salinan Aman  : $rollbackDir" -ForegroundColor White
    Write-Host "  - Status DB     : Terverifikasi utuh dan konsisten" -ForegroundColor White
    Write-Host "=================================================================" -ForegroundColor Green
    Write-Host ""

} finally {
    if (Test-Path $stagingDir) {
        Remove-Item -Path $stagingDir -Recurse -Force -ErrorAction SilentlyContinue
    }
}
