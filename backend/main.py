import os
import uuid
import shutil
import numpy as np
import cv2
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI(title="AI Document Fraud Detection API")

# Setup CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

from services.ocr_service import ocr_service
from services.fraud_detector import calculate_ela, image_to_base64

class FraudResult(BaseModel):
    filename: str
    anomaly_score: float
    is_fraud: bool
    ocr_data: List[dict]
    heatmap_base64: str

@app.post("/upload", response_model=FraudResult)
async def upload_document(file: UploadFile = File(...)):
    # 1. Save File
    file_id = str(uuid.uuid4())
    extension = os.path.splitext(file.filename)[1].lower()
    
    # Ensure it's an image
    if extension not in ['.jpg', '.jpeg', '.png']:
        raise HTTPException(status_code=400, detail="Only JPG and PNG images are supported.")

    saved_path = os.path.join(UPLOAD_DIR, f"{file_id}{extension}")
    
    with open(saved_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    try:
        # 2. Run OCR Pipeline
        ocr_results = ocr_service.extract_text(saved_path)
        
        # 3. Run ELA Fraud Detection
        ela_image, anomaly_score = calculate_ela(saved_path)
        
        # 4. Convert Heatmap to Base64
        heatmap_base64 = image_to_base64(ela_image)
        
        # Determine fraud status based on a simple threshold for baseline
        is_fraud = anomaly_score > 0.5 
        
        return FraudResult(
            filename=file.filename,
            anomaly_score=round(anomaly_score, 4),
            is_fraud=is_fraud,
            ocr_data=ocr_results,
            heatmap_base64=heatmap_base64
        )
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Optional: Clean up saved file after processing
        # if os.path.exists(saved_path): os.remove(saved_path)
        pass

@app.get("/")
async def root():
    return {"message": "AI Document Fraud Detection API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
