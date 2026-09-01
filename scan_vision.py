import os
import sys
import json
import base64
import requests
import time
from pathlib import Path

# Ollama vision model endpoint
OLLAMA_URL = "http://192.168.1.174:11434/api/chat"
MODEL = "qwen3.8:27b-mlx"  # Has vision capability

# Image folder
IMAGE_FOLDER = Path("/tmp/soccer_pics")

# Prompt for vision model
PROMPT = """Look at this soccer photo carefully. Are there any players wearing a jersey with the number **13** visible?

Return ONLY a JSON object with these fields:
- "has_13": true/false
- "confidence": "high"/"medium"/"low"
- "details": brief description of what you see (jersey color, player position, any other visible numbers)
- "other_numbers": list of other jersey numbers you can see

Be thorough - check all players in the image including those on the sidelines/bench."""

def encode_image(image_path):
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode('utf-8')

def analyze_image(image_path):
    b64_img = encode_image(image_path)
    
    payload = {
        "model": MODEL,
        "messages": [
            {
                "role": "user",
                "content": PROMPT,
                "images": [b64_img]
            }
        ],
        "stream": False,
        "format": "json"
    }
    
    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=120)
        response.raise_for_status()
        result = response.json()
        content = result.get('message', {}).get('content', '{}')
        return json.loads(content)
    except Exception as e:
        return {"has_13": False, "confidence": "low", "details": f"Error: {e}", "other_numbers": []}

def main():
    images = sorted(IMAGE_FOLDER.glob("*.JPG"))
    print(f"Found {len(images)} images to analyze")
    
    results = []
    for i, img_path in enumerate(images, 1):
        print(f"[{i}/{len(images)}] Analyzing {img_path.name}...", end=" ")
        result = analyze_image(img_path)
        result['filename'] = img_path.name
        results.append(result)
        
        if result.get('has_13'):
            print(f"✓ FOUND #13 ({result['confidence']})")
        else:
            print("✗")
        
        # Small delay to not overwhelm the model
        time.sleep(0.5)
    
    # Save results
    output_file = Path("/home/scott/projects/jersey13_results.json")
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to {output_file}")
    
    # Summary
    found = [r for r in results if r.get('has_13')]
    print(f"\n=== SUMMARY ===")
    print(f"Total images: {len(results)}")
    print(f"Images with #13: {len(found)}")
    if found:
        print("\nMatches:")
        for r in found:
            print(f"  {r['filename']} - {r['confidence']} confidence - {r['details']}")

if __name__ == "__main__":
    main()