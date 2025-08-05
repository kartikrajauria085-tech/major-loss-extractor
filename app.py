import streamlit as st
import re
import pandas as pd
from datetime import datetime

st.title("CH/HEAD LINE Loss Extractor")

raw_text = st.text_area("Paste Raw WhatsApp Data:")

def extract_loss_data(text):
    shift_pattern = re.compile(r"(?P<date>\d{2}/\d{2}/\d{4}).*?HEAD LINE.*?\((?P<shift>[ABC])-SHIFT\)(.*?)(?=(\d{2}/\d{2}/\d{4}|$))", re.DOTALL)
    loss_pattern = re.compile(r"#?\s*Op\s*(\d+(?:[-–]\d+)?)(?:\s*\((.*?)\))?-?\s*(.*?)(?:\(|-)?\s*(\d{1,2}:\d{2})\s*[-–]\s*(\d{1,2}:\d{2})\)?-?\s*(\d+)\s*min", re.IGNORECASE)
    alt_loss_pattern = re.compile(r"#?\s*Op\s*(\d+(?:[-–]\d+)?)(?:\s*\((.*?)\))?-?\s*(.*?)\-?\s*(\d+)\s*min", re.IGNORECASE)

    records = []
    for shift_match in shift_pattern.finditer(text):
        date_str = shift_match.group("date")
        shift = shift_match.group("shift").upper()
        losses_text = shift_match.group(3)

        try:
            date_obj = datetime.strptime(date_str, "%d/%m/%Y")
            wk = date_obj.strftime("%V")
        except:
            date_obj = None
            wk = ""

        found_loss = False
        for match in loss_pattern.finditer(losses_text):
            found_loss = True
            station = match.group(1)
            machine_no = match.group(2) or ""
            issue = match.group(3).strip()
            downtime = match.group(7).strip()
            station_full = f"{station}({machine_no})" if machine_no else station

            records.append({
                "Line": "CH",
                "WK": wk,
                "Date": date_obj.strftime("%d/%m/%Y") if date_obj else "",
                "Shift": shift,
                "Station": station_full,
                "E/M": "",  # Placeholder
                "Issue/Observation": issue,
                "Down time": downtime
            })

        for match in alt_loss_pattern.finditer(losses_text):
            found_loss = True
            station = match.group(1)
            machine_no = match.group(2) or ""
            issue = match.group(3).strip()
            downtime = match.group(4).strip()
            station_full = f"{station}({machine_no})" if machine_no else station

            records.append({
                "Line": "CH",
                "WK": wk,
                "Date": date_obj.strftime("%d/%m/%Y") if date_obj else "",
                "Shift": shift,
                "Station": station_full,
                "E/M": "",
                "Issue/Observation": issue,
                "Down time": downtime
            })

        # If no losses found, still insert an empty row for this shift
        if not found_loss:
            records.append({
                "Line": "CH",
                "WK": wk,
                "Date": date_obj.strftime("%d/%m/%Y") if date_obj else "",
                "Shift": shift,
                "Station": "",
                "E/M": "",
                "Issue/Observation": "",
                "Down time": ""
            })

    return pd.DataFrame(records)

if raw_text:
    df = extract_loss_data(raw_text)
    if df.empty:
        st.error("No valid loss data found.")
    else:
        st.success("Data extracted successfully!")
        st.dataframe(df)
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("Download CSV", csv, "loss_data.csv", "text/csv")
