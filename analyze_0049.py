import os
import sys
import pytesseract
from PIL import Image
import cv2
import numpy as np
import re

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
            custom_config = f'--oem 3 --psm {psm}'
            text = pytesseract.image_to_string(proc_img, config=custom_config)
            results.append((name, psm, text.strip()))
    return results

def main():
    filepath = "/tmp/soccer_pics/DSC_0049.JPG"
    print(f"Analyzing: DSC_0049.JPG")
    print("=" * 60)
    results = extract_text(filepath)
    found_any = False
    for name, psm, text in results:
        if text.strip():
            print(f"[{name} psm{psm}]: '{text}'")
            found_any = True
    if not found_any:
        print("No text detected in any variation.")
    # Also try with digits-only config
    print("\n--- Digits-only mode ---")
    variations = preprocess_variations(filepath)
    for name, proc_img in variations:
        for psm in [6, 7, 8, 13]:
            custom_config = f'--oem 3 --psm {psm} outputbase digits'
            text = pytesseract.image_to_string(proc_img, config=custom_config)
            if text.strip():
                print(f"[{name} psm{psm} digits]: '{text}'")

if __name__ == "__main__":
    main()