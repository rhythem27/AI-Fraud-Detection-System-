import streamlit as st
import requests
import base64
import pandas as pd
from PIL import Image
from io import BytesIO

# --- Page Configuration ---
st.set_page_config(
    page_title="AI Document Fraud Detection",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Custom CSS for Premium Look ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    .main {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }
    
    .stMetric {
        background-color: white;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        border: 1px solid #eef2f7;
    }
    
    .stFileUploader {
        border: 2px dashed #007bff;
        border-radius: 15px;
        padding: 20px;
    }
    
    .header-text {
        font-weight: 800;
        color: #1e293b;
        margin-bottom: 0.5rem;
    }
    
    .sub-text {
        color: #64748b;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }
    
    .result-card {
        background-color: white;
        padding: 2rem;
        border-radius: 20px;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
        margin-top: 2rem;
    }
    </style>
    """, unsafe_allow_html=True)

# --- App Header ---
st.markdown('<h1 class="header-text">🛡️ AI Document Fraud Detector</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-text">Advanced forensic analysis for document integrity using multi-modal AI and ELA technology.</p>', unsafe_allow_html=True)

# --- Sidebar ---
with st.sidebar:
    st.image("https://img.icons8.com/isometric/512/security-shield.png", width=100)
    st.header("Settings")
    api_url = st.text_input("Backend API URL", value="http://localhost:8000/analyze")
    st.divider()
    st.info("Supported formats: JPG, JPEG, PNG")
    st.markdown("---")
    st.caption("AI Document Fraud Detection System v1.0")

# --- API Integration Function ---
def analyze_document(file_bytes, filename, content_type):
    files = {"file": (filename, file_bytes, content_type)}
    try:
        response = requests.post(api_url, files=files, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        return {"error": "Could not connect to the FastAPI backend. Is it running?"}
    except requests.exceptions.HTTPError as e:
        return {"error": f"API Error ({response.status_code}): {response.text}"}
    except Exception as e:
        return {"error": f"An unexpected error occurred: {str(e)}"}

# --- File Upload Logic ---
uploaded_file = st.file_uploader("Upload document for forensic analysis", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    # Display processing button
    if st.button("🚀 Run Fraud Analysis", use_container_width=True):
        with st.spinner("🔍 Processing Document..."):
            file_bytes = uploaded_file.getvalue()
            results = analyze_document(file_bytes, uploaded_file.name, uploaded_file.type)
            
            if "error" in results:
                st.error(results["error"])
            else:
                st.balloons()
                
                # --- Result Dashboard ---
                st.markdown('<div class="result-card">', unsafe_allow_html=True)
                
                # 1. Primary Metrics
                col_m1, col_m2, col_m3 = st.columns(3)
                
                label = results.get("classification", "Unknown")
                score = results.get("final_score", 0.0)
                
                with col_m1:
                    st.metric(label="Classification Label", value=label, 
                             delta="Alert" if label != "Authentic" else "Safe",
                             delta_color="inverse" if label != "Authentic" else "normal")
                
                with col_m2:
                    st.metric(label="Fraud Confidence Score", value=f"{score}%")
                
                with col_m3:
                    is_fraud = results.get("is_fraud", False)
                    status = "⚠️ TAMPERED" if is_fraud else "✅ AUTHENTIC"
                    st.metric(label="Investigation Status", value=status)

                st.divider()

                # 2. Visual Evidence (Side-by-Side)
                st.subheader("🖼️ Forensic Evidence Visualization")
                v_col1, v_col2 = st.columns(2)
                
                with v_col1:
                    st.markdown("### Original Document")
                    st.image(uploaded_file, use_column_width=True, caption="Original Input")
                
                with v_col2:
                    st.markdown("### Tampering Heatmap (ELA)")
                    heatmap_b64 = results.get("heatmap_base64", "")
                    if heatmap_b64:
                        heatmap_bytes = base64.b64decode(heatmap_b64)
                        heatmap_img = Image.open(BytesIO(heatmap_bytes))
                        st.image(heatmap_img, use_column_width=True, caption="Error Level Analysis (ELA) Result")
                    else:
                        st.warning("Heatmap data not returned from API.")

                st.divider()

                # 3. Extracted Data & Anomalies
                st.subheader("📊 Extracted Data Analysis")
                ocr_data = results.get("ocr_data", [])
                
                if ocr_data:
                    # Parse into a clean dataframe
                    df = pd.DataFrame(ocr_data)
                    # Keep relevant columns if they exist
                    cols_to_show = [c for c in ['text', 'confidence'] if c in df.columns]
                    st.dataframe(df[cols_to_show], use_container_width=True)
                else:
                    st.info("No text data extracted from the document.")
                
                st.markdown('</div>', unsafe_allow_html=True)
else:
    # Empty State
    st.info("👆 Please upload an image file to begin document forensic analysis.")
    
    # Feature Showcase
    feat_col1, feat_col2, feat_col3 = st.columns(3)
    with feat_col1:
        st.markdown("#### 🧠 Multi-Modal AI")
        st.caption("Combines ELA and Layout Transformer models for hybrid detection.")
    with feat_col2:
        st.markdown("#### 🔍 Error Level Analysis")
        st.caption("Detects digital tampering by analyzing compression artifacts.")
    with feat_col3:
        st.markdown("#### 📄 OCR Extraction")
        st.caption("Extracts and verifies textual data for structural consistency.")
