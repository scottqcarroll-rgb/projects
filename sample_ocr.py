import os
import sys
import pytesseract
from PIL import Image
import cv2
import numpy as np

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
    count = 0
    for filename in sorted(os.listdir(folder)):
        if filename.lower().endswith('.jpg'):
            filepath = os.path.join(folder, filename)
            text = extract_text(filepath)
            if text.strip():
                print(f"{filename}: '{text.strip()}'")
                count += 1
                if count >= 5:
                    break

if __name__ == "__main__":
    main()