import base64
import requests
import json
import time
from PIL import Image
import io
from pathlib import Path

OLLAMA_URL = "http://192.168.1.174:11434/api/chat"
MODEL = "qwen3.6:27b"  # GGUF format with vision

def encode_image(image_path, max_size=512):
    with Image.open(image_path) as img:
        if max(img.size) > max_size:
            img.thumbnail((max_size, max_size))
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=85)
        return base64.b64encode(buffer.getvalue()).decode('utf-8')

def analyze_image(image_path):
    b64_img = encode_image(image_path, max_size=512)
    
    payload = {
        "model": MODEL,
        "messages": [
            {
                "role": "user",
                "content": """Look at this soccer photo. Are there any players wearing jersey number 13?

Return ONLY a JSON object:
{
  "has_13": true/false,
  "confidence": "high"/"medium"/"low",
  "details": "brief description",
  "other_numbers": [list of numbers]
}""",
                "images": [b64_img]
            }
        ],
        "stream": False,
        "format": "json"
    }
    
    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=120)
        if response.status_code != 200:
            return {"has_13": False, "confidence": "low", "details": f"HTTP {response.status_code}", "other_numbers": []}
        result = response.json()
        content = result.get('message', {}).get('content', '{}')
        return json.loads(content)
    except Exception as e:
        return {"has_13": False, "confidence": "low", "details": f"Error: {e}", "other_numbers": []}

def main():
    folder = Path("/tmp/soccer_pics")
    images = sorted(folder.glob("*.JPG"))
    print(f"Found {len(images)} images")
    
    results = []
    for i, img_path in enumerate(images, 1):
        print(f"[{i}/{len(images)}] {img_path.name}...", end=" ", flush=True)
        result = analyze_image(img_path)
        result['filename'] = img_path.name
        results.append(result)
        
        if result.get('has_13'):
            print(f"✓ #13 FOUND ({result['confidence']})")
        else:
            print("✗")
        time.sleep(0.3)  # Rate limit
    
    # Save
    output = Path("/home/scott/projects/jersey13_results_vision.json")
    with open(output, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\nSaved to {output}")
    
    found = [r for r in results if r.get('has_13')]
    print(f"\n=== SUMMARY ===")
    print(f"Total: {len(results)}, With #13: {len(found)}")
    for r in found:
        print(f"  {r['filename']}: {r['details']}")

if __name__ == "__main__":
    main()