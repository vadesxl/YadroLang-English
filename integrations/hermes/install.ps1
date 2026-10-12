# Installs Yadro Guard plugin into Hermes dashboard.
# Run: powershell -ExecutionPolicy Bypass -File integrations\hermes\install.ps1
# What it does: copies the plugin to %LOCALAPPDATA%\hermes\plugins\yadro-guard,
# writes config.json (path to engine and to Python with llvmlite), enables the plugin.
# Does not touch other plugins (home-dashboard etc.).
$ErrorActionPreference = "Stop"
$EngineHome = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$HermesHome = if ($env:HERMES_HOME) { $env:HERMES_HOME } else { Join-Path $env:LOCALAPPDATA "hermes" }
$Target = Join-Path $HermesHome "plugins\yadro-guard"
$Python = (Get-Command python -ErrorAction Stop).Source

& $Python -c "import llvmlite" 2>$null
if ($LASTEXITCODE -ne 0) { throw "$Python has no llvmlite: pip install -r requirements.txt" }

New-Item -ItemType Directory -Force $Target | Out-Null
Copy-Item -Recurse -Force (Join-Path $PSScriptRoot "yadro-guard\*") $Target
$cfg = @{ engine_home = $EngineHome; python = $Python } | ConvertTo-Json
[IO.File]::WriteAllText((Join-Path $Target "config.json"), $cfg, (New-Object Text.UTF8Encoding($false)))

$hermes = Join-Path $HermesHome "bin\hermes.exe"
if (Test-Path $hermes) { & $hermes plugins enable yadro-guard }
Write-Host "Done: $Target"
Write-Host "Restart the Hermes dashboard or click Re-scan on the Plugins page."
