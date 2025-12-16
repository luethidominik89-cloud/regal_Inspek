import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime
from PIL import Image
import io
import os

st.set_page_config(page_title="Regal-Check Profi", layout="wide")

if 'inspections' not in st.session_state:
    st.session_state.inspections = []
if 'edit_index' not in st.session_state:
    st.session_state.edit_index = None

st.title("🛡️ Regal-Inspektion mit Inhaltsverzeichnis")

# --- STAMMDATEN ---
with st.expander("📋 Kunden- & Standortdetails", expanded=True):
    c1, c2 = st.columns(2)
    with c1:
        kunde = st.text_input("Kunde / Firma")
        standort = st.text_input("Standort / Werk")
    with c2:
        gebaeude = st.text_input("Halle / Bereich")
        inspektor = st.text_input("Prüfer Name")

# --- EINGABEMASKE ---
st.divider()
if st.session_state.edit_index is not None:
    st.info(f"🔄 Bearbeite Eintrag #{st.session_state.edit_index + 1}")
    data = st.session_state.inspections[st.session_state.edit_index]
else:
    data = {"Regal": "", "Typ": "Palettenregal", "Bauteil": "Stütze", "Position": "", "Stufe": "Grün", "Mangel": "Stapleranprall", "Massnahme": "Beobachten", "Fotos": []}

col1, col2, col3 = st.columns([1, 1, 1])

with col1:
    regal_nr = st.text_input("Regal-Nummer", value=data["Regal"])
    regal_typ = st.selectbox("Regalanlage", ["Palettenregal", "Fachbodenregal", "Kragarmregal", "Durchlaufregal", "Sonstiges"], index=0)
    bauteil = st.selectbox("Bauteil", ["Stütze", "Traverse", "Rammschutz", "Aussteifung"], index=0)
    
    # Dynamische Label
    pos_label = "Position (Stütze)" if bauteil == "Stütze" else "Ebene & Feld" if bauteil == "Traverse" else "Genaue Position"
    pos = st.text_input(pos_label, value=data["Position"])

with col2:
    gefahr = st.radio("Status wählen", ["Grün", "Gelb", "ROT"], index=["Grün", "Gelb", "ROT"].index(data["Stufe"]), horizontal=True)
    mangel = st.selectbox("Mangel", ["Stapleranprall", "Sicherungsstift fehlt", "Bodenanker lose", "Überladung", "Sonstiges"])
    kommentar = st.text_input("Zusatz-Kommentar", value=data.get("Mangel", "").split(": ")[-1] if ":" in data["Mangel"] else "")
    massnahme = st.selectbox("Maßnahme", ["Beobachten", "Tausch binnen 4 Wo.", "SOFORT SPERREN", "Stift ersetzen"])

with col3:
    st.write("📸 **Fotos**")
    f1 = st.camera_input("Foto 1", key="c1")
    f2 = st.camera_input("Foto 2", key="c2")

# Speichern Logik
if st.button("✅ Speichern"):
    current_photos = []
    for f in [f1, f2]:
        if f:
            img = Image.open(f).convert("RGB")
            path = f"img_{datetime.now().timestamp()}.jpg"
            img.save(path)
            current_photos.append(path)
    
    entry = {
        "Regal": regal_nr, "Typ": regal_typ, "Bauteil": bauteil, "Position": pos,
        "Stufe": gefahr, "Mangel": f"{mangel}: {kommentar}", "Massnahme": massnahme, "Fotos": current_photos
    }
    
    if st.session_state.edit_index is not None:
        st.session_state.inspections[st.session_state.edit_index] = entry
        st.session_state.edit_index = None
    else:
        st.session_state.inspections.append(entry)
    st.rerun()

# --- PDF GENERIERUNG ---
if st.session_state.inspections:
    st.divider()
    if st.button("📄 PDF-Bericht mit Inhaltsverzeichnis erstellen"):
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=20)
        
        # 1. Deckblatt
        pdf.add_page()
        pdf.set_font("Arial", 'B', 24)
        pdf.cell(0, 40, "Inspektionsbericht Regalanlagen", ln=True, align='C')
        pdf.set_font("Arial", '', 14)
        pdf.cell(0, 10, f"Kunde: {kunde}", ln=True)
        pdf.cell(0, 10, f"Datum: {datetime.now().strftime('%d.%m.%Y')}", ln=True)
        
        # 2. Inhaltsverzeichnis (Platzhalter-Logik)
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 15, "Inhaltsverzeichnis (Regal-Positionen)", ln=True)
        pdf.set_font("Arial", '', 12)
        
        # Wir sammeln hier die Seitenzahlen während wir die Details schreiben
        toc_entries = []

        # 3. Details schreiben
        for item in st.session_state.inspections:
            pdf.add_page()
            toc_entries.append((item['Regal'], item['Bauteil'], pdf.page_no()))
            
            # Farbiger Balken
            if item['Stufe'] == "ROT": pdf.set_fill_color(255, 200, 200)
            elif item['Stufe'] == "Gelb": pdf.set_fill_color(255, 243, 200)
            else: pdf.set_fill_color(200, 255, 200)
            
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(0, 15, f"REGAL: {item['Regal']} - {item['Stufe']}", ln=True, fill=True)
            
            pdf.set_font("Arial", 'B', 13)
            pdf.cell(0, 10, "Bauteil:", ln=True)
            pdf.set_font("Arial", '', 13)
            pdf.cell(0, 10, f"{item['Bauteil']}", ln=True)
            
            pdf.set_font("Arial", 'B', 13)
            pdf.cell(0, 10, "Position / Ebene:", ln=True)
            pdf.set_font("Arial", '', 13)
            pdf.cell(0, 10, f"{item['Position']}", ln=True)
            
            pdf.set_font("Arial", 'B', 13)
            pdf.cell(0, 10, "Mangel & Maßnahme:", ln=True)
            pdf.set_font("Arial", '', 12)
            pdf.multi_cell(0, 8, f"{item['Mangel']}\nMassnahme: {item['Massnahme']}")
            
            if item['Fotos']:
                pdf.ln(5)
                y_img = pdf.get_y()
                x_img = 10
                for p in item['Fotos']:
                    pdf.image(p, x=x_img, y=y_img, w=50)
                    x_img += 55
        
        # Zurück zum Inhaltsverzeichnis (Seite 2) und die Einträge schreiben
        pdf.page = 2
        pdf.set_y(30)
        for entry in toc_entries:
            pdf.cell(0, 10, f"Regal {entry[0]} ({entry[1]}) ......................... Seite {entry[2]}", ln=True)

        pdf_bytes = pdf.output(dest='S').encode('latin-1', 'replace')
        st.download_button("📥 PDF herunterladen", data=pdf_bytes, file_name="Bericht.pdf")