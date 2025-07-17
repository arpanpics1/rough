Add-Type -AssemblyName System.Windows.Forms

while ($true) {
    # Move to (500, 500)
    [System.Windows.Forms.Cursor]::Position = New-Object System.Drawing.Point(500, 500)
    Start-Sleep -Seconds 20

    # Move to (505, 500)
    [System.Windows.Forms.Cursor]::Position = New-Object System.Drawing.Point(505, 500)
    Start-Sleep -Seconds 20
}
