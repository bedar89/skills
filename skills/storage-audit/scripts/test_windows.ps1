# Run in Windows PowerShell 5.1 with a process-scoped ExecutionPolicy Bypass.
$ErrorActionPreference = 'Stop'
$fixture = Join-Path $env:TEMP ('storage-audit-test-' + [guid]::NewGuid().ToString('N'))
[void][IO.Directory]::CreateDirectory($fixture)
try {
    $a=Join-Path $fixture 'a'; $b=Join-Path $fixture 'b'
    [void][IO.Directory]::CreateDirectory($a)
    [void][IO.Directory]::CreateDirectory($b)
    [IO.File]::WriteAllBytes((Join-Path $a 'first.bin'), [byte[]]::new(8192))
    [IO.File]::WriteAllBytes((Join-Path $b 'second.bin'), [byte[]]::new(4096))
    $output=Join-Path $fixture 'snapshot.json'
    & (Join-Path $PSScriptRoot 'collect_windows.ps1') -Roots @($a,$b) -Seconds 5 -LargeMiB 0 -OutputPath $output
    $r=Get-Content -LiteralPath $output -Raw | ConvertFrom-Json
    if (($r.components | Measure-Object -Property logical_bytes -Sum).Sum -ne 12288) { throw 'Incorrect file sizes' }
    if ($r.coverage.Count -ne 2) { throw 'Equal-length roots must both be scanned' }
    if (@($r.coverage | Where-Object { -not $_.complete }).Count) { throw 'Fixture incomplete' }
    $acl=Get-Acl -LiteralPath $output
    if (-not $acl.AreAccessRulesProtected -or $acl.Access.Count -ne 2) { throw 'Private output ACL missing' }
    $failed=$false
    try { & (Join-Path $PSScriptRoot 'collect_windows.ps1') -Roots @($a) -Seconds 1 -OutputPath $output }
    catch { $failed=$true }
    if (-not $failed) { throw 'Existing output was overwritten' }
    $output2=Join-Path $fixture 'parent.json'
    & (Join-Path $PSScriptRoot 'collect_windows.ps1') -Roots @($a,(Join-Path $a '.')) -Seconds 5 -OutputPath $output2
    $parent=Get-Content -LiteralPath $output2 -Raw | ConvertFrom-Json
    if ($parent.coverage.Count -ne 1) { throw 'Equivalent roots scanned twice' }
    $nested=Join-Path $a 'nested'
    [void][IO.Directory]::CreateDirectory($nested)
    [IO.File]::WriteAllBytes((Join-Path $nested 'nested.bin'),[byte[]]::new(4096))
    $surveyPath=Join-Path $fixture 'tree.json'
    & (Join-Path $PSScriptRoot 'measure_windows_tree.ps1') -Root $a -Seconds 5 -OutputPath $surveyPath
    $survey=Get-Content -LiteralPath $surveyPath -Raw | ConvertFrom-Json
    if ($survey.result.directories[0].subtree_logical_bytes -ne 12288 -or $survey.result.file_count -ne 2) { throw 'Whole-root survey accounting failed' }
    if ($survey.result.directories[0].direct_bytes -ne 8192) { throw 'Subtree and direct bytes were confused' }
    Write-Output 'PASS: measured bytes, equal-length roots, private ACL, no overwrite, equivalent roots.'
} finally {
    Remove-Item -LiteralPath $fixture -Recurse -Force
}
