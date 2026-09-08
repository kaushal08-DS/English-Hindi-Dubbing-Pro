import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

def load_config(app):
    load_dotenv(BASE_DIR / ".env")

    app.config["BASE_DIR"] = BASE_DIR
    app.config["DEBUG"] = os.getenv("FLASK_DEBUG", "1") == "1"
    app.config["HOST"] = os.getenv("HOST", "127.0.0.1")
    app.config["PORT"] = int(os.getenv("PORT", "5000"))
    app.config["MAX_CONTENT_LENGTH"] = (
        int(os.getenv("MAX_CONTENT_LENGTH_MB", "4096")) * 1024 * 1024
    )

    storage = BASE_DIR / "storage"
    app.config["STORAGE"] = storage

    for name in ("uploads", "jobs", "output", "work"):
        (storage / name).mkdir(parents=True, exist_ok=True)

    app.config["HF_TOKEN"] = os.getenv("HF_TOKEN", "").strip()
    app.config["DEVICE"] = os.getenv("DEVICE", "cpu")
    app.config["COMPUTE_TYPE"] = os.getenv("COMPUTE_TYPE", "int8")
    app.config["WHISPER_MODEL"] = os.getenv("WHISPER_MODEL", "small")
    app.config["WHISPER_BATCH_SIZE"] = int(os.getenv("WHISPER_BATCH_SIZE", "4"))

    app.config["MIN_SPEAKERS"] = int(os.getenv("MIN_SPEAKERS", "2"))
    app.config["MAX_SPEAKERS"] = int(os.getenv("MAX_SPEAKERS", "8"))

    app.config["TRANSLATION_MODEL"] = os.getenv(
        "TRANSLATION_MODEL",
        "facebook/nllb-200-distilled-600M",
    )
    app.config["TRANSLATION_BATCH_SIZE"] = int(
        os.getenv("TRANSLATION_BATCH_SIZE", "4")
    )
    app.config["SOURCE_LANG"] = os.getenv("SOURCE_LANG", "eng_Latn")
    app.config["TARGET_LANG"] = os.getenv("TARGET_LANG", "hin_Deva")

    app.config["TTS_MALE"] = os.getenv("TTS_MALE", "hi-IN-MadhurNeural")
    app.config["TTS_FEMALE"] = os.getenv("TTS_FEMALE", "hi-IN-SwaraNeural")
    app.config["TTS_RATE"] = os.getenv("TTS_RATE", "+0%")
    app.config["TTS_VOLUME"] = os.getenv("TTS_VOLUME", "+0%")

    app.config["GENDER_MODEL"] = os.getenv(
        "GENDER_MODEL",
        "moorlee/gender-voice-classifier-ecapa",
    )
    app.config["GENDER_SAMPLE_SECONDS"] = float(
        os.getenv("GENDER_SAMPLE_SECONDS", "18")
    )
