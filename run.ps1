<#
.SYNOPSIS
    PowerShell runner for project targets (Windows alternative to Makefile).
.EXAMPLE
    .\run.ps1 install
    .\run.ps1 explore
    .\run.ps1 prepare
    .\run.ps1 baseline
    .\run.ps1 evaluate
    .\run.ps1 demo
    .\run.ps1 test
#>

param (
    [Parameter(Position=0, Mandatory=$false)]
    [ValidateSet("ui", "install", "explore", "prepare", "baseline", "evaluate", "demo", "test", "lint", "format", "clean", "help")]
    [string]$Target = "ui"
)

$ErrorActionPreference = "Stop"

switch ($Target) {
    "ui" {
        Write-Host "==> Launching Hiver Agent Web UI at http://localhost:8000..." -ForegroundColor Green
        python app.py
    }
    "install" {
        Write-Host "==> Installing dependencies..." -ForegroundColor Cyan
        pip install -r requirements.txt
        pip install -r requirements-dev.txt
    }
    "explore" {
        Write-Host "==> Running data exploration..." -ForegroundColor Cyan
        python scripts/explore.py
    }
    "prepare" {
        Write-Host "==> Preparing data and generating deterministic splits..." -ForegroundColor Cyan
        python scripts/prepare_data.py
    }
    "baseline" {
        Write-Host "==> Training baseline model..." -ForegroundColor Cyan
        python scripts/train_baseline.py
    }
    "evaluate" {
        Write-Host "==> Evaluating model on test split..." -ForegroundColor Cyan
        python scripts/evaluate.py
    }
    "demo" {
        Write-Host "==> Running demo inference..." -ForegroundColor Cyan
        python scripts/demo.py
    }
    "test" {
        Write-Host "==> Running test suite..." -ForegroundColor Cyan
        pytest tests/
    }
    "lint" {
        Write-Host "==> Running flake8 linter..." -ForegroundColor Cyan
        flake8 src/ scripts/ tests/
    }
    "format" {
        Write-Host "==> Formatting code with black..." -ForegroundColor Cyan
        black src/ scripts/ tests/
    }
    "clean" {
        Write-Host "==> Cleaning cache directories..." -ForegroundColor Cyan
        Get-ChildItem -Path . -Include "__pycache__", ".pytest_cache" -Recurse -Force -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force
    }
    Default {
        Write-Host "Usage: .\run.ps1 <target>" -ForegroundColor Yellow
        Write-Host "Available targets: install, explore, prepare, baseline, evaluate, demo, test, lint, format, clean"
    }
}
