<#
.SYNOPSIS
    Collects recent Critical and Error events from Windows Event Logs and queues them for AI analysis.
.DESCRIPTION
    This script filters the System and Application logs for Level 1 (Critical) and Level 2 (Error) 
    events generated in the last 5 minutes. It exports the findings to a JSON file.
#>

$queuePath = "C:\SRE_Agent\queue"
$outputFile = "$queuePath\event_queue.json"

# Ensure the queue directory exists
if (-not (Test-Path -Path $queuePath)) {
    New-Item -ItemType Directory -Path $queuePath | Out-Null
}

# Fetch errors from the last 5 minutes to prevent overlapping analysis
$timeSpan = (Get-Date).AddMinutes(-5)

Write-Output "Scanning Windows Event Logs for Critical/Error events..."

# Query Event Logs (Level 1 = Critical, Level 2 = Error)
$events = Get-WinEvent -FilterHashtable @{
    LogName   = 'System', 'Application'
    Level     = 1, 2
    StartTime = $timeSpan
} -ErrorAction SilentlyContinue

if ($events) {
    # Sanitize and structure the data
    $sanitizedEvents = $events | Select-Object TimeCreated, Id, LevelDisplayName, Message, ProviderName
    
    # Export to JSON for the Python Agent
    $sanitizedEvents | ConvertTo-Json -Depth 3 | Out-File $outputFile -Encoding utf8
    Write-Output "Successfully queued $($events.Count) events for AI analysis at $outputFile."
} else {
    Write-Output "System is healthy. No critical events found."
}