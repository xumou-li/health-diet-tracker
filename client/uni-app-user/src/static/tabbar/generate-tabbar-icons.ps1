$ErrorActionPreference = 'Stop'

Add-Type -AssemblyName System.Drawing

$size = 81
$stroke = 5.2
$green = [System.Drawing.Color]::FromArgb(255, 76, 175, 80)
$gray = [System.Drawing.Color]::FromArgb(255, 153, 153, 153)
$transparent = [System.Drawing.Color]::Transparent
$baseDir = Split-Path -Parent $MyInvocation.MyCommand.Path

function New-Bitmap {
    $bmp = New-Object System.Drawing.Bitmap($size, $size)
    $bmp.SetResolution(96, 96)
    $graphics = [System.Drawing.Graphics]::FromImage($bmp)
    $graphics.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
    $graphics.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
    $graphics.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality
    $graphics.Clear($transparent)

    return @{ Bitmap = $bmp; Graphics = $graphics }
}

function New-Pen([System.Drawing.Color] $color) {
    $pen = New-Object System.Drawing.Pen($color, $stroke)
    $pen.StartCap = [System.Drawing.Drawing2D.LineCap]::Round
    $pen.EndCap = [System.Drawing.Drawing2D.LineCap]::Round
    $pen.LineJoin = [System.Drawing.Drawing2D.LineJoin]::Round
    return $pen
}

function Draw-RoundedRectangle($g, $pen, [float] $x, [float] $y, [float] $width, [float] $height, [float] $radius) {
    $diameter = $radius * 2
    $path = New-Object System.Drawing.Drawing2D.GraphicsPath

    try {
        $path.AddArc($x, $y, $diameter, $diameter, 180, 90)
        $path.AddArc($x + $width - $diameter, $y, $diameter, $diameter, 270, 90)
        $path.AddArc($x + $width - $diameter, $y + $height - $diameter, $diameter, $diameter, 0, 90)
        $path.AddArc($x, $y + $height - $diameter, $diameter, $diameter, 90, 90)
        $path.CloseFigure()
        $g.DrawPath($pen, $path)
    }
    finally {
        $path.Dispose()
    }
}

function Fill-Circle($g, [System.Drawing.Color] $color, [float] $x, [float] $y, [float] $diameter) {
    $brush = New-Object System.Drawing.SolidBrush($color)
    try {
        $g.FillEllipse($brush, $x, $y, $diameter, $diameter)
    }
    finally {
        $brush.Dispose()
    }
}

function Save-Icon([string] $name, [scriptblock] $drawer) {
    foreach ($variant in @(
        @{ Suffix = ''; Color = $gray },
        @{ Suffix = '-active'; Color = $green }
    )) {
        $surface = New-Bitmap
        $bmp = $surface.Bitmap
        $g = $surface.Graphics
        $pen = New-Pen $variant.Color

        try {
            & $drawer $g $pen $variant.Color
            $path = Join-Path $baseDir ("{0}{1}.png" -f $name, $variant.Suffix)
            $bmp.Save($path, [System.Drawing.Imaging.ImageFormat]::Png)
        }
        finally {
            $pen.Dispose()
            $g.Dispose()
            $bmp.Dispose()
        }
    }
}

function Draw-Home($g, $pen, $color) {
    $g.DrawLines($pen, @(
        [System.Drawing.PointF]::new(18, 38),
        [System.Drawing.PointF]::new(40.5, 20),
        [System.Drawing.PointF]::new(63, 38)
    ))
    $g.DrawRectangle($pen, 24, 36, 33, 24)
    $g.DrawLine($pen, 38, 60, 38, 45)
    $g.DrawLine($pen, 44, 60, 44, 45)
}

function Draw-Stats($g, $pen, $color) {
    $g.DrawLine($pen, 20, 59, 61, 59)
    $g.DrawLine($pen, 27, 59, 27, 45)
    $g.DrawLine($pen, 41, 59, 41, 35)
    $g.DrawLine($pen, 55, 59, 55, 25)
    $g.DrawLine($pen, 24, 42, 41, 31)
    $g.DrawLine($pen, 41, 31, 55, 21)
    Fill-Circle $g $color 23.8 39.8 6.2
    Fill-Circle $g $color 37.8 28.8 6.2
    Fill-Circle $g $color 51.8 18.8 6.2
}

function Draw-AI($g, $pen, $color) {
    Draw-RoundedRectangle $g $pen 22 18 37 31 9
    $g.DrawLine($pen, 40.5, 18, 40.5, 10)
    Fill-Circle $g $color 37.2 5.8 6.6
    $g.DrawLine($pen, 18, 33.5, 22, 33.5)
    $g.DrawLine($pen, 59, 33.5, 63, 33.5)
    Fill-Circle $g $color 30.2 29 5.2
    Fill-Circle $g $color 45.6 29 5.2
    $g.DrawArc($pen, 31, 34, 19, 11, 10, 160)
    $g.DrawLine($pen, 33, 49, 33, 56)
    $g.DrawLine($pen, 48, 49, 48, 56)
    $g.DrawLine($pen, 28, 61, 53, 61)
}

function Draw-Mine($g, $pen, $color) {
    $g.DrawEllipse($pen, 28, 16, 25, 25)
    $g.DrawArc($pen, 20, 40, 41, 22, 200, 140)
    $g.DrawArc($pen, 12, 52, 57, 16, 200, 140)
}

Save-Icon 'home' ${function:Draw-Home}
Save-Icon 'stats' ${function:Draw-Stats}
Save-Icon 'ai' ${function:Draw-AI}
Save-Icon 'mine' ${function:Draw-Mine}
