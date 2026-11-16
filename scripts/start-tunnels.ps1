<#
  ForKhatri: start every server and public tunnel with one command.

  Run from anywhere:
      powershell -ExecutionPolicy Bypass -File C:\Users\krish\Krishna2025\startup2026\ForKhatri\scripts\start-tunnels.ps1

  Other options:
      ...start-tunnels.ps1 -Stop      stop the tunnels and servers, and put the env files back to localhost
      ...start-tunnels.ps1 -Status    show what is running, and the public links
      ...start-tunnels.ps1 -Foreground   run in this window (Ctrl+C stops everything cleanly)

  What it does:
    1. Stops anything already listening on ForKhatri's ports and any old tunnel launcher,
       because scripts/tunnel.mjs needs every port free to start every server fresh.
    2. Deletes each web app's .next build cache (this cures the "next/font/google" build error).
    3. Starts scripts/tunnel.mjs (cloudflared quick tunnels + every server), hidden, in the background.
    4. Waits, then prints the public links and checks each one answers.

  The links change on every run (Cloudflare quick tunnels). The latest are always in
  scripts\.tunnel.log and shown by -Status.
#>
param(
  [switch]$Stop,
  [switch]$Status,
  [switch]$Foreground
)

$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $PSScriptRoot
$Log  = Join-Path $PSScriptRoot '.tunnel.log'
$Ports = 8100,3100,8000,3000,8001,3001,8011,3011,8014,3014,8013
$WebDirs = @(
  'platform\forkhatri-web',
  'modules\MOD01-vyapar\vyapar-web',
  'modules\MOD02-milavn\milavn-web',
  'modules\MOD03-mangalya\mangaly-web',
  'modules\MOD04-counsel\counsel-web'
)

# cloudflared is installed here on this machine; add it to PATH if it is not already found.
$cf = Join-Path ${env:ProgramFiles(x86)} 'cloudflared'
if (-not (Get-Command cloudflared -ErrorAction SilentlyContinue) -and (Test-Path $cf)) { $env:Path += ";$cf" }
if (-not (Get-Command cloudflared -ErrorAction SilentlyContinue)) { throw 'cloudflared not found. Install it (winget install Cloudflare.cloudflared) and try again.' }
if (-not (Get-Command node -ErrorAction SilentlyContinue)) { throw 'node not found on PATH.' }

function Get-Launcher {
  Get-CimInstance Win32_Process -Filter "Name='node.exe'" | Where-Object { $_.CommandLine -like '*scripts*tunnel.mjs*' }
}

function Stop-Everything {
  # Ask the launcher to stop with its own revert logic first (it reverts the env files on exit).
  foreach ($l in Get-Launcher) { try { Stop-Process -Id $l.ProcessId -Force } catch {} }
  $ids = Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue |
    Where-Object { $Ports -contains $_.LocalPort } | Select-Object -ExpandProperty OwningProcess -Unique
  foreach ($id in $ids) { & taskkill /pid $id /t /f 2>$null | Out-Null }
  foreach ($c in Get-Process cloudflared -ErrorAction SilentlyContinue) { try { Stop-Process -Id $c.Id -Force -ErrorAction Stop } catch {} }
  Start-Sleep -Seconds 2
}

function Show-Links {
  if (-not (Test-Path $Log)) { Write-Host 'No log yet.'; return }
  $text = (Get-Content $Log -Raw) -replace ([char]27 + '\[[0-9;]*m'), ''
  $lines = $text -split "`r?`n" | Where-Object { $_ -match 'trycloudflare\.com' -and $_ -match '(ForKhatri|MOD0)' }
  if ($lines) { Write-Host "`nOpen these (each is a different public link):" -ForegroundColor Cyan; $lines | ForEach-Object { Write-Host "  $_" } }
}

if ($Status) {
  $up = Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue | Where-Object { $Ports -contains $_.LocalPort } | Select-Object -ExpandProperty LocalPort | Sort-Object
  Write-Host ("Listening ports : " + ($up -join ', '))
  Write-Host ("Launcher running: " + [bool](Get-Launcher))
  Show-Links
  return
}

if ($Stop) {
  Write-Host 'Stopping tunnels and servers...'
  Stop-Everything
  Write-Host 'Stopped. The launcher reverts env files to localhost when it exits cleanly; if you stopped it by force, run:  npm run dev  once to confirm localhost works.'
  return
}

Write-Host 'Stopping anything already running...'
Stop-Everything

Write-Host 'Clearing web build caches...'
foreach ($d in $WebDirs) { Remove-Item -Recurse -Force (Join-Path $Root "$d\.next") -ErrorAction SilentlyContinue }

if ($Foreground) {
  Set-Location $Root
  & node scripts/tunnel.mjs
  return
}

Remove-Item $Log, "$Log.err" -ErrorAction SilentlyContinue
$p = Start-Process -FilePath node -ArgumentList 'scripts/tunnel.mjs' -WorkingDirectory $Root `
       -RedirectStandardOutput $Log -RedirectStandardError "$Log.err" -WindowStyle Hidden -PassThru
Write-Host "Launcher started (pid $($p.Id)). Waiting for the tunnels..."

$deadline = (Get-Date).AddSeconds(150)
$ready = $false
while ((Get-Date) -lt $deadline) {
  Start-Sleep -Seconds 3
  if (Test-Path $Log) {
    $t = Get-Content $Log -Raw -ErrorAction SilentlyContinue
    if ($t -match 'Ctrl\+C stops') { $ready = $true; break }
    if ($t -match 'blocked|missing') { break }
  }
}
if (-not $ready) { Write-Host 'The launcher did not finish starting. Last lines:' -ForegroundColor Yellow; Get-Content $Log -Tail 15; return }

Show-Links

Write-Host "`nChecking each link (the first load of a page can take a minute while it builds)..."
$text = (Get-Content $Log -Raw) -replace ([char]27 + '\[[0-9;]*m'), ''
$urls = [regex]::Matches($text, 'https://[a-z0-9-]+\.trycloudflare\.com') | ForEach-Object { $_.Value } | Select-Object -Unique
$webLinks = ($text -split "`r?`n" | Where-Object { $_ -match '^\S*https://.*(ForKhatri|MOD0)' }) | ForEach-Object { [regex]::Match($_, 'https://[a-z0-9-]+\.trycloudflare\.com').Value }
foreach ($u in $webLinks) {
  try { $r = Invoke-WebRequest -Uri $u -UseBasicParsing -TimeoutSec 120; $code = $r.StatusCode } catch { $code = $_.Exception.Response.StatusCode.value__ }
  Write-Host ("  {0}  {1}" -f $code, $u)
}
Write-Host "`nDone. Stop everything later with:  scripts\start-tunnels.ps1 -Stop" -ForegroundColor Green
