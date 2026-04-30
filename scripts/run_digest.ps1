$ErrorActionPreference = "Stop"

# Use UTF-8 and keep fixed console messages in English for better Windows compatibility.
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::InputEncoding  = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONUTF8 = "1"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
$LogDir = Join-Path $ProjectRoot "logs"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

$Timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$LogFile = Join-Path $LogDir "digest-$Timestamp.log"

Set-Location $ProjectRoot
python -m literature_digest 2>&1 | Tee-Object -FilePath $LogFile

[Console]::WriteLine("")
[Console]::WriteLine("Log saved to: $LogFile")
[Console]::WriteLine("Output directory: $ProjectRoot\outputs")
Read-Host "Press Enter to close this window"
