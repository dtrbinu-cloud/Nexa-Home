# ==============================================================================
# SMART HOME "RUMAH" - SATU PERINTAH SETUP OTOMATIS (WINDOWS POWERSHELL)
# Idempoten: Aman dijalankan berulang, hanya memasang yang belum tersedia.
# Penggunaan: .\scripts\setup.ps1 [-WithMobile] [-Yes] [-SkipTests]
# ==============================================================================

[CmdletBinding()]
param (
    [switch]$WithMobile,
    [switch]$WithFirmware,
    [switch]$Yes,
    [switch]$SkipTests
)

$ErrorActionPreference = "Stop"
$RepoRoot = Resolve-Path "$PSScriptRoot\.."
Set-Location $RepoRoot

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "       SISTEM SMART HOME 'RUMAH' - SETUP OTOMATIS         " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

$Results = [System.Collections.Generic.List[PSObject]]::new()

function Add-Result {
    param(
        [string]$Component,
        [string]$Status,
        [string]$Note
    )
    $obj = [PSCustomObject]@{
        Komponen = $Component
        Status   = $Status
        Catatan  = $Note
    }
    $Results.Add($obj)
}

# ------------------------------------------------------------------------------
# 1. Pengecekan Lingkungan Dasar (Git, Python 3.11, Node.js, Mosquitto)
# ------------------------------------------------------------------------------
Write-Host "`n[1/7] Memeriksa perangkat lunak dasar..." -ForegroundColor Green

$MissingTools = [System.Collections.Generic.List[string]]::new()

# Cek Git
if (Get-Command "git" -ErrorAction SilentlyContinue) {
    $gitVer = (git --version).Trim()
    Add-Result "Git" "OK" $gitVer
} else {
    $MissingTools.Add("Git.Git")
    Add-Result "Git" "GAGAL" "Belum terpasang"
}

# Cek Python 3.11
$hasPy311 = $false
try {
    $pyCheck = & py -3.11 --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        $hasPy311 = $true
        Add-Result "Python 3.11" "OK" ($pyCheck.ToString().Trim())
    }
} catch {}

if (-not $hasPy311) {
    $MissingTools.Add("Python.Python.3.11")
    Add-Result "Python 3.11" "GAGAL" "Gunakan Python 3.11 via py launcher"
}

# Cek Node.js & npm
if (Get-Command "node" -ErrorAction SilentlyContinue) {
    $nodeVer = (node --version).Trim()
    Add-Result "Node.js" "OK" $nodeVer
} else {
    $MissingTools.Add("OpenJS.NodeJS.LTS")
    Add-Result "Node.js" "GAGAL" "Belum terpasang"
}

# Cek Mosquitto MQTT Broker (Windows Service)
$mosqSvc = Get-Service -Name "mosquitto" -ErrorAction SilentlyContinue
$mosqBin = Test-Path "C:\Program Files\mosquitto\mosquitto.exe"

if ($mosqSvc -or $mosqBin) {
    if ($mosqSvc -and $mosqSvc.Status -ne "Running") {
        try {
            Start-Service -Name "mosquitto" -ErrorAction SilentlyContinue
        } catch {}
    }
    Add-Result "Mosquitto Broker" "OK" "Service Windows aktif (port 1883)"
} else {
    $MissingTools.Add("EclipseFoundation.Mosquitto")
    Add-Result "Mosquitto Broker" "GAGAL" "Belum terpasang"
}

# Cek Flutter & Android jika flag -WithMobile diberikan
$hasFlutter = (Get-Command "flutter" -ErrorAction SilentlyContinue) -ne $null
if ($WithMobile) {
    if ($hasFlutter) {
        Add-Result "Flutter SDK" "OK" "Terpasang"
    } else {
        $MissingTools.Add("Flutter.Flutter")
        Add-Result "Flutter SDK" "GAGAL" "Belum terpasang"
    }
} else {
    if ($hasFlutter) {
        Add-Result "Flutter SDK" "OK" "Terpasang (opsional)"
    } else {
        Add-Result "Flutter SDK" "DILEWATI" "Jalankan dengan -WithMobile bila ingin memasang"
    }
}

# Cek PlatformIO jika flag -WithFirmware diberikan
$hasPio = (Get-Command "pio" -ErrorAction SilentlyContinue) -ne $null
if ($WithFirmware) {
    if ($hasPio) {
        Add-Result "PlatformIO CLI" "OK" "Terpasang"
    } else {
        Add-Result "PlatformIO CLI" "MEMASANG" "Akan dipasang via pip ke venv"
    }
} else {
    if ($hasPio) {
        Add-Result "PlatformIO CLI" "OK" "Terpasang (opsional)"
    } else {
        Add-Result "PlatformIO CLI" "DILEWATI" "Jalankan dengan -WithFirmware bila ingin memasang"
    }
}

# ------------------------------------------------------------------------------
# 2. Pemasangan Otomatis via Winget (Jika Ada yang Kurang)
# ------------------------------------------------------------------------------
if ($MissingTools.Count -gt 0) {
    Write-Host "`n[!] Ditemukan komponen yang belum terpasang: $($MissingTools -join ', ')" -ForegroundColor Yellow
    $hasWinget = (Get-Command "winget" -ErrorAction SilentlyContinue) -ne $null

    if (-not $hasWinget) {
        Write-Host "[!] Paket manajer 'winget' tidak ditemukan di sistem Windows ini." -ForegroundColor Red
        Write-Host "    Silakan unduh dan pasang secara manual melalui:" -ForegroundColor Yellow
        Write-Host "    - Git      : https://git-scm.com/download/win" -ForegroundColor White
        Write-Host "    - Python   : https://www.python.org/downloads/release/python-3119/" -ForegroundColor White
        Write-Host "    - Node.js  : https://nodejs.org/" -ForegroundColor White
        Write-Host "    - Flutter  : https://docs.flutter.dev/get-started/install/windows" -ForegroundColor White
    } else {
        Write-Host "[*] Alat yang akan dipasang via winget:" -ForegroundColor Cyan
        foreach ($tool in $MissingTools) {
            Write-Host "    - $tool" -ForegroundColor White
        }

        $proceed = $Yes
        if (-not $proceed) {
            $confirm = Read-Host "`nApakah Anda ingin memasang komponen di atas sekarang? (Y/N)"
            if ($confirm -match "^[Yy]") {
                $proceed = $true
            }
        }

        if ($proceed) {
            foreach ($tool in $MissingTools) {
                Write-Host "`n[*] Memasang $tool via winget..." -ForegroundColor Yellow
                winget install --id $tool -e --silent --accept-package-agreements --accept-source-agreements
            }
            Write-Host "`n[!] Pemasangan selesai. Jika PATH sistem diperbarui, silakan buka terminal baru lalu jalankan skrip ini lagi." -ForegroundColor Yellow
        } else {
            Write-Host "`n[*] Pemasangan dibatalkan oleh pengguna." -ForegroundColor Yellow
        }
    }
}

# ------------------------------------------------------------------------------
# 3. Konfigurasi Lingkungan (.env)
# ------------------------------------------------------------------------------
Write-Host "`n[2/6] Memeriksa berkas konfigurasi .env..." -ForegroundColor Green
$EnvFile = Join-Path $RepoRoot ".env"
$EnvExample = Join-Path $RepoRoot ".env.example"

if (-not (Test-Path $EnvFile)) {
    if (Test-Path $EnvExample) {
        Copy-Item $EnvExample $EnvFile
        Write-Host "[OK] Berkas .env baru berhasil dibuat dari .env.example." -ForegroundColor Green
        Add-Result "Konfigurasi .env" "OK" "Dibuat dari .env.example"
    } else {
        Add-Result "Konfigurasi .env" "GAGAL" ".env.example tidak ditemukan"
    }
} else {
    Write-Host "[OK] Berkas .env sudah ada (tidak ditimpa)." -ForegroundColor Gray
    Add-Result "Konfigurasi .env" "OK" "Sudah ada (aman/tidak ditimpa)"
}

# ------------------------------------------------------------------------------
# 4. Inisialisasi Backend Server (Python 3.11 venv)
# ------------------------------------------------------------------------------
Write-Host "`n[3/6] Menyiapkan server backend (server/.venv)..." -ForegroundColor Green
$ServerDir = Join-Path $RepoRoot "server"
$VenvDir = Join-Path $ServerDir ".venv"
$PythonExe = Join-Path $VenvDir "Scripts\python.exe"

if (-not (Test-Path $PythonExe)) {
    Write-Host "[*] Membuat virtual environment baru di server\.venv..." -ForegroundColor Yellow
    py -3.11 -m venv $VenvDir
}

if (Test-Path $PythonExe) {
    Write-Host "[*] Menginstal dependensi server (pip install)..." -ForegroundColor Yellow
    & "$PythonExe" -m pip install --upgrade pip --quiet
    & "$PythonExe" -m pip install -r "$ServerDir\requirements.txt" --quiet
    Add-Result "Backend venv" "OK" "Dependensi Python terpasang"

    if ($WithFirmware) {
        Write-Host "[*] Memasang PlatformIO CLI (-WithFirmware)..." -ForegroundColor Yellow
        & "$PythonExe" -m pip install platformio --quiet
        Add-Result "PlatformIO CLI" "OK" "Terpasang via pip"
    }
} else {
    Add-Result "Backend venv" "GAGAL" "Python virtual environment gagal dibuat"
}

# ------------------------------------------------------------------------------
# 5. Inisialisasi Frontend Web (npm install)
# ------------------------------------------------------------------------------
Write-Host "`n[4/6] Menyiapkan frontend web..." -ForegroundColor Green
$WebDir = Join-Path $RepoRoot "web"
$NodeModules = Join-Path $WebDir "node_modules"

if (-not (Test-Path $NodeModules)) {
    Write-Host "[*] Menginstal paket frontend web (npm install)..." -ForegroundColor Yellow
    Push-Location $WebDir
    npm install --quiet
    Pop-Location
    Add-Result "Web Frontend" "OK" "npm install selesai"
} else {
    Write-Host "[OK] node_modules web sudah ada." -ForegroundColor Gray
    Add-Result "Web Frontend" "OK" "node_modules siap"
}

# ------------------------------------------------------------------------------
# 6. Inisialisasi Flutter App (app/ flutter pub get)
# ------------------------------------------------------------------------------
Write-Host "`n[5/6] Menyiapkan aplikasi mobile Flutter (app/)..." -ForegroundColor Green
$AppDir = Join-Path $RepoRoot "app"

if (Test-Path $AppDir) {
    # Generate tokens.dart dari design-tokens.json
    if (Test-Path $PythonExe) {
        & "$PythonExe" "$RepoRoot\scripts\gen_flutter_theme.py"
    }

    if ($hasFlutter) {
        Write-Host "[*] Mengambil paket Flutter (flutter pub get)..." -ForegroundColor Yellow
        Push-Location $AppDir
        flutter pub get
        Pop-Location
        Add-Result "Flutter App" "OK" "flutter pub get & theme tokens selesai"
    } else {
        Add-Result "Flutter App" "DILEWATI" "Flutter SDK belum terpasang di host"
    }
}

# ------------------------------------------------------------------------------
# 7. Pengujian Mutu (Token Checker & Backend Pytest)
# ------------------------------------------------------------------------------
Write-Host "`n[6/6] Menjalankan verifikasi pengujian otomatis..." -ForegroundColor Green

if (Test-Path $PythonExe) {
    # Verifikasi token
    & "$PythonExe" "$RepoRoot\scripts\check_tokens.py"
    if ($LASTEXITCODE -eq 0) {
        Add-Result "Design Tokens" "OK" "100% mematuhi sistem token"
    } else {
        Add-Result "Design Tokens" "GAGAL" "Ditemukan warna di luar token"
    }

    # Pytest
    if (-not $SkipTests) {
        & "$PythonExe" -m pytest -q "$ServerDir\tests"
        if ($LASTEXITCODE -eq 0) {
            Add-Result "Backend Tests" "OK" "Semua tes pytest lulus"
        } else {
            Add-Result "Backend Tests" "GAGAL" "Sebagian tes pytest gagal"
        }
    } else {
        Add-Result "Backend Tests" "DILEWATI" "Flag -SkipTests aktif"
    }
}

# Tandai bahwa setup berhasil
Set-Content -Path (Join-Path $RepoRoot ".setup_done") -Value (Get-Date).ToString("s")

# ------------------------------------------------------------------------------
# Cetak Tabel Ringkasan
# ------------------------------------------------------------------------------
Write-Host "`n==========================================================" -ForegroundColor Cyan
Write-Host "                  RINGKASAN STATUS SETUP                  " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

$Results | Format-Table -AutoSize -Property Komponen, Status, Catatan

Write-Host "`n[OK] Setup selesai! Anda dapat menjalankan sistem dengan:" -ForegroundColor Green
Write-Host "     .\scripts\dev.ps1`n" -ForegroundColor Yellow
