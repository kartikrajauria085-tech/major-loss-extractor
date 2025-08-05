import streamlit as st
import re
import pandas as pd
from io import BytesIO
from datetime import datetime

st.title("CB/CH Loss Data Extractor")

raw_text = st.text_area("Paste raw WhatsApp-style production reports here (CB + CH, multiple dates allowed):", height=300)

def parse_date(text_block):
    date_match = re.search(r"\b(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})\b", text_block)
    if date_match:
        day, month, year = date_match.groups()
        if len(year) == 2:
            year = '20' + year  # Convert 25 to 2025
        try:
            return datetime.strptime(f"{day}/{month}/{year}", "%d/%m/%Y").strftime("%d/%m/%Y")
        except:
            return ""
    return ""

def extract_losses(text):
    blocks = re.split(r"\n(?=.*?(CB LINE|BLOCK|CH|HEAD))", text, flags=re.IGNORECASE)
    combined_blocks = ["".join(pair) for pair in zip(blocks[1::2], blocks[2::2])]
    
    results = []

    for block in combined_blocks:
        line = "CB" if re.search(r"\b(CB LINE|BLOCK)\b", block, re.IGNORECASE) else "CH"
        date = parse_date(block)
        shift_match = re.search(r"\(([A-Ca-c])\)", block)
        shift = shift_match.group(1).upper() if shift_match else ""

        # Match stations like OP70, OP150-2, OP120(#241), etc.
        loss_entries = re.findall(
            r"(OP\d{2,3}(?:-\d)?(?:\(#?\d+(?:-\d+)?\))?)\s*[-:]?\s*(.*?)(\d{1,3})\s*min",
            block, re.IGNORECASE
        )

        for station, issue, mins in loss_entries:
            results.append({
                "Line": line,
                "Date": date,
                "Shift": shift,
                "Station": station.strip().upper(),
                "E/M": "",
                "Issue/Observation": issue.strip(),
                "Down time": int(mins),
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

    return pd.DataFrame(results)

if st.button("Extract Data"):
    if raw_text.strip():
        df = extract_losses(raw_text)
        if not df.empty:
            st.success("✅ Data extracted successfully!")
            st.dataframe(df)

            output = BytesIO()
            df.to_excel(output, index=False, engine='openpyxl')
            st.download_button(
                "📥 Download as Excel",
                output.getvalue(),
                file_name="cb_ch_loss_data.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.error("⚠️ No valid loss data found.")
    else:
        st.warning("⚠️ Please paste some raw report data first.")
