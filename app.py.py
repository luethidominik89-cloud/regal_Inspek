import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime
from PIL import Image
import os

st.set_page_config(page_title="Regal-Inspektion Pro", layout="wide")

if 'inspections' not in st.session_state:
    st.session_state.inspections = []

st.title("🛡️ Regal-Inspektions-System (DIN EN 15635)")

# --- STAMMDATEN ---
with st.expander("📋 Stammdaten (Kunde & Projekt)", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        kunde_name = st.text_input("Firma / Kunde")
        kunde_adresse = st.text_input("Straße / Ort")
    with col2:
        inspektor = st.text_input("Prüfer Name")
        datum_check = st.date_input("Prüfdatum", datetime.now())

# --- SCHADENSAUFNAHME ---
st.divider()
st.subheader("⚠️ Neuen Mangel erfassen")
c1, c2, c3 = st.columns([1, 1, 1])

with c1:
    # NEUES FELD: Eindeutige Nummer für das Regal
    regal_nr = st.text_input("Regal-Nummer / ID (z.B. R-104)", help="Eindeutige Kennung des Regals")
    regal_typ = st.selectbox("Regaltyp", ["Palettenregal", "Fachboden", "Kragarm", "Sonstiges"])
    bauteil = st.selectbox("Bauteil", ["Stütze", "Traverse", "Aussteifung", "Ankerschraube", "Rammschutz"])
    
with c2:
    gefahr = st.select_slider("Gefahrenstufe", options=["Grün", "Gelb", "ROT"], value="Grün")
    ursache = st.text_input("Mangel / Ursache")
    massnahme = st.text_area("Erforderliche Maßnahme")

with c3:
    foto = st.camera_input("Foto aufnehmen")

if st.button("Schaden zur Liste hinzufügen"):
    if not regal_nr:
        st.error("Bitte vergeben Sie eine Regal-Nummer!")
    else:
        img_path = None
        if foto:
            img = Image.open(foto)
            img_path = f"temp_{len(st.session_state.inspections)}.jpg"
            img.save(img_path)

        st.session_state.inspections.append({
            "RegalNr": regal_nr,
            "Typ": regal_typ,
            "Bauteil": bauteil,
            "Stufe": gefahr,
            "Mangel": ursache,
            "Massnahme": massnahme,
            "Foto": img_path
        })
        st.success(f"Regal {regal_nr} wurde hinzugefügt!")

# --- VORSCHAU & PDF ---
if st.session_state.inspections:
    st.divider()
    df_display = pd.DataFrame(st.session_state.inspections).drop(columns=['Foto'])
    st.dataframe(df_display, use_container_width=True)

    if st.button("📄 PDF-Protokoll generieren"):
        pdf = FPDF()
        pdf.add_page()
        
        # Kopfzeile
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, "Inspektionsbericht Regalanlagen", ln=True, align='C')
        pdf.set_font("Arial", size=10)
        pdf.cell(0, 8, f"Kunde: {kunde_name} | Datum: {datum_check}", ln=True, align='C')
        pdf.ln(10)

        for item in st.session_state.inspections:
            # Rahmen für jeden Eintrag
            pdf.set_fill_color(245, 245, 245)
            pdf.set_font("Arial", 'B', 11)
            
            # Kennzeichnung der Gefahr durch Farbe im PDF
            if item['Stufe'] == "ROT": pdf.set_text_color(255, 0, 0)
            elif item['Stufe'] == "Gelb": pdf.set_text_color(200, 150, 0)
            else: pdf.set_text