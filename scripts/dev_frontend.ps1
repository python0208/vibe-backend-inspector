$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$FrontendRoot = Resolve-Path (Join-Path $ScriptRoot "..\frontend")
Set-Location $FrontendRoot
npm run dev
