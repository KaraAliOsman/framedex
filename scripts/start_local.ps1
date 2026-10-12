# Isolated DEKOPEN review stack; see docs/GUIA-REVISION.md.
$ErrorActionPreference = "Stop"
$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$python = Join-Path $root ".venv/Scripts/python.exe"
if (-not (Test-Path -LiteralPath $python)) { $python = (Get-Command python).Source }
& $python (Join-Path $PSScriptRoot "review_stack.py") start
if ($LASTEXITCODE -ne 0) { throw "Revisa los requisitos de docs/GUIA-REVISION.md." }
