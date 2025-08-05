import streamlit as st
import re
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Loss Data Extractor", layout="wide")

st.title("📋 CB & CH WhatsApp Loss Data Extractor")

raw_input = st.text_area("Paste WhatsApp Loss Data Below:", height=400)

def extract_entries(raw_text):
    entries = []
    current_date = None
    current_shift = None
    current_line = None

    # Normalize input
    lines = raw_text.strip().split('\n')

    for line in lines:
        # Extract date
        date_match = re.search(r'(\d{1,2}[/-]\d{1,2}[/-]\d{4})', line)
        if date_match:
            date_str = date_match.group(1).replace("-", "/")
            try:
                current_date = datetime.strptime(date_str, "%d/%m/%Y").strftime("%d/%m/%Y")
            except:
                current_date = None
            continue

        # Extract shift
        shift_match = re.search(r'\((A|B|C)\)', line, re.IGNORECASE)
        if shift_match:
            current_shift = shift_match.group(1).upper()
            continue

        # Determine line type
        if "HEAD" in line.upper() or "CH" in line.upper():
            current_line = "CH"
        elif "BLOCK" in line.upper() or "CB" in line.upper():
            current_line = "CB"

        # Extract loss entries
        loss_match = re.search(
            r'(Op\d+(?:[-/#]?\d+)?(?:\(#\d+(?:&?#\d+)?\))?)\W*[^\d\n\r]{0,10}(.*?)(?:-|–|—)?\s*(\(?\d{1,4})\s*min\)?',
            line, re.IGNORECASE
        )
        if loss_match:
            station = loss_match.group(1).strip()
            issue = loss_match.group(2).strip(" :-–—")
            downtime = loss_match.group(3).strip(" (min)").replace("(", "")
            entries.append({
                "Line": current_line or "",
                "Date": current_date or "",
                "Shift": current_shift or "",
                "Station": station,
                "Issue/Observation": issue,
                "Down time": downtime
            })

    return entries

if raw_input:
    extracted = extract_entries(raw_input)
    if extracted:
        df = pd.DataFrame(extracted)
        st.success(f"✅ Extracted {len(df)} entries.")
        st.dataframe(df, use_container_width=True)
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download CSV", csv, "loss_data.csv", "text/csv")
    else:
        st.error("❌ No valid data found. Please check the input format.")
