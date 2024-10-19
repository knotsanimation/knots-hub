param (
    [Parameter(Mandatory = $true)][string]$shortcutPath,
    [Parameter(Mandatory = $true)][string]$referencePath,
    [string]$arguments = ""
)

# https://superuser.com/a/836818
$wsobject = New-Object -ComObject WScript.Shell;
$shortcut = $wsobject.CreateShortcut($shortcutPath);
$shortcut.TargetPath = "$referencePath";
$shortcut.Arguments = "$arguments";
$shortcut.Save()