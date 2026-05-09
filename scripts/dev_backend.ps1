$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$BackendRoot = Resolve-Path (Join-Path $ScriptRoot "..\backend")
Set-Location $BackendRoot
python -m uvicorn app.main:app --reload
