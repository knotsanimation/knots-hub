param (
    [Parameter(Mandatory = $true)][string]$shortcutPath,
    [Parameter(Mandatory = $true)][string]$referencePath,
    [string]$iconPath = ""
)

# https://superuser.com/a/836818
$wsobject = New-Object -ComObject WScript.Shell;
$shortcut = $wsobject.CreateShortcut($shortcutPath);
# https://learn.microsoft.com/en-us/previous-versions/3s9bx7at(v=vs.80)
$shortcut.IconLocation = "$iconPath";
$shortcut.TargetPath = $referencePath;
$shortcut.Save()