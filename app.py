import streamlit as st
import pandas as pd
from fpdf import FPDF
import import streamlit as st
import pandas as pd

# 1. APP SETUP
st.set_page_config(page_title="Romeo Auditor 2.0", layout="centered")
st.title("🛡️ Romeo Auditor: Scanner Mode")

# 2. SESSION STATE MEMORY
if 'audit_list' not in st.session_state:
    st.session_state.audit_list = []

# 3. UPLOAD THE MASTER DICTIONARY
st.header("1. Load Master Dictionary")
st.info("Upload your cleaned Store2358_Master.csv file here.")
uploaded_file = st.file_uploader("Upload Master CSV", type=["csv"])

if uploaded_file is not None:
    try:
        # Read the CSV (Forces Product Id to be text so starting zeros aren't lost!)
        master_df = pd.read_csv(uploaded_file, dtype={'Product Id': str})
        st.success(f"✅ Master DB Loaded: {len(master_df)} items ready!")
        
        st.divider()
        
        # 4. THE SCANNER INPUT ZONE
        st.header("2. Scan Merchandise")
        barcode = st.text_input("Tap here, then pull scanner trigger:", key="scanner")
        
        if barcode:
            # Look up the scanned barcode
            match = master_df[master_df['Product Id'] == barcode]
            
            if not match.empty:
                item_name = match.iloc[0]['Product']
                st.session_state.audit_list.append({"Barcode": barcode, "Item": item_name, "Count": 1})
                st.success(f"✅ Scanned: {item_name}")
            else:
                st.error(f"⚠️ Unknown Barcode: {barcode}")
                st.session_state.audit_list.append({"Barcode": barcode, "Item": "UNKNOWN ITEM", "Count": 1})
        
        # 5. LIVE AUDIT TABLE
        if st.session_state.audit_list:
            st.subheader("Current Audit Session")
            audit_df = pd.DataFrame(st.session_state.audit_list)
            
            # Group by item to sum up the quantities automatically
            summary_df = audit_df.groupby(['Barcode', 'Item']).size().reset_index(name='Total Scanned')
            st.dataframe(summary_df, use_container_width=True)
            
            if st.button("🗑️ Clear Session"):
                st.session_state.audit_list = []
                st.rerun()

    except Exception as e:
        st.error(f"Error reading CSV: {e}. Please ensure it has 'Product Id' and 'Product' columns.")json
import google.generativeai as genai
from PIL import Image

# ==========================================
# 1. AI CONFIGURATION & FALLBACK ENGINE
# ==========================================
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    ai_configured = True
except Exception:
    ai_configured = False

def count_with_ai(image_buffer):
    if not ai_configured:
        return None, "API Key missing in Streamlit Secrets."
    try:
        # THE MAGIC LINE: Forcing the absolute most stable, modern model
        model_brain = genai.GenerativeModel("gemini-1.5-flash")
        
        img_for_ai = Image.open(image_buffer)
        prompt = "Identify and count every item of merchandise. Return ONLY a JSON list: [{'Item': 'name', 'AI_Count': 1}]"
        
        response = model_brain.generate_content([prompt, img_for_ai])
        raw_text = response.text.replace('```json', '').replace('```', '').strip()
        data = json.loads(raw_text)
        
        df = pd.DataFrame(data)
        if 'Auditor_Count' not in df.columns:
            df['Auditor_Count'] = 0
        return df, None
    except Exception as e:
        return None, f"AI Analysis Error: {str(e)}"

# ==========================================
# 2. PDF ENGINE
# ==========================================
def create_pdf(target, data):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, f"AUDIT REPORT: {target}", ln=1)
    pdf.set_font("Arial", size=10)
    pdf.ln(5)
    
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

# ==========================================
# 3. STREAMLIT UI
# ==========================================
st.set_page_config(page_title="Romeo Auditor", layout="centered")
st.title("🛡️ Romeo Auditor: Store 2358")

if 'status' not in st.session_state:
    st.session_state.update({'status': 'Idle', 'scan_data': None, 'img': None})

fixture = st.selectbox("Select Fixture:", ["Gondola Shelf", "Promo Bin"])
loc_id = st.text_input("Location ID:", "G1")

st.divider()
st.subheader("Status Monitor")

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

# ==========================================
# 4. CAPTURE CONTROLS
# ==========================================
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
