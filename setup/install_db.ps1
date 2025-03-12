# Simple PostgreSQL installation script
Write-Host "Installing PostgreSQL..." -ForegroundColor Green

# Check if running as administrator
$currentPrincipal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
$isAdmin = $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "This script requires administrator privileges. Please run as administrator." -ForegroundColor Red
    exit 1
}

# Install Chocolatey if not already installed
if (-not (Get-Command choco -ErrorAction SilentlyContinue)) {
    Write-Host "Installing Chocolatey package manager..." -ForegroundColor Yellow
    Set-ExecutionPolicy Bypass -Scope Process -Force
    [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
    iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))
    
    # Reload PATH
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
}

# Install PostgreSQL
Write-Host "Installing PostgreSQL..." -ForegroundColor Yellow
choco install postgresql --params '/Password:postgres' --version=16.2 -y

Write-Host "Installation initiated. PostgreSQL will be installed with:" -ForegroundColor Green
Write-Host "Username: postgres" -ForegroundColor Green
Write-Host "Password: postgres" -ForegroundColor Green
Write-Host "Port: 5432" -ForegroundColor Green
