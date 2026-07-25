param(
    [switch]$Clean
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

if ($Clean) {
    Remove-Item -Recurse -Force -ErrorAction SilentlyContinue "$Root\build", "$Root\dist"
}

uv sync --dev
uv run pyinstaller --noconfirm "$Root\GetbijiEx.spec"

Write-Host ""
Write-Host "构建完成：$Root\dist\GetbijiEx\GetbijiEx.exe"
