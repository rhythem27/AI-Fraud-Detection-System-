import os
import uuid
import shutil
import numpy as np
import cv2
from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.orm import Session

from core.database import engine, Base, get_db, SessionLocal
from core.security import get_client_company
from models.schema import ClientCompany, ScanRecord
from services.ocr_service import ocr_service
from services.fraud_detector import calculate_ela, image_to_base64
from services.layout_analyzer import layout_analyzer
from services.scoring_engine import calculate_final_score

# Create tables on startup
Base.metadata.create_all(bind=engine)

# Dependency to check/init test data
def init_db():
    db = SessionLocal()
    if db.query(ClientCompany).count() == 0:
        test_company = ClientCompany(
            name="Test Corp",
            api_key="test_key_123",
            credits_remaining=100
        )
        db.add(test_company)
        db.commit()
    db.close()

init_db()

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

class FraudResult(BaseModel):
    filename: str
    final_score: float
    classification: str
    ela_score: float
    layout_score: float
    is_fraud: bool
    ocr_data: List[dict]
    heatmap_base64: str

@app.post("/analyze", response_model=FraudResult)
async def analyze_document_simple(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Simplified analyze endpoint for local frontend testing without mandatory API keys.
    """
    # 1. Save File
    file_id = str(uuid.uuid4())
    extension = os.path.splitext(file.filename)[1].lower()
    
    if extension not in ['.jpg', '.jpeg', '.png']:
        raise HTTPException(status_code=400, detail="Only JPG and PNG images are supported.")

    saved_path = os.path.join(UPLOAD_DIR, f"{file_id}{extension}")
    with open(saved_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    try:
        # 2. OCR and Layout Analysis
        ocr_results = ocr_service.extract_text(saved_path)
        layout_score = layout_analyzer.analyze_spatial_consistency(ocr_results)
        
        # 3. ELA Fraud Detection
        ela_image, ela_score = calculate_ela(saved_path)
        heatmap_base64 = image_to_base64(ela_image)
        
        # 4. Final Scoring
        final_score, classification = calculate_final_score(ela_score, layout_score)
        
        return FraudResult(
            filename=file.filename,
            final_score=final_score,
            classification=classification,
            ela_score=round(float(ela_score), 4),
            layout_score=round(float(layout_score), 4),
            is_fraud=classification != "Authentic",
            ocr_data=ocr_results,
            heatmap_base64=heatmap_base64
        )
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/upload", response_model=FraudResult)
async def upload_document(
    file: UploadFile = File(...),
    company: ClientCompany = Depends(get_client_company),
    db: Session = Depends(get_db)
):
    # 1. Save File
    file_id = str(uuid.uuid4())
    extension = os.path.splitext(file.filename)[1].lower()
    
    if extension not in ['.jpg', '.jpeg', '.png']:
        raise HTTPException(status_code=400, detail="Only JPG and PNG images are supported.")

    saved_path = os.path.join(UPLOAD_DIR, f"{file_id}{extension}")
    with open(saved_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    try:
        # 2. OCR and Layout Analysis
        ocr_results = ocr_service.extract_text(saved_path)
        layout_score = layout_analyzer.analyze_spatial_consistency(ocr_results)
        
        # 3. ELA Fraud Detection
        ela_image, ela_score = calculate_ela(saved_path)
        heatmap_base64 = image_to_base64(ela_image)
        
        # 4. Final Scoring
        final_score, classification = calculate_final_score(ela_score, layout_score)
        
        # 5. Log Scan Record to DB
        scan_log = ScanRecord(
            confidence_score=final_score,
            classification_label=classification,
            company_id=company.id
        )
        db.add(scan_log)
        db.commit()
        
        return FraudResult(
            filename=file.filename,
            final_score=final_score,
            classification=classification,
            ela_score=round(float(ela_score), 4),
            layout_score=round(float(layout_score), 4),
            is_fraud=classification != "Authentic",
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
