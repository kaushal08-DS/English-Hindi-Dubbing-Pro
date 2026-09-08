import subprocess
from pathlib import Path

def run_cmd(args):
    result = subprocess.run(
        [str(x) for x in args],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        raise RuntimeError(
            "FFmpeg command failed:\n"
            + " ".join(map(str, args))
            + "\n\n"
            + result.stderr[-5000:]
        )
    return result

def extract_audio(video_path: Path, audio_path: Path):
    audio_path.parent.mkdir(parents=True, exist_ok=True)
    run_cmd([
        "ffmpeg", "-y",
        "-i", video_path,
        "-vn",
        "-ac", "1",
        "-ar", "16000",
        "-c:a", "pcm_s16le",
        audio_path,
    ])

def _atempo_chain(factor: float):
    parts = []
    remaining = factor
    while remaining > 2.0:
        parts.append("atempo=2.0")
        remaining /= 2.0
    while remaining < 0.5:
        parts.append("atempo=0.5")
        remaining /= 0.5
    parts.append(f"atempo={remaining:.6f}")
    return ",".join(parts)

def fit_audio_to_duration(src: Path, dst: Path, target_seconds: float):
    probe = run_cmd([
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        src,
    ])
    actual = float(probe.stdout.strip() or "0")
    if actual <= 0 or target_seconds <= 0:
        raise RuntimeError("Invalid TTS duration.")

    dst.parent.mkdir(parents=True, exist_ok=True)

    if actual > target_seconds * 1.02:
        factor = actual / target_seconds
        filt = _atempo_chain(factor)
        run_cmd([
            "ffmpeg", "-y",
            "-i", src,
            "-filter:a", filt,
            "-ar", "24000",
            "-ac", "1",
            dst,
        ])
    else:
        run_cmd([
            "ffmpeg", "-y",
            "-i", src,
            "-ar", "24000",
            "-ac", "1",
            dst,
        ])

    # final exact-fit pad/trim using pydub
    from pydub import AudioSegment
    audio = AudioSegment.from_file(dst)
    target_ms = max(100, int(target_seconds * 1000))
    if len(audio) > target_ms:
        audio = audio[:target_ms]
    elif len(audio) < target_ms:
        audio += AudioSegment.silent(duration=target_ms - len(audio))
    audio.export(dst, format="wav")

def mux_video(video_path: Path, dubbed_audio: Path, output_path: Path):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    run_cmd([
        "ffmpeg", "-y",
        "-i", video_path,
        "-i", dubbed_audio,
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-c:v", "copy",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        output_path,
    ])
