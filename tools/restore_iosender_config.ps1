[CmdletBinding()]
param(
    [string]$Backup = "",
    [string]$Target = "",
    [switch]$Launch
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Find-InstallConfig {
    if ($Target) {
        return [IO.Path]::GetFullPath($Target)
    }

    $running = Get-Process -Name "ioSender" -ErrorAction SilentlyContinue |
        Where-Object { $_.Path } |
        Select-Object -First 1
    if ($running) {
        return (Join-Path (Split-Path -Parent $running.Path) "App.config")
    }

    $desktop = [Environment]::GetFolderPath("Desktop")
    $candidate = Get-ChildItem -LiteralPath $desktop -Directory -Filter "ioSender*" |
        Where-Object { Test-Path -LiteralPath (Join-Path $_.FullName "ioSender.exe") } |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 1
    if ($candidate) {
        return (Join-Path $candidate.FullName "App.config")
    }
    throw "Could not find an ioSender install. Pass -Target explicitly."
}

function Find-LatestBackup {
    $roots = @()
    $oneDrive = [Environment]::GetEnvironmentVariable("OneDrive")
    if (-not $oneDrive) {
        $candidate = Join-Path ([Environment]::GetFolderPath("UserProfile")) "OneDrive"
        if (Test-Path -LiteralPath $candidate -PathType Container) {
            $oneDrive = $candidate
        }
    }
    if ($oneDrive) {
        $roots += Join-Path $oneDrive "ioSender Backups"
    }
    $roots += Join-Path ([Environment]::GetFolderPath("LocalApplicationData")) "Theta\ioSender-Backups"

    $candidate = foreach ($root in $roots) {
        if (Test-Path -LiteralPath $root -PathType Container) {
            Get-ChildItem -LiteralPath $root -File -Filter "ioSender-App.config.*" |
                Where-Object {
                    $_.Name -match "^ioSender-App\.config\.\d{8}-\d{9}$"
                }
        }
    }
    $latest = $candidate | Sort-Object Name -Descending | Select-Object -First 1
    if (-not $latest) {
        $latest = foreach ($root in $roots) {
            $stable = Join-Path $root "ioSender-App.config.latest"
            if (Test-Path -LiteralPath $stable -PathType Leaf) {
                Get-Item -LiteralPath $stable
            }
        }
        $latest = $latest | Select-Object -First 1
    }
    if (-not $latest) {
        throw "No ioSender backup was found. Pass -Backup explicitly."
    }
    return $latest.FullName
}

function Read-ValidatedConfig {
    param([string]$Path)

    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        throw "Config file does not exist: $Path"
    }
    if ((Get-Item -LiteralPath $Path).Length -eq 0) {
        throw "Config file is empty: $Path"
    }
    try {
        [xml]$document = Get-Content -Raw -LiteralPath $Path
    }
    catch {
        throw "Config file is not valid XML: $Path"
    }
    if ($document.DocumentElement.LocalName -ne "Config") {
        throw "Config file root element is not <Config>: $Path"
    }
}

function Get-Sha256 {
    param([string]$Path)

    $stream = [IO.File]::OpenRead($Path)
    try {
        $sha = [Security.Cryptography.SHA256]::Create()
        try {
            return ([BitConverter]::ToString($sha.ComputeHash($stream))).Replace("-", "")
        }
        finally {
            $sha.Dispose()
        }
    }
    finally {
        $stream.Dispose()
    }
}

try {
    $targetPath = Find-InstallConfig
    $targetDirectory = Split-Path -Parent $targetPath
    $runningInTarget = Get-Process -Name "ioSender" -ErrorAction SilentlyContinue |
        Where-Object {
            $_.Path -and
            ([IO.Path]::GetFullPath((Split-Path -Parent $_.Path)) -eq [IO.Path]::GetFullPath($targetDirectory))
        }
    if ($runningInTarget) {
        throw "Close ioSender before restoring this installation's App.config."
    }
    if (-not $Backup) {
        $Backup = Find-LatestBackup
    }
    $backupPath = (Resolve-Path -LiteralPath $Backup).Path
    Read-ValidatedConfig -Path $backupPath

    if (-not (Test-Path -LiteralPath $targetDirectory -PathType Container)) {
        throw "Target directory does not exist: $targetDirectory"
    }
    $preserved = $null
    if (Test-Path -LiteralPath $targetPath -PathType Leaf) {
        $preserved = "$targetPath.before-restore-" + (Get-Date -Format "yyyyMMdd-HHmmssfff")
        Copy-Item -LiteralPath $targetPath -Destination $preserved
    }
    Copy-Item -LiteralPath $backupPath -Destination $targetPath -Force

    $backupHash = Get-Sha256 -Path $backupPath
    $restoredHash = Get-Sha256 -Path $targetPath
    if ($backupHash -ne $restoredHash) {
        throw "Restored file hash does not match the backup."
    }

    Write-Output "Restored $backupPath to $targetPath"
    if ($preserved) {
        Write-Output "Previous target preserved at $preserved"
    }
    if ($Launch) {
        Start-Process -FilePath (Join-Path $targetDirectory "ioSender.exe") -WorkingDirectory $targetDirectory
    }
}
catch {
    Write-Error $_
    exit 1
}
