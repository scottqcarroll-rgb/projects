import os
import sys
import pytesseract
from PIL import Image
import cv2
import numpy as np

def preprocess_image(image_path):
    # Read image
    img = cv2.imread(image_path)
    if img is None:
        return None
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
    for filename in os.listdir(folder):
        if filename.lower().endswith('.jpg'):
            filepath = os.path.join(folder, filename)
            text = extract_text(filepath)
            # Look for the number 13 as a standalone number or surrounded by non-digits
            # We'll split by non-digit and check for '13'
            import re
            numbers = re.findall(r'\d+', text)
            if '13' in numbers:
                found.append(filename)
                print(f"Found '13' in {filename}: {text.strip()}")
            else:
                # Uncomment to see what text we got for debugging
                # if text.strip():
                #     print(f"No 13 in {filename}: {text.strip()}")
                pass
    print(f"\nTotal images with jersey number 13: {len(found)}")
    if found:
        print("Files:")
        for f in found:
            print(f)

if __name__ == "__main__":
    main()