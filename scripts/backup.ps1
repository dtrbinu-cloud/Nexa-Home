[CmdletBinding()]
param (
    [string]$OutputDir = "backups",
    [switch]$IncludeClips = $true,
    [string]$PythonExe = "server\data\..\.venv\Scripts\python.exe"
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot

Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "  NEXA HOME -- PEMBUATAN ARSIP CADANGAN SISTEM (TAHAP 7 BACKUP)" -ForegroundColor Cyan
Write-Host "=================================================================" -ForegroundColor Cyan

if (-not (Test-Path $PythonExe)) {
    $PythonExe = "server\.venv\Scripts\python.exe"
}
if (-not (Test-Path $PythonExe)) {
    $PythonExe = "python.exe"
}

$dbPath = "server\data\rumah.db"
if (-not (Test-Path $dbPath)) {
    Write-Warning "Database $dbPath belum ditemukan! Pastikan server pernah dijalankan minimal satu kali."
}

if (-not (Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
}

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$archiveName = "nexa_backup_$timestamp.zip"
$archivePath = Join-Path $OutputDir $archiveName
$stagingDir = Join-Path $OutputDir "staging_$timestamp"

Write-Host "[*] Mempersiapkan direktori penampungan: $stagingDir" -ForegroundColor Yellow
New-Item -ItemType Directory -Path $stagingDir -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $stagingDir "config") -Force | Out-Null

try {
    # 1. Snapshot database SQLite via Online Backup API
    if (Test-Path $dbPath) {
        $stagedDb = Join-Path $stagingDir "rumah.db"
        Write-Host "[*] Mengambil snapshot database atomik (Online Backup API)..." -ForegroundColor Yellow
        & $PythonExe "scripts\sqlite_backup_helper.py" --source $dbPath --target $stagedDb
        if ($LASTEXITCODE -ne 0) {
            throw "Gagal melakukan online backup database SQLite!"
        }
    }

    # 2. Salin rekaman klip terenkripsi jika ada
    if ($IncludeClips) {
        $clipsDir = "server\data\clips"
        if (Test-Path $clipsDir) {
            $stagedClips = Join-Path $stagingDir "clips"
            Write-Host "[*] Mengarsipkan klip video terenkripsi dari $clipsDir..." -ForegroundColor Yellow
            Copy-Item -Path $clipsDir -Destination $stagedClips -Recurse -Force
        }
    }

    # 3. Salin file konfigurasi penting (.env dan nexa_tunnel.yml)
    if (Test-Path ".env") {
        Copy-Item -Path ".env" -Destination (Join-Path $stagingDir "config\.env") -Force
    }
    if (Test-Path "server\nexa_tunnel.yml") {
        Copy-Item -Path "server\nexa_tunnel.yml" -Destination (Join-Path $stagingDir "config\nexa_tunnel.yml") -Force
    }

    # 4. Buat metadata info backup
    $metaPath = Join-Path $stagingDir "backup_info.json"
    $isoDate = (Get-Date).ToString("o")
    $metaContent = "{`"created_at`": `"$isoDate`", `"version`": `"0.2.0`", `"system`": `"Nexa Home`"}"
    Set-Content -Path $metaPath -Value $metaContent -Encoding UTF8

    # 5. Kompresi seluruh staging ke ZIP
    Write-Host "[*] Mengompresi seluruh data ke $archivePath..." -ForegroundColor Yellow
    Compress-Archive -Path "$stagingDir\*" -DestinationPath $archivePath -Force

    # 6. Hitung Checksum SHA-256
    $hashResult = Get-FileHash -Path $archivePath -Algorithm SHA256
    $sha256 = $hashResult.Hash
    $sha256Path = "$archivePath.sha256"
    Set-Content -Path $sha256Path -Value "$sha256  $archiveName" -Encoding ASCII

    $fileSize = (Get-Item $archivePath).Length
    $fileSizeKb = [math]::Round($fileSize / 1024, 2)

    Write-Host ""
    Write-Host "=================================================================" -ForegroundColor Green
    Write-Host "  [SUKSES] CADANGAN SISTEM BERHASIL DIBUAT!" -ForegroundColor Green
    Write-Host "  - Lokasi Berkas : $archivePath" -ForegroundColor White
    Write-Host "  - Ukuran Berkas : $fileSizeKb KB" -ForegroundColor White
    Write-Host "  - Checksum SHA  : $sha256" -ForegroundColor White
    Write-Host "  - File Verif    : $sha256Path" -ForegroundColor White
    Write-Host "=================================================================" -ForegroundColor Green
    Write-Host ""

} finally {
    if (Test-Path $stagingDir) {
        Remove-Item -Path $stagingDir -Recurse -Force -ErrorAction SilentlyContinue
    }
}
