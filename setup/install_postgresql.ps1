# PostgreSQL installation script
Write-Host "Installing PostgreSQL and PostGIS..." -ForegroundColor Green

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

# Install PostgreSQL
Write-Host "Installing PostgreSQL..." -ForegroundColor Yellow
choco install postgresql16 --params '/Password:postgres' -y
refreshenv

# Add PostgreSQL tools to PATH if not already there
$pgPath = "C:\Program Files\PostgreSQL\16\bin"
if ($env:Path -notlike "*$pgPath*") {
    [Environment]::SetEnvironmentVariable("Path", $env:Path + ";$pgPath", [System.EnvironmentVariableTarget]::Machine)
    $env:Path = $env:Path + ";$pgPath"
}

# Wait for PostgreSQL service to start
Write-Host "Waiting for PostgreSQL service to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Create the GNSS database
Write-Host "Creating GNSS database..." -ForegroundColor Yellow
$env:PGPASSWORD = "postgres"
psql -U postgres -c "CREATE DATABASE gnss_data;"

# Install PostGIS extension
Write-Host "Installing PostGIS..." -ForegroundColor Yellow
choco install postgis --params '/Version:16' -y
refreshenv

# Enable PostGIS extension
Write-Host "Enabling PostGIS extension..." -ForegroundColor Yellow
psql -U postgres -d gnss_data -c "CREATE EXTENSION IF NOT EXISTS postgis;"

Write-Host "Installation completed successfully!" -ForegroundColor Green
Write-Host "PostgreSQL is now running on port 5432" -ForegroundColor Green
Write-Host "Database: gnss_data" -ForegroundColor Green
Write-Host "Username: postgres" -ForegroundColor Green
Write-Host "Password: postgres" -ForegroundColor Green

# Update the .env file with database credentials
$envContent = @"
FLASK_APP=app
FLASK_ENV=development
DATABASE_URL=postgresql://postgres:postgres@localhost/gnss_data
MONGO_URI=mongodb://localhost:27017/
SECRET_KEY=dev-secret-key
"@

Set-Content -Path "..\app\.env" -Value $envContent

Write-Host "Environment configuration updated." -ForegroundColor Green
