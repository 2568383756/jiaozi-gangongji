$ErrorActionPreference = 'Stop'
$introDevelopmentRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$introOutput = Join-Path $introDevelopmentRoot 'Art/开场纸书_v05_20261111'
$introFrameDirectory = Join-Path $PSScriptRoot 'work/frames_final'
$introFrames = Join-Path $introFrameDirectory 'frame_%04d.jpg'
$introAudio = Join-Path $introOutput 'assets/开场配乐与纸声_v05.wav'
$introVideo = Join-Path $introOutput '开场纸书_v05_20261111.mp4'
$introTemporaryVideo = Join-Path $introOutput '开场纸书_v05_20261111.encoding.mp4'
$introSource = Join-Path $introOutput '开场纸书_v05_20261111.blend'
$introFfmpeg = 'C:/Program Files/ffmpeg/bin/ffmpeg.exe'
if (-not (Test-Path -LiteralPath $introFfmpeg)) { throw "FFmpeg not found: $introFfmpeg" }
if (-not (Test-Path -LiteralPath $introAudio)) { throw "Audio not found: $introAudio" }
if (-not (Test-Path -LiteralPath $introSource)) { throw "Blender source not found: $introSource" }
$introManifest = Get-Content -LiteralPath (Join-Path $introFrameDirectory 'render_manifest.json') -Raw | ConvertFrom-Json
$introSourceHash = (Get-FileHash -LiteralPath $introSource -Algorithm SHA256).Hash.ToLowerInvariant()
if ($introManifest.fingerprint.source_sha256 -ne $introSourceHash) { throw 'The Blender source changed after rendering.' }
$introCount = @(Get-ChildItem -LiteralPath $introFrameDirectory -File -Filter 'frame_*.jpg').Count
if ($introCount -ne 1152) { throw "Expected exactly 1152 frames, found $introCount" }
foreach ($introIndex in 1..1152) {
    $introFrameName = 'frame_{0:d4}' -f $introIndex
    $introFramePath = Join-Path $introFrameDirectory ($introFrameName + '.jpg')
    if (-not (Test-Path -LiteralPath $introFramePath)) { throw "Missing frame: $introFrameName" }
    $introBytes = [System.IO.File]::ReadAllBytes($introFramePath)
    if ($introBytes.Length -lt 10000 -or $introBytes[0] -ne 255 -or $introBytes[1] -ne 216 -or $introBytes[-2] -ne 255 -or $introBytes[-1] -ne 217) {
        throw "Incomplete JPEG: $introFrameName"
    }
    $introTagPath = Join-Path $introFrameDirectory ('source_tags/' + $introFrameName + '.sha256')
    $introTag = (Get-Content -LiteralPath $introTagPath -Raw).Trim()
    if ($introTag -ne $introManifest.fingerprint_sha256) { throw "Stale-source frame: $introFrameName" }
}
& $introFfmpeg -y -framerate 24 -start_number 1 -i $introFrames -i $introAudio -map 0:v:0 -map 1:a:0 -c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p -vf 'fade=t=in:st=0:d=0.6,fade=t=out:st=47.2:d=0.8' -c:a aac -b:a 192k -ar 44100 -ac 2 -t 48 -movflags +faststart $introTemporaryVideo
if ($LASTEXITCODE -ne 0) { throw 'Video encoding failed; existing final video was not replaced.' }
if ((Get-Item -LiteralPath $introTemporaryVideo).Length -lt 1000000) { throw 'Encoded video is unexpectedly small.' }
Move-Item -LiteralPath $introTemporaryVideo -Destination $introVideo -Force
Write-Output $introVideo
