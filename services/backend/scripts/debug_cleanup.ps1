#Requires -Version 7.0

# Debug script to test file operations and content creation
Write-Host "Starting debug process..." -ForegroundColor Blue
Write-Host "PowerShell Version: $($PSVersionTable.PSVersion)" -ForegroundColor Yellow

# 1. Test directory access
Write-Host "`nTesting directory access:" -ForegroundColor Yellow
$testPaths = @(
    ".",
    "..",
    "../src",
    "../src/models",
    "../tests"
)

foreach ($path in $testPaths) {
    try {
        $fullPath = Join-Path (Get-Location).Path $path
        Write-Host "Testing path: $fullPath" -ForegroundColor Yellow
        if (Test-Path -Path $fullPath) {
            Write-Host "✓ Can access: $fullPath" -ForegroundColor Green
        } else {
            Write-Host "✗ Cannot access: $fullPath" -ForegroundColor Red
        }
    } catch {
        Write-Host "✗ Error testing path $path : $_" -ForegroundColor Red
    }
}

# 2. Test file content creation
Write-Host "`nTesting file content creation:" -ForegroundColor Yellow

# Test simple content first
$testContent = @'
# Test content
print("Hello world")
'@

$testFile = Join-Path -Path (Get-Location).Path -ChildPath "../tests/debug_test.py"
try {
    Write-Host "Attempting to create file: $testFile" -ForegroundColor Yellow
    Set-Content -Path $testFile -Value $testContent -ErrorAction Stop
    Write-Host "✓ Successfully created test file" -ForegroundColor Green
    Write-Host "Content:"
    Get-Content -Path $testFile | ForEach-Object { Write-Host "  $_" }
} catch {
    Write-Host "✗ Failed to create test file: $_" -ForegroundColor Red
}

# 3. Test here-string handling
Write-Host "`nTesting here-string handling:" -ForegroundColor Yellow

$testHereString = @'
import pytest
from fastapi.testclient import TestClient

def test_example():
    assert True
'@

$testHereFile = Join-Path -Path (Get-Location).Path -ChildPath "../tests/debug_here_string.py"
try {
    Write-Host "Attempting to create here-string file: $testHereFile" -ForegroundColor Yellow
    Set-Content -Path $testHereFile -Value $testHereString -ErrorAction Stop
    Write-Host "✓ Successfully created here-string test file" -ForegroundColor Green
    Write-Host "Content:"
    Get-Content -Path $testHereFile | ForEach-Object { Write-Host "  $_" }
} catch {
    Write-Host "✗ Failed to create here-string test file: $_" -ForegroundColor Red
}

# 4. Test dictionary creation
Write-Host "`nTesting dictionary handling:" -ForegroundColor Yellow

$testDict = @{
    "test_file.py" = 'print("test")'
}

try {
    foreach ($key in $testDict.Keys) {
        Write-Host "Attempting to create dictionary file: $key" -ForegroundColor Yellow
        $testDictFile = Join-Path -Path (Get-Location).Path -ChildPath "../tests/$key"
        Set-Content -Path $testDictFile -Value $testDict[$key] -ErrorAction Stop
        Write-Host "✓ Successfully created dictionary test file: $key" -ForegroundColor Green
    }
} catch {
    Write-Host "✗ Failed to create dictionary test file: $_" -ForegroundColor Red
}

# 5. Test PowerShell version and execution policy
Write-Host "`nSystem Information:" -ForegroundColor Yellow
Write-Host "PowerShell Version: $($PSVersionTable.PSVersion)"
Write-Host "Execution Policy: $(Get-ExecutionPolicy)"
Write-Host "Current Directory: $(Get-Location)"
Write-Host "Parent Directory: $(Split-Path -Path (Get-Location) -Parent)"

# 6. Test directory creation
Write-Host "`nTesting directory creation:" -ForegroundColor Yellow
$testDir = Join-Path -Path (Get-Location).Path -ChildPath "../tests/test_dir"

try {
    Write-Host "Attempting to create directory: $testDir" -ForegroundColor Yellow
    New-Item -Path $testDir -ItemType Directory -Force -ErrorAction Stop | Out-Null
    Write-Host "✓ Successfully created test directory" -ForegroundColor Green
    
    Write-Host "Attempting to remove directory: $testDir" -ForegroundColor Yellow
    Remove-Item -Path $testDir -Force -ErrorAction Stop
    Write-Host "✓ Successfully removed test directory" -ForegroundColor Green
} catch {
    Write-Host "✗ Failed directory operations: $_" -ForegroundColor Red
}

Write-Host "`nDebug process complete!" -ForegroundColor Blue