Add-Type -AssemblyName System.Windows.Forms

function Move-MouseCircle {
    $radius = 30
    $centerX = [System.Windows.Forms.Cursor]::Position.X
    $centerY = [System.Windows.Forms.Cursor]::Position.Y
    $startAngle = Get-Random -Minimum 0 -Maximum 360  # Random starting angle
    $direction = if ((Get-Random -Minimum 0 -Maximum 2) -eq 0) { 30 } else { -30 }  # Random direction: clockwise or counterclockwise

    for ($angle = $startAngle; $angle -lt ($startAngle + 360) -and $direction -gt 0 -or $angle -gt ($startAngle - 360) -and $direction -lt 0; $angle += $direction) {
        $radian = $angle * [Math]::PI / 180
        $x = $centerX + [Math]::Round($radius * [Math]::Cos($radian))
        $y = $centerY + [Math]::Round($radius * [Math]::Sin($radian))
        [System.Windows.Forms.Cursor]::Position = New-Object System.Drawing.Point($x, $y)
        Start-Sleep -Milliseconds 100
    }
}

while ($true) {
    Move-MouseCircle
    Start-Sleep -Seconds 2  # Reduced delay for smoother transitions
}

------




Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

# Add mouse click functionality using Win32 API
Add-Type @"
using System;
using System.Runtime.InteropServices;
public class MouseSimulator {
    [DllImport("user32.dll", CharSet=CharSet.Auto, CallingConvention=CallingConvention.StdCall)]
    public static extern void mouse_event(long dwFlags, long dx, long dy, long cButtons, long dwExtraInfo);
    public const int MOUSEEVENTF_LEFTDOWN = 0x02;
    public const int MOUSEEVENTF_LEFTUP = 0x04;
}
"@

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

function Left-Click {
    $pos = [System.Windows.Forms.Cursor]::Position
    [MouseSimulator]::mouse_event(0x02, $pos.X, $pos.Y, 0, 0)  # Left button down
    Start-Sleep -Milliseconds 100
    [MouseSimulator]::mouse_event(0x04, $pos.X, $pos.Y, 0, 0)  # Left button up
}

# Main loop
while ($true) {
    Move-MouseCircle
    Left-Click
    Start-Sleep -Seconds 10
}
