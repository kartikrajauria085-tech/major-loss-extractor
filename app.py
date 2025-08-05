import streamlit as st
import pandas as pd
import re
from io import BytesIO
from datetime import datetime

st.set_page_config(page_title="Loss Extractor", layout="wide")
st.title("🛠️ WhatsApp Loss Data Extractor")

uploaded_text = st.text_area("📋 Paste WhatsApp Report Here", height=400)

def extract_date(text):
    date_match = re.search(r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})', text)
    if date_match:
        day, month, year = date_match.groups()
        return f"{int(day):02d}/{int(month):02d}/{year}"
    return None

def extract_shift(text):
    shift_match = re.search(r'\((A|B|C)-?SHIFT\)|SHIFT[:\- ]*(A|B|C)', text, re.IGNORECASE)
    if shift_match:
        return (shift_match.group(1) or shift_match.group(2)).upper()
    return None

def extract_line_type(text):
    if re.search(r'\bCH\b|\bHEAD\b', text, re.IGNORECASE):
        return "CH"
    elif re.search(r'\bCB\b|\bBLOCK\b', text, re.IGNORECASE):
        return "CB"
    return "UNKNOWN"

def extract_losses(text, date, shift, line):
    pattern = re.compile(
        r'(OP\d+(?:-\d+)?(?:\([^)]+\))?)\s*[-:]?\s*(.*?)(?:\(\d{1,2}:\d{2}(?:-\d{1,2}:\d{2})?\))?[-:]?\s*(\d+)\s*min',
        flags=re.IGNORECASE
    )
    losses = []
    matches = pattern.finditer(text)
    for match in matches:
        station, issue, downtime = match.groups()
        losses.append({
            "Line": line,
            "Date": date,
            "Shift": shift,
            "Station": station.strip(),
            "E/M": "",  # Optional field to fill later
            "Issue/Observation": issue.strip(),
            "Down time": downtime,
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

if uploaded_text:
    blocks = re.split(r'\n\s*\n', uploaded_text.strip())  # Split by empty lines
    all_data = []
    for block in blocks:
        date = extract_date(block)
        shift = extract_shift(block)
        line = extract_line_type(block)
        if date and shift and line != "UNKNOWN":
            block_data = extract_losses(block, date, shift, line)
            all_data.extend(block_data)

    if all_data:
        df = pd.DataFrame(all_data)
        st.dataframe(df, use_container_width=True)

        # Excel download
        buffer = BytesIO()
        df.to_excel(buffer, index=False, engine='openpyxl')
        buffer.seek(0)
        st.download_button(
            label="📥 Download Extracted Losses as Excel",
            data=buffer,
            file_name="loss_report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.warning("No loss data found. Please check if format is correct.")

else:
    st.info("Paste your WhatsApp-format CB or CH report above to begin.")
