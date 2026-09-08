import json
from functools import lru_cache

import joblib
import numpy as np
import soundfile as sf
import torch
from huggingface_hub import hf_hub_download
from speechbrain.inference.speaker import EncoderClassifier

@lru_cache(maxsize=2)
def load_gender_model(repo):
    scaler = joblib.load(hf_hub_download(repo, "scaler.pkl"))
    clf = joblib.load(hf_hub_download(repo, "logreg.pkl"))
    threshold = json.load(
        open(
            hf_hub_download(repo, "thresholds.json"),
            "r",
            encoding="utf-8",
        )
    )["female_optimized"]

    encoder = EncoderClassifier.from_hparams(
        source="speechbrain/spkrec-ecapa-voxceleb",
        run_opts={"device": "cpu"},
    )
    encoder.eval()
    return scaler, clf, float(threshold), encoder

def predict_gender(wav_path, repo):
    scaler, clf, threshold, encoder = load_gender_model(repo)

    arr, sr = sf.read(str(wav_path), dtype="float32")
    if arr.ndim > 1:
        arr = arr.mean(axis=1)

    if sr != 16000:
        import torchaudio
        x = torchaudio.transforms.Resample(sr, 16000)(
            torch.tensor(arr).unsqueeze(0)
        )
        arr = x.squeeze(0).numpy()

    arr = np.asarray(arr, dtype=np.float32)

    with torch.no_grad():
        emb = encoder.encode_batch(
            torch.tensor(arr).unsqueeze(0)
        ).squeeze().cpu().numpy()

    p_female = float(
        clf.predict_proba(
            scaler.transform(emb.reshape(1, -1))
        )[0, 1]
    )

    gender = "female" if p_female >= threshold else "male"
    confidence = p_female if gender == "female" else 1.0 - p_female

    return {
        "gender": gender,
        "female_probability": round(p_female, 4),
        "confidence": round(confidence, 4),
    }
