# Set UTF-8 encoding
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "=== Git Status ==="
git status 2>&1

Write-Host ""
Write-Host "=== Git Diff --stat ==="
git diff --stat 2>&1

Write-Host ""
Write-Host "=== Check .git exists ==="
if (Test-Path ".git") {
    Write-Host ".git directory exists"
} else {
    Write-Host "No .git directory found"
}

Write-Host ""
Write-Host "=== Git Remote ==="
git remote -v 2>&1

Write-Host ""
Write-Host "=== Check .gitignore ==="
if (Test-Path ".gitignore") {
    Get-Content ".gitignore" | Select-Object -First 50
} else {
    Write-Host "No .gitignore found"
}