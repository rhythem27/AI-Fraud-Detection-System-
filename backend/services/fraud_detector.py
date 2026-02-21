from PIL import Image, ImageChops, ImageEnhance
import os
import numpy as np
import cv2
import io
import base64

def calculate_ela(image_path: str, quality: int = 90):
    """
    Error Level Analysis (ELA) implementation.
    """
    temp_path = "temp_ela.jpg"
    original = Image.open(image_path).convert('RGB')
    
    # Save at a specific quality
    original.save(temp_path, 'JPEG', quality=quality)
    resaved = Image.open(temp_path)
    
    # Calculate difference
    ela_image = ImageChops.difference(original, resaved)
    
    # Extrapolate (enhance) the difference
    extrema = ela_image.getextrema()
    max_diff = max([ex[1] for ex in extrema])
    if max_diff == 0:
        max_diff = 1
    scale = 255.0 / max_diff
    
    ela_image = ImageEnhance.Brightness(ela_image).enhance(scale)
    
    # Calculate anomaly score (variance of the difference)
    # Higher variance often indicates non-uniform compression levels (potential tampering)
    ela_array = np.array(ela_image)
    anomaly_score = float(np.var(ela_array) / 100.0) # Normalized score
    
    # Cleanup
    if os.path.exists(temp_path):
        os.remove(temp_path)
        
    return ela_image, anomaly_score

def image_to_base64(image):
    """
    Converts a PIL image to a base64 encoded string.
    """
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return img_str
