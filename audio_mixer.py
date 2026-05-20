import os
import re
import tempfile
import asyncio
from pydub import AudioSegment
from tts import generate_voice

# Dossier des sons d'ambiance
SOUNDS_DIR = os.path.join(os.path.dirname(__file__), "sounds")

# Balises disponibles → fichier son correspondant
SOUND_TAGS = {
    "/toux":      "toux.mp3",
    "/baillement":"baillement.mp3",
    "/rire":      "rire.mp3",
    "/soupir":    "soupir.mp3",
    "/hmm":       "hmm.mp3",
    "/pause":     "pause.mp3",
}

# Regex pour détecter les balises
TAG_PATTERN = re.compile(
    r'(' + '|'.join(re.escape(tag) for tag in SOUND_TAGS.keys()) + r')',
    re.IGNORECASE
)


def load_sound(tag: str) -> AudioSegment:
    """Charge un fichier son depuis le dossier sounds/."""
    filename = SOUND_TAGS.get(tag.lower())
    if not filename:
        return AudioSegment.silent(duration=300)
    path = os.path.join(SOUNDS_DIR, filename)
    if not os.path.exists(path):
        return AudioSegment.silent(duration=300)
    return AudioSegment.from_file(path)


async def mix_audio(text: str) -> str:
    """
    Parse le texte, génère le TTS pour chaque segment texte,
    insère les sons d'ambiance, et retourne un fichier .ogg final.
    """

    # Découpe le message en segments [texte, /tag, texte, /tag, ...]
    parts = TAG_PATTERN.split(text)

    segments = []

    # Génère les segments TTS en parallèle
    text_parts = [(i, p.strip()) for i, p in enumerate(parts)
                  if p.strip() and p.strip().lower() not in SOUND_TAGS]
    sound_parts = [(i, p.strip()) for i, p in enumerate(parts)
                   if p.strip().lower() in SOUND_TAGS]

    # Génération TTS pour tous les segments texte
    async def gen_tts(index, txt):
        if txt:
            path = await generate_voice(txt)
            return index, path
        return index, None

    tts_tasks = [gen_tts(i, p) for i, p in text_parts]
    tts_results = await asyncio.gather(*tts_tasks)
    tts_map = {i: path for i, path in tts_results if path}

    # Reconstruction dans l'ordre
    final_audio = AudioSegment.silent(duration=0)

    for i, part in enumerate(parts):
        part_clean = part.strip()
        if not part_clean:
            continue

        if part_clean.lower() in SOUND_TAGS:
            # C'est un son d'ambiance
            sound = load_sound(part_clean.lower())
            final_audio += sound
        elif i in tts_map:
            # C'est un segment vocal TTS
            tts_audio = AudioSegment.from_file(tts_map[i])
            final_audio += tts_audio
            os.remove(tts_map[i])  # Nettoyage

    # Export en .ogg (format vocal Telegram)
    output = tempfile.NamedTemporaryFile(suffix=".ogg", delete=False)
    output.close()

    final_audio.export(
        output.name,
        format="ogg",
        codec="libopus",
        parameters=["-ar", "48000"]
    )

    return output.name
