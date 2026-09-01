import base64
import requests
import json
from PIL import Image
import io

OLLAMA_URL = "http://192.168.1.174:11434/api/chat"
MODEL = "qwen3:14b"  # Try smaller model

def encode_image(image_path, max_size=512):
    with Image.open(image_path) as img:
        # Resize if too large
        if max(img.size) > max_size:
            img.thumbnail((max_size, max_size))
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=85)
        return base64.b64encode(buffer.getvalue()).decode('utf-8')

# Test on DSC_0049 which we know has #13
b64_img = encode_image("/tmp/soccer_pics/DSC_0049.JPG", max_size=512)

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