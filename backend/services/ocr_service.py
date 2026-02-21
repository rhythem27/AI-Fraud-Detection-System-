import easyocr
import numpy as np
from PIL import Image

class OCRService:
    def __init__(self, languages=['en']):
        # Initialize easyocr reader (will download model on first run)
        self.reader = easyocr.Reader(languages, gpu=False)

    def extract_text(self, image_path: str):
        """
        Extracts text from image and returns a list of results with bounding boxes.
        """
        results = self.reader.readtext(image_path)
        
        structured_data = []
        for (bbox, text, prob) in results:
            # Convert numpy types to native python for JSON serialization
            bbox_list = [[float(point[0]), float(point[1])] for point in bbox]
            structured_data.append({
                "text": text,
                "confidence": float(prob),
                "bounding_box": bbox_list
            })
            
        return structured_data

# Singleton instance
ocr_service = OCRService()
