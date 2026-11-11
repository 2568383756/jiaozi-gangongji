// Run after the source, 1152-frame render, video and review artifacts are final.
// This performs metadata checks and full A/V decoding; it does not claim visual review.
import {readFile, writeFile, readdir, stat} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
import crypto from 'node:crypto';
import {spawnSync} from 'node:child_process';

const here = path.dirname(fileURLToPath(import.meta.url));
const out = path.resolve(here, '../../Art/开场纸书_v05_20261111');
const frames = path.join(here, 'work/frames_final');
const ffmpeg = 'C:/Program Files/ffmpeg/bin/ffmpeg.exe';
const expected = Array.from({length:1152}, (_, i) => `frame_${String(i + 1).padStart(4, '0')}`);
const names = await readdir(frames);
const frameNames = names.filter(name => /^frame_.*\.jpg$/i.test(name));
if (frameNames.length !== 1152) throw Error(`Expected 1152 JPEG frames, got ${frameNames.length}`);
const missing = expected.filter(name => !names.includes(`${name}.jpg`));
if (missing.length) throw Error(`Missing frames: ${missing.slice(0, 10).join(', ')}`);
const sha256 = data => crypto.createHash('sha256').update(data).digest('hex');
const blendName = '开场纸书_v05_20261111.blend';
const blendData = await readFile(path.join(out, blendName));
const renderManifest = JSON.parse(await readFile(path.join(frames, 'render_manifest.json'), 'utf8'));
if (renderManifest.fingerprint.source_sha256 !== sha256(blendData)) throw Error('Source changed after frame rendering.');
const dimensions = renderManifest.fingerprint;
if (dimensions.width !== 1920 || dimensions.height !== 1080 || dimensions.fps !== 24) throw Error('Wrong render settings.');
for (const name of expected) {
    const file = await readFile(path.join(frames, `${name}.jpg`));
    if (file.length < 10000 || file[0] !== 255 || file[1] !== 216 || file.at(-2) !== 255 || file.at(-1) !== 217) {
        throw Error(`Incomplete JPEG: ${name}`);
    }
    const tag = (await readFile(path.join(frames, 'source_tags', `${name}.sha256`), 'utf8')).trim();
    if (tag !== renderManifest.fingerprint_sha256) throw Error(`Stale-source frame: ${name}`);
}

const videoName = '开场纸书_v05_20261111.mp4';
const video = path.join(out, videoName);
const probe = spawnSync(ffmpeg, ['-hide_banner', '-i', video], {encoding:'utf8', maxBuffer:2 * 1024 * 1024});
if (probe.error) throw probe.error;
const metadata = probe.stderr || '';
const requiredMetadata = [
    /Video:\s*h264/, /1920x1080/, /\b24 fps\b/, /yuv420p/,
    /Duration:\s*00:00:48\.\d+/, /Audio:\s*aac/, /44100 Hz/, /stereo/,
];
if (!requiredMetadata.every(pattern => pattern.test(metadata))) throw Error(`Unexpected video metadata:\n${metadata}`);
// AAC packets can extend the MP4 container by one 1024-sample packet. The
// video itself must still decode to precisely 1152 frames at 24 fps.
const containerDuration = Number(metadata.match(/Duration:\s*00:00:(48\.\d+)/)?.[1]);
if (!Number.isFinite(containerDuration) || Math.abs(containerDuration - 48) > .03) throw Error('Container duration exceeds one AAC packet of rounding.');
const decode = spawnSync(ffmpeg, [
    '-v', 'error', '-nostats', '-progress', 'pipe:1', '-i', video,
    '-map', '0:v:0', '-map', '0:a:0', '-f', 'null', 'NUL',
], {encoding:'utf8', maxBuffer:8 * 1024 * 1024});
if (decode.error) throw decode.error;
if (decode.status !== 0 || decode.stderr.trim()) throw Error(`Full A/V decode failed: ${decode.stderr}`);
const decodedFrameMatches = [...decode.stdout.matchAll(/^frame=(\d+)/gm)];
const decodedFrames = Number(decodedFrameMatches.at(-1)?.[1]);
if (decodedFrames !== 1152 || !decode.stdout.includes('progress=end')) throw Error(`Decoded frame mismatch: ${decode.stdout}`);

const audioReport = JSON.parse(await readFile(path.join(out, 'assets/开场音轨来源_v05.json'), 'utf8'));
if (audioReport.duration_seconds !== 48 || audioReport.sample_rate !== 44100 || audioReport.channels !== 2) throw Error('Audio specification mismatch.');
if (JSON.stringify(audioReport.seal_seconds) !== '[37,43]') throw Error('v05 seal cues are not aligned.');
if (JSON.stringify(audioReport.paper_turn_seconds) !== '[6.9,14.9,22.9,30.9,38.9]') throw Error('v05 page cues are not aligned.');
const player = await readFile(path.join(out, '播放开场.html'), 'utf8');
if (!player.includes(videoName)) throw Error('Preview player does not reference the v05 video.');

const manifest = [];
async function record(relativeName, base=out, prefix='') {
    const data = await readFile(path.join(base, relativeName));
    manifest.push({file:prefix + relativeName, bytes:data.length, sha256:sha256(data)});
}
const sourceReview = JSON.parse(await readFile(path.join(out, '工程核验_v05.json'), 'utf8'));
const playerReview = JSON.parse(await readFile(path.join(out, '播放器核验_v05.json'), 'utf8'));
if (!sourceReview.passed) throw Error('Source validation is not passed.');
if (playerReview.status !== 'passed' || !playerReview.media_checks_run) throw Error('Player validation is not passed.');
const required = [blendName, videoName, '播放开场.html', '分镜总览_v05_20261111.jpg', '制作核验_v05.json', '工程核验_v05.json', '播放器核验_v05.json', '从这里开始.md'];
for (const name of required) await record(name);
for (const name of await readdir(path.join(out, 'assets'))) {
    const relative = `assets/${name}`;
    if ((await stat(path.join(out, relative))).isFile()) await record(relative);
}
for (const name of ['build_book.py', 'create_audio.py', 'render_frames.py', 'encode_video.ps1', 'verify_delivery.mjs', 'validate_source.py', 'verify_player.mjs', 'README.md']) {
    await record(name, here, '../../Scripts/开场纸书_v05_20261111/');
}
const result = {
    version:'v05_20261111', frame_sequence_count:1152,
    source_frame_fingerprint_verified:true,
    full_decode_passed:true, decoded_frames:decodedFrames,
    width:1920, height:1080, fps:24, duration_seconds:48, container_duration_seconds:containerDuration,
    video_codec:'H.264', pixel_format:'yuv420p',
    audio_codec:'AAC', sample_rate:44100, channels:2,
    audio_cues_verified:true,
    browser_playback_checked:true, browser_check_scope:'Independent headless browser: actual media playback, pause, seek, replay, skip and media-ended event.',
    source_validation_passed:true, visual_review_completed:false,
    unity_integration_tested:false, files:manifest,
};
await writeFile(path.join(out, '交付核验_v05.json'), JSON.stringify(result, null, 2) + '\n');
await writeFile(path.join(here, 'work/media_probe.txt'), metadata);
console.log(JSON.stringify({passed:true, frames:1152, duration:48, files:manifest.length}));
