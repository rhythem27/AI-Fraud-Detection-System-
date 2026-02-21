import streamlit as st
import requests
import os
from PIL import Image
import io

# FastAPI Backend URL
BACKEND_URL = "http://localhost:8000/upload"

st.set_page_config(page_title="Document Fraud Detector", layout="wide")

st.title("🛡️ AI Document Fraud Detection System")
st.markdown("""
Upload a document (Salary Slip, ID, Bill) to analyze for signs of tampering.
The system uses Vision Transformers to detect anomalies and EasyOCR for layout consistency.
""")

uploaded_file = st.sidebar.file_uploader("Choose a document image...", type=["jpg", "jpeg", "png", "pdf"])

if uploaded_file is not None:
    # Display original image
    image = Image.open(uploaded_file)
    st.image(image, caption='Uploaded Document', use_column_width=True)
    
    if st.button("Analyze Document"):
        with st.spinner('Analyzing... This may take a few seconds.'):
            # Send file to FastAPI
            files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
            try:
                response = requests.post(BACKEND_URL, files=files)
                if response.status_code == 200:
                    result = response.json()
                    
                    st.success("Analysis Complete!")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.subheader("Original Document")
                        st.image(image, use_column_width=True)
                        
                        st.subheader("Detection Metrics")
                        st.metric(label="Anomaly Score (ELA)", value=f"{result['anomaly_score']:.4f}")
                        fraud_status = "🔴 TAMPERED / HIGH RISK" if result['is_fraud'] else "🟢 GENUINE / LOW RISK"
                        st.write(f"**Status:** {fraud_status}")
                        
                    with col2:
                        st.subheader("ELA Tampering Heatmap")
                        # Decode base64 image
                        import base64
                        from io import BytesIO
                        heatmap_data = base64.b64decode(result['heatmap_base64'])
                        heatmap_image = Image.open(BytesIO(heatmap_data))
                        st.image(heatmap_image, caption='Error Level Analysis (ELA)', use_column_width=True)
                        st.info("ELA highlights areas with different compression levels. Bright areas in regions like text or stamps may indicate tampering.")

                    st.divider()
                    st.subheader("Extracted Text & Layout")
                    
                    # Create a searchable table for OCR results
                    import pandas as pd
                    ocr_df = pd.DataFrame(result['ocr_data'])
                    if not ocr_df.empty:
                        st.dataframe(ocr_df[['text', 'confidence']], use_container_width=True)
                    else:
                        st.write("No text detected.")
                        
                else:
                    st.error(f"Error: {response.status_code} - {response.text}")
            except Exception as e:
                st.error(f"Could not connect to backend: {e}")

else:
    st.info("Please upload a document to begin.")
