from elevenlabs.play import play
from pathlib import Path
import os
from playsound import playsound
os.environ["ELEVENLABS_API_KEY"] = "insert_API_key"


def getVoice(filename):
    elevenlabs = ElevenLabs(
        api_key=os.getenv("ELEVENLABS_API_KEY"),
    )
    file_content = Path(filename).read_text()
    # with open("test.txt", "r", encoding="utf-8") as f:
    #     text = f.read()
    audio = elevenlabs.text_to_speech.convert(
        voice_id="DLsHlh26Ugcm6ELvS0qi",
        output_format="mp3_44100_128",
        model_id="eleven_multilingual_v2",
        text=file_content
    )

    play(audio)
    with open(f"/home/rozilla/speech.mp3", "wb") as f:
        for chunk in audio:
            if chunk:
                f.write(chunk)

    os.system(f"mpv /home/rozilla/speech.mp3")

#getVoice("test.txt")
