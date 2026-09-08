from collections import defaultdict
from pathlib import Path

from .audio import make_speaker_sample
from .gender import predict_gender

def build_speaker_profiles(
    segments,
    source_audio,
    work_dir,
    gender_repo,
    sample_seconds=18.0,
):
    by_speaker = defaultdict(list)
    for seg in segments:
        by_speaker[seg["speaker"]].append(seg)

    profiles = {}
    speaker_dir = Path(work_dir) / "speaker_samples"
    speaker_dir.mkdir(parents=True, exist_ok=True)

    for speaker, turns in sorted(by_speaker.items()):
        sample_path = speaker_dir / f"{speaker}.wav"
        make_speaker_sample(
            source_audio,
            turns,
            sample_path,
            max_seconds=sample_seconds,
        )

        try:
            gender_info = predict_gender(sample_path, gender_repo)
        except Exception as exc:
            gender_info = {
                "gender": "unknown",
                "female_probability": None,
                "confidence": 0.0,
                "error": str(exc),
            }

        profiles[speaker] = {
            "speaker": speaker,
            **gender_info,
        }

    return profiles

def choose_voice(profile, male_voice, female_voice):
    if profile.get("gender") == "female":
        return female_voice
    return male_voice
