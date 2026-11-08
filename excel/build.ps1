$ErrorActionPreference = 'Stop'

# Configuration
$ProjectRoot = Split-Path $PSScriptRoot -Parent
$RuntimeRoot = 'C:\Users\yazad\.cache\codex-runtimes\codex-primary-runtime\dependencies'
$NodeExecutable = Join-Path $RuntimeRoot 'node\bin\node.exe'
$PythonExecutable = Join-Path $RuntimeRoot 'python\python.exe'
$TaskWork = Join-Path $ProjectRoot '.work'
$DependencyTarget = Join-Path $RuntimeRoot 'node\node_modules'

New-Item -ItemType Directory -Path $TaskWork -Force | Out-Null
if (-not (Test-Path (Join-Path $TaskWork 'node_modules'))) {
    New-Item -ItemType Junction -Path (Join-Path $TaskWork 'node_modules') -Target $DependencyTarget | Out-Null
}
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'build.mjs') -Destination (Join-Path $TaskWork 'build.mjs')
Push-Location $ProjectRoot
try {
    & $NodeExecutable (Join-Path $TaskWork 'build.mjs')
    if ($LASTEXITCODE -ne 0) { throw 'Workbook build failed' }
    & $PythonExecutable (Join-Path $ProjectRoot 'scripts\verify_workbook.py')
    if ($LASTEXITCODE -ne 0) { throw 'Workbook verification failed' }
} finally {
    Pop-Location
}
