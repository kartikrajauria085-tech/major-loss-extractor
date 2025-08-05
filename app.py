import streamlit as st
import re
import pandas as pd
from io import BytesIO
from datetime import datetime

st.title("CB/CH Loss Data Extractor")

# Input field
raw_text = st.text_area("Paste your full WhatsApp-style raw data here (CB/CH multiple dates allowed):", height=300)

def extract_data(text):
    pattern = re.compile(
        r"(CB|CH)[\s\S]*?(?=CB|CH|$)", re.IGNORECASE)
    entries = []

    for block in pattern.findall(text + "\nCB"):
        line_match = re.search(r"\b(CB|BLOCK|CH|HEAD)\b", block, re.IGNORECASE)
        date_match = re.search(r"(\d{1,2})[/-](\d{1,2})[/-](\d{4})", block)
        shift_match = re.search(r"\(([A-Ca-c])\)", block)
        loss_lines = re.findall(
            r"(OP\d{2,3}(?:-\d)?(?:\(#?\d+[-&]?\d*\))?)\s*[-:]?\s*(.*?)(\d{1,3})\s*min", block, re.IGNORECASE)

        if line_match and date_match and shift_match:
            line = line_match.group(1).upper()
            raw_date = f"{date_match.group(1)}/{date_match.group(2)}/{date_match.group(3)}"
            try:
                date = datetime.strptime(raw_date, "%d/%m/%Y").strftime("%d/%m/%Y")
            except:
                date = None
            shift = shift_match.group(1).upper()

            for match in loss_lines:
                station = match[0].strip().upper()
                issue = match[1].strip()
                downtime = int(match[2])
                entries.append({
                    "Line": line,
                    "Date": date,
                    "Shift": shift,
                    "Station": station,
                    "E/M": "",  # Can be filled manually later
                    "Issue/Observation": issue,
                    "Down time": downtime,
                    "Impacted loss": "",  # To be filled later
                    "OLE Impacted Loss": "",  # Optional
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
    return pd.DataFrame(entries)

if st.button("Extract Data"):
    if raw_text:
        df = extract_data(raw_text)
        if not df.empty:
            st.success("Extraction completed!")
            st.dataframe(df)

            buffer = BytesIO()
            df.to_excel(buffer, index=False, engine='openpyxl')
            st.download_button("Download Excel", buffer.getvalue(), "loss_data.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        else:
            st.error("No valid data found.")
    else:
        st.warning("Please paste some data.")
