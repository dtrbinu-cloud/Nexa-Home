# ==============================================================================
# SMART HOME "NEXA / RUMAH" - CLOUDFLARE TUNNEL RUNNER (aujasena.my.id)
# ==============================================================================

$RepoRoot = Resolve-Path "$PSScriptRoot\.."
$CloudflaredExe = "C:\Program Files (x86)\cloudflared\cloudflared.exe"
$ConfigFile = Join-Path $RepoRoot "server\nexa_tunnel.yml"

if (-not (Test-Path $CloudflaredExe)) {
    Write-Error "cloudflared.exe tidak ditemukan di $CloudflaredExe"
    exit 1
}

if (-not (Test-Path $ConfigFile)) {
    Write-Error "File konfigurasi tunnel tidak ditemukan di $ConfigFile"
    exit 1
}

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " Memulai Cloudflare Tunnel untuk domain: aujasena.my.id    " -ForegroundColor Cyan
Write-Host " Target Lokal: http://127.0.0.1:8000                       " -ForegroundColor White
Write-Host " Layanan Twork Flow (aujasenarisang.my.id) tidak terganggu " -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Cyan

& $CloudflaredExe tunnel --config $ConfigFile run 4e13bb28-53f8-475a-8021-3f11d3e07722
