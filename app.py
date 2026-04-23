import streamlit as st
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
        st.error(f"Error reading CSV: {e}. Please ensure it has 'Product Id' and 'Product' columns.")
