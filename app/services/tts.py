import asyncio
from pathlib import Path
import edge_tts

async def _speak(text, output_file, voice, rate, volume):
    communicate = edge_tts.Communicate(
        text=text,
        voice=voice,
        rate=rate,
        volume=volume,
    )
    await communicate.save(str(output_file))

def synthesize(text, output_file: Path, voice, rate="+0%", volume="+0%"):
    output_file.parent.mkdir(parents=True, exist_ok=True)
    asyncio.run(
        _speak(
            text,
            output_file,
            voice,
            rate,
            volume,
        )
    )
