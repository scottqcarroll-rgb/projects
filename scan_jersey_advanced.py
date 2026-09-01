import os
import sys
import pytesseract
from PIL import Image
import cv2
import numpy as np

def preprocess_variations(image_path):
    img = cv2.imread(image_path)
    if img is None:
        return []
    # Resize to width 300 for speed while maintaining aspect ratio
    h, w = img.shape[:2]
    if w > 300:
        new_w = 300
        new_h = int(h * (new_w / w))
        img = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)
    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    variations = []
    # Original grayscale
    variations.append(('gray', gray))
    # Threshold at different values
    for thresh_val in [100, 150, 200]:
        _, thresh = cv2.threshold(gray, thresh_val, 255, cv2.THRESH_BINARY_INV)
        variations.append((f'thresh_{thresh_val}', thresh))
        _, thresh = cv2.threshold(gray, thresh_val, 255, cv2.THRESH_BINARY)
        variations.append((f'thresh_inv_{thresh_val}', thresh))
    # Adaptive threshold
    adapt = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2)
    variations.append(('adapt_inv', adapt))
    adapt = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
    variations.append(('adapt', adapt))
    return variations

def extract_text(image_path):
    variations = preprocess_variations(image_path)
    results = []
    for name, proc_img in variations:
        # Try different PSM modes
        for psm in [6, 7, 8, 13]:
            custom_config = f'--oem 3 --psm {psm} outputbase digits'
            text = pytesseract.image_to_string(proc_img, config=custom_config)
            results.append((name, psm, text.strip()))
    return results

def main():
    folder = "/tmp/soccer_pics"
    found = []
    for filename in sorted(os.listdir(folder)):
        if filename.lower().endswith('.jpg'):
            filepath = os.path.join(folder, filename)
            results = extract_text(filepath)
            # Look for the number 13 in any of the results
            for name, psm, text in results:
                if '13' in text:
                    # Check if it's a standalone 13 or part of a larger number
                    # We'll use regex to find 13 as a separate number
                    import re
                    if re.search(r'(^|[^0-9])13([^0-9]|$)', text):
                        found.append((filename, name, psm, text))
                        break  # No need to check other variations for this image
            # Progress every 20 images
            if len(found) > 0 and len(found) % 5 == 0:
                print(f"Found {len(found)} matches so far")
    print(f"\nTotal images with jersey number 13: {len(found)}")
    if found:
        print("Details:")
        for f in found:
            print(f"  File: {f[0]}, Preprocess: {f[1]}, PSM: {f[2]}, Text: '{f[3]}'")
    else:
        print("No matches found. Let's try a different approach: look for any two-digit numbers and see if we can spot 13 manually.")
        # Let's check a few images for any two-digit numbers
        count = 0
        for filename in sorted(os.listdir(folder)):
            if filename.lower().endswith('.jpg'):
                if count >= 10:
                    break
                filepath = os.path.join(folder, filename)
                results = extract_text(filepath)
                for name, psm, text in results:
                    if text.strip():
                        # Look for any two-digit numbers
                        import re
                        numbers = re.findall(r'\d{2}', text)
                        if numbers:
                            print(f"{filename} [{name} psm{psm}]: '{text}' -> numbers: {numbers}")
                            count += 1
                            break

if __name__ == "__main__":
    main()