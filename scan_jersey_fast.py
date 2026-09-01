import os
import sys
import pytesseract
from PIL import Image
import cv2
import numpy as np
import time

def preprocess_image(image_path):
    # Read image
    img = cv2.imread(image_path)
    if img is None:
        return None
    # Resize to width 300 for speed while maintaining aspect ratio
    h, w = img.shape[:2]
    if w > 300:
        new_w = 300
        new_h = int(h * (new_w / w))
        img = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)
    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # Apply threshold to get binary image
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)
    # Optional: dilation to connect components
    kernel = np.ones((2,2), np.uint8)
    dilated = cv2.dilate(thresh, kernel, iterations=1)
    return dilated

def extract_text(image_path):
    # Preprocess
    processed = preprocess_image(image_path)
    if processed is None:
        return ""
    # Use pytesseract
    custom_config = r'--oem 3 --psm 6 outputbase digits'
    text = pytesseract.image_to_string(processed, config=custom_config)
    return text

def main():
    folder = "/tmp/soccer_pics"
    found = []
    total = 0
    start = time.time()
    for filename in sorted(os.listdir(folder)):
        if filename.lower().endswith('.jpg'):
            total += 1
            filepath = os.path.join(folder, filename)
            text = extract_text(filepath)
            # Look for the number 13 as a standalone number or surrounded by non-digits
            # We'll split by non-digit and check for '13'
            import re
            numbers = re.findall(r'\d+', text)
            if '13' in numbers:
                found.append(filename)
                print(f"Found '13' in {filename}: {text.strip()}")
            # Progress every 20 images
            if total % 20 == 0:
                elapsed = time.time() - start
                print(f"Processed {total} images, found {len(found)} matches so far, elapsed {elapsed:.1f}s")
    elapsed = time.time() - start
    print(f"\nTotal images processed: {total}")
    print(f"Total images with jersey number 13: {len(found)}")
    print(f"Time elapsed: {elapsed:.1f}s")
    if found:
        print("Files:")
        for f in found:
            print(f)

if __name__ == "__main__":
    main()