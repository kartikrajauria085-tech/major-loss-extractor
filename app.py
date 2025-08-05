import streamlit as st
import re
import pandas as pd
from datetime import datetime
from io import BytesIO

# --- App Setup ---
st.set_page_config(page_title="CB & CH Multi-Report Extractor", layout="wide")
st.title("📋 CB & CH Major Losses Extractor (Multiple Reports)")

# --- Parse shift & date ---
def parse_shift_and_date(text):
    # CB style: DATE-15/07/2025 (B)
    date_match = re.search(r'DATE[-:\s]*([0-9]{2}/[0-9]{2}/[0-9]{4})', text, re.IGNORECASE)

    # CH style: 15/07/2025\nHEAD LINE (B-SHIFT)
    if not date_match:
        date_match = re.search(r'(^|\n)([0-9]{2}/[0-9]{2}/[0-9]{4})(?=\n)', text)

    date = ''
    if date_match:
        try:
            date = date_match.group(1).strip()
            if date.count("/") != 2:
                date = date_match.group(2).strip()
        except:
            pass

    # Shift: (B), (C-SHIFT)
    shift_match = re.search(r'\(([ABCabc])(?:-?SHIFT)?\)', text)
    shift = shift_match.group(1).upper() if shift_match else ''

    return date, shift

# --- Extract major losses from one report ---
def extract_losses(text, line_type):
    date, shift = parse_shift_and_date(text)
    try:
        wk = datetime.strptime(date, "%d/%m/%Y").isocalendar().week if date else ''
    except:
        wk = ''
    
    losses = []
    pattern = re.compile(r'(OP\d+(?:-\d+)?(?:\([^)]+\))?)\s*[-:]?\s*(.*?)(?:\(\d{1,2}:\d{2}(?:-\d{1,2}:\d{2})?\))?[-:]?\s*(\d+)\s*min', flags=re.IGNORECASE)
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

# --- Split input into multiple reports ---
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

# --- User Input ---
user_input = st.text_area("📥 Paste multiple CB + CH reports below:", height=400)

# --- Process Button ---
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

            # ✅ Format date properly
            df["Date"] = pd.to_datetime(df["Date"], format="%d/%m/%Y", errors='coerce').dt.strftime("%d/%m/%Y")

            st.success(f"✅ Extracted {len(df)} losses from {len(reports)} reports.")
            st.dataframe(df, use_container_width=True)

            # --- Excel Download ---
            buffer = BytesIO()
            df.to_excel(buffer, index=False, engine='openpyxl')
            buffer.seek(0)
            st.download_button("⬇️ Download Excel", buffer, file_name="All_Major_Losses.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        else:
            st.error("❌ No major losses found in the reports.")
