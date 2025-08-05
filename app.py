import streamlit as st
import re
import pandas as pd
from datetime import datetime
from io import BytesIO

st.set_page_config(page_title="CB/CH Major Loss Extractor", layout="wide")
st.title("📋 WhatsApp Report to Major Loss Table")

# --- Function to extract shift & date ---
def parse_shift_and_date(text):
    date_match = re.search(r'DATE[-:]*([0-9/]+)', text) or re.search(r'^([0-9/]{2,})', text)
    shift_match = re.search(r'\(([ABCabc]\-?SHIFT?)\)', text)
    date = date_match.group(1) if date_match else ''
    shift = shift_match.group(1).upper().replace("-SHIFT", "") if shift_match else ''
    return date, shift

# --- Function to extract major losses ---
def extract_losses(text, line):
    date, shift = parse_shift_and_date(text)
    losses = []
    for match in re.finditer(r'(OP\d+(?:\([^)]+\))?)\s*[-:]?\s*(.*?)(\(?\d{1,2}:\d{2}(?:-\d{1,2}:\d{2})?\)?)*[-:]?\s*(\d+)\s*min', text, flags=re.IGNORECASE):
        station = match.group(1).strip()
        issue = match.group(2).strip()
        time = int(match.group(4))
        losses.append({
            "Line": line,
            "WK": datetime.strptime(date, "%d/%m/%Y").isocalendar().week if date else '',
            "Date": date,
            "Shift": shift,
            "Station": station,
            "E/M": "",
            "Issue/Observation": issue,
            "Down time": time,
            "Impacted loss": "",
            "OLE Impacted Loss": "",
            "Activity Performed": "",
            "Attend by": "",
            "EWO Status": "",
            "Countermeasure": "",
            "Responsibility": "",
            "Target date": "",
            "Status": "",
            "Spare Required": "",
            "Stratification": "",
            "Remark": ""
        })
    return losses

# --- Text input area ---
user_input = st.text_area("📥 Paste your CB/CH Line report text below", height=400)

if st.button("🔍 Extract Major Losses"):
    if not user_input.strip():
        st.warning("Please paste some text to extract.")
    else:
        line_type = "CB" if "CB LINE" in user_input.upper() or "BLOCK" in user_input.upper() else "CH"
        data = extract_losses(user_input, line_type)
        if data:
            df = pd.DataFrame(data)
            st.success(f"✅ Extracted {len(df)} records for {line_type} line.")
            st.dataframe(df, use_container_width=True)

            # --- Download as Excel ---
            buffer = BytesIO()
            df.to_excel(buffer, index=False, engine='openpyxl')
            buffer.seek(0)
            st.download_button("⬇️ Download Excel", buffer, file_name="Major_Loss_Report.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        else:
            st.error("❌ No major losses found in the report.")
