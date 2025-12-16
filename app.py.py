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
        "Stapleranprall / Verformung",
        "Fehlender Sicherungsstift",
        "Riss in Schweißnaht",
        "Lockerung der Bodenanker",
        "Überladung / Durchbiegung",
        "Sonstiges (siehe Kommentar)"
    ]
    mangel = st.selectbox("Art des Mangels", mangel_liste)
    mangel_detail = st.text_input("Zusatzkommentar Mangel (optional)")

    # DROP-DOWN FÜR MASSNAHMEN
    massnahmen_liste = [
        "Keine sofortige Maßnahme (Beobachtung)",
        "Sicherungstifte ersetzen",
        "Bauteil innerhalb 4 Wochen austauschen",
        "SOFORTIGE SPERRUNG & Entladung",
        "Bodenanker nachziehen",
        "Fachlast reduzieren"
    ]
    gewaehlte_massnahme = st.selectbox("Erforderliche Maßnahme", massnahmen_liste)

with col3:
    foto = st.camera_input("Foto aufnehmen")

if st.button("Schaden speichern"):
    if not regal_nr or not pos:
        st.error("Bitte Regal-Nr. und Position angeben!")
    else:
        img_path = None
        if foto:
            img = Image.open(foto)
            img_path = f"temp_{len(st.session_state.inspections)}.jpg"
            img.save(img_path)

        st.session_state.inspections.append({
            "Regal": regal_nr,
            "Bauteil": bauteil,
            "Position": pos,
            "Stufe": gefahr,
            "Mangel": f"{mangel} ({mangel_detail})",
            "Massnahme": gewaehlte_massnahme,
            "Foto": img_path
        })
        st.success("Eintrag erfolgreich hinzugefügt.")

# --- BERICHT & PDF ---
if st.session_state.inspections:
    st.divider()
    df = pd.DataFrame(st.session_state.inspections).drop(columns=['Foto'])
    st.table(df)

    if st.button("📄 PDF-Prüfbericht generieren"):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, "Regal-Inspektionsprotokoll", ln=True, align='C')
        
        pdf.set_font("Arial", size=10)
        pdf.cell(0, 8, f"Kunde: {kunde} | Standort: {standort} | Bereich: {gebaeude}", ln=True, align='C')
        pdf.ln(10)

        for item in st.session_state.inspections:
            pdf.set_fill_color(240, 240, 240)
            pdf.set_font("Arial", 'B', 11)
            
            # Farbe für Gefahrenstufe
            if item['Stufe'] == "ROT": pdf.set_text_color(255, 0, 0)
            elif item['Stufe'] == "Gelb": pdf.set_text_color(200, 150, 0)
            else: pdf.set_text_color(0, 128, 0)
            
            pdf.cell(0, 10, f"REGAL: {item['Regal']} - Status: {item['Stufe']}", ln=True, fill=True)
            
            pdf.set_text_color(0, 0, 0)
            pdf.set_font("Arial", size=10)
            content = (f"Bauteil/Position: {item['Bauteil']} - {item['Position']}\n"
                       f"Mangel: {item['Mangel']}\n"
                       f"Massnahme: {item['Massnahme']}")
            pdf.multi_cell(0, 6, content)
            
            if item['Foto']:
                pdf.image(item['Foto'], x=150, w=45)
            
            pdf.ln(5)
            pdf.line(10, pdf.get_y(), 200, pdf.get_y())
            pdf.ln(5)

        pdf_bytes = pdf.output(dest='S').encode('latin-1', 'replace')
        st.download_button("📥 PDF-Bericht laden", data=pdf_bytes, file_name=f"Bericht_{kunde}_{standort}.pdf")