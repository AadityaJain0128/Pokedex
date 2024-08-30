import ollama
import json
import requests
from uuid import uuid4
import os
import time


PROMPT = '''
            You have to respond like you are a Pokedex.
            Given an image of a Pokémon, provide the following information in JSON format, if any object in the image is not identified, you can return 'Not Applicable' and all values should be in string format:
            {
                'name': 'Pokémon name',
                'description': 'Brief description of the Pokémon' (about 15-25 words),
                'health': 'Health points',
                'height': 'Height in meters' (it should always include the unit i.e. m and dont specify anything else),
                'weight': 'Weight in kilograms' (it should always include the unit i.e. kg and dont specify anything else),
                'type': ['Primary type', 'Secondary type (if applicable)']
            }
            Please respond with the above JSON structure only with proper delimeter (,), it should strictly have quotes as strings, no extra content and no text formatting.

            You have to respond as a Pokedex. Given an image of a Pokémon, identify the Pokémon and provide the following information in JSON format. If any object in the image is not identified, return 'Not Applicable'. Ensure all values are in string format and follow the exact JSON structure below. Do not include any extra content or text formatting.
        '''

PROMPT = '''
            You have to respond as a Pokedex. Given an image of a Pokémon, identify the Pokémon and provide the following information in JSON format.
            
            Ensure to use the image to determine the Pokémon's details accurately. If you cannot identify the Pokémon, return 'Not Applicable' in the respective fields.
            If you know the name of the Pokemon, you should give appropriate information about it in all fields.
            {
                'name': 'Pokémon name',
                'description': 'Brief description of the Pokémon (about 15-25 words)',
                'health': 'Health points',
                'height': 'Height in meters (include the unit, e.g., 1.5 m)',
                'weight': 'Weight in kilograms (include the unit, e.g., 50 kg)',
                'type': ['Primary type', 'Secondary type (if applicable)']
            }

            For example, if the Pokémon is Pikachu:
            {
                'name': 'Pikachu',
                'description': 'Electric-type Pokémon known for its yellow fur and ability to generate electricity.',
                'health': '35',
                'height': '0.4 m',
                'weight': '6 kg',
                'type': ['Electric']
            }
            
            If any object in the image is not identified, return 'Not Applicable'. Ensure all values are in string format and follow the exact JSON structure below. Do not include any extra content or text formatting.
        '''


def fetch_response(img_path, folder):
    res = ollama.generate(model="llava:13b", prompt=PROMPT, images=[img_path])["response"]
    l = res.find("{")
    r = res.rfind("}") + 1
    res = res[l : r]
    print(res)
    res = json.loads(res)
    

    audio_path = "voices/no-content.wav"
    if res["name"] != "Not Applicable":
        generate_audio = requests.post("https://api.fakeyou.com/tts/inference", json={"tts_model_token": "weight_dh8zry5bgkfm0z6nv3anqa9y5", "uuid_idempotency_token": str(uuid4()), "inference_text": res["name"] + ",\n" + res["description"] + ".\n", "wait": True}).json()

        flag = True
        status = "started"
        while status != "complete_success":
            time.sleep(3)
            fetch_audio = requests.get(f"https://api.fakeyou.com/tts/job/{generate_audio['inference_job_token']}").json()
            status = fetch_audio["state"]["status"]
            if status in ["complete_failure", "dead"]:
                flag = False
                break
            print(fetch_audio)

        if flag:
            file_path = fetch_audio["state"]["maybe_public_bucket_wav_audio_path"]
            print(file_path)
            audio = requests.get("https://storage.googleapis.com/vocodes-public" + file_path)

            audio_path = "voices/" + file_path.split("/")[-1]
            with open(os.path.join(folder, audio_path), "wb") as audio_file:
                audio_file.write(audio.content)

    return res, audio_path