import base64
import requests
import json

OLLAMA_URL = "http://192.168.1.174:11434/api/chat"
MODEL = "qwen3.8:27b-mlx"

def encode_image(image_path):
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode('utf-8')

# Test on DSC_0049 which we know has #13
b64_img = encode_image("/tmp/soccer_pics/DSC_0049.JPG")

payload = {
    "model": MODEL,
    "messages": [
        {
            "role": "user",
            "content": "Does this image show any soccer player wearing jersey number 13? Answer yes or no and describe what you see.",
            "images": [b64_img]
        }
    ],
    "stream": False
}

response = requests.post(OLLAMA_URL, json=payload, timeout=120)
print("Status:", response.status_code)
print("Response:", json.dumps(response.json(), indent=2))