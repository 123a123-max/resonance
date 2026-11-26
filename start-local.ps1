param(
    [ValidateRange(1, 65535)]
    [int]$Port = 8010,
    [switch]$NoBrowser
)

$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot

function Invoke-Checked {
    param([string]$Executable, [string[]]$Arguments)
    & $Executable @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "$Executable exited with code $LASTEXITCODE."
    }
}

function Get-DependencyHash {
    param([string]$Path)
    $algorithm = [Security.Cryptography.SHA256]::Create()
    try {
        $bytes = [IO.File]::ReadAllBytes((Join-Path $PSScriptRoot $Path))
        [BitConverter]::ToString($algorithm.ComputeHash($bytes))
    } finally {
        $algorithm.Dispose()
    }
}

function Get-LanAddress {
    $adapterTypes = @('Wireless80211', 'Ethernet', 'GigabitEthernet', 'FastEthernetT', 'FastEthernetFx')
    $adapters = [Net.NetworkInformation.NetworkInterface]::GetAllNetworkInterfaces() |
        Where-Object {
            $_.OperationalStatus -eq 'Up' -and $_.NetworkInterfaceType.ToString() -in $adapterTypes -and
            $_.Description -notmatch 'Virtual|Hyper-V|VMware|VirtualBox|VPN|Tailscale|TAP|Tunnel'
        } | Sort-Object @{ Expression = { $_.NetworkInterfaceType -ne 'Wireless80211' } }

    foreach ($adapter in $adapters) {
        $properties = $adapter.GetIPProperties()
        if (-not ($properties.GatewayAddresses | Where-Object {
            $_.Address.AddressFamily -eq 'InterNetwork' -and $_.Address.ToString() -ne '0.0.0.0'
        })) { continue }
        $entry = $properties.UnicastAddresses | Where-Object {
            $_.Address.AddressFamily -eq 'InterNetwork' -and
            $_.Address.ToString() -notmatch '^(127\.|169\.254\.|0\.)'
        } | Select-Object -First 1
        if ($entry) { return $entry.Address.ToString() }
    }
}

$npm = (Get-Command npm.cmd -ErrorAction Stop).Source
$python = Join-Path $PSScriptRoot 'backend/.venv/Scripts/python.exe'
if (-not (Test-Path -LiteralPath $python)) {
    $systemPython = (Get-Command python.exe -ErrorAction Stop).Source
    Invoke-Checked $systemPython @('-m', 'venv', 'backend/.venv')
}

$pythonHash = Get-DependencyHash 'backend/requirements.txt'
$pythonStamp = 'backend/.venv/requirements.sha256'
if (-not (Test-Path -LiteralPath $pythonStamp) -or (Get-Content -LiteralPath $pythonStamp -Raw).Trim() -ne $pythonHash) {
    Invoke-Checked $python @('-m', 'pip', 'install', '-r', 'backend/requirements.txt')
    Set-Content -LiteralPath $pythonStamp -Value $pythonHash -Encoding ascii
}

$npmHash = Get-DependencyHash 'package-lock.json'
$npmStamp = 'node_modules/.resonance-lock.sha256'
if (-not (Test-Path -LiteralPath $npmStamp) -or (Get-Content -LiteralPath $npmStamp -Raw).Trim() -ne $npmHash) {
    Invoke-Checked $npm @('ci')
    Set-Content -LiteralPath $npmStamp -Value $npmHash -Encoding ascii
}

# Local builds always use the same HTTP origin as the page.
$env:VITE_API_BASE_URL = '/api'
Invoke-Checked $npm @('run', 'build')

$launchArgs = @('backend/launch_local.py', '--port', $Port.ToString())
$lanAddress = Get-LanAddress
if ($lanAddress) { $launchArgs += @('--lan', $lanAddress) }
if ($NoBrowser) { $launchArgs += '--no-browser' }
Invoke-Checked $python $launchArgs
