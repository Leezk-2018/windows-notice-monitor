param(
  [string]$ProjectDir = (Split-Path -Parent $PSScriptRoot)
)

$Action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-ExecutionPolicy Bypass -File `"$ProjectDir\scripts\run.ps1`""
$Trigger = New-ScheduledTaskTrigger -AtLogOn
Register-ScheduledTask -TaskName "WeChatNotifyBridge" -Action $Action -Trigger $Trigger -Description "Start WeChat notification bridge at logon"
