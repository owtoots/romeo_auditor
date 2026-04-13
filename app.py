import streamlit as st
import pandas as pd
from fpdf import FPDF
import time

# ==========================================
# 1. PDF GENERATOR ENGINE
# ==========================================
class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.set_text_color(0, 94, 90) # 7-Eleven Dark Green
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
    
    # Metadata Block
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, txt=f"Target Location: {target_name}", ln=1, align='L')
    pdf.set_font("Arial", size=10)
    pdf.cell(200, 6, txt=f"Capture Method: {scan_type}", ln=1, align='L')
    pdf.cell(200, 6, txt="Staff on Duty: Joseph / Joy", ln=1, align='L')
    pdf.ln(10)
    
    # Table Header
    pdf.set_font("Arial", 'B', 10)
    pdf.set_fill_color(200, 220, 255)
    pdf.cell(60, 10, 'Item Description', 1, 0, 'C', fill=True)
    pdf.cell(30, 10, 'AI Count', 1, 0, 'C', fill=True)
    pdf.cell(30, 10, 'Auditor Count', 1, 0, 'C', fill=True)
    pdf.cell(30, 10, 'Variance', 1, 1, 'C', fill=True)
    
    # Table Rows
    pdf.set_font("Arial", size=10)
    for index, row in scan_data.iterrows():
        pdf.cell(60, 10, str(row['Item']), 1, 0, 'L')
        pdf.cell(30, 10, str(row['AI_Count']), 1, 0, 'C')
        pdf.cell(30, 10, str(row['Auditor_Count']), 1, 0, 'C')
        
        # Color Code Variances (Red for shortages/overages, Green for perfect matches)
        variance = row['AI_Count'] - row['Auditor_Count']
        if variance != 0:
            pdf.set_text_color(200, 0, 0)
        else:
            pdf.set_text_color(0, 150, 0)
            
        pdf.cell(30, 10, f"{'+' if variance > 0 else ''}{variance}", 1, 1, 'C')
        pdf.set_text_color(0, 0, 0) # Reset to black
    
    # Clean filename so it doesn't break Windows/Mac file paths
    safe_name = target_name.replace(" ", "_").replace("/", "-")
    output_path = f"{safe_name}_Dispute_Report.pdf"
    pdf.output(output_path)
    return output_path

# ==========================================
# 2. STREAMLIT UI & LOGIC
# ==========================================
st.set_page_config(page_title="Romeo Auditor", layout="centered")

st.title("🛡️ Romeo Auditor")
st.write("Dynamic capture system for Store 2358 fixtures.")

# Initialize Session States
if 'status' not in st.session_state:
    st.session_state.status = "Idle"
if 'scan_data' not in st.session_state:
    st.session_state.scan_data = None

# --- TARGET LOCATION SETUP ---
st.header("1. Target Location Setup")

fixture_type = st.radio("Select Fixture Type:", [
    "Standard Gondola (Multi-sided)", 
    "Wall Section / Chiller (Single-sided)", 
    "Promo Bin / Dump Bin (Single Shot)"
])

col_a, col_b = st.columns(2)

with col_a:
    fixture_id = st.text_input("Name/ID (e.g., G2, Wall-Chips, Promo-Door):", value="G2")

with col_b:
    if fixture_type == "Standard Gondola (Multi-sided)":
        side_id = st.selectbox("Select Side:", ["A (Front)", "B (Right)", "C (Back)", "D (Left)"])
        target_name = f"{fixture_id} - Side {side_id[0]}"
        scan_instruction = "Zigzag Video Scan"
        action_text = "Move Zigzag: Top-Right to Bottom-Right."
    elif fixture_type == "Wall Section / Chiller (Single-sided)":
        target_name = fixture_id
        scan_instruction = "Zigzag Video Scan"
        action_text = "Move Zigzag: Top-Right to Bottom-Right."
    else:
        target_name = fixture_id
        scan_instruction = "Single Photo Capture"
        action_text = "Take one clear, top-down photo of the entire bin."

st.info(f"📍 **Current Target:** {target_name} | 📷 **Method:** {scan_instruction}")


# --- STATUS MONITOR (TOP VISIBILITY) ---
st.header("Status Monitor")

if st.session_state.status == "Recording":
    if scan_instruction == "Single Photo Capture":
        st.error(f"📸 READY: {action_text} Press E when captured.")
    else:
        st.error(f"🎥 LIVE SCANNING: {action_text} Press E when finished.")

elif st.session_state.status == "Stopped":
    st.success(f"Capture complete for {target_name}. Review data before uploading.")
    st.dataframe(st.session_state.scan_data)

elif st.session_state.status == "Processing":
    with st.spinner(f"Generating Dispute Report for {target_name}..."):
        time.sleep(1) # Simulating server processing time
        
        pdf_path = create_pdf(target_name, scan_instruction, st.session_state.scan_data)
        
        with open(pdf_path, "rb") as pdf_file:
            pdf_bytes = pdf_file.read()
            
        st.success("✅ Audit Report Generated Successfully!")
        
        st.download_button(
            label="📄 Download PDF Dispute Report",
            data=pdf_bytes,
            file_name=pdf_path,
            mime="application/pdf"
        )

# --- CAPTURE CONTROLS (BOTTOM BUTTONS) ---
st.header("2. Capture Controls")
c1, c2, c3, c4 = st.columns(4)

with c1:
    if st.button("🔴 (S) START", key="btn_start"):
        st.session_state.status = "Recording"
        st.session_state.scan_data = None
        st.rerun()

with c2:
    if st.button("⏹️ (E) END", key="btn_end"):
        if st.session_state.status == "Recording":
            st.session_state.status = "Stopped"
            
            # --- MOCK DATA --- 
            # This simulates what your AI Vision model will eventually return
            mock_data = pd.DataFrame({
                "Item": ["Lays Classic 50g", "Piattos Cheese", "Coke 500ml", "Missing Item"],
                "AI_Count": [15, 20, 0, 5],
                "Auditor_Count": [12, 20, 0, 0] # Simulating an auditor missing 3 Lays and 5 "Missing Items"
            })
            st.session_state.scan_data = mock_data
            st.rerun()
        else:
            st.warning("Press S to start recording first.")

with c3:
    if st.button("🗑️ (R) REPEAT", key="btn_repeat"):
        st.session_state.status = "Idle"
        st.session_state.scan_data = None
        st.rerun()

with c4:
    if st.button("📤 (U) UPLOAD", key="btn_upload"):
        if st.session_state.status == "Stopped" and st.session_state.scan_data is not None:
            st.session_state.status = "Processing"
            st.rerun()
        else:
            st.error("You must finish a scan (Press E) before uploading.")
