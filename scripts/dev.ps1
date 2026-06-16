<#
.SYNOPSIS
  One-command local bootstrap for InfraMind (no Docker required).

.DESCRIPTION
  Creates the backend virtualenv, installs the lite dependency set, initializes
  and seeds a local SQLite database, then starts the FastAPI backend and the Vite
  frontend. Uses the built-in mock LLM and hashing embedder, so NO API keys and
  NO Postgres/Redis are required.

.PARAMETER Reseed
  Force re-initialization and re-seeding of the database even if it already exists.

.EXAMPLE
  ./scripts/dev.ps1
  ./scripts/dev.ps1 -Reseed
#>
[CmdletBinding()]
param(
    [switch]$Reseed
)

$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $PSScriptRoot
Set-Location $repo

Write-Host '==> InfraMind local bootstrap (SQLite + mock LLM, no Docker)' -ForegroundColor Cyan

# --- Backend ---------------------------------------------------------------
Set-Location (Join-Path $repo 'backend')

if (-not (Test-Path '.venv')) {
    Write-Host '==> Creating Python virtual environment...' -ForegroundColor Cyan
    python -m venv .venv
}

$py = Join-Path (Get-Location) '.venv\Scripts\python.exe'

Write-Host '==> Installing backend dependencies (lite)...' -ForegroundColor Cyan
& $py -m pip install --upgrade pip --quiet
& $py -m pip install -r requirements.txt --quiet

$dbFile = Join-Path (Get-Location) '.data\inframind.db'
if ($Reseed -or -not (Test-Path $dbFile)) {
    Write-Host '==> Initializing and seeding database...' -ForegroundColor Cyan
    & $py -m app.cli init-db
    & $py -m app.cli seed
} else {
    Write-Host '==> Database already present; skipping seed (use -Reseed to force).' -ForegroundColor DarkGray
}

Write-Host '==> Starting backend at http://127.0.0.1:8000 (docs: /docs) ...' -ForegroundColor Green
Start-Process -FilePath $py `
    -ArgumentList '-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', '8000' `
    -WorkingDirectory (Get-Location)

# --- Frontend --------------------------------------------------------------
Set-Location (Join-Path $repo 'frontend')

if (-not (Test-Path 'node_modules')) {
    Write-Host '==> Installing frontend dependencies...' -ForegroundColor Cyan
    npm install
}

Write-Host '==> Starting frontend at http://localhost:5173 ...' -ForegroundColor Green
Write-Host '    (Backend runs in a separate window. Press Ctrl+C here to stop the frontend.)' -ForegroundColor DarkGray
npm run dev
