import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime
from PIL import Image

st.set_page_config(page_title="Regal-Check Profi Plus", layout="wide")

if 'inspections' not in st.session_state:
    st.session_state.inspections = []

st.title("🛡️ Professionelle Regal-Inspektion")

# --- ERWEITERTE STAMMDATEN ---
with st.expander("📋 Kunden- & Standortdetails", expanded=True):
    c1, c2 = st.columns(2)
    with c1:
        kunde = st.text_input("Kunde / Firma")
        standort = st.text_input("Standort (Stadt / Werk)")
    with c2:
        gebaeude = st.text_input("Gebäudeteil / Halle (z.B. Halle A, OG)")
        inspektor = st.text_input("Prüfer")

# --- SCHADENSAUFNAHME ---
st.divider()
st.subheader("⚠️ Mängel-Erfassung")
col1, col2, col3 = st.columns([1, 1, 1])

with col1:
    regal_nr = st.text_input("Regal-Nummer (z.B. R-01)")
    
    # NEU: Dropdown für die Regalanlage
    regal_typ = st.selectbox("Regalanlage", [
        "Palettenregal", 
        "Fachbodenregal", 
        "Kragarmregal", 
        "Einfahrregal", 
        "Durchlaufregal", 
        "Verschieberegal",
        "Sonstiges"
    ])
    
    bauteil = st.selectbox("Bauteil", ["Stütze", "Traverse", "Rammschutz", "Aussteifung", "Fachboden"])
    
    # Detail-Position
    if bauteil == "Stütze":
        pos = st.text_input("Genaue Stütze", placeholder="z.B. vorne links")
    elif bauteil == "Traverse":
        pos = st.text_input("Ebene / Position", placeholder="z.B. Ebene 2, Feld 3")
    else:
        pos = st.text_input("Zusatz-Info Position")

with col2:
    gefahr = st.select_slider("Gefahrenstufe", options=["Grün", "Gelb", "ROT"], value="Grün")
    
    # DROP-DOWN FÜR GÄNGIGE MÄNGEL
    mangel_liste = [
        "Stapleranprall / Verform