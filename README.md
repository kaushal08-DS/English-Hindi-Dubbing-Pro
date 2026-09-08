# English → Hindi AI Dubbing Pro V2

This version upgrades the basic pipeline with:

- WhisperX transcription
- word-level alignment
- pyannote speaker diarization
- automatic speaker profiles
- automatic male/female voice classification
- stable Hindi voice per speaker
- NLLB English → Hindi translation
- timing-aware TTS fitting
- speaker map + translation JSON
- Flask web UI with progress tracking

## Pipeline

English video
→ audio extraction
→ WhisperX ASR
→ word alignment
→ speaker diarization
→ speaker gender profiling
→ English → Hindi translation
→ speaker-specific Hindi TTS
→ timing correction
→ final Hindi-dubbed MP4

## Important

This is designed to be substantially better than the original one-voice pipeline, but "100% perfect" automatic dubbing is not realistic. Difficult cases include overlapping speakers, music over dialogue, very short utterances, accents, children, whispering, and ambiguous speech.

For professional results, this V2 keeps a JSON transcript/speaker map so uncertain lines can be corrected before a final export in a later UI upgrade.

## Requirements

Recommended:
- Windows 10/11
- Python 3.12
- FFmpeg in PATH
- 16 GB RAM minimum for practical long-form local processing
- NVIDIA GPU strongly recommended for 1-hour episodes

CPU mode works, but long episodes can be slow.

## 1. Create the Python environment

From the project root:

```cmd
py -3.12 -m venv venv
venv\Scripts\activate
python --version
```

The version should be Python 3.12.x.

## 2. Install PyTorch

CPU-only:

```cmd
pip install torch torchaudio
```

For an NVIDIA GPU, install a PyTorch build appropriate for your CUDA driver before installing the rest.

## 3. Install project dependencies

```cmd
pip install -r requirements.txt
```

## 4. Hugging Face setup for speaker diarization

WhisperX's diarization uses pyannote. Create a Hugging Face account and a Read token.

Accept the model terms for:

```text
pyannote/speaker-diarization-community-1
```

The model card states that access requires accepting the conditions and using a Hugging Face token. citeturn882092search0

Create `.env` from `.env.example` and set:

```env
HF_TOKEN=hf_your_token_here
```

You can also set it only for the terminal:

```cmd
set HF_TOKEN=hf_your_token_here
```

## 5. Start the website

```cmd
python run.py
```

Open:

```text
http://127.0.0.1:5000
```

## 6. Recommended first test

Use the supplied ~79 second English sample first.

Recommended settings:

```text
Whisper model: small
Min speakers: 2
Max speakers: 4
Device: cpu
```

For a machine with an NVIDIA GPU:

```env
DEVICE=cuda
COMPUTE_TYPE=float16
```

For CPU:

```env
DEVICE=cpu
COMPUTE_TYPE=int8
```

## 7. What happens

The UI progresses through:

1. Extracting audio
2. WhisperX transcription
3. Word-level alignment
4. Speaker diarization
5. Speaker gender profiling
6. English → Hindi translation
7. Speaker-specific Hindi TTS
8. Timing correction
9. Final MP4 muxing

A `speaker_map.json` and `translation.json` are also written into the job work folder.

## Speaker voices

Default mapping:

```text
male   → hi-IN-MadhurNeural
female → hi-IN-SwaraNeural
```

Other Hindi Edge TTS voices can be configured in `.env`.

The current Microsoft voice catalog includes Hindi male and female neural voices. Verify availability in your Edge TTS installation if a voice is unavailable.

## Translation

The default model is:

```text
facebook/nllb-200-distilled-600M
```

Source language:

```text
eng_Latn
```

Target language:

```text
hin_Deva
```

For even more natural dialogue, a later version can add an LLM post-editor that sees the previous/current/next speaker turns before generating the final Hindi line.

## Timing

The pipeline uses WhisperX alignment and then creates Hindi TTS clips using each original speech segment's exact start/end window.

Long TTS clips are speed-adjusted with FFmpeg `atempo` instead of simply chopping words off.

## Gender classification

The default classifier:

```text
moorlee/gender-voice-classifier-ecapa
```

uses an ECAPA-TDNN speaker embedding and a gender classifier trained/tested on English, Hindi and Tamil. Its model card reports speaker-disjoint evaluation results and also notes limitations on noisy or unusual speech. citeturn824830view0

Gender is treated as a voice characteristic for selecting a TTS voice. It is not an identity detector.

## Project structure

```text
English_Hindi_Dubbing_Pro_V2/
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── routes.py
│   └── services/
│       ├── audio.py
│       ├── dubbing.py
│       ├── ffmpeg_service.py
│       ├── gender.py
│       ├── speaker.py
│       ├── translation.py
│       ├── tts.py
│       └── whisperx_engine.py
├── static/
│   ├── app.js
│   └── styles.css
├── templates/
│   └── index.html
├── storage/
├── .env.example
├── .gitignore
├── requirements.txt
├── run.py
└── README.md
```

## Troubleshooting

### HF token error
Accept the pyannote model conditions while logged in to Hugging Face, then create a Read token and put it in `.env`.

### CUDA problems
Set:

```env
DEVICE=cpu
COMPUTE_TYPE=int8
```

first and confirm the project works.

### Edge TTS 403
Test it separately:

```cmd
edge-tts --text "नमस्ते, यह परीक्षण है।" --voice hi-IN-SwaraNeural --write-media test.mp3
```

If that works but the app fails, restart the VS Code terminal and ensure the same venv is active.

### Memory usage
For a 1-hour episode, use `small` or `medium` depending on hardware. Large models can require substantial GPU/CPU memory.

## Copyright and usage

Only upload and dub video that you have permission to process.
