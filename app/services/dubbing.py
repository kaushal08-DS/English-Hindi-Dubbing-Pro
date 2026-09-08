import json
import traceback
from pathlib import Path

from .ffmpeg_service import (
    extract_audio,
    fit_audio_to_duration,
    mux_video,
)
from .whisperx_engine import process_audio
from .speaker import build_speaker_profiles, choose_voice
from .translation import translate_segments
from .tts import synthesize

def update_job(app, job_id, **changes):
    path = app.config["STORAGE"] / "jobs" / f"{job_id}.json"
    job = json.loads(path.read_text(encoding="utf-8"))
    job.update(changes)
    path.write_text(
        json.dumps(job, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

def assemble_timeline(items, clips_dir, output_wav):
    from pydub import AudioSegment

    if not items:
        raise RuntimeError("No generated Hindi clips were available.")

    total_seconds = max(
        item["end"] for item in items
    ) + 1.0
    track = AudioSegment.silent(
        duration=int(total_seconds * 1000)
    )

    for item in items:
        clip_path = clips_dir / f'{item["index"]:06d}.wav'
        if not clip_path.exists():
            continue

        clip = AudioSegment.from_file(clip_path)
        position = max(0, int(item["start"] * 1000))
        track = track.overlay(clip, position=position)

    track = track.set_channels(2)
    output_wav.parent.mkdir(parents=True, exist_ok=True)
    track.export(output_wav, format="wav")

def run_dubbing(
    app,
    job_id,
    video_path,
    whisper_model,
    min_speakers,
    max_speakers,
):
    with app.app_context():
        storage = app.config["STORAGE"]
        work_dir = storage / "work" / job_id
        work_dir.mkdir(parents=True, exist_ok=True)

        try:
            update_job(
                app, job_id,
                status="processing",
                progress=3,
                stage="Extracting audio",
                message="Preparing mono 16 kHz audio for the speech models.",
            )

            source_audio = work_dir / "source.wav"
            extract_audio(video_path, source_audio)

            update_job(
                app, job_id,
                progress=8,
                stage="WhisperX transcription",
                message="Transcribing the English dialogue.",
            )

            segments = process_audio(
                source_audio,
                whisper_model,
                app.config["DEVICE"],
                app.config["COMPUTE_TYPE"],
                app.config["WHISPER_BATCH_SIZE"],
                app.config["HF_TOKEN"],
                min_speakers,
                max_speakers,
                progress=lambda p: update_job(
                    app, job_id,
                    progress=8 + int(p * 0.34),
                    stage="WhisperX + speaker analysis",
                    message=f"Speech analysis {p:.0f}%.",
                ),
            )

            if not segments:
                raise RuntimeError(
                    "No usable English speech segments were detected."
                )

            raw_json = work_dir / "segments_english.json"
            raw_json.write_text(
                json.dumps(segments, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

            update_job(
                app, job_id,
                progress=45,
                stage="Profiling speakers",
                message="Detecting speakers and estimating voice characteristics.",
            )

            profiles = build_speaker_profiles(
                segments,
                source_audio,
                work_dir,
                app.config["GENDER_MODEL"],
                app.config["GENDER_SAMPLE_SECONDS"],
            )

            speaker_map = {}
            for speaker, profile in profiles.items():
                speaker_map[speaker] = {
                    **profile,
                    "voice": choose_voice(
                        profile,
                        app.config["TTS_MALE"],
                        app.config["TTS_FEMALE"],
                    ),
                }

            speaker_json = work_dir / "speaker_map.json"
            speaker_json.write_text(
                json.dumps(speaker_map, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

            update_job(
                app, job_id,
                progress=52,
                stage="Translating to Hindi",
                message=f"Translating {len(segments)} dialogue segments.",
                speaker_map=str(speaker_json),
            )

            translated = translate_segments(
                segments,
                app.config["TRANSLATION_MODEL"],
                app.config["DEVICE"],
                app.config["SOURCE_LANG"],
                app.config["TARGET_LANG"],
                app.config["TRANSLATION_BATCH_SIZE"],
            )

            translated_json = work_dir / "translation.json"
            translated_json.write_text(
                json.dumps(translated, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

            clips_dir = work_dir / "tts"
            clips_dir.mkdir(exist_ok=True)

            ready = []
            total = len(translated)

            for i, item in enumerate(translated):
                text = item["hindi"].strip()
                if not text:
                    continue

                profile = speaker_map.get(
                    item["speaker"],
                    {
                        "voice": app.config["TTS_MALE"]
                    }
                )
                voice = profile["voice"]
                target_seconds = max(
                    0.30,
                    float(item["end"] - item["start"]),
                )

                raw_tts = clips_dir / f"{i:06d}.mp3"
                final_clip = clips_dir / f"{i:06d}.wav"

                synthesize(
                    text,
                    raw_tts,
                    voice,
                    app.config["TTS_RATE"],
                    app.config["TTS_VOLUME"],
                )

                fit_audio_to_duration(
                    raw_tts,
                    final_clip,
                    target_seconds,
                )

                ready_item = dict(item)
                ready_item["index"] = i
                ready_item["voice"] = voice
                ready.append(ready_item)

                update_job(
                    app,
                    job_id,
                    progress=60 + int(25 * (i + 1) / max(total, 1)),
                    stage="Generating Hindi voices",
                    message=f"Generating speaker-specific Hindi voice {i + 1}/{total}.",
                )

            if not ready:
                raise RuntimeError(
                    "Hindi TTS did not generate any usable segments."
                )

            update_job(
                app, job_id,
                progress=87,
                stage="Assembling timed Hindi audio",
                message="Placing each Hindi voice segment on the aligned timeline.",
            )

            dubbed_audio = work_dir / "hindi_timeline.wav"
            assemble_timeline(
                ready,
                clips_dir,
                dubbed_audio,
            )

            update_job(
                app, job_id,
                progress=93,
                stage="Creating final video",
                message="Muxing the Hindi soundtrack into the original video.",
            )

            output = storage / "output" / f"{job_id}_hindi_dubbed.mp4"
            mux_video(
                video_path,
                dubbed_audio,
                output,
            )

            update_job(
                app, job_id,
                status="completed",
                progress=100,
                stage="Completed",
                message="Hindi dubbed video is ready.",
                output=str(output),
                transcript=str(translated_json),
            )

        except Exception as exc:
            traceback.print_exc()
            update_job(
                app, job_id,
                status="failed",
                progress=0,
                stage="Failed",
                message=str(exc),
                error=traceback.format_exc(),
            )
