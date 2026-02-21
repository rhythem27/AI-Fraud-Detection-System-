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
from services.entity_extractor import entity_extractor, ExtractedData
from services.kyc_validator import kyc_validator, ValidationResult
from services.dl_detector import dl_detector, dl_image_to_base64
from services.pdf_processor import pdf_processor, PDFMetadata
from services.rag_service import rag_service, ChatResponse

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
    dl_heatmap_base64: str
    dl_score: float
    extracted_entities: Optional[ExtractedData] = None
    pdf_metadata: Optional[PDFMetadata] = None
    ai_explanation_64: Optional[str] = None

class BatchFraudResult(BaseModel):
    results: List[FraudResult]
    kyc_validation: ValidationResult

class CopilotRequest(BaseModel):
    question: str

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
    
    if extension not in ['.jpg', '.jpeg', '.png', '.pdf']:
        raise HTTPException(status_code=400, detail="Only JPG, PNG, and PDF documents are supported.")

    saved_path = os.path.join(UPLOAD_DIR, f"{file_id}{extension}")
    with open(saved_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    try:
        # 2. PDF Handling
        pdf_metadata = None
        processing_path = saved_path
        
        if extension == '.pdf':
            pdf_metadata = pdf_processor.extract_metadata(saved_path)
            images = pdf_processor.convert_to_images(saved_path)
            if not images:
                raise HTTPException(status_code=500, detail="Failed to convert PDF to image.")
            # Use the first page for analysis
            temp_img_path = os.path.join(UPLOAD_DIR, f"{file_id}_page1.jpg")
            images[0].save(temp_img_path, "JPEG")
            processing_path = temp_img_path

        # 3. OCR and Layout Analysis
        ocr_results = ocr_service.extract_text(processing_path)
        layout_score = layout_analyzer.analyze_spatial_consistency(ocr_results)
        
        # 4. Visual Fraud Detection (ELA + DL)
        ela_image, ela_score = calculate_ela(processing_path)
        heatmap_base64 = image_to_base64(ela_image)
        
        dl_image, dl_score = dl_detector.sliding_window_inference(processing_path)
        dl_heatmap_base64 = dl_image_to_base64(dl_image)
        
        # 5. Final Scoring
        final_score, classification = calculate_final_score(ela_score, layout_score, dl_score)
        
        # 6. NLP Entity Extraction
        extracted_entities = entity_extractor.extract(ocr_results)
        
        return FraudResult(
            filename=file.filename,
            final_score=final_score,
            classification=classification,
            ela_score=round(float(ela_score), 4),
            layout_score=round(float(layout_score), 4),
            dl_score=round(float(dl_score), 4),
            is_fraud=classification != "Authentic" or (pdf_metadata.is_suspicious if pdf_metadata else False),
            ocr_data=ocr_results,
            heatmap_base64=heatmap_base64,
            dl_heatmap_base64=dl_heatmap_base64,
            extracted_entities=extracted_entities,
            pdf_metadata=pdf_metadata,
            ai_explanation_64=dl_image_to_base64(dl_detector.generate_explanation(processing_path)) if dl_score > 0.2 else None
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
    
    if extension not in ['.jpg', '.jpeg', '.png', '.pdf']:
        raise HTTPException(status_code=400, detail="Only JPG, PNG, and PDF documents are supported.")

    saved_path = os.path.join(UPLOAD_DIR, f"{file_id}{extension}")
    with open(saved_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    try:
        # 2. PDF Handling
        pdf_metadata = None
        processing_path = saved_path
        
        if extension == '.pdf':
            pdf_metadata = pdf_processor.extract_metadata(saved_path)
            images = pdf_processor.convert_to_images(saved_path)
            if not images:
                raise HTTPException(status_code=500, detail="Failed to convert PDF to image.")
            temp_img_path = os.path.join(UPLOAD_DIR, f"{file_id}_page1.jpg")
            images[0].save(temp_img_path, "JPEG")
            processing_path = temp_img_path

        # 3. OCR and Layout Analysis
        ocr_results = ocr_service.extract_text(processing_path)
        layout_score = layout_analyzer.analyze_spatial_consistency(ocr_results)
        
        # 4. Visual Fraud Detection
        ela_image, ela_score = calculate_ela(processing_path)
        heatmap_base64 = image_to_base64(ela_image)
        
        dl_image, dl_score = dl_detector.sliding_window_inference(processing_path)
        dl_heatmap_base64 = dl_image_to_base64(dl_image)
        
        # 5. Final Scoring
        final_score, classification = calculate_final_score(ela_score, layout_score, dl_score)
        
        # 6. NLP Entity Extraction
        extracted_entities = entity_extractor.extract(ocr_results)
        
        # 7. Log Scan Record to DB
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
            dl_score=round(float(dl_score), 4),
            is_fraud=classification != "Authentic" or (pdf_metadata.is_suspicious if pdf_metadata else False),
            ocr_data=ocr_results,
            heatmap_base64=heatmap_base64,
            dl_heatmap_base64=dl_heatmap_base64,
            extracted_entities=extracted_entities,
            pdf_metadata=pdf_metadata,
            ai_explanation_64=dl_image_to_base64(dl_detector.generate_explanation(processing_path)) if dl_score > 0.2 else None
        )
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Optional: Clean up saved file after processing
        # if os.path.exists(saved_path): os.remove(saved_path)
        pass

@app.post("/analyze-batch", response_model=BatchFraudResult)
async def analyze_batch(
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    """
    Multi-document batch analysis with KYC cross-validation.
    """
    if len(files) < 2:
        raise HTTPException(status_code=400, detail="At least two documents are required for KYC cross-validation.")

    results = []
    extracted_docs_data = []

    for file in files:
        # 1. Save File
        file_id = str(uuid.uuid4())
        extension = os.path.splitext(file.filename)[1].lower()
        if extension not in ['.jpg', '.jpeg', '.png', '.pdf']:
            continue

        saved_path = os.path.join(UPLOAD_DIR, f"{file_id}{extension}")
        with open(saved_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        try:
            # 2. PDF Handling
            pdf_metadata = None
            processing_path = saved_path
            
            if extension == '.pdf':
                pdf_metadata = pdf_processor.extract_metadata(saved_path)
                images = pdf_processor.convert_to_images(saved_path)
                if images:
                    temp_img_path = os.path.join(UPLOAD_DIR, f"{file_id}_page1.jpg")
                    images[0].save(temp_img_path, "JPEG")
                    processing_path = temp_img_path

            # 3. Visual Fraud Analysis
            ocr_results = ocr_service.extract_text(processing_path)
            layout_score = layout_analyzer.analyze_spatial_consistency(ocr_results)
            ela_image, ela_score = calculate_ela(processing_path)
            heatmap_base64 = image_to_base64(ela_image)
            
            # Deep Learning Visual Analysis
            dl_image, dl_score = dl_detector.sliding_window_inference(processing_path)
            dl_heatmap_base64 = dl_image_to_base64(dl_image)
            
            final_score, classification = calculate_final_score(ela_score, layout_score, dl_score)

            # 4. NLP Entity Extraction
            extracted_entities = entity_extractor.extract(ocr_results)
            extracted_docs_data.append(extracted_entities)

            results.append(FraudResult(
                filename=file.filename,
                final_score=final_score,
                classification=classification,
                ela_score=round(float(ela_score), 4),
                layout_score=round(float(layout_score), 4),
                dl_score=round(float(dl_score), 4),
                is_fraud=classification != "Authentic" or (pdf_metadata.is_suspicious if pdf_metadata else False),
                ocr_data=ocr_results,
                heatmap_base64=heatmap_base64,
                dl_heatmap_base64=dl_heatmap_base64,
                extracted_entities=extracted_entities,
                pdf_metadata=pdf_metadata,
                ai_explanation_64=dl_image_to_base64(dl_detector.generate_explanation(processing_path)) if dl_score > 0.2 else None
            ))
        except Exception as e:
            print(f"Error processing {file.filename}: {e}")
            continue

    # 4. KYC Cross-Validation (between first two valid documents)
    if len(extracted_docs_data) >= 2:
        val_result = kyc_validator.validate(extracted_docs_data[0], extracted_docs_data[1])
    else:
        val_result = ValidationResult(consistency_score=0, mismatches=["Not enough valid documents"], is_valid=False)

    return BatchFraudResult(
        results=results,
        kyc_validation=val_result
    )

@app.post("/copilot-chat", response_model=ChatResponse)
async def copilot_chat(request: CopilotRequest):
    """
    RAG-based Analyst Copilot Chat.
    """
    try:
        response = rag_service.query(request.question)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    return {"message": "AI Document Fraud Detection API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
