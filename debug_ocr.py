import os
import sys
import pytesseract
from PIL import Image
import cv2
import numpy as np

def try_ocr(image_path):
    img = cv2.imread(image_path)
    if img is None:
        return None
    # Try original
    text_orig = pytesseract.image_to_string(img, config='--psm 6')
    # Try grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    text_gray = pytesseract.image_to_string(gray, config='--psm 6')
    # Try threshold
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)
    text_thresh = pytesseract.image_to_string(thresh, config='--psm 6')
    # Try adaptive threshold
    adapt = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2)
    text_adapt = pytesseract.image_to_string(adapt, config='--psm 6')
    return {
        'orig': text_orig.strip(),
        'gray': text_gray.strip(),
        'thresh': text_thresh.strip(),
        'adapt': text_adapt.strip()
    }

def main():
    folder = "/tmp/soccer_pics"
    count = 0
    for filename in sorted(os.listdir(folder)):
        if filename.lower().endswith('.jpg'):
            filepath = os.path.join(folder, filename)
            results = try_ocr(filepath)
            # Check if any contain a number
            for key, text in results.items():
                if any(c.isdigit() for c in text):
                    print(f"{filename} [{key}]: '{text}'")
                    count += 1
                    if count >= 10:
                        return

if __name__ == "__main__":
    main()