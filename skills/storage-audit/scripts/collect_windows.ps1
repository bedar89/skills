<# Metadata-only Windows collector. Compatible with Windows PowerShell 5.1. #>
[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$OutputPath,
    [string[]]$Roots,
    [int]$Seconds = 120,
    [int]$LargeMiB = 100,
    [string]$RulesPath,
    [switch]$IncludeBam,
    [switch]$InventoryOnly
)
$ErrorActionPreference = 'Stop'
if (-not $RulesPath) { $RulesPath = Join-Path $PSScriptRoot '..\assets\apps.json' }
if ($Seconds -le 0 -or $LargeMiB -lt 0) { throw 'Invalid scan limits' }
$OutputPath = [IO.Path]::GetFullPath($OutputPath)
if (Test-Path -LiteralPath $OutputPath) { throw 'Output exists; use a new snapshot path' }
$captured = [DateTime]::UtcNow.ToString('o')
$deadline = [DateTime]::UtcNow.AddSeconds($Seconds)
$rules = @((Get-Content -LiteralPath $RulesPath -Raw | ConvertFrom-Json).windows | ForEach-Object {
    @{ path = [Environment]::ExpandEnvironmentVariables($_[0]).TrimEnd('\'); app = $_[1]; kind = $_[2]; boundary = $_[3] }
})
$apps = @()
$limits = [Collections.Generic.List[string]]::new()
foreach ($registry in @('HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*',
    'HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*',
    'HKLM:\Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*')) {
    try {
        foreach ($a in @(Get-ItemProperty -Path $registry -ErrorAction Stop)) {
            if (-not $a.DisplayName) { continue }
            $apps += @{ name = $a.DisplayName; version = $a.DisplayVersion; install_date = $a.InstallDate;
                install_location = $a.InstallLocation; estimated_kib = $a.EstimatedSize; source = $registry }
            $loc = [Environment]::ExpandEnvironmentVariables([string]$a.InstallLocation).TrimEnd('\')
            if ($loc -and [IO.Path]::IsPathRooted($loc) -and
                $loc -notin @($env:USERPROFILE, $env:ProgramFiles, ${env:ProgramFiles(x86)}, $env:WINDIR, $env:ProgramData) -and
                $loc.Length -gt 8) {
                $rules += @{ path = $loc; app = [string]$a.DisplayName; kind = 'installation'; boundary = $false }
            }
        }
    } catch { $limits.Add("Uninstall registry unavailable: $registry") }
}
$rules = @($rules | Sort-Object { $_.path.Length } -Descending)
if (-not $Roots) { $Roots = @($env:USERPROFILE, $env:ProgramFiles, ${env:ProgramFiles(x86)}, $env:ProgramData, $env:WINDIR) }
if ($InventoryOnly) { $Roots = @() }
$selected = [Collections.Generic.List[string]]::new()
$excluded = @()
foreach ($root in @($Roots | Where-Object { $_ } | ForEach-Object {
    $full = [IO.Path]::GetFullPath($_)
    if ($full.Length -gt 3) { $full.TrimEnd('\') } else { $full }
} | Sort-Object -Unique | Sort-Object Length)) {
    if (-not [IO.Directory]::Exists($root)) { $excluded += @{ path=$root; reason='missing' }; continue }
    if (([IO.File]::GetAttributes($root) -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
        $excluded += @{ path=$root; reason='reparse-root' }; continue
    }
    $covered = $false
    foreach ($parent in $selected) {
        if ($root.StartsWith($parent.TrimEnd('\') + '\', [StringComparison]::OrdinalIgnoreCase)) { $covered=$true }
    }
    if ($covered) { $excluded += @{ path=$root; reason='covered-by-parent' } } else { $selected.Add($root) }
}
$components = @{}
$large = [Collections.Generic.List[object]]::new()
$coverage = @()
foreach ($root in $selected) {
    $row = @{ root=$root; complete=$true; files=0; errors=0; skipped=@{}; examples=@() }
    $stack = [Collections.Generic.Stack[string]]::new()
    $stack.Push($root)
    while ($stack.Count -gt 0) {
        if ([DateTime]::UtcNow -ge $deadline) { $row.complete=$false; $row.skipped.deadline=$stack.Count; break }
        $dir = $stack.Pop()
        try {
            foreach ($entry in [IO.Directory]::EnumerateFileSystemEntries($dir)) {
                if ([DateTime]::UtcNow -ge $deadline) { $row.complete=$false; $row.skipped.deadline=1; break }
                try {
                    $attributes = [IO.File]::GetAttributes($entry)
                    # Reparse, Offline, RecallOnOpen and RecallOnDataAccess. Avoid hydration.
                    if (([int]$attributes -band (1024 -bor 4096 -bor 262144 -bor 4194304)) -ne 0) {
                        $row.skipped.reparse_or_offline = 1 + [int]$row.skipped.reparse_or_offline
                        $row.complete=$false
                        continue
                    }
                    if (($attributes -band [IO.FileAttributes]::Directory) -ne 0) { $stack.Push($entry); continue }
                    if ($entry -eq $OutputPath) { continue }
                    $file = [IO.FileInfo]::new($entry)
                    $owner = $null
                    foreach ($rule in $rules) {
                        if ($entry.Equals($rule.path, [StringComparison]::OrdinalIgnoreCase) -or
                            $entry.StartsWith($rule.path + '\', [StringComparison]::OrdinalIgnoreCase)) { $owner=$rule; break }
                    }
                    if ($owner) { $bucket=$owner.path; $app=$owner.app; $kind=$owner.kind; $boundary=$owner.boundary }
                    else {
                        $parts = $entry.Substring($root.Length).TrimStart('\').Split('\')
                        $bucket = $root
                        for ($i=0; $i -lt [Math]::Min(2, $parts.Length - 1); $i++) { $bucket = Join-Path $bucket $parts[$i] }
                        $app='Unmapped'; $kind='unclassified'; $boundary=$false
                    }
                    if (-not $components.ContainsKey($bucket)) {
                        $sha = [Security.Cryptography.SHA256]::Create()
                        try { $id = ([BitConverter]::ToString($sha.ComputeHash([Text.Encoding]::UTF8.GetBytes($bucket.ToLowerInvariant())))).Replace('-','').Substring(0,16).ToLowerInvariant() }
                        finally { $sha.Dispose() }
                        $components[$bucket] = @{ id=$id; path=$bucket; app=$app; kind=$kind; boundary=$boundary;
                            logical_bytes=[long]0; allocated_bytes=$null; files=0; old_180d_bytes=[long]0; latest_mtime=0; root=$root }
                    }
                    $c=$components[$bucket]
                    $c.logical_bytes += $file.Length
                    $c.files++
                    $mtime = ($file.LastWriteTimeUtc - [DateTime]'1970-01-01').TotalSeconds
                    $c.latest_mtime = [Math]::Max($c.latest_mtime, $mtime)
                    if ($file.LastWriteTimeUtc -lt [DateTime]::UtcNow.AddDays(-180)) { $c.old_180d_bytes += $file.Length }
                    $row.files++
                    if ($file.Length -ge [long]$LargeMiB * 1048576) {
                        $large.Add(@{ path=$entry; logical_bytes=$file.Length })
                        if ($large.Count -gt 110) {
                            $largest = @($large | Sort-Object { $_.logical_bytes } -Descending | Select-Object -First 100)
                            $large.Clear(); foreach ($item in $largest) { $large.Add($item) }
                        }
                    }
                } catch {
                    $row.errors++; $row.complete=$false
                    if ($row.examples.Count -lt 8) { $row.examples += @{ path=$entry; error=$_.Exception.GetType().Name } }
                }
            }
        } catch {
            $row.errors++; $row.complete=$false
            if ($row.examples.Count -lt 8) { $row.examples += @{ path=$dir; error=$_.Exception.GetType().Name } }
        }
    }
    $coverage += $row
}
$volumes = @([IO.DriveInfo]::GetDrives() | Where-Object { $_.IsReady -and $_.DriveType -eq 'Fixed' } | ForEach-Object {
    @{ id=$_.Name; path=$_.Name; total_bytes=$_.TotalSize; free_bytes=$_.AvailableFreeSpace }
})
$processes = @(Get-Process | ForEach-Object { try { if ($_.Path) { @{ pid=$_.Id; exe=$_.Path } } } catch {} })
$services = @()
try { $services = @(Get-Service | ForEach-Object { @{ name=$_.Name; state=[string]$_.Status } }) }
catch { $limits.Add('Service enumeration unavailable') }
$wsl = @()
try {
    $distroKeys = @(Get-ChildItem -LiteralPath 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Lxss' -ErrorAction Stop)
    foreach ($key in $distroKeys) {
        $d = Get-ItemProperty -LiteralPath $key.PSPath
        $base = [Environment]::ExpandEnvironmentVariables($d.BasePath)
        $imageName = if ($d.VhdFileName) { [string]$d.VhdFileName } else { 'ext4.vhdx' }
        $vhd = [IO.Path]::Combine([string]$base, $imageName)
        $length=$null
        try { $length = (Get-Item -LiteralPath $vhd).Length } catch {}
        $wsl += @{ distro=$d.DistributionName; vhd_path=$vhd; logical_bytes=$length; registry_id=$key.PSChildName }
    }
} catch { $limits.Add('WSL registration metadata unavailable or no registered distro') }
$execution = @()
if ($IncludeBam) {
    $sid = [Security.Principal.WindowsIdentity]::GetCurrent().User.Value
    try {
        $bam = Get-Item -LiteralPath "HKLM:\SYSTEM\CurrentControlSet\Services\bam\State\UserSettings\$sid"
        foreach ($name in $bam.GetValueNames()) {
            $value=$bam.GetValue($name)
            if ($value -is [byte[]] -and $value.Length -ge 8 -and $name.StartsWith('\Device\')) {
                try { $execution += @{ path=$name; observed_at=[DateTime]::FromFileTimeUtc([BitConverter]::ToInt64($value,0)).ToString('o'); source='BAM execution, not human use' } } catch {}
            }
        }
    } catch { $limits.Add('BAM not accessible or unavailable for current SID') }
} else { $limits.Add('BAM not requested; last execution unknown') }
$limits.Add('Logical file lengths only: hardlinks, sparse files and compression are not resolved.')
$limits.Add('mtime is file activity, never last human use. No private content inspected.')
$limits.Add('Store apps, containers, other users, secondary drives and service executable dependencies need follow-up.')
$result = @{ schema=1; captured_at=$captured; host=$env:COMPUTERNAME; platform='windows'; context='host';
    user=$env:USERNAME; home=$env:USERPROFILE; os=[Environment]::OSVersion.VersionString; volumes=$volumes;
    environment_paths=@{USERPROFILE=$env:USERPROFILE;APPDATA=$env:APPDATA;LOCALAPPDATA=$env:LOCALAPPDATA;WINDIR=$env:WINDIR};
    components=@($components.Values); large_files=@($large | Sort-Object { $_.logical_bytes } -Descending | Select-Object -First 100);
    processes=$processes; services=$services; packages=$apps; wsl_images=$wsl; execution=$execution;
    coverage=$coverage; excluded_roots=$excluded; limits=@($limits) }
$parent = Split-Path -Parent $OutputPath
[void][IO.Directory]::CreateDirectory($parent)
$json = $result | ConvertTo-Json -Depth 12
$acl = [Security.AccessControl.FileSecurity]::new()
$acl.SetAccessRuleProtection($true, $false)
foreach ($identity in @([Security.Principal.WindowsIdentity]::GetCurrent().User,
                       [Security.Principal.SecurityIdentifier]::new('S-1-5-18'))) {
    $acl.AddAccessRule([Security.AccessControl.FileSystemAccessRule]::new($identity, 'FullControl', 'Allow'))
}
$stream = [IO.FileStream]::new($OutputPath, [IO.FileMode]::CreateNew,
    [Security.AccessControl.FileSystemRights]::Write, [IO.FileShare]::None,
    4096, [IO.FileOptions]::None, $acl)
try {
    $bytes=[Text.UTF8Encoding]::new($false).GetBytes($json)
    $stream.Write($bytes,0,$bytes.Length)
} finally { $stream.Dispose() }
Write-Output "Saved $($components.Count) components to $OutputPath"
