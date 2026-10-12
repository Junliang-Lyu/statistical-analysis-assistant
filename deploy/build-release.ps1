param([string]$ReleaseId = (Get-Date).ToUniversalTime().ToString("yyyyMMdd'T'HHmmss'Z'"))
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
if ($ReleaseId -notmatch '^\d{8}T\d{6}Z$') { throw 'Invalid release id' }
$out = Join-Path $root "deploy/release/$ReleaseId"
if (Test-Path -LiteralPath $out) { throw 'Release directory already exists' }
$image = "stats-api:$ReleaseId"
& "$root/.venv/Scripts/python.exe" -m pytest -q "--basetemp=$root/.artifact-build/pytest-release-$ReleaseId"
if ($LASTEXITCODE -ne 0) { throw 'Tests failed' }
docker build -f deploy/api.Dockerfile -t $image .
if ($LASTEXITCODE -ne 0) { throw 'Image build failed' }
$smoke = Join-Path $root 'deploy/smoke_public.py'
docker run --rm --entrypoint python --mount "type=bind,source=$smoke,target=/smoke.py,readonly" -e PYTHONPATH=/app $image /smoke.py
if ($LASTEXITCODE -ne 0) { throw 'Image smoke test failed' }
New-Item -ItemType Directory -Path $out | Out-Null
Copy-Item deploy/compose.stats.yaml, deploy/stats.caddy, deploy/check-release.sh $out
Set-Content -LiteralPath (Join-Path $out 'release.txt') -Value "release-$ReleaseId" -Encoding utf8NoBOM
docker save $image -o (Join-Path $out "stats-api-$ReleaseId.tar")
if ($LASTEXITCODE -ne 0) { throw 'Image export failed' }
$archive = Join-Path $root "deploy/release/stats-release-$ReleaseId.tar.gz"
tar -czf $archive -C (Join-Path $root 'deploy/release') $ReleaseId
if ($LASTEXITCODE -ne 0) { throw 'Packaging failed' }
$hash = (Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash.ToLowerInvariant()
Set-Content -LiteralPath "$archive.sha256" -Value "$hash  stats-release-$ReleaseId.tar.gz" -Encoding utf8NoBOM
Write-Host "Verified local release: $archive"
Write-Host 'No server connection or deployment performed.'
