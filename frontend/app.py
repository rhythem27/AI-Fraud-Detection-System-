import streamlit as st
import requests
import base64
import pandas as pd
from PIL import Image
from io import BytesIO

# --- Page Configuration ---
st.set_page_config(
    page_title="AI Document Fraud Detection & KYC",
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
        padding: 1.5rem;
        border-radius: 20px;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
        margin-bottom: 2rem;
        border: 1px solid #f1f5f9;
    }
    
    .kyc-highlight {
        background-color: #f8fafc;
        border-left: 5px solid #007bff;
        padding: 1rem;
        border-radius: 0 10px 10px 0;
    }
    </style>
    """, unsafe_allow_html=True)

# --- App Header ---
st.markdown('<h1 class="header-text">🛡️ AI Document & KYC Cross-Validator</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-text">Forensic visual analysis meets NLP-powered KYC data validation.</p>', unsafe_allow_html=True)

# --- Sidebar ---
with st.sidebar:
    st.image("https://img.icons8.com/isometric/512/security-shield.png", width=100)
    st.header("Control Center")
    mode = st.radio("Select Analysis Mode", ["Single Document", "Multi-Document KYC"])
    
    st.divider()
    st.header("Backend Config")
    backend_base = st.text_input("Backend URL", value="http://localhost:8000")
    
    st.divider()
    st.header("Vision Engine")
    vision_engine = st.radio("Select Analysis Engine", ["Baseline (ELA)", "Advanced (ViT/CNN)"], index=1)
    
    st.divider()
    st.info("Supported: JPG, JPEG, PNG, PDF")
    st.caption("AI Fraud Detection System v1.3 (RAG Copilot)")

    st.divider()
    with st.expander("🤖 Analyst Copilot (RAG)", expanded=False):
        st.markdown("Ask questions about **KYC Policies** and **Fraud Protocols**.")
        
        # Chat history state
        if "messages" not in st.session_state:
            st.session_state.messages = []

        # Display chat history
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # Chat input
        if prompt := st.chat_input("Ask a policy question..."):
            # Add user message to chat history
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            # Get response from AI
            with st.chat_message("assistant"):
                with st.spinner("Consulting Rulebook..."):
                    res = call_chat_api(prompt)
                    if "error" in res:
                        full_res = f"Backend Error: {res['error']}"
                    else:
                        full_res = res['answer']
                        if res.get('sources'):
                            full_res += f"\n\n**Sources:** {', '.join(res['sources'])}"
                    
                    st.markdown(full_res)
                    st.session_state.messages.append({"role": "assistant", "content": full_res})

# --- API Integration Helper ---
def call_api(endpoint, files):
    url = f"{backend_base}{endpoint}"
    try:
        response = requests.post(url, files=files, timeout=60)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}

def call_chat_api(question):
    url = f"{backend_base}/copilot-chat"
    try:
        response = requests.post(url, json={"question": question}, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}

# --- UI Logic ---
if mode == "Single Document":
    uploaded_file = st.file_uploader("Upload document for forensic analysis", type=["jpg", "jpeg", "png", "pdf"])
    
    if uploaded_file:
        if st.button("🚀 Analyze Document", use_container_width=True):
            with st.spinner("🔍 Running Visual & NLP Checks..."):
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                result = call_api("/analyze", files)
                
                if "error" in result:
                    st.error(f"Backend Error: {result['error']}")
                else:
                    st.success("Analysis Complete!")
                    
                    # Dashboard Layout
                    m1, m2, m3 = st.columns(3)
                    label = result.get('classification', 'Unknown')
                    m1.metric("Classification", label, delta="Warning" if label != "Authentic" else "Normal", delta_color="inverse")
                    m2.metric("Fraud Score", f"{result.get('final_score', 0)}%")
                    m3.metric("Status", "⚠️ Alert" if result.get('is_fraud') else "✅ Safe")
                    
                    st.divider()
                    col_img1, col_img2 = st.columns(2)
                    with col_img1:
                        st.subheader("Original")
                        st.image(uploaded_file, use_column_width=True)
                    with col_img2:
                        if vision_engine == "Baseline (ELA)":
                            st.subheader("Tampering Map (ELA)")
                            heatmap_data = base64.b64decode(result['heatmap_base64'])
                        else:
                            st.subheader("Deep Learning Map (ViT)")
                            heatmap_data = base64.b64decode(result['dl_heatmap_base64'])
                            
                        st.image(Image.open(BytesIO(heatmap_data)), use_column_width=True, caption=f"Engine: {vision_engine}")
                    
                    # Extracted Entities
                    entities = result.get('extracted_entities')
                    if entities:
                        st.divider()
                        st.subheader("📝 Intelligent Data Extraction")
                        e1, e2, e3 = st.columns(3)
                        e1.write(f"**Name:** {entities['person_name']}")
                        e2.write(f"**Address:** {entities['address']}")
                        e3.write(f"**Date:** {entities['date']}")

                    # 4. Digital Forensics (PDF only)
                    pdf_meta = result.get('pdf_metadata')
                    if pdf_meta:
                        st.divider()
                        with st.expander("🔍 Digital Forensics & Metadata", expanded=pdf_meta.get('is_suspicious')):
                            if pdf_meta.get('is_suspicious'):
                                st.error("⚠️ **Digital Forgery Warning**: Suspicious metadata anomalies detected.")
                                for reason in pdf_meta.get('suspicious_reasons', []):
                                    st.write(f"- {reason}")
                                st.divider()
                            
                            m_col1, m_col2 = st.columns(2)
                            with m_col1:
                                st.write("**Author:**", pdf_meta.get('author'))
                                st.write("**Creator:**", pdf_meta.get('creator'))
                                st.write("**Producer:**", pdf_meta.get('producer'))
                            with m_col2:
                                st.write("**Creation Date:**", pdf_meta.get('created'))
                                st.write("**Mod Date:**", pdf_meta.get('modified'))

                    # 5. AI Explanation (Grad-CAM)
                    xai_img_64 = result.get('ai_explanation_64')
                    if xai_img_64:
                        st.divider()
                        st.subheader("🧠 AI Decision Explanation (Grad-CAM)")
                        st.info(f"The AI is **{result['final_score']}%** confident this document is tampered. The highlighted regions below indicate the specific pixels and artifacts that most strongly influenced this decision.")
                        xai_data = base64.b64decode(xai_img_64)
                        st.image(Image.open(BytesIO(xai_data)), use_column_width=True, caption="Model Activation Map (Red = High Suspicion)")

else: # Multi-Document KYC
    col_u1, col_u2 = st.columns(2)
    with col_u1:
        doc1 = st.file_uploader("Upload Document A", type=["jpg", "jpeg", "png", "pdf"], key="doc1")
    with col_u2:
        doc2 = st.file_uploader("Upload Document B", type=["jpg", "jpeg", "png", "pdf"], key="doc2")

    if doc1 and doc2:
        if st.button("🤝 Run KYC Cross-Validation", use_container_width=True):
            with st.spinner("🔄 Benchmarking Data Points across documents..."):
                # Prepare batch request
                files = [
                    ("files", (doc1.name, doc1.getvalue(), doc1.type)),
                    ("files", (doc2.name, doc2.getvalue(), doc2.type))
                ]
                batch_result = call_api("/analyze-batch", files)
                
                if "error" in batch_result:
                    st.error(f"Error: {batch_result['error']}")
                else:
                    st.balloons()
                    
                    # 1. KYC CONSISTENCY SECTION
                    kyc = batch_result['kyc_validation']
                    st.markdown("### 🧬 KYC Cross-Check Results")
                    score_color = "green" if kyc['is_valid'] else "red"
                    st.markdown(f"""
                    <div style="background-color: white; padding: 20px; border-radius: 15px; border-left: 10px solid {score_color}; shadow: 0 4px 6px rgba(0,0,0,0.1);">
                        <h2 style="margin:0; color:{score_color};">Data Consistency Score: {kyc['consistency_score']}%</h2>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if kyc['mismatches']:
                        st.warning("#### 🚩 Flagged Mismatches")
                        for m in kyc['mismatches']:
                            st.write(f"- {m}")
                    else:
                        st.success("✅ All key data points consistent between documents.")
                    
                    st.divider()
                    
                    # 2. COMPARISON TABLE
                    st.subheader("📊 Entity Comparison Table")
                    data = []
                    for i, res in enumerate(batch_result['results']):
                        ent = res['extracted_entities']
                        data.append({
                            "Document": f"Doc {chr(65+i)} ({res['filename']})",
                            "Name": ent['person_name'],
                            "Address": ent['address'],
                            "Date": ent['date'],
                            "Fraud Score": f"{res['final_score']}%"
                        })
                    st.table(pd.DataFrame(data))
                    
                    st.divider()
                    
                    # 3. VISUAL HEATMAPS
                    st.subheader("🖼️ Visual Forensic Evidence")
                    h_col1, h_col2 = st.columns(2)
                    for i, res in enumerate(batch_result['results']):
                        with [h_col1, h_col2][i]:
                            st.markdown(f"**Doc {chr(65+i)} Analysis**")
                            if vision_engine == "Baseline (ELA)":
                                h_map = base64.b64decode(res['heatmap_base64'])
                            else:
                                h_map = base64.b64decode(res['dl_heatmap_base64'])
                                
                            st.image(Image.open(BytesIO(h_map)), use_column_width=True, caption=f"{res['classification']} ({vision_engine})")
                            
                            # PDF Metadata for Batch
                            p_meta = res.get('pdf_metadata')
                            if p_meta and p_meta.get('is_suspicious'):
                                st.warning(f"🚩 Digital anomaly in {res['filename']}")
                                
                            # XAI for Batch
                            x_img = res.get('ai_explanation_64')
                            if x_img:
                                with st.expander(f"🧠 View AI Reason for Doc {chr(65+i)}"):
                                    st.image(Image.open(BytesIO(base64.b64decode(x_img))), use_column_width=True)
                                    st.caption("Grad-CAM: Highlighted regions influenced the forgery score.")

    else:
        st.info("Please upload two documents to perform a cross-validation check.")

# Feature Showcase Footer
st.markdown("---")
f1, f2, f3 = st.columns(3)
with f1:
    st.caption("🔒 **Security**: All processing is local and ephemeral.")
with f2:
    st.caption("🤖 **AI**: Uses LayoutLM + SpaCy + ResNet ELA.")
with f3:
    st.caption("✅ **Accuracy**: Fuzzy matching handles OCR typos.")
