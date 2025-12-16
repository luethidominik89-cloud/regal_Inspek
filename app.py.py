import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime
from PIL import Image
import io
import os

st.set_page_config(page_title="Regal-Check Profi Multi-Foto", layout="wide")

if 'inspections' not in st.session_state:
    st.session_state.inspections = []

st.title("🛡️ Regal-Inspektion (Multi-Foto Support)")

# --- STAMMDATEN ---
with st.expander("📋 Kunden- & Standortdetails", expanded=True):
    c1, c2 = st.columns(2)
    with c1:
        kunde = st.text_input("Kunde / Firma")
        standort = st.text_input("Standort")
    with c2:
        gebaeude = st.text_input("Gebäudeteil / Halle")
        inspektor = st.text_input("Prüfer")

# --- MÄNGEL-ERFASSUNG ---
st.divider()
st.subheader("⚠️ Mangel aufnehmen")
col1, col2, col3 = st.columns([1, 1, 1])

with col1:
    regal_nr = st.text_input("Regal-Nummer")
    regal_typ = st.selectbox("Regalanlage", ["Palettenregal", "Fachbodenregal", "Kragarmregal", "Einfahrregal", "Sonstiges"])
    bauteil = st.selectbox("Bauteil", ["Stütze", "Traverse", "Rammschutz", "Aussteifung", "Fachboden"])
    pos = st.text_input("Genaue Position (Ebene/Pfosten)")

with col2:
    gefahr = st.select_slider("Gefahrenstufe", options=["Grün", "Gelb", "ROT"], value="Grün")
    mangel_auswahl = st.selectbox("Art des Mangels", ["Stapleranprall", "Sicherungsstift fehlt", "Bodenanker lose", "Überladung", "Sonstiges"])
    mangel_detail = st.text_input("Kommentar")
    massnahme = st.selectbox("Maßnahme", ["Beobachten", "Tausch binnen 4 Wo.", "SOFORT SPERREN", "Stift ersetzen"])

with col3:
    st.write("📸 **Fotos aufnehmen (max. 3)**")
    foto1 = st.camera_input("Foto 1 (Detail)", key="f1")
    foto2 = st.camera_input("Foto 2 (Übersicht)", key="f2")
    foto3 = st.camera_input("Foto 3 (Nahaufnahme)", key="f3")

if st.button("Schaden mit Fotos speichern"):
    if not regal_nr:
        st.error("Regal-Nummer fehlt!")
    else:
        saved_photos = []
        # Fotos verarbeiten und temporär speichern
        for i, f in enumerate([foto1, foto2, foto3]):
            if f:
                img = Image.open(f)
                if img.mode in ("RGBA", "P"): img = img.convert("RGB")
                path = f"temp_{len(st.session_state.inspections)}_{i}.jpg"
                img.save(path)
                saved_photos.append(path)

        st.session_state.inspections.append({
            "Regal": regal_nr,
            "Typ": regal_typ,
            "Bauteil": bauteil,
            "Position": pos,
            "Stufe": gefahr,
            "Mangel": f"{mangel_auswahl} {mangel_detail}".strip(),
            "Massnahme": massnahme,
            "Fotos": saved_photos
        })
        st.success("Erfolgreich gespeichert!")

# --- BERICHT & PDF ---
if st.session_state.inspections:
    st.divider()
    if st.button("📄 PDF-Bericht mit allen Fotos generieren"):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, "Inspektionsbericht", ln=True, align='C')
        pdf.set_font("Arial", size=10)
        pdf.cell(0, 8, f"{kunde} - {standort} - {gebaeude}", ln=True, align='C')
        pdf.ln(10)

        for item in st.session_state.inspections:
            # Kopfzeile
            pdf.set_fill_color(240, 240, 240)
            if item['Stufe'] == "ROT": pdf.set_text_color(255, 0, 0)
            elif item['Stufe'] == "Gelb": pdf.set_text_color(200, 150, 0)
            else: pdf.set_text_color(0, 128, 0)
            
            pdf.set_font("Arial", 'B', 11)
            pdf.cell(0, 10, f"REGAL: {item['Regal']} ({item['Typ']}) - {item['Stufe']}", ln=True, fill=True)
            
            pdf.set_text_color(0, 0, 0)
            pdf.set_font("Arial", size=10)
            pdf.multi_cell(0, 6, f"Pos: {item['Bauteil']} {item['Position']}\nMangel: {item['Mangel']}\nMassnahme: {item['Massnahme']}")
            
            # Fotos nebeneinander einfügen
            if item['Fotos']:
                x_pos = 10
                for img_p in item['Fotos']:
                    pdf.image(img_p, x=x_pos, w=45)
                    x_pos += 50 # Abstand zum nächsten Bild
                pdf.ln(35) # Platz nach den Bildern
            
            pdf.ln(5)
            pdf.line(10, pdf.get_y(), 200, pdf.get_y())
            pdf.ln(5)

        pdf_bytes = pdf.output(dest='S').encode('latin-1', 'replace')
        st.download_button("📥 PDF Herunterladen", data=pdf_bytes, file_name="Bericht.pdf")