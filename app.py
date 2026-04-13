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
        # 1. Initialize the model inside the function to avoid 'str' errors
        model_brain = genai.GenerativeModel("gemini-3-flash")
        
        # 2. Open the image
        img_for_ai = Image.open(image_buffer)
        
        # 3. Create the prompt
        prompt = "Identify and count every item of merchandise. Return ONLY a JSON list: [{'Item': 'name', 'AI_Count': 1}]"
        
        # 4. Generate content using the new variable name to avoid confusion
        response = model_brain.generate_content([prompt, img_for_ai])
        
        # 5. Process the JSON
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
    for i, r in data.iterrows():
        pdf.cell(0, 10, f"{r['Item']}: AI={r['AI_Count']} | Auditor={r['Auditor_Count']}", ln=1)
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

# --- APP STATES ---
if st.session_state.status == "Recording":
    cam = st.camera_input("Take a photo of the shelf")
    if cam:
        st.session_state.img = cam
        st.success("Photo captured! Press ⏹️ END to analyze.")

elif st.session_state.status == "Processing":
    with st.spinner("AI is counting items..."):
        df, err = count_with_ai(st.session_state.img)
        if err:
            st.error(err)
            st.session_state.status = "Idle"
        else:
            st.session_state.scan_data = df
            st.session_state.status = "Result"
        st.rerun()

elif st.session_state.status == "Result":
    st.success("✅ Counting Finished")
    st.session_state.scan_data = st.data_editor(st.session_state.scan_data)
    
    if st.button("📤 Generate & Download PDF"):
        report_path = create_pdf(f"{fixture}-{loc_id}", st.session_state.scan_data)
        with open(report_path, "rb") as f:
            st.download_button("Click here to Download", f, file_name=report_path)
            st.balloons()

# --- CONTROLS ---
st.divider()
c1, c2, c3 = st.columns(3)
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
