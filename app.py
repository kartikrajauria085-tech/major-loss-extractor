import streamlit as st
import re
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="CB & CH Loss Extractor", layout="wide")
st.title("📋 CB/CH Loss Data Extractor by Shift")

raw_input = st.text_area("📥 Paste WhatsApp Loss Data:", height=400)

def extract_entries(raw_text):
    entries = []
    current_date = None
    current_shift = None
    current_line = None

    lines = raw_text.strip().split('\n')

    for line in lines:
        # 1. Extract date
        date_match = re.search(r'(\d{1,2}[/-]\d{1,2}[/-]\d{4})', line)
        if date_match:
            try:
                dt_obj = datetime.strptime(date_match.group(1).replace("-", "/"), "%d/%m/%Y")
                current_date = dt_obj.strftime("%d/%m/%Y")
            except:
                current_date = None
            continue

        # 2. Extract shift
        shift_match = re.search(r'\((A|B|C)\)', line, re.IGNORECASE)
        if shift_match:
            current_shift = shift_match.group(1).upper()
            # Check line type
            if "HEAD" in line.upper() or "CH" in line.upper():
                current_line = "CH"
            elif "BLOCK" in line.upper() or "CB" in line.upper():
                current_line = "CB"
            continue

        # 3. Check for line-only updates
        if "HEAD" in line.upper() or "CH" in line.upper():
            current_line = "CH"
        elif "BLOCK" in line.upper() or "CB" in line.upper():
            current_line = "CB"

        # 4. Extract loss entries
        loss_match = re.search(
            r'(Op\d+(?:[-/#]?\d+)?(?:\(#\d+(?:&?#\d+)?\))?)\W*[^\d\n\r]{0,10}(.*?)(?:-|–|—)?\s*(\(?\d{1,4})\s*min\)?',
            line, re.IGNORECASE
        )
        if loss_match:
            station = loss_match.group(1).strip()
            issue = loss_match.group(2).strip(" :-–—")
            downtime = loss_match.group(3).strip(" (min)").replace("(", "")
            entries.append({
                "Date": current_date or "",
                "Shift": current_shift or "",
                "Line": current_line or "",
                "Station": station,
                "Issue/Observation": issue,
                "Down time": downtime
            })

    return entries

if raw_input:
    extracted = extract_entries(raw_input)
    if extracted:
        df_all = pd.DataFrame(extracted)

        # Ensure Shift A/B/C always present, even if empty
        shifts = ['A', 'B', 'C']
        for shift in shifts:
            df_shift = df_all[df_all['Shift'] == shift]
            st.subheader(f"🔹 Shift {shift}")
            if not df_shift.empty:
                st.dataframe(df_shift, use_container_width=True)
                csv = df_shift.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label=f"📥 Download Shift {shift} CSV",
                    data=csv,
                    file_name=f"shift_{shift}_loss_data.csv",
                    mime="text/csv"
                )
            else:
                st.info(f"No data for Shift {shift}")
    else:
        st.error("❌ No valid data found. Please check the format.")
