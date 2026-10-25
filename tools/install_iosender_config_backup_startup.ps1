[CmdletBinding()]
param(
    [switch]$Remove,
    [string]$StartupDir = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

try {
    $backupScript = Join-Path $PSScriptRoot "backup_iosender_config.ps1"
    if (-not $Remove -and -not (Test-Path -LiteralPath $backupScript -PathType Leaf)) {
        throw "Backup script is missing: $backupScript"
    }

    $startup = if ($StartupDir) {
        [IO.Path]::GetFullPath($StartupDir)
    }
    else {
        [Environment]::GetFolderPath("Startup")
    }
    if (-not $startup -or -not (Test-Path -LiteralPath $startup -PathType Container)) {
        throw "Could not locate the current user's Startup folder."
    }
    $launcher = Join-Path $startup "ioSender Config Backup.cmd"
    if ($Remove) {
        if (Test-Path -LiteralPath $launcher -PathType Leaf) {
            Remove-Item -LiteralPath $launcher
            Write-Output "Removed startup backup: $launcher"
        }
        else {
            Write-Output "Startup backup is not installed: $launcher"
        }
    }
    else {
        $content = @(
            "@echo off"
            "powershell.exe -NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$backupScript`""
        ) -join "`r`n"
        Set-Content -LiteralPath $launcher -Value ($content + "`r`n") -Encoding ASCII
        Write-Output "Installed startup backup: $launcher"
    }
}
catch {
    Write-Error $_
    exit 1
}
