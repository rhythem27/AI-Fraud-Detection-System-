import streamlit as st
import requests
import os
from PIL import Image
import io
import base64
from io import BytesIO
import pandas as pd

# FastAPI Backend URL
BACKEND_URL = "http://localhost:8000/upload"

st.set_page_config(page_title="Document Fraud Detector", layout="wide")

st.title("🛡️ AI Document Fraud Detection System")
st.markdown("""
Upload a document (Salary Slip, ID, Bill) to analyze for signs of tampering.
The system uses multi-modal analysis (ELA + Layout) to ensure document integrity.
""")

uploaded_file = st.sidebar.file_uploader("Choose a document image...", type=["jpg", "jpeg", "png"])
api_key = st.sidebar.text_input("Enter Company API Key", type="password")

if uploaded_file is not None:
    # Display original image
    image = Image.open(uploaded_file)
    
    if st.button("Analyze Document"):
        if not api_key:
            st.warning("Please enter an API Key in the sidebar.")
        else:
            with st.spinner('Analyzing... This may take a few seconds.'):
                # Send file to FastAPI with API Key header
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                headers = {"X-API-Key": api_key}
                
                try:
                    response = requests.post(BACKEND_URL, files=files, headers=headers)
                    
                    if response.status_code == 200:
                        result = response.json()
                        st.success("Analysis Complete!")
                        
                        # Classification Banner
                        if result['classification'] == "Highly Forged":
                            st.error(f"⚠️ **Result:** {result['classification']}")
                        elif result['classification'] == "Suspicious":
                            st.warning(f"🧐 **Result:** {result['classification']}")
                        else:
                            st.success(f"✅ **Result:** {result['classification']}")

                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.subheader("Final Confidence Score")
                            st.progress(result['final_score'] / 100.0)
                            st.metric(label="Fraud Confidence", value=f"{result['final_score']}%")
                            
                            st.divider()
                            st.subheader("Detailed Metrics")
                            m1, m2 = st.columns(2)
                            m1.metric(label="Pixel Anomaly (ELA)", value=f"{result['ela_score']:.3f}")
                            m2.metric(label="Layout Anomaly", value=f"{result['layout_score']:.3f}")
                            
                        with col2:
                            st.subheader("Tampering Heatmap (ELA)")
                            heatmap_data = base64.b64decode(result['heatmap_base64'])
                            heatmap_image = Image.open(BytesIO(heatmap_data))
                            st.image(heatmap_image, use_column_width=True)

                        st.divider()
                        st.subheader("Original Document & OCR Data")
                        img_col, data_col = st.columns([1, 1])
                        with img_col:
                            st.image(image, use_column_width=True, caption="Original Image")
                        with data_col:
                            ocr_df = pd.DataFrame(result['ocr_data'])
                            if not ocr_df.empty:
                                st.dataframe(ocr_df[['text', 'confidence']], use_container_width=True)
                            else:
                                st.write("No text detected.")
                            
                    elif response.status_code == 401:
                        st.error("🔒 Invalid or Missing API Key.")
                    elif response.status_code == 402:
                        st.error("💳 Insufficient Credits. Please top up your company account.")
                    else:
                        st.error(f"Error: {response.status_code} - {response.text}")
                        
                except Exception as e:
                    st.error(f"Could not connect to backend: {e}")

else:
    st.info("Please upload a document and provide your API key to begin.")
