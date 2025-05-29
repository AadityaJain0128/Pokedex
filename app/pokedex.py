import json
import requests
from uuid import uuid4
import os
import time
import base64
from dotenv import load_dotenv


load_dotenv()
API_URL = os.environ.get("API_URL")
API_KEY = os.environ.get("API_KEY")

PROMPT = '''
            You have to respond as a Pokedex. Given an image of a Pokémon, identify the Pokémon and provide the following information in JSON format.
            
            Ensure to use the image to determine the Pokémon's details accurately.
            If you know the name of the Pokemon, you should give appropriate information about it in all fields.
            
            {
                "name": "Pokémon name",
                "description": "Brief description of the Pokémon (about 20-30 words)",
                "height": "Height in meters (include the unit, e.g., 1.5 m)",
                "weight": "Weight in kilograms (include the unit, e.g., 50 kg)",
                "type": ["Primary type", "Secondary type (if applicable)"],
                "evolves_from": "If applicable, name of the Pokemon which it evolves from, else NA",
                "evolves_to": "If applicable, name of the Pokemon which it evolves to, else NA"
            }
            
            If any object in the image is not identified, return only "NA" in all fields. For example :-
            {
                "name": "NA",
                "description": "NA",
                "height": "NA",
                "weight": "NA",
                "type": ["NA"],
                "evolves_from": "NA",
                "evolves_to": "NA"
            }
            Ensure all values are in string format and follow the JSON structure described above. Do not include any extra content or text formatting.
            You should keep in mind that you don't have to describe the pokemon according to what their significance was in the show. You should only describe their attributes.
        '''


def fetch_response(img_path, folder):
    with open(img_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode("utf-8")

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "messages": [
            {
                "role": "system",
                "content": PROMPT
            },
            {
                "role": "user",
                "content": [{"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}}]
            }
        ],
        "model": "meta-llama/llama-4-maverick-17b-128e-instruct",
        "temperature": 1,
        "max_completion_tokens": 1024,
        "top_p": 1,
        "stream": False,
        "response_format": {
            "type": "json_object"
        },
        "stop": None
    }

    res = requests.post(API_URL, headers=headers, json=payload)
    print(res, res.json())
    res = res.json()["choices"][0]["message"]["content"]
    
    l, r = res.find("{"), res.rfind("}") + 1
    res = json.loads(res[l:r])

    audio_path = "voices/no-content.wav"
    if res["name"].lower() != "na":
        generate_audio = requests.post("https://api.fakeyou.com/tts/inference", json={"tts_model_token": "weight_dh8zry5bgkfm0z6nv3anqa9y5", "uuid_idempotency_token": str(uuid4()), "inference_text": res["name"] + ",\n" + res["description"] + ".\n", "wait": True}).json()

        flag = True
        status = "started"
        while status != "complete_success":
            time.sleep(2)
            fetch_audio = requests.get(f"https://api.fakeyou.com/tts/job/{generate_audio['inference_job_token']}").json()
            status = fetch_audio["state"]["status"]
            if status in ["complete_failure", "dead"]:
                flag = False
                break
            print(fetch_audio)

        if flag:
            file_path = fetch_audio["state"]["maybe_public_bucket_wav_audio_path"]
            print(file_path)
            audio = requests.get("https://cdn-2.fakeyou.com" + file_path)

            audio_path = "voices/" + file_path.split("/")[-1]
            with open(os.path.join(folder, audio_path), "wb") as audio_file:
                audio_file.write(audio.content)

    return res, audio_path
