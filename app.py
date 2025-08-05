import streamlit as st
import pandas as pd
import re
from datetime import datetime

def extract_loss_data(raw_text):
    pattern = re.compile(
        r'(?P<line>CB|CH)[^\d]{0,10}'                                  # Line
        r'(?P<date>\d{1,2}/\d{1,2}/\d{4})\s*[\-]?\s*'                   # Date
        r'\(?\s*(?P<shift>[ABCabc])\s*\)?[\s\-:]+'                      # Shift
        r'(?P<station>(Op|OP|LM)[^\s\-:\n,]*)[^\n]*?'                   # Station (with support for -1, (#123), etc.)
        r'(?P<issue>.+?)'                                               # Issue
        r'(?:\s|,|\(|\[)*'                                              # Optional separator
        r'(?P<duration>\d{2,4})\s*(?:min|minutes|MIN)?'                 # Duration at end
        , re.IGNORECASE | re.DOTALL
    )

    matches = pattern.finditer(raw_text)
    data = []

    for match in matches:
        line = match.group('line').upper()
        raw_date = match.group('date')
        shift = match.group('shift').upper()
        station = match.group('station').replace("#", "").strip()
        issue = match.group('issue').strip().strip('-–:')
        duration = match.group('duration').strip()

        try:
            formatted_date = datetime.strptime(raw_date, "%d/%m/%Y").strftime("%d/%m/%Y")
        except ValueError:
            try:
                formatted_date = datetime.strptime(raw_date, "%d-%m-%Y").strftime("%d/%m/%Y")
            except:
                formatted_date = None

        data.append({
            "Line": line,
            "Date": formatted_date,
            "Shift": shift,
            "Station": station,
            "Issue/Observation": issue,
            "Down time": duration
        })

    return pd.DataFrame(data)

# Streamlit App
st.set_page_config(page_title="Loss Data Extractor", layout="wide")
st.title("🔍 CB / CH Loss Data Extractor")

raw_input = st.text_area("Paste raw WhatsApp-style loss data below:", height=400)

if st.button("Extract Loss Data"):
    if raw_input.strip() == "":
        st.warning("Please paste some raw text data first.")
    else:
        df = extract_loss_data(raw_input)

        if df.empty:
            st.error("🚫 No valid data found. Please check the input format.")
        else:
            st.success(f"✅ Extracted {len(df)} entries!")
            st.dataframe(df, use_container_width=True)

            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name='extracted_loss_data.csv',
                mime='text/csv'
            )
