$ErrorActionPreference = 'Stop'
$introArt = Join-Path $PSScriptRoot '../../Art/开场机关书_v09_20261113'
$introFrames = Join-Path $PSScriptRoot 'work/frames/%05d.jpg'
& 'C:/Program Files/ffmpeg/bin/ffmpeg.exe' -hide_banner -y -framerate 24 -i $introFrames -i (Join-Path $introArt 'assets/开场配乐与纸声_v09.wav') -c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p -r 24 -c:a aac -b:a 192k -t 56 -movflags +faststart (Join-Path $introArt '开场机关书_v09.mp4')
if ($LASTEXITCODE -ne 0) { throw 'FFmpeg encoding failed' }
& 'C:/Program Files/ffmpeg/bin/ffmpeg.exe' -v error -i (Join-Path $introArt '开场机关书_v09.mp4') -f null -
if ($LASTEXITCODE -ne 0) { throw 'Full media decode failed' }
