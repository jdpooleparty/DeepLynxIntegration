param(
    [switch]$coverage,
    [switch]$verbose
)

Write-Host "Installing test dependencies..." -ForegroundColor Blue
pip install -r requirements-test.txt

$testCommand = "pytest"
if ($verbose) {
    $testCommand += " -v"
}
if ($coverage) {
    $testCommand += " --cov=src --cov-report=term-missing"
}
$testCommand += " tests/"

Write-Host "Running tests..." -ForegroundColor Blue
Invoke-Expression $testCommand 