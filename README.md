# AI Document Fraud Detection System

An end-to-end system to detect tampering in documents (Salary Slips, IDs, Utility Bills) using Computer Vision and OCR.

## Features
- **OCR Extraction**: Uses EasyOCR to extract text and bounding boxes from documents.
- **Tampering Detection**: Implements Error Level Analysis (ELA) to identify localized compression anomalies (potential forgeries).
- **Interactive Dashboard**: Streamlit-based UI for uploading documents and visualizing results.
- **Modular Backend**: FastAPI server with pluggable services for fraud detection and OCR.

## Tech Stack
- **Backend**: FastAPI, Python
- **Frontend**: Streamlit
- **CV/ML**: OpenCV, EasyOCR, Pillow
- **Infrastructure**: Docker, Docker Compose

## Quick Start (with Docker)
1. Clone the repository.
2. Run the system:
   ```bash
   docker-compose up --build
   ```
   (Note: The Docker containers now use **Poetry** to manage dependencies.)

## Manual Setup
To set up the project locally, it is recommended to have [Poetry](https://python-poetry.org/docs/#installation) installed.

### Backend
```bash
cd backend
poetry install
poetry run uvicorn main:app --reload
```

### Frontend
```bash
cd frontend
poetry install
poetry run streamlit run app.py
```

## How ELA Works
Error Level Analysis resaves an image at a known quality (90%) and calculates the difference with the original. Genuine images have a uniform distribution of error, whereas manipulated images show significantly higher error levels in the tampered regions.
