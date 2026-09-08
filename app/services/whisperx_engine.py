from functools import lru_cache
import torch
import whisperx

@lru_cache(maxsize=4)
def load_asr(model_name, device, compute_type):
    return whisperx.load_model(
        model_name,
        device,
        compute_type=compute_type,
        language="en",
        vad_method="silero",
    )

def process_audio(
    audio_path,
    model_name,
    device,
    compute_type,
    batch_size,
    hf_token,
    min_speakers,
    max_speakers,
    progress=None,
):
    if progress:
        progress(0.0)

    model = load_asr(model_name, device, compute_type)
    audio = whisperx.load_audio(str(audio_path))

    if progress:
        progress(10.0)

    result = model.transcribe(
        audio,
        batch_size=batch_size,
        language="en",
    )

    # Alignment gives much more useful timing than raw ASR segment boundaries.
    if progress:
        progress(25.0)

    align_model, metadata = whisperx.load_align_model(
        language_code=result["language"],
        device=device,
    )

    aligned = whisperx.align(
        result["segments"],
        align_model,
        metadata,
        audio,
        device,
        return_char_alignments=False,
    )

    if progress:
        progress(45.0)

    if not hf_token:
        raise RuntimeError(
            "HF_TOKEN is required for speaker diarization. "
            "Add it to your .env file."
        )

    diarize_model = whisperx.DiarizationPipeline(
        model_name="pyannote/speaker-diarization-community-1",
        token=hf_token,
        device=device,
    )

    diarized = diarize_model(
        str(audio_path),
        min_speakers=min_speakers,
        max_speakers=max_speakers,
    )

    if progress:
        progress(80.0)

    final = whisperx.assign_word_speakers(
        diarized,
        aligned,
        fill_nearest=True,
    )

    if progress:
        progress(100.0)

    segments = []
    for seg in final.get("segments", []):
        start = float(seg.get("start", 0.0))
        end = float(seg.get("end", start))
        text = (seg.get("text") or "").strip()
        speaker = seg.get("speaker") or "SPEAKER_UNKNOWN"
        if text and end > start:
            segments.append({
                "start": start,
                "end": end,
                "speaker": speaker,
                "text": text,
                "words": seg.get("words", []),
            })

    return segments
