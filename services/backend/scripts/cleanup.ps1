#Requires -Version 7.0

# Cleanup script for removing deprecated files and organizing structure
Write-Host "Starting cleanup process..." -ForegroundColor Blue

# 1. Remove duplicate config file
try {
    $configPath = Join-Path -Path (Get-Location).Path -ChildPath "../src/models/config.py"
    if (Test-Path -Path $configPath) {
        Write-Host "Removing duplicate config.py..." -ForegroundColor Yellow
        Remove-Item -Path $configPath -ErrorAction Stop
        Write-Host "✓ Removed duplicate config.py" -ForegroundColor Green
    }
} catch {
    Write-Host "✗ Failed to remove config.py: $_" -ForegroundColor Red
}

# 2. Remove Docker-related files
$dockerFiles = @(
    "../Dockerfile",
    "../../docker-compose.yml"
)

foreach ($file in $dockerFiles) {
    try {
        $filePath = Join-Path -Path (Get-Location).Path -ChildPath $file
        if (Test-Path -Path $filePath) {
            Write-Host "Removing Docker file: $file..." -ForegroundColor Yellow
            Remove-Item -Path $filePath -ErrorAction Stop
            Write-Host "✓ Removed $file" -ForegroundColor Green
        }
    } catch {
        Write-Host "✗ Failed to remove $file : $_" -ForegroundColor Red
    }
}

# 3. Create test directory structure
$testDirs = @(
    "../tests",
    "../tests/unit",
    "../tests/integration",
    "../tests/fixtures"
)

foreach ($dir in $testDirs) {
    try {
        $dirPath = Join-Path -Path (Get-Location).Path -ChildPath $dir
        if (-not (Test-Path -Path $dirPath)) {
            Write-Host "Creating directory: $dir..." -ForegroundColor Yellow
            New-Item -ItemType Directory -Path $dirPath -ErrorAction Stop | Out-Null
            Write-Host "✓ Created $dir" -ForegroundColor Green
        }
    } catch {
        Write-Host "✗ Failed to create $dir : $_" -ForegroundColor Red
    }
}

# Create test files
$testFiles = @{
    "../tests/conftest.py" = @'
import pytest
from fastapi.testclient import TestClient
from src.main import app

@pytest.fixture
def client():
    return TestClient(app)
'@

    "../tests/unit/test_deep_lynx.py" = @'
import pytest
from src.core.deep_lynx import DeepLynxClient

def test_deep_lynx_client_initialization():
    client = DeepLynxClient()
    assert client is not None
    assert client.settings is not None
'@

    "../tests/integration/test_files.py" = @'
import pytest
from fastapi.testclient import TestClient

def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}
'@

    "../tests/fixtures/test_data.py" = @'
# Test data fixtures
MOCK_CONTAINER_RESPONSE = {
    "is_error": False,
    "value": {
        "id": "1",
        "name": "Test Container",
        "description": "Test container for unit tests"
    }
}
'@
}

foreach ($file in $testFiles.Keys) {
    try {
        $filePath = Join-Path -Path (Get-Location).Path -ChildPath $file
        if (-not (Test-Path -Path $filePath)) {
            Write-Host "Creating test file: $file..." -ForegroundColor Yellow
            Set-Content -Path $filePath -Value $testFiles[$file] -ErrorAction Stop
            Write-Host "✓ Created $file" -ForegroundColor Green
        }
    } catch {
        Write-Host "✗ Failed to create $file : $_" -ForegroundColor Red
    }
}

# Create requirements-test.txt
$testRequirements = @'
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0
httpx==0.25.1
pytest-mock==3.12.0
'@

try {
    $reqPath = Join-Path -Path (Get-Location).Path -ChildPath "../requirements-test.txt"
    if (-not (Test-Path -Path $reqPath)) {
        Write-Host "Creating requirements-test.txt..." -ForegroundColor Yellow
        Set-Content -Path $reqPath -Value $testRequirements -ErrorAction Stop
        Write-Host "✓ Created requirements-test.txt" -ForegroundColor Green
    }
} catch {
    Write-Host "✗ Failed to create requirements-test.txt : $_" -ForegroundColor Red
}

# Create __init__.py files
$initDirs = @(
    "../src",
    "../src/core",
    "../src/models",
    "../src/routers",
    "../tests",
    "../tests/unit",
    "../tests/integration",
    "../tests/fixtures"
)

foreach ($dir in $initDirs) {
    try {
        $initPath = Join-Path -Path (Get-Location).Path -ChildPath "$dir/__init__.py"
        if (-not (Test-Path -Path $initPath)) {
            Write-Host "Creating __init__.py in: $dir..." -ForegroundColor Yellow
            New-Item -ItemType File -Path $initPath -Force -ErrorAction Stop | Out-Null
            Write-Host "✓ Created __init__.py in $dir" -ForegroundColor Green
        }
    } catch {
        Write-Host "✗ Failed to create __init__.py in $dir : $_" -ForegroundColor Red
    }
}

# Create pytest.ini
$pytestIniContent = @'
[pytest]
pythonpath = .
testpaths = tests
python_files = test_*.py
addopts = -v --tb=short
'@

try {
    $pytestIniPath = Join-Path -Path (Get-Location).Path -ChildPath "../pytest.ini"
    if (-not (Test-Path -Path $pytestIniPath)) {
        Write-Host "Creating pytest.ini..." -ForegroundColor Yellow
        Set-Content -Path $pytestIniPath -Value $pytestIniContent -ErrorAction Stop
        Write-Host "✓ Created pytest.ini" -ForegroundColor Green
    }
} catch {
    Write-Host "✗ Failed to create pytest.ini : $_" -ForegroundColor Red
}

Write-Host "`nCleanup process complete!" -ForegroundColor Green
Write-Host "`nNext steps:" -ForegroundColor Blue
Write-Host "1. Install test dependencies: pip install -r requirements-test.txt" -ForegroundColor White
Write-Host "2. Run tests: pytest tests/" -ForegroundColor White
Write-Host "3. Check test coverage: pytest --cov=src tests/" -ForegroundColor White