import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime
from PIL import Image
import io
import os

# Konfiguration
st.set_page_config(page_title="Regal-Check Profi", layout="wide")

# Speicher initialisieren
if 'inspections' not in st.session_state:
    st.session_state.inspections = []
if 'edit_index' not in st.session_state:
    st.session_state.edit_index = None

st.title("🛡️ Regal-Inspektion mit Inhaltsverzeichnis")

# --- STAMMDATEN ---
with st.expander("📋 Kunden- & Standortdetails", expanded=True):
    c_head1, c_head2 = st.columns(2)
    kunde = c_head1.text_input("Kunde / Firma", key="k_name_input")
    standort = c_head1.text_input("Standort / Werk", key="k_ort_input")
    gebaeude = c_head2.text_input("Halle / Bereich", key="k_halle_input")
    inspektor = c_head2.text_input("Prüfer Name", key="k_pruefer_input")

# --- EINGABEMASKE ---
st.divider()
if st.session_state.edit_index is not None:
    st.warning(f"🔄 Bearbeite Eintrag #{st.session_state.edit_index + 1}")
    current_data = st.session_state.inspections[st.session_state.edit_index]
else:
    current_data = {"Regal": "", "Typ": "Palettenregal", "Bauteil": "Stütze", "Position": "", "Stufe": "Grün", "Mangel": "Stapleranprall", "Massnahme": "Beobachten", "Fotos": []}

col1, col2, col3 = st.columns([1, 1, 1])

with col1:
    regal_nr = st.text_input("Regal-Nummer", value=current_data["Regal"])
    regal_typ = st.selectbox("Regalanlage", ["Palettenregal", "Fachbodenregal", "Kragarmregal", "Durchlaufregal", "Sonstiges"], index=0)
    
    bauteil_liste = ["Stütze", "Traverse", "Rammschutz", "Aussteifung"]
    b_idx = bauteil_liste.index(current_data["Bauteil"]) if current_data["Bauteil"] in bauteil_liste else 0
    bauteil = st.selectbox("Bauteil", bauteil_liste, index=b_idx)
    
    # Dynamische Label
    if bauteil == "Stütze":
        pos_label = "Position (z.B. vorne links)"
    elif bauteil == "Traverse":
        pos_label = "Ebene und Feld (z.B. E2, F4)"
    else:
        pos_label = "Genaue Position"
    pos = st.text_input(pos_label, value=current_data["Position"])

with col2:
    gefahr = st.radio("Status", ["Grün", "Gelb", "ROT"], index=["Grün", "Gelb", "ROT"].index(current_data["Stufe"]), horizontal=True)
    mangel_opt = ["Stapleranprall", "Sicherungsstift fehlt", "Bodenanker lose", "Überladung", "Sonstiges"]
    mangel = st.selectbox("Mangel", mangel_opt)
    kommentar = st.text_input("Zusatz-Kommentar", value=current_data.get("Mangel", "").split(": ")[-1] if ":" in current_data["Mangel"] else "")
    massnahme = st.selectbox("Maßnahme", ["Beobachten", "Tausch binnen 4 Wo.", "SOFORT SPERREN", "Stift ersetzen"])

with col3:
    st.write("📸 **Fotos**")
    f1 = st.camera_input("Foto 1", key="cam1")
    f2 = st.camera_input("Foto 2", key="cam2")

# --- SPEICHERN ---
if st.button("✅ Eintrag Speichern / Aktualisieren", use_container_width=True):
    current_photos = current_data.get("Fotos", [])
    for f in [f1, f2]:
        if f:
            img = Image.open(f).convert("RGB")
            path = f"img_{datetime.now().timestamp()}.jpg"
            img.save(path)
            current_photos.append(path)
    
    new_entry = {
        "Regal": regal_nr, "Typ": regal_typ, "Bauteil": bauteil, "Position": pos,
        "Stufe": gefahr, "Mangel": f"{mangel}: {kommentar}", "Massnahme": massnahme, "Fotos": current_photos
    }
    
    if st.session_state.edit_index is not None:
        st.session_state.inspections[st.session_state.edit_index] = new_entry
        st.session_state.edit_index = None
    else:
        st.session_state.inspections.append(new_entry)
    st.rerun()

# --- PDF GENERATOR ---
if st.session_state.inspections:
    st.divider()
    if st.button("📄 PDF-Bericht mit vollständigem Verzeichnis erstellen", type="primary"):
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=20)
        
        # 1. Deckblatt
        pdf.add_page()
        pdf.set_font("Arial", 'B', 26)
        pdf.cell(0, 40, "Inspektionsbericht", ln=True, align='C')
        pdf.set_font("Arial", '', 14)
        pdf.cell(0, 10, f"Kunde: {kunde}", ln=True)
        pdf.cell(0, 10, f"Standort: {standort} | Prüfer: {inspektor}", ln=True)
        
        # 2. Inhaltsverzeichnis (Seite 2)
        pdf.add_page()
        pdf.set_font("Arial", 'B', 18)
        pdf.cell(0, 15, "Inhaltsverzeichnis der Positionen", ln=True)
        pdf.ln(5)
        toc_list = []

        # 3. Details
        for item in st.session_state.inspections:
            pdf.add_page()
            toc_list.append((item['Regal'], item['Stufe'], item['Bauteil'], item['Position'], pdf.page_no()))
            
            # Kopfzeile
            if item['Stufe'] == "ROT": pdf.set_fill_color(255, 200, 200)
            elif item['Stufe'] == "Gelb": pdf.set_fill_color(255, 243, 200)
            else: pdf.set_fill_color(200, 255, 200)
            
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(0, 15, f"REGAL: {item['Regal']} - {item['Stufe']}", ln=True, fill=True)
            
            # Bauteil & Position UNTEREINANDER & GRÖSSER
            pdf.ln(5)
            pdf.set_font("Arial", 'B', 13)
            pdf.cell(0, 8, "Bauteil:", ln=True)
            pdf.set_font("Arial", '', 13)
            pdf.cell(0, 8, f"{item['Bauteil']}", ln=True)
            
            pdf.ln(2)
            pdf.set_font("Arial", 'B', 13)
            pdf.cell(0, 8, "Genaue Position / Ebene:", ln=True)
            pdf.set_font("Arial", '', 13)
            pdf.cell(0, 8, f"{item['Position']}", ln=True)
            
            pdf.ln(2)
            pdf.set_font("Arial", 'B', 13)
            pdf.cell(0, 8, "Mangel & Massnahme:", ln=True)
            pdf.set_font("Arial", '', 12)
            pdf.multi_cell(0, 7, f"{item['Mangel']}\nMassnahme: {item['Massnahme']}")
            
            if item['Fotos']:
                pdf.ln(5)
                y_pos = pdf.get_y()
                x_pos = 10
                for p in item['Fotos']:
                    if os.path.exists(p):
                        pdf.image(p, x=x_pos, y=y_pos, w=48)
                        x_pos += 53
                pdf.set_y(y_pos + 42)

        # Inhaltsverzeichnis befüllen
        pdf.page = 2
        pdf.set_y(35)
        pdf.set_font("Arial", '', 11)
        for entry in toc_list:
            # Farbkreis zeichnen
            if entry[1] == "ROT": pdf.set_fill_color(255, 0, 0)
            elif entry[1] == "Gelb": pdf.set_fill_color(255, 243, 0)
            else: pdf.set_fill_color(0, 255, 0)
            pdf.ellipse(10, pdf.get_y()+2, 4, 4, style='F')
            
            # Text im Verzeichnis: Regal + Bauteil + Position
            pdf.set_x(18)
            pdf.cell(0, 10, f"Regal {entry[0]}: {entry[2]} ({entry[3]})", ln=False)
            pdf.set_x(160)
            pdf.cell(0, 10, f"Seite {entry[4]}", ln=True)

        pdf_bytes = pdf.output(dest='S').encode('latin-1', 'replace')
        st.download_button("📥 PDF Bericht herunterladen", data=pdf_bytes, file_name=f"Inspektion_{kunde}.pdf")