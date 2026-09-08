from functools import lru_cache
import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

@lru_cache(maxsize=2)
def load_translation_model(model_name, device):
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
    model.to(torch.device(device))
    model.eval()
    return tokenizer, model

def translate_segments(
    segments,
    model_name,
    device,
    source_lang="eng_Latn",
    target_lang="hin_Deva",
    batch_size=4,
):
    tokenizer, model = load_translation_model(model_name, device)
    tokenizer.src_lang = source_lang

    texts = [s["text"] for s in segments]
    output = []

    forced_bos = tokenizer.convert_tokens_to_ids(target_lang)

    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        inputs = tokenizer(
            batch,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=512,
        )
        inputs = {k: v.to(model.device) for k, v in inputs.items()}

        with torch.no_grad():
            generated = model.generate(
                **inputs,
                forced_bos_token_id=forced_bos,
                max_length=512,
                num_beams=4,
                length_penalty=1.0,
            )

        hi = tokenizer.batch_decode(
            generated,
            skip_special_tokens=True,
        )

        output.extend(hi)

    enriched = []
    for seg, translated in zip(segments, output):
        item = dict(seg)
        item["hindi"] = translated.strip()
        enriched.append(item)

    return enriched
