# GNSS Data Processing Application Installation Script
# Platform: Windows

Write-Host "Installing GNSS Data Processing Application..." -ForegroundColor Green

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
    refreshenv
}

# Install PostgreSQL with PostGIS
Write-Host "Installing PostgreSQL and PostGIS..." -ForegroundColor Yellow
choco install postgresql16 --params '/Password:postgres' -y
choco install postgis --params '/Version:16' -y
refreshenv

# Add PostgreSQL tools to PATH
$pgPath = "C:\Program Files\PostgreSQL\16\bin"
if ($env:Path -notlike "*$pgPath*") {
    [Environment]::SetEnvironmentVariable("Path", $env:Path + ";$pgPath", [System.EnvironmentVariableTarget]::Machine)
    $env:Path = $env:Path + ";$pgPath"
}

# Install MongoDB
Write-Host "Installing MongoDB..." -ForegroundColor Yellow
choco install mongodb -y
refreshenv

# Create Python virtual environment and install dependencies
Write-Host "Setting up Python environment..." -ForegroundColor Yellow
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r ..\requirements.txt

# Initialize databases
Write-Host "Initializing databases..." -ForegroundColor Yellow
$env:PGPASSWORD = "postgres"
psql -U postgres -c "CREATE DATABASE gnss_data;"
psql -U postgres -d gnss_data -c "CREATE EXTENSION postgis;"

Write-Host "Installation completed!" -ForegroundColor Green
Write-Host @"
Configuration:
- PostgreSQL:
  - Database: gnss_data
  - Username: postgres
  - Password: postgres
  - Port: 5432
- MongoDB:
  - URL: mongodb://localhost:27017/
  - Database: gnss_raw_data
"@ -ForegroundColor Cyan
