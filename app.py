import streamlit as st
import pandas as pd
from fpdf import FPDF
import json
import google.generativeai as genai
from PIL import Image
import io

# 1. AI CONFIGURATION
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    ai_configured = True
except:
    ai_configured = False

def count_with_ai(image_buffer):
    if not ai_configured:
        return None, "API Key missing in Streamlit Secrets."
    try:
        # Initialize the latest model
        model_brain = genai.GenerativeModel("gemini-1.5-flash-latest")

        
        # Open the image from the camera buffer
        img_for_ai = Image.open(image_buffer)
        
        # Professional Auditor Prompt
        prompt = """
        You are a retail inventory auditor. Look at this shelf image.
        Identify the merchandise and count exactly how many of each item you see.
        Respond ONLY with a valid JSON array of objects.
        Format: [{"Item": "Item Name", "AI_Count": 5}]
        """
        
        response = model_brain.generate_content([prompt, img_for_ai])
        
        # Clean up the AI text to extract pure JSON
        raw_text = response.text.replace('```json', '').replace('```', '').strip()
        data = json.loads(raw_text)
        
        df = pd.DataFrame(data)
        if 'Auditor_Count' not in df.columns:
            df['Auditor_Count'] = 0
        return df, None
    except Exception as e:
        return None, f"AI Analysis Error: {str(e)}"

# 2. PDF ENGINE
def create_pdf(target, data):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, f"AUDIT REPORT: {target}", ln=1)
    pdf.set_font("Arial", size=10)
    pdf.ln(5)
    
    # Table headers for the PDF
    pdf.cell(80, 10, "Item Name", 1)
    pdf.cell(30, 10, "AI Count", 1)
    pdf.cell(30, 10, "Auditor", 1, 1)
    
    for i, r in data.iterrows():
        pdf.cell(80, 10, str(r['Item'])[:30], 1)
        pdf.cell(30, 10, str(r['AI_Count']), 1)
        pdf.cell(30, 10, str(r['Auditor_Count']), 1, 1)
        
    path = "audit_report.pdf"
    pdf.output(path)
    return path

# 3. STREAMLIT UI
st.set_page_config(page_title="Romeo Auditor", layout="centered")
st.title("🛡️ Romeo Auditor: Store 2358")

if 'status' not in st.session_state:
    st.session_state.update({'status': 'Idle', 'scan_data': None, 'img': None})

fixture = st.selectbox("Select Fixture:", ["Gondola Shelf", "Promo Bin"])
loc_id = st.text_input("Location ID:", "G1")

st.divider()
st.subheader("Status Monitor")

# --- APP LOGIC BY STATE ---

if st.session_state.status == "Recording":
    cam = st.camera_input("Take a photo of the shelf")
    if cam:
        st.session_state.img = cam
        st.success("✅ Photo captured! Press ⏹️ END to analyze.")

elif st.session_state.status == "Processing":
    with st.spinner("🧠 AI is analyzing the shelf..."):
        df, err = count_with_ai(st.session_state.img)
        if err:
            st.error(err)
            st.session_state.status = "Idle"
        else:
            st.session_state.scan_data = df
            st.session_state.status = "Result"
            st.rerun()

elif st.session_state.status == "Result":
    st.success("✅ AI Count Complete. Please verify the numbers.")
    # Allow manual correction in the table
    st.session_state.scan_data = st.data_editor(st.session_state.scan_data, use_container_width=True)
    st.info("Press 📤 UPLOAD below to generate your PDF report.")

elif st.session_state.status == "PDF":
    if st.session_state.scan_data is not None:
        report_path = create_pdf(f"{fixture}-{loc_id}", st.session_state.scan_data)
        with open(report_path, "rb") as f:
            st.download_button(
                label="📄 DOWNLOAD PDF AUDIT REPORT", 
                data=f, 
                file_name=report_path,
                mime="application/pdf"
            )
        st.balloons()
    else:
        st.warning("⚠️ No data found. Please scan first.")
        st.session_state.status = "Idle"

# --- 4-BUTTON CONTROL PANEL ---
st.divider()
st.subheader("2. Capture Controls")
c1, c2, c3, c4 = st.columns(4)

with c1:
    if st.button("🔴 START"):
        st.session_state.status = "Recording"
        st.rerun()

with c2:
    if st.button("⏹️ END"):
        st.session_state.status = "Processing"
        st.rerun()

with c3:
    if st.button("🗑️ RESET"):
        st.session_state.update({'status': 'Idle', 'scan_data': None, 'img': None})
        st.rerun()

with c4:
    if st.button("📤 UPLOAD"):
        st.session_state.status = "PDF"
        st.rerun()
