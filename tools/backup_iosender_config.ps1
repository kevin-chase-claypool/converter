[CmdletBinding()]
param(
    [string]$Source = "",
    [string[]]$BackupDirs = @()
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Find-IoSenderConfig {
    if ($Source) {
        return (Resolve-Path -LiteralPath $Source).Path
    }

    $running = Get-CimInstance Win32_Process -Filter "Name = 'ioSender.exe'" |
        Where-Object { $_.ExecutablePath } |
        Select-Object -First 1
    if ($running) {
        $candidate = Join-Path (Split-Path -Parent $running.ExecutablePath) "App.config"
        if (Test-Path -LiteralPath $candidate -PathType Leaf) {
            return (Resolve-Path -LiteralPath $candidate).Path
        }
    }

    $desktop = [Environment]::GetFolderPath("Desktop")
    $candidate = Get-ChildItem -LiteralPath $desktop -Directory -Filter "ioSender*" |
        ForEach-Object { Join-Path $_.FullName "App.config" } |
        Where-Object { (Test-Path -LiteralPath $_ -PathType Leaf) -and (Get-Item -LiteralPath $_).Length -gt 0 } |
        Select-Object -First 1
    if ($candidate) {
        return (Resolve-Path -LiteralPath $candidate).Path
    }

    throw "Could not find ioSender App.config. Pass -Source explicitly."
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
    return $document
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
    $sourcePath = Find-IoSenderConfig
    $document = Read-ValidatedConfig -Path $sourcePath
    $sourceHash = Get-Sha256 -Path $sourcePath
    $macroCount = 0
    if ($null -ne $document.Config.Macros -and $null -ne $document.Config.Macros.Macro) {
        $macroCount = @($document.Config.Macros.Macro).Count
    }

    if (-not $BackupDirs) {
        $oneDrive = [Environment]::GetEnvironmentVariable("OneDrive")
        if (-not $oneDrive) {
            $candidate = Join-Path ([Environment]::GetFolderPath("UserProfile")) "OneDrive"
            if (Test-Path -LiteralPath $candidate -PathType Container) {
                $oneDrive = $candidate
            }
        }
        if ($oneDrive -and (Test-Path -LiteralPath $oneDrive -PathType Container)) {
            $BackupDirs += Join-Path $oneDrive "ioSender Backups"
        }
        $localData = [Environment]::GetFolderPath("LocalApplicationData")
        if ($localData) {
            $BackupDirs += Join-Path $localData "Theta\ioSender-Backups"
        }
    }
    if (-not $BackupDirs) {
        throw "No backup directory is available."
    }

    $stamp = Get-Date -Format "yyyyMMdd-HHmmssfff"
    $capturedAt = (Get-Date).ToString("o")
    foreach ($directory in $BackupDirs) {
        New-Item -ItemType Directory -Path $directory -Force | Out-Null
        $versioned = Join-Path $directory "ioSender-App.config.$stamp"
        $latest = Join-Path $directory "ioSender-App.config.latest"
        Copy-Item -LiteralPath $sourcePath -Destination $versioned
        $copyHash = Get-Sha256 -Path $versioned
        if ($copyHash -ne $sourceHash) {
            throw "Backup copy hash does not match the source: $versioned"
        }
        Copy-Item -LiteralPath $versioned -Destination $latest -Force
        $supportFiles = [ordered]@{}
        $installDirectory = Split-Path -Parent $sourcePath
        foreach ($support in @(
            @{ Source = "settings.txt"; Prefix = "grblhal-settings"; Extension = ".txt" },
            @{ Source = "offsets.nc"; Prefix = "grblhal-offsets"; Extension = ".nc" }
        )) {
            $supportSource = Join-Path $installDirectory $support.Source
            if (
                (Test-Path -LiteralPath $supportSource -PathType Leaf) -and
                (Get-Item -LiteralPath $supportSource).Length -gt 0
            ) {
                $supportVersioned = Join-Path $directory (
                    "$($support.Prefix).$stamp$($support.Extension)"
                )
                $supportLatest = Join-Path $directory (
                    "$($support.Prefix).latest$($support.Extension)"
                )
                Copy-Item -LiteralPath $supportSource -Destination $supportVersioned
                Copy-Item -LiteralPath $supportVersioned -Destination $supportLatest -Force
                $supportFiles[$support.Source] = [ordered]@{
                    sha256 = Get-Sha256 -Path $supportVersioned
                    versioned_backup = $supportVersioned
                }
            }
        }
        [ordered]@{
            source = $sourcePath
            captured_at = $capturedAt
            sha256 = $sourceHash
            macro_count = $macroCount
            versioned_backup = $versioned
            support_files = $supportFiles
        } |
            ConvertTo-Json |
            Set-Content -LiteralPath (Join-Path $directory "ioSender-App.config.latest.json") -Encoding UTF8
        Write-Output "Backed up $macroCount macros to $latest"
    }
}
catch {
    Write-Error $_
    exit 1
}
