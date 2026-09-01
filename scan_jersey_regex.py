import os
import sys
import pytesseract
from PIL import Image
import cv2
import numpy as np
import re

def preprocess_image(image_path):
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
    processed = preprocess_image(image_path)
    if processed is None:
        return ""
    custom_config = r'--oem 3 --psm 6 outputbase digits'
    text = pytesseract.image_to_string(processed, config=custom_config)
    return text

def main():
    folder = "/tmp/soccer_pics"
    found = []
    for filename in sorted(os.listdir(folder)):
        if filename.lower().endswith('.jpg'):
            filepath = os.path.join(folder, filename)
            text = extract_text(filepath)
            # Look for any two-digit numbers
            numbers = re.findall(r'\d{2}', text)
            if numbers:
                print(f"{filename}: {text.strip()} -> numbers: {numbers}")
                if '13' in numbers:
                    found.append(filename)
            # Also look for '13' as separate digits surrounded by non-digits
            if re.search(r'(^|[^0-9])13([^0-9]|$)', text):
                if filename not in found:
                    found.append(filename)
                    print(f"{filename}: FOUND 13 via regex: {text.strip()}")
    print(f"\nTotal images with jersey number 13: {len(found)}")
    if found:
        print("Files:")
        for f in found:
            print(f)

if __name__ == "__main__":
    main()