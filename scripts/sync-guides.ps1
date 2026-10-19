#Requires -Version 5.1
<#
.SYNOPSIS
  Keep AGENTS.md and .claude/CLAUDE.md byte-identical (bidirectional sync).

.DESCRIPTION
  The two project guide files must always be identical. This script compares them:
  - identical : exit 0, no changes
  - different : by default the file with the newer LastWriteTime overwrites the older
                one (use -From to force a direction); mtimes are then aligned so the
                next run does not misjudge the direction.

  Called automatically by the git pre-commit hook; can also be run manually:
    powershell scripts/sync-guides.ps1              # auto sync (newer wins)
    powershell scripts/sync-guides.ps1 -Check       # check only, exit 1 if different
    powershell scripts/sync-guides.ps1 -From claude # force .claude/CLAUDE.md as source
#>
param(
  [switch]$Check,
  [ValidateSet('agents', 'claude')] [string]$From
)

$ErrorActionPreference = 'Stop'
$root   = Split-Path $PSScriptRoot -Parent
$agents = Join-Path $root 'AGENTS.md'
$claude = Join-Path $root '.claude\CLAUDE.md'

foreach ($f in @($agents, $claude)) {
  if (-not (Test-Path $f)) { Write-Error "[sync-guides] file not found: $f"; exit 2 }
}

$ha = (Get-FileHash $agents -Algorithm SHA256).Hash
$hc = (Get-FileHash $claude -Algorithm SHA256).Hash

if ($ha -eq $hc) {
  Write-Host "[sync-guides] OK: AGENTS.md and .claude/CLAUDE.md are identical"
  exit 0
}

if ($Check) {
  Write-Host "[sync-guides] FAIL: guides differ - run scripts/sync-guides.ps1 to sync"
  exit 1
}

if ($From -eq 'agents') {
  $src = $agents; $dst = $claude
} elseif ($From -eq 'claude') {
  $src = $claude; $dst = $agents
} else {
  # default: newer LastWriteTime wins
  if ((Get-Item $agents).LastWriteTime -ge (Get-Item $claude).LastWriteTime) {
    $src = $agents; $dst = $claude
  } else {
    $src = $claude; $dst = $agents
  }
}

Copy-Item $src $dst -Force
# align mtime: after sync both are the same version, avoid direction flip next run
(Get-Item $dst).LastWriteTime = (Get-Item $src).LastWriteTime

$srcName = if ($src -eq $agents) { 'AGENTS.md' } else { '.claude/CLAUDE.md' }
$dstName = if ($dst -eq $agents) { 'AGENTS.md' } else { '.claude/CLAUDE.md' }
Write-Host "[sync-guides] synced: $srcName -> $dstName"
exit 0
