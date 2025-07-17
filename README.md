Add-Type -AssemblyName System.Windows.Forms
[System.Windows.Forms.Cursor]::Position = New-Object System.Drawing.Point(500,500)
Start-Sleep -Seconds 5
[System.Windows.Forms.Cursor]::Position = New-Object System.Drawing.Point(505,500)
