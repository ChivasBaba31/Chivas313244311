param([Parameter(Mandatory = $true)][string]$Folder)

$exe = Join-Path $Folder "NexaTweak.exe"
if (-not (Test-Path $exe)) { exit 1 }

$ws = New-Object -ComObject WScript.Shell
$lnk = $ws.CreateShortcut((Join-Path $Folder "Nexa Tweak.lnk"))
$lnk.TargetPath = $exe
$lnk.WorkingDirectory = $Folder
$lnk.IconLocation = "$exe,0"
$lnk.Description = "Nexa Tweak - Developer by Chivas"
$lnk.Save()

$desktop = [Environment]::GetFolderPath("Desktop")
$d = $ws.CreateShortcut((Join-Path $desktop ("Nexa Tweak - " + (Split-Path $Folder -Leaf) + ".lnk")))
$d.TargetPath = $exe
$d.WorkingDirectory = $Folder
$d.IconLocation = "$exe,0"
$d.Description = "Nexa Tweak - Developer by Chivas"
$d.Save()
