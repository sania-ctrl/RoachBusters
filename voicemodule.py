# export API key
# Linux/MacOs
# export ELEVENLABS_API_KEY="Insert_API_KEY"
# Windows
# set ELEVENLABS_API_KEY="Insert_API_KEY"

# INSTALL PYTHON PLAYSOUND BEFORE USING WITH THE FOLLOWING COMMAND
# pip install playsound==1.2.2

# ALSO INSTALL ELEVENLABS PACKAGE WITH THE FOLLOWING COMMANDS
# pip install elevenlabs
# npm install @elevenlabs/elevenlabs-js

# install ffmpeg 
# 


from elevenlabs import ElevenLabs #set_api_key, generate 
from elevenlabs.play import play
from pathlib import Path
import os
from playsound import playsound
os.environ["ELEVENLABS_API_KEY"] = "Insert_API_KEY"



def getVoice(filename):

    elevenlabs = ElevenLabs(

        api_key=os.getenv("ELEVENLABS_API_KEY"),
    )
    file_content = Path(filename).read_text()
  
    audio = elevenlabs.text_to_speech.convert(
        voice_id="DLsHlh26Ugcm6ELvS0qi",
        output_format="mp3_44100_128",
        model_id="eleven_multilingual_v2",
        text=file_content
    )
    with open(f"/home/rozilla/speech.mp3", "wb") as f:
        for chunk in audio:
            if chunk:
                f.write(chunk)
    
    os.system(f"mpv /home/rozilla/speech.mp3")

#getVoice("test.txt")
