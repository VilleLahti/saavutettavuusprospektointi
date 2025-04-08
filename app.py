import streamlit as st
import openai
from googleapiclient.discovery import build
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
import time

# API-avaimet
openai.api_key = st.secrets["OPENAI_API_KEY"]
API_KEY = st.secrets["GOOGLE_API_KEY"]
CSE_ID = st.secrets["CSE_ID"]

# Google Sheets -yhteys Streamlit secretsistä
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = st.secrets["google_service_account"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(json.loads(creds_dict.to_json()), scope)
client = gspread.authorize(creds)

# Luo Sheets-taulukko
spreadsheet = client.create("Saavutettavuusprospektointi")
worksheet = spreadsheet.get_worksheet(0)
worksheet.append_row(["Hakutermi", "Otsikko", "URL", "Kuvaus"])

# UI
st.title("Saavutettavuusprospektointi")
kuvaus = st.text_input("Kuvaile kohderyhmä, jonka verkkosivustoja etsit")

def generate_search_terms(description):
    prompt = f"Luo 5 tarkkaa Google-hakutermiä, jotka auttavat löytämään verkkosivustoja, jotka vastaavat tätä kuvausta: '{description}'"
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    terms = response.choices[0].message.content.split("\n")
    return [t.strip("- ").strip() for t in terms if t.strip()]

def google_search(query, api_key, cse_id, num=10):
    service = build("customsearch", "v1", developerKey=api_key)
    res = service.cse().list(q=query, cx=cse_id, num=num).execute()
    return res.get("items", [])

if st.button("Käynnistä prospektointi"):
    if kuvaus:
        with st.spinner("Haetaan..."):
            terms = generate_search_terms(kuvaus)
            for term in terms:
                results = google_search(term, API_KEY, CSE_ID)
                for result in results:
                    title = result.get("title")
                    link = result.get("link")
                    snippet = result.get("snippet")
                    worksheet.append_row([term, title, link, snippet])
                    st.write(f"🔗 [{title}]({link}) — {snippet}")
                time.sleep(2)
            st.success("Valmis! Tulokset tallennettu Google Sheetiin.")
            st.write(f"[Avaa Sheets täällä]({spreadsheet.url})")
    else:
        st.warning("Anna ensin kuvaus kohderyhmästä.")
