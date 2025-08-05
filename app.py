import streamlit as st
import re
import pandas as pd
from datetime import datetime
from io import BytesIO

st.set_page_config(page_title="CB & CH Multi-Report Extractor", layout="wide")
st.title("📋 Extract Major Losses from CB & CH WhatsApp Reports")

# --- Extract shift and date ---
def parse_shift_and_date(text):
    date_match = re.search(r'DATE[-: ]*([0-9/]{2,})', text, re.IGNORECASE) or re.search(r'(^[0-9]{2}/[0-9]{2}/[0-9]{4})', text)
    shift_match = re.search(r'\(([ABCabc]\-?SHIFT?)\)', text)
    date = date_match.group(1).strip() if date_match else ''
    shift = shift_match.group(1).upper().replace("-SHIFT", "") if shift_match else ''
    return date, shift

# --- Extract major losses ---
def extract_losses(text, line_type):
    date, shift = parse_shift_and_date(text)
    wk = ''
    try:
        wk = datetime.strptime(date, "%d/%m/%Y").isocalendar().week if date else ''
    except:
        pass
    losses = []
    pattern = re.compile(r'(OP\d+(?:\([^)]+\))?)\s*[-:]?\s*(.*?)(?:\(\d{1,2}:\d{2}(?:-\d{1,2}:\d{2})?\))?[-:]?\s*(\d+)\s*min', flags=re.IGNORECASE)
    for match in pattern.finditer(text):
        station = match.group(1).strip()
        issue = match.group(2).strip()
        time = int(match.group(3).strip())
        losses.append({
            "Line": line_type,
            "WK": wk,
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

# --- Split multiple CB/CH reports ---
def split_reports(full_text):
    pattern = r'((?:CB LINE PRODUCTION REPORT|BLOCK LINE|HEAD LINE|CH LINE).*?)(?=CB LINE PRODUCTION REPORT|BLOCK LINE|HEAD LINE|CH LINE|$)'
    blocks = re.findall(pattern, full_text, re.DOTALL | re.IGNORECASE)
    results = []
    for block in blocks:
        if "CB LINE" in block.upper() or "BLOCK LINE" in block.upper():
            results.append(("CB", block.strip()))
        elif "HEAD LINE" in block.upper() or "CH LINE" in block.upper():
            results.append(("CH", block.strip()))
    return results

# --- Streamlit UI ---
user_input = st.text_area("📥 Paste multiple CB/CH reports here", height=400)

if st.button("🔍 Extract Major Losses"):
    if not user_input.strip():
        st.warning("Please paste report text.")
    else:
        all_data = []
        reports = split_reports(user_input)

        for line_type, report_text in reports:
            extracted = extract_losses(report_text, line_type)
            all_data.extend(extracted)

        if all_data:
            df = pd.DataFrame(all_data)
            st.success(f"✅ Extracted {len(df)} total losses from {len(reports)} reports.")
            st.dataframe(df, use_container_width=True)

            # Excel download
            buffer = BytesIO()
            df.to_excel(buffer, index=False, engine='openpyxl')
            buffer.seek(0)
            st.download_button("⬇️ Download Excel", buffer, file_name="All_Major_Losses.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        else:
            st.error("❌ No major losses found in the data.")
