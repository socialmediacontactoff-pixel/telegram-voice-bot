import os
import httpx
import tempfile

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
VOICE_NAME = "Marine"


async def get_voice_id() -> str:
    """Récupère l'ID de la voix Marine depuis ElevenLabs."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://api.elevenlabs.io/v1/voices",
            headers={"xi-api-key": ELEVENLABS_API_KEY}
        )
        response.raise_for_status()
        voices = response.json().get("voices", [])
        for voice in voices:
            if voice["name"].lower() == VOICE_NAME.lower():
                return voice["voice_id"]
        raise ValueError(f"Voix '{VOICE_NAME}' introuvable dans votre compte ElevenLabs.")


async def generate_voice(text: str) -> str:
    """
    Génère un fichier audio MP3 depuis le texte via ElevenLabs.
    Retourne le chemin du fichier temporaire.
    """
    voice_id = await get_voice_id()

    payload = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75,
            "style": 0.3,
            "use_speaker_boost": True
        }
    }

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
            headers={
                "xi-api-key": ELEVENLABS_API_KEY,
                "Content-Type": "application/json"
            },
            json=payload
        )
        response.raise_for_status()

        # Sauvegarde dans un fichier temporaire
        tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
        tmp.write(response.content)
        tmp.close()
        return tmp.name
