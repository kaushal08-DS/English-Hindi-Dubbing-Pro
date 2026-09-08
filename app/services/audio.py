from pathlib import Path
from pydub import AudioSegment

def make_speaker_sample(source_audio: Path, turns, output_path: Path, max_seconds=18.0):
    source = AudioSegment.from_file(source_audio)
    pieces = []
    collected = 0.0

    for turn in sorted(turns, key=lambda x: x["start"]):
        if collected >= max_seconds:
            break

        start = max(0, int(turn["start"] * 1000))
        end = min(len(source), int(turn["end"] * 1000))
        if end <= start:
            continue

        clip = source[start:end]
        remaining = max_seconds - collected
        if len(clip) > int(remaining * 1000):
            clip = clip[: int(remaining * 1000)]

        pieces.append(clip)
        collected += len(clip) / 1000.0

    if not pieces:
        raise RuntimeError("No audio available for speaker sample.")

    merged = pieces[0]
    for piece in pieces[1:]:
        merged += piece

    merged = merged.set_channels(1).set_frame_rate(16000)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    merged.export(output_path, format="wav")
