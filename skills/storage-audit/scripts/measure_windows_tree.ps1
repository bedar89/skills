<# Fast whole-volume metadata survey. Directory rows are overlapping subtree totals.
   No data is read, removed, hydrated or stopped. Run before targeted app scans. #>
[CmdletBinding()]
param(
    [string]$Root = 'C:\',
    [Parameter(Mandatory=$true)][string]$OutputPath,
    [int]$Seconds = 240
)
$ErrorActionPreference='Stop'
if ($Seconds -le 0) { throw 'Seconds must be positive' }
if (Test-Path -LiteralPath $OutputPath) { throw 'Use a new output snapshot' }
if (-not ('StorageTreeSurvey' -as [type])) {
Add-Type -TypeDefinition @'
using System;
using System.IO;
using System.Collections.Generic;
using System.Diagnostics;
public class StorageTreeNode {
    public string path;
    public int parent;
    public long direct_bytes, subtree_logical_bytes, files;
    public int errors, skipped;
    public bool complete=true;
}
public class StorageLargeFile { public string path; public long bytes; }
public class StorageTreeResult {
    public List<StorageTreeNode> directories=new List<StorageTreeNode>();
    public List<StorageLargeFile> large_files=new List<StorageLargeFile>();
    public List<string> errors=new List<string>();
    public Dictionary<string,long> extensions=new Dictionary<string,long>(StringComparer.OrdinalIgnoreCase);
    public long file_count;
    public double elapsed_seconds;
    public bool deadline_reached;
}
public class StorageTreeSurvey {
    public static StorageTreeResult Run(string root, int seconds) {
        var result=new StorageTreeResult();
        var watch=Stopwatch.StartNew();
        var start=new DirectoryInfo(root);
        if((start.Attributes & FileAttributes.ReparsePoint)!=0) throw new IOException("Reparse root refused");
        result.directories.Add(new StorageTreeNode {path=start.FullName,parent=-1});
        var stack=new Stack<int>(); stack.Push(0);
        while(stack.Count>0) {
            if(watch.Elapsed.TotalSeconds>=seconds) {result.deadline_reached=true;break;}
            int index=stack.Pop(); var node=result.directories[index];
            try {
                foreach(var entry in new DirectoryInfo(node.path).EnumerateFileSystemInfos()) {
                    if(watch.Elapsed.TotalSeconds>=seconds) {node.complete=false;result.deadline_reached=true;break;}
                    try {
                        var attr=entry.Attributes;
                        if(((int)attr & (1024|4096|262144|4194304))!=0) {node.skipped++;node.complete=false;continue;}
                        if((attr & FileAttributes.Directory)!=0) {
                            result.directories.Add(new StorageTreeNode {path=entry.FullName,parent=index});
                            stack.Push(result.directories.Count-1);
                        } else {
                            long length=((FileInfo)entry).Length;
                            node.direct_bytes+=length;node.files++;result.file_count++;
                            string ext=entry.Extension.ToLowerInvariant();
                            if(!result.extensions.ContainsKey(ext))result.extensions[ext]=0;
                            result.extensions[ext]+=length;
                            if(length>=100L*1048576) {
                                result.large_files.Add(new StorageLargeFile {path=entry.FullName,bytes=length});
                                if(result.large_files.Count>250) {
                                    result.large_files.Sort((a,b)=>b.bytes.CompareTo(a.bytes));
                                    result.large_files.RemoveRange(200,result.large_files.Count-200);
                                }
                            }
                        }
                    } catch(Exception e) {
                        node.errors++;node.complete=false;
                        if(result.errors.Count<40)result.errors.Add(entry.FullName+" : "+e.GetType().Name);
                    }
                }
            } catch(Exception e) {
                node.errors++;node.complete=false;
                if(result.errors.Count<40)result.errors.Add(node.path+" : "+e.GetType().Name);
            }
        }
        foreach(int i in stack) result.directories[i].complete=false;
        for(int i=result.directories.Count-1;i>=0;i--) {
            var n=result.directories[i];n.subtree_logical_bytes+=n.direct_bytes;
            if(n.parent>=0) {
                var parent=result.directories[n.parent];parent.subtree_logical_bytes+=n.subtree_logical_bytes;
                parent.files+=n.files;parent.errors+=n.errors;parent.skipped+=n.skipped;
                if(!n.complete)parent.complete=false;
            }
        }
        result.large_files.Sort((a,b)=>b.bytes.CompareTo(a.bytes));
        result.elapsed_seconds=watch.Elapsed.TotalSeconds;
        return result;
    }
}
'@
}
$captured=[DateTime]::UtcNow.ToString('o')
$result=[StorageTreeSurvey]::Run([IO.Path]::GetFullPath($Root),$Seconds)
$payload=@{schema=1;kind='directory-survey';host=$env:COMPUTERNAME;root=$Root;captured_at=$captured;
    measurement='logical file lengths; hardlinks and compression unresolved';result=$result}
$acl=[Security.AccessControl.FileSecurity]::new()
$acl.SetAccessRuleProtection($true,$false)
foreach($identity in @([Security.Principal.WindowsIdentity]::GetCurrent().User,[Security.Principal.SecurityIdentifier]::new('S-1-5-18'))) {
    $acl.AddAccessRule([Security.AccessControl.FileSystemAccessRule]::new($identity,'FullControl','Allow'))
}
$OutputPath=[IO.Path]::GetFullPath($OutputPath)
[void][IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($OutputPath))
$stream=[IO.FileStream]::new($OutputPath,[IO.FileMode]::CreateNew,[Security.AccessControl.FileSystemRights]::Write,[IO.FileShare]::None,4096,[IO.FileOptions]::None,$acl)
try {
    $bytes=[Text.UTF8Encoding]::new($false).GetBytes(($payload|ConvertTo-Json -Depth 10 -Compress))
    $stream.Write($bytes,0,$bytes.Length)
}finally{$stream.Dispose()}
Write-Output ('Survey saved: '+$OutputPath+'; files='+$result.file_count+'; seconds='+[Math]::Round($result.elapsed_seconds,1)+'; deadline='+$result.deadline_reached)
