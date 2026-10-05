# Start DEKOPEN local stack services
$ErrorActionPreference = "Stop"
$root = if ($PSScriptRoot) { (Resolve-Path (Join-Path $PSScriptRoot "..")).Path } else { (Get-Location).Path }
$logDir = Join-Path $root ".run"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null

# Load .env into process env
Get-Content (Join-Path $root ".env") | ForEach-Object {
  if ($_ -match '^\s*([A-Z0-9_]+)=(.*)$') {
    $value = $matches[2].Trim()
    if (($value.StartsWith('"') -and $value.EndsWith('"')) -or
        ($value.StartsWith("'") -and $value.EndsWith("'"))) {
      $value = $value.Substring(1, $value.Length - 2)
    }
    Set-Item -Path "Env:$($matches[1])" -Value $value
  }
}

Write-Host "Local environment loaded (values withheld)"
$env:PYTHONUTF8 = "1"
if (-not $env:WEASYPRINT_DLL_DIRECTORIES -and (Test-Path "C:/msys64/ucrt64/bin")) {
  $env:WEASYPRINT_DLL_DIRECTORIES = "C:/msys64/ucrt64/bin"
}
if (-not $env:VITE_SUPABASE_URL) { $env:VITE_SUPABASE_URL = $env:SUPABASE_URL }
if (-not $env:VITE_SUPABASE_ANON_KEY) { $env:VITE_SUPABASE_ANON_KEY = $env:SUPABASE_ANON_KEY }
$listeners = Get-NetTCPConnection -LocalPort 8000,5173 -State Listen -ErrorAction SilentlyContinue
if ($listeners) { throw "Ports 8000/5173 must be free; stop the existing stack first." }

# Storage bucket
docker exec supabase_db_dekopen psql -U postgres -d postgres -c "INSERT INTO storage.buckets (id, name, public) VALUES ('documents','documents', false) ON CONFLICT (id) DO NOTHING;"
if ($LASTEXITCODE -ne 0) { throw "Local Supabase must be running before starting the app." }

$py = Join-Path $root ".venv\Scripts\python.exe"
$node = (Get-Command node.exe).Source
$startedProcesses = [System.Collections.Generic.List[System.Diagnostics.Process]]::new()
$pidFileWritten = $false

try {
# Django
$djangoProcess = Start-Process -FilePath $py `
  -ArgumentList @("backend\manage.py","runserver","127.0.0.1:8000","--noreload") `
  -WorkingDirectory $root `
  -RedirectStandardOutput "$logDir\django.out.log" `
  -RedirectStandardError "$logDir\django.err.log" `
  -WindowStyle Hidden -PassThru
$startedProcesses.Add($djangoProcess)
Write-Host "Django launched"

# Jobs worker
$jobsProcess = Start-Process -FilePath $py `
  -ArgumentList @("backend\manage.py","runjobs","--poll","1.5") `
  -WorkingDirectory $root `
  -RedirectStandardOutput "$logDir\jobs.out.log" `
  -RedirectStandardError "$logDir\jobs.err.log" `
  -WindowStyle Hidden -PassThru
$startedProcesses.Add($jobsProcess)
Write-Host "Jobs worker launched"

# Vite
$viteProcess = Start-Process -FilePath $node `
  -ArgumentList @("node_modules/vite/bin/vite.js","--host","127.0.0.1","--strictPort") `
  -WorkingDirectory (Join-Path $root "frontend") `
  -RedirectStandardOutput "$logDir\vite.out.log" `
  -RedirectStandardError "$logDir\vite.err.log" `
  -WindowStyle Hidden -PassThru
$startedProcesses.Add($viteProcess)
Write-Host "Vite launched"

Start-Sleep -Seconds 6
if ($djangoProcess.HasExited -or $jobsProcess.HasExited -or $viteProcess.HasExited) {
  throw "A local service exited; inspect the .run logs."
}
@{ django = $djangoProcess.Id; jobs = $jobsProcess.Id; vite = $viteProcess.Id } |
  ConvertTo-Json | Set-Content -LiteralPath "$logDir\stack-pids.json"
$pidFileWritten = $true
Write-Host "Local services running; process IDs in .run/stack-pids.json"
} catch {
  foreach ($startedProcess in $startedProcesses) {
    if (-not $startedProcess.HasExited) {
      Stop-Process -Id $startedProcess.Id -ErrorAction SilentlyContinue
    }
  }
  if ($pidFileWritten) { Remove-Item -LiteralPath "$logDir\stack-pids.json" }
  throw
}
