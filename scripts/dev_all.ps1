$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Start-Process powershell -ArgumentList "-NoExit", "-File", "`"$ScriptRoot\dev_backend.ps1`""
Start-Process powershell -ArgumentList "-NoExit", "-File", "`"$ScriptRoot\dev_frontend.ps1`""
