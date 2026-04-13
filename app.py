import streamlit as st
import pandas as pd
from fpdf import FPDF
import time
import json
import google.generativeai as genai
from PIL import Image
import io

# ==========================================
# 1. AI VISION CONFIGURATION
# ==========================================
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    ai_configured = True
except Exception:
    ai_configured = False

def count_with_ai(image_buffer):
    """Sends the image to Gemini Vision to count merchandise."""
    if not ai_configured:
        return None, "API Key missing in Streamlit Secrets."
        
    try:
        # Using the reliable 2.0 Flash model
        model = genai.GenerativeModel('gemini-2.0-flash') 
        img_for_ai = Image.open(image_buffer)
        
        prompt = """
        You are a retail inventory auditor. Look at this shelf or bin.
        Identify the merchandise and count exactly how many of each item you see.
        Respond ONLY with a valid JSON array of objects.
        Format: [{"Item": "Item Name", "AI_Count": 5}, {"Item": "Another Item", "AI_Count": 2}]
        """
        
        response = model.generate_content([prompt, img_for_ai])
        raw_text = response.text.replace('```json', '').replace('```', '').strip()
        data = json.loads(raw_text)
        
        df = pd.DataFrame(data)
        if 'Auditor_Count' not in df.columns:
            df['Auditor_Count'] = 0 
        return df, None
        
    except Exception as e:
        return None, f"AI Analysis Error: {str(e)}"

# ==========================================
# 2. PDF GENERATOR ENGINE
# ==========================================
class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.set_text_color(0, 94, 90) 
        self.cell(0, 10, 'ROMEO AUDITOR: STORE 2358', 0, 1, 'C')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def create_pdf(target_name, scan_data):
    pdf = PDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Target: {target_name}", ln=1, align='L')
    pdf.ln(5)
    
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(60, 10, 'Item', 1)
    pdf.cell(30, 10, 'AI Count', 1)
    pdf.cell(30, 10, 'Auditor', 1)
    pdf.cell(30, 10, 'Diff', 1, 1)
    
    pdf.set_font("Arial", size=10)
    for index, row in scan_data.iterrows():
        pdf.cell(60, 10, str(row['Item'])[:25], 1)
        pdf.cell(30, 10, str(row['AI_Count']), 1)
        pdf.cell(30, 10, str(row['Auditor_Count']), 1)
        diff = int(row['AI_Count']) - int(row['Auditor_Count'])
        pdf.cell(30, 10, str(diff), 1, 1)
    
    output_path = f"Audit_Report.pdf"
    pdf.output(output_path)
    return output_path

# ==========================================
# 3. STREAMLIT UI LOGIC
# ==========================================
st.set_page_config(page_title="Romeo Auditor", layout="centered")

st.title("🛡️ Romeo Auditor: Store 2358")

if 'status' not in st.session_state:
    st.session_state.status = "Idle"
if 'scan_data' not in st.session_state:
    st.session_state.scan_data = None
if 'captured_image' not in st.session_state:
    st.session_state.captured_image = None

# TARGET SETUP
fixture_type = st.radio("Fixture Type:", ["Gondola Shelf", "Promo Bin"])
target_id = st.text_input("Location ID:", value="G2")
target_name = f"{fixture_type} - {target_id}"

# STATUS MONITOR
st.header("Status Monitor")

if st.session_state.status == "Recording":
    img_buffer = st.camera_input("Capture Merchandise")
    if img_buffer:
        st.session_state.captured_image = img_buffer
        st.success("✅ Image secured! Press (E) END to analyze.")

elif st.session_state.status == "Processing_AI":
    with st.spinner("🧠 AI is counting..."):
        df, error = count_with_ai(st.session_state.captured_image)
        if error:
            st.error(error)
            st.session_state.status = "Idle"
        else:
            st.session_state.scan_data = df
            st.session_state.status = "Stopped"
            st.rerun()

elif st.session_state.status == "Stopped":
    st.success("✅ AI Counting Complete.")
    edited_df = st.data_editor(st.session_state.scan_data)
    st.session_state.scan_data = edited_df

elif st.session_state.status == "Generating_PDF":
    pdf_path = create_pdf(target_name, st.session_state.scan_data)
    with open(pdf_path, "rb") as f:
        btn = st.download_button("📄 Download PDF Report", f, file_name=pdf_path)
        if btn:
            st.balloons()

# CAPTURE CONTROLS
st.header("2. Capture Controls")
c1, c2, c3, c4 = st.columns(4)
with c1:
    if st.button("🔴 START"):
        st.session_state.status = "Recording"
        st.rerun()
with c2:
    if st.button("⏹️ END"):
        st.session_state.status = "Processing_AI"
        st.rerun()
with c3:
    if st.button("🗑️ REPEAT"):
        st.session_state.status = "Idle"
        st.rerun()
with c4:
    if st.button("📤 UPLOAD"):
        st.session_state.status = "Generating_PDF"
        st.rerun()
        
        # Send to Gemini
        response = model.generate_content([prompt, img_for_ai])
        
        # Clean up the response
        raw_text = response.text.replace('```json', '').replace('```', '').strip()
        data = json.loads(raw_text)
        
        df = pd.DataFrame(data)
        if 'Auditor_Count' not in df.columns:
            df['Auditor_Count'] = 0 
        return df, None
        
    except Exception as e:
        return None, f"AI Analysis Error: {str(e)}"

# ==========================================
# PDF GENERATOR ENGINE
# ==========================================
class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.set_text_color(0, 94, 90) 
        self.cell(0, 10, 'ROMEO AUDITOR: STORE 2358', 0, 1, 'C')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def create_pdf(target_name, scan_type, scan_data):
    pdf = PDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Target: {target_name}", ln=1, align='L')
    pdf.ln(5)
    
    # Table Header
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(60, 10, 'Item', 1)
    pdf.cell(30, 10, 'AI Count', 1)
    pdf.cell(30, 10, 'Auditor', 1)
    pdf.cell(30, 10, 'Diff', 1, 1)
    
    pdf.set_font("Arial", size=10)
    for index, row in scan_data.iterrows():
        pdf.cell(60, 10, str(row['Item'])[:25], 1)
        pdf.cell(30, 10, str(row['AI_Count']), 1)
        pdf.cell(30, 10, str(row['Auditor_Count']), 1)
        diff = int(row['AI_Count']) - int(row['Auditor_Count'])
        pdf.cell(30, 10, str(diff), 1, 1)
    
    output_path = f"Audit_{target_name.replace(' ', '_')}.pdf"
    pdf.output(output_path)
    return output_path

# --- UI SECTION STARTS BELOW ---
        """
        
        # Pass the opened image directly to the model
        response = model.generate_content([prompt, raw_img])
        
        # Clean up response
        raw_text = response.text.replace('```json', '').replace('```', '').strip()
        data = json.loads(raw_text)
        
        df = pd.DataFrame(data)
        if 'Auditor_Count' not in df.columns:
            df['Auditor_Count'] = 0 
        return df, None
        
    except Exception as e:
        return None, f"AI Analysis Error: {str(e)}"

# ==========================================
# PDF GENERATOR ENGINE
# ==========================================
class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.set_text_color(0, 94, 90) 
        self.cell(0, 10, 'ROMEO AUDITOR: STORE 2358', 0, 1, 'C')
        self.set_font('Arial', 'I', 10)
        self.set_text_color(100, 100, 100)
        self.cell(0, 5, 'AI-Powered Inventory Verification Report', 0, 1, 'C')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def create_pdf(target_name, scan_type, scan_data):
    pdf = PDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, txt=f"Target Location: {target_name}", ln=1, align='L')
    pdf.set_font("Arial", size=10)
    pdf.cell(200, 6, txt=f"Capture Method: AI Vision Image Analysis", ln=1, align='L')
    pdf.cell(200, 6, txt="Staff on Duty: Joseph / Joy", ln=1, align='L')
    pdf.ln(10)
    
    pdf.set_font("Arial", 'B', 10)
    pdf.set_fill_color(200, 220, 255)
    pdf.cell(60, 10, 'Item Description', 1, 0, 'C', fill=True)
    pdf.cell(30, 10, 'AI Count', 1, 0, 'C', fill=True)
    pdf.cell(30, 10, 'Auditor Count', 1, 0, 'C', fill=True)
    pdf.cell(30, 10, 'Variance', 1, 1, 'C', fill=True)
    
    pdf.set_font("Arial", size=10)
    for index, row in scan_data.iterrows():
        pdf.cell(60, 10, str(row['Item'])[:25], 1, 0, 'L')
        pdf.cell(30, 10, str(row['AI_Count']), 1, 0, 'C')
        pdf.cell(30, 10, str(row['Auditor_Count']), 1, 0, 'C')
        
        variance = int(row['AI_Count']) - int(row['Auditor_Count'])
        if variance != 0:
            pdf.set_text_color(200, 0, 0)
        else:
            pdf.set_text_color(0, 150, 0)
            
        pdf.cell(30, 10, f"{'+' if variance > 0 else ''}{variance}", 1, 1, 'C')
        pdf.set_text_color(0, 0, 0) 
    
    safe_name = target_name.replace(" ", "_").replace("/", "-")
    output_path = f"{safe_name}_Dispute_Report.pdf"
    pdf.output(output_path)
    return output_path

# ==========================================
# STREAMLIT UI & LOGIC
# ==========================================
st.set_page_config(page_title="Romeo Auditor", layout="centered")

st.title("🛡️ Romeo Auditor: Store 2358")
if not ai_configured:
    st.error("⚠️ AI NOT CONFIGURED: Please add GEMINI_API_KEY to Streamlit Secrets.")

if 'status' not in st.session_state:
    st.session_state.status = "Idle"
if 'scan_data' not in st.session_state:
    st.session_state.scan_data = None
if 'captured_image' not in st.session_state:
    st.session_state.captured_image = None

# --- TARGET SETUP ---
st.header("1. Target Location Setup")
fixture_type = st.radio("Select Fixture Type:", ["Gondola Shelf (Wide Photo)", "Promo Bin / Dump Bin (Top-Down)"])

col_a, col_b = st.columns(2)
with col_a:
    fixture_id = st.text_input("Name/ID (e.g., G2, Promo-Door):", value="G2")
with col_b:
    if "Gondola" in fixture_type:
        side_id = st.selectbox("Select Side:", ["A (Front)", "B (Right)", "C (Back)", "D (Left)"])
        target_name = f"{fixture_id} - Side {side_id[0]}"
    else:
        target_name = fixture_id

st.info(f"📍 **Target:** {target_name}")

# --- STATUS MONITOR ---
st.header("Status Monitor")

if st.session_state.status == "Recording":
    st.error("📸 READY: Take a clear, well-lit photo of the merchandise.")
    img_buffer = st.camera_input("Capture Merchandise")
    
    if img_buffer:
        st.session_state.captured_image = img_buffer
        st.success("✅ Image secured! Press (E) END to begin AI Analysis.")

elif st.session_state.status == "Processing_AI":
    with st.spinner(f"🧠 Romeo AI is actively counting items on {target_name}..."):
        df, error = count_with_ai(st.session_state.captured_image)
        
        if error:
            st.error(error)
            st.session_state.status = "Idle"
        else:
            st.session_state.scan_data = df
            st.session_state.status = "Stopped"
            st.rerun()

elif st.session_state.status == "Stopped":
    st.success(f"✅ AI Counting Complete for {target_name}.")
    st.write("Input the 7-Eleven Auditor's count below to find the variance:")
    
    # Allow user to edit the Auditor Count column
    edited_df = st.data_editor(st.session_state.scan_data)
    st.session_state.scan_data = edited_df

elif st.session_state.status == "Generating_PDF":
    with st.spinner("Generating Dispute Report..."):
        pdf_path = create_pdf(target_name, "AI Photo Analysis", st.session_state.scan_data)
        with open(pdf_path, "rb") as pdf_file:
            pdf_bytes = pdf_file.read()
            
        st.success("✅ Audit Report Generated Successfully!")
        
        # --- NEW INTERACTIVE DOWNLOAD BUTTON ---
        download_clicked = st.download_button(
            label="📄 Download PDF Dispute Report", 
            data=pdf_bytes, 
            file_name=pdf_path, 
            mime="application/pdf"
        )
        
        # If the user clicks the download button, trigger this!
        if download_clicked:
            st.balloons()
            st.success("🎉 Download complete! The PDF is saved to your phone.")
            st.info("Press 🗑️ (R) REPEAT below to audit the next fixture.")
# --- CAPTURE CONTROLS ---
st.header("2. Capture Controls")
c1, c2, c3, c4 = st.columns(4)

with c1:
    if st.button("🔴 (S) START", key="start"):
        st.session_state.status = "Recording"
        st.session_state.scan_data = None
        st.session_state.captured_image = None
        st.rerun()

with c2:
    if st.button("⏹️ (E) END", key="end"):
        if st.session_state.status == "Recording" and st.session_state.captured_image is not None:
            st.session_state.status = "Processing_AI"
            st.rerun()
        else:
            st.warning("Please capture an image first.")

with c3:
    if st.button("🗑️ (R) REPEAT", key="repeat"):
        st.session_state.status = "Idle"
        st.session_state.scan_data = None
        st.session_state.captured_image = None
        st.rerun()

with c4:
    if st.button("📤 UPLOAD"):
        st.session_state.status = "Generating_PDF"
        st.rerun()
