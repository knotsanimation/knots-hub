# entry point script to start the hub
# all command line arguments are passed directly to the python CLI

# // global config
$ErrorActionPreference = "Stop"

# // Utility code
# ===============
$SCRIPTNAME = "hub-launcher"
function Log {
    param ($message, $level, $color)
    Write-Host "$($level.PadRight(8, ' ') ) | $((Get-Date).ToString() ) [$SCRIPTNAME] $message" -ForegroundColor $color
}
function LogDebug { Log @args "DEBUG" "DarkGray" }
function LogInfo { Log @args "INFO" "White" }


# // Update Hub if necessary
# ==========================
if ($env:_KNOTSHUBLAUNCHER_UPDATE_CWD) {
    Push-Location -Path $env:_KNOTSHUBLAUNCHER_UPDATE_CWD
    # the current directory is assumed to be at root of an hub installation
    $root_path = (Resolve-Path "..").Path
    $install_path = (Resolve-Path ".").Path
    $install_dir_name = (Get-Item $install_path).Name
    $install_udpate_path = (Resolve-Path ".\__newupdate__").Path

    LogDebug "Found hub update '$install_udpate_path', installing ..."
    Move-Item -Path $install_udpate_path -Destination $root_path
    Remove-Item $install_path -Force -Recurse
    Rename-Item -Path $install_udpate_path -NewName $install_dir_name
    LogDebug "Hub update installed."
}
else {
    # ensure cwd is this script directory which must be a hub installation directory
    Push-Location -Path $PSScriptRoot
}

# // Launch Hub
# =============
$python_bin_path = (Resolve-Path ".\python\python.exe").Path
$venv_path = (Resolve-Path ".\.venv").Path

# activate python venv
$env:VENV = $venv_path

LogInfo "Launching hub from '$( (Get-Location).Path )'"
Start-Process $python_bin_path -Wait -NoNewWindow -ArgumentList "-m knots_hub $args"

# restore cwd
Pop-Location
