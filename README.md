Add-Type -AssemblyName System.Windows.Forms

function Move-MouseCircle {
    $radius = 30
    $centerX = [System.Windows.Forms.Cursor]::Position.X
    $centerY = [System.Windows.Forms.Cursor]::Position.Y

    for ($angle = 0; $angle -lt 360; $angle += 30) {
        $radian = $angle * [Math]::PI / 180
        $x = $centerX + [Math]::Round($radius * [Math]::Cos($radian))
        $y = $centerY + [Math]::Round($radius * [Math]::Sin($radian))
        [System.Windows.Forms.Cursor]::Position = New-Object System.Drawing.Point($x, $y)
        Start-Sleep -Milliseconds 100
    }
}

while ($true) {
    Move-MouseCircle
    Start-Sleep -Seconds 10
}
