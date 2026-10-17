# Session-local runtime and large outputs. No global user settings are changed.
param([string]$DataHome)
$repo = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
if (-not $DataHome) {
    $container = Split-Path $repo -Parent
    if ((Split-Path $container -Leaf) -eq 'academic-homepage') { $container = Split-Path $container -Parent }
    $DataHome = if ($env:WIRELESS_REPRO_DATA_HOME) { $env:WIRELESS_REPRO_DATA_HOME } else { Join-Path $container 'paper-reproduction-data' }
}
$DataHome = [IO.Path]::GetFullPath($DataHome)
$cacheRoot = Join-Path $DataHome 'runtime'
foreach ($relative in @('temp', 'matplotlib', 'cache', 'matlab-prefs')) {
    New-Item -ItemType Directory -Path (Join-Path $cacheRoot $relative) -Force | Out-Null
}
$env:WIRELESS_REPRO_DATA_HOME = $DataHome
$env:TEMP = Join-Path $cacheRoot 'temp'
$env:TMP = $env:TEMP
$env:MPLCONFIGDIR = Join-Path $cacheRoot 'matplotlib'
$env:XDG_CACHE_HOME = Join-Path $cacheRoot 'cache'
$env:MATLAB_PREFDIR = Join-Path $cacheRoot 'matlab-prefs'
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:PYTHONUTF8 = '1'
$env:OPENBLAS_NUM_THREADS = '1'
$env:OMP_NUM_THREADS = '1'
$env:MKL_NUM_THREADS = '1'
$cvxRoot = Join-Path (Split-Path $repo -Parent) 'work\external-cvx-2.2.2\cvx'
if (Test-Path -LiteralPath (Join-Path $cvxRoot 'cvx_startup.m')) { $env:WIRELESS_REPRO_CVX_ROOT = $cvxRoot }
Write-Output "Runtime ready; data and caches: $DataHome"
