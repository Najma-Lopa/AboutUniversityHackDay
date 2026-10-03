import os

from elevenlabs.client import ElevenLabs


def text_to_speech(text):
    """
    Convert answer text to MP3 audio.
    """

    if not text:
        return None

    key = os.getenv(
        "ELEVENLABS_API_KEY"
    )

    if not key:
        return None

    try:

        client = ElevenLabs(
            api_key=key
        )

        audio = client.text_to_speech.convert(
            text=text[:4500],
            voice_id=os.getenv(
                "ELEVENLABS_VOICE_ID",
                "JBFqnCBsd6RMkjVDRZzb"
            ),
            model_id=os.getenv(
                "ELEVENLABS_MODEL",
                "eleven_multilingual_v2"
            ),
            output_format="mp3_44100_128",
        )

        if isinstance(audio, bytes):
            return audio

        return b"".join(audio)

    except Exception:
        return None