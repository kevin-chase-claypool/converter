param(
    [string]$BaseUrl = "https://cad.onshape.com"
)

$ErrorActionPreference = "Stop"

function ConvertFrom-SecureStringPlainText {
    param([securestring]$SecureValue)

    $bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($SecureValue)
    try {
        [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr)
    }
    finally {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
    }
}

$accessKey = Read-Host "Onshape access key"
$secretSecure = Read-Host "Onshape secret key" -AsSecureString
$secretKey = ConvertFrom-SecureStringPlainText $secretSecure

setx ONSHAPE_ACCESS_KEY $accessKey | Out-Null
setx ONSHAPE_SECRET_KEY $secretKey | Out-Null
setx ONSHAPE_BASE_URL $BaseUrl | Out-Null

$env:ONSHAPE_ACCESS_KEY = $accessKey
$env:ONSHAPE_SECRET_KEY = $secretKey
$env:ONSHAPE_BASE_URL = $BaseUrl

Write-Host "Onshape API environment variables were saved for future terminals."
Write-Host "They are also available in this PowerShell process."
Write-Host ""
Write-Host "Test with:"
Write-Host "  python tools\onshape\onshape_client.py list-documents --limit 5"
