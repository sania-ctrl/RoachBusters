RoachBusters was a project made by a team of 5 during the MakeCU-2025 Competition

# Objective
The team wanted a low price alternative to tackle the issue of Roach infestations. By targeting lifestyle causes for roach infestations, we wanted users to be able to identify which of their life style options cause roach detection, and be able to idetify any roaches that are present within the camera's range. 

# Installation
In order for these files to run, the following programs need to be downloaded in the RaspPi 4 on the virtual envirnoment:

1. ElevenLabs
```python
pip install playsound==1.2.2
pip install elevenlabs 
npm install @elevenlabs/elevenlabs-js
```
3. Google Gemini
```python
pip install -U -q "google-genai>=1.16.0
```
4. piCamera2
Ususally this module would be pre installed within the raspberry pi

# Stack
Some of the tools that we had used in our build included the Raspberry Pi 4, a Raspbeery Pi Camera, a speaker with a filter, and an RF dectecting module. All of this was integrated within our system as shown in the files. 
To run the software files, BusterRoach.py has to be run after the hardware set up connecting a button to the GPIO in the raspberry pi 4 is made along with a connection to a speaker. 

# Pictures
