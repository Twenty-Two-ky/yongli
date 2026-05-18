# AI API Testing Platform — Start All (PowerShell)
$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RootDir = Split-Path -Parent $ScriptDir

Write-Host "=== AI API Testing Platform — Start All ===" -ForegroundColor Cyan

# Cleanup on Ctrl+C
$jobs = @()

try {
    Write-Host "[1/5] Starting demo service (local :8001)..." -ForegroundColor Green
    $job1 = Start-Job -Name "demo-local" -ArgumentList $RootDir {
        param($dir)
        Set-Location "$dir\demo-service"
        python server.py --env-name local --port 8001
    }
    $jobs += $job1

    Write-Host "[2/5] Starting demo service (staging :8002)..." -ForegroundColor Green
    $job2 = Start-Job -Name "demo-staging" -ArgumentList $RootDir {
        param($dir)
        Set-Location "$dir\demo-service"
        python server.py --env-name staging --port 8002
    }
    $jobs += $job2

    Start-Sleep -Seconds 2

    Write-Host "[3/5] Starting backend Master (:8080)..." -ForegroundColor Green
    $job3 = Start-Job -Name "backend" -ArgumentList $RootDir {
        param($dir)
        Set-Location "$dir\backend"
        python main.py
    }
    $jobs += $job3

    Start-Sleep -Seconds 3

    Write-Host "[4/5] Starting 3 Worker instances..." -ForegroundColor Green
    $job4 = Start-Job -Name "worker-1" -ArgumentList $RootDir {
        param($dir)
        Set-Location "$dir\worker"
        $env:WORKER_NAME = "worker-1"
        python worker.py
    }
    $jobs += $job4

    $job5 = Start-Job -Name "worker-2" -ArgumentList $RootDir {
        param($dir)
        Set-Location "$dir\worker"
        $env:WORKER_NAME = "worker-2"
        python worker.py
    }
    $jobs += $job5

    $job6 = Start-Job -Name "worker-3" -ArgumentList $RootDir {
        param($dir)
        Set-Location "$dir\worker"
        $env:WORKER_NAME = "worker-3"
        python worker.py
    }
    $jobs += $job6

    Write-Host "[5/5] Starting frontend dev server (:5173)..." -ForegroundColor Green
    $job7 = Start-Job -Name "frontend" -ArgumentList $RootDir {
        param($dir)
        Set-Location "$dir\frontend"
        npm run dev
    }
    $jobs += $job7

    Write-Host ""
    Write-Host "All services started!" -ForegroundColor Cyan
    Write-Host "  Demo (local):     http://localhost:8001" -ForegroundColor Yellow
    Write-Host "  Demo (staging):   http://localhost:8002" -ForegroundColor Yellow
    Write-Host "  Backend API:      http://localhost:8080" -ForegroundColor Yellow
    Write-Host "  Frontend:         http://localhost:5173" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Press Ctrl+C to stop all." -ForegroundColor Gray
    Write-Host "To view output: Receive-Job -Name <job-name> | select -Last 20" -ForegroundColor Gray

    # Keep script running until Ctrl+C
    while ($true) {
        Start-Sleep -Seconds 1
    }
}
finally {
    Write-Host "`nStopping all services..." -ForegroundColor Red
    foreach ($job in $jobs) {
        Stop-Job -Job $job
        Remove-Job -Job $job -Force
    }
    Write-Host "All stopped." -ForegroundColor Red
}
