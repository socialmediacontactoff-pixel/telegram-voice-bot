import os
import re
import tempfile
import asyncio
from tts import generate_voice

SOUNDS_DIR = os.path.join(os.path.dirname(__file__), "sounds")

SOUND_TAGS = {
    "/toux":       "toux.mp3",
    "/baillement": "baillement.mp3",
    "/rire":       "rire.mp3",
    "/soupir":     "soupir.mp3",
    "/hmm":        "hmm.mp3",
    "/pause":      "pause.mp3",
}

TAG_PATTERN = re.compile(
    r'(' + '|'.join(re.escape(tag) for tag in SOUND_TAGS.keys()) + r')',
    re.IGNORECASE
)


async def mix_audio(text: str) -> str:
    parts = TAG_PATTERN.split(text)
    temp_files = []

    for part in parts:
        part_clean = part.strip()
        if not part_clean:
            continue

        if part_clean.lower() in SOUND_TAGS:
            tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
            tmp.close()
            proc = await asyncio.create_subprocess_exec(
                "ffmpeg", "-y", "-f", "lavfi", "-i",
                "anullsrc=r=44100:cl=mono", "-t", "0.5", tmp.name,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL
            )
            await proc.wait()
            temp_files.append(tmp.name)
        else:
            mp3_path = await generate_voice(part_clean)
            tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
            tmp.close()
            proc = await asyncio.create_subprocess_exec(
                "ffmpeg", "-y", "-i", mp3_path, tmp.name,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL
            )
            await proc.wait()
            os.remove(mp3_path)
            temp_files.append(tmp.name)

    list_file = tempfile.NamedTemporaryFile(mode='w', suffix=".txt", delete=False)
    for f in temp_files:
        list_file.write(f"file '{f}'\n")
    list_file.close()

    concat_wav = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    concat_wav.close()
    proc = await asyncio.create_subprocess_exec(
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", list_file.name, concat_wav.name,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL
    )
    await proc.wait()

    output = tempfile.NamedTemporaryFile(suffix=".ogg", delete=False)
    output.close()
    proc = await asyncio.create_subprocess_exec(
        "ffmpeg", "-y", "-i", concat_wav.name,
        "-c:a", "libopus", "-ar", "48000", output.name,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL
    )
    await proc.wait()

    for f in temp_files:
        try: os.remove(f)
        except: pass
    try:
        os.remove(list_file.name)
        os.remove(concat_wav.name)
    except: pass

    return output.name
    
