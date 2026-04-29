$ErrorActionPreference = "Stop"

$ProjectRoot = "E:\Researching\My-literature-digest"
$LogDir = Join-Path $ProjectRoot "logs"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

$Timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$LogFile = Join-Path $LogDir "digest-$Timestamp.log"

Set-Location $ProjectRoot
python -m literature_digest 2>&1 | Tee-Object -FilePath $LogFile

Write-Host ""
Write-Host "日志已保存到: $LogFile"
Write-Host "输出目录: $ProjectRoot\outputs"
Read-Host "按 Enter 关闭窗口"

