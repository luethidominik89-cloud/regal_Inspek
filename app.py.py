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
    bauteil = st.selectbox("Bauteil", ["Stütze", "Traverse", "Rammschutz", "Aussteifung"], index=0)
    
    # Dynamische Label je nach Bauteil
    if bauteil == "Stütze":
        pos_label = "Position (z.B. vorne links, 3. Pfosten)"
    elif bauteil == "Traverse":
        pos_label = "Ebene und Feld (z.B. Ebene 3, Feld 12)"
    else:
        pos_label = "Genaue Position"
    pos = st.text_input(pos_label, value=current_data["Position"])

with col2:
    gefahr = st.radio("Gefahrenstufe wählen (🟢 🟡 🔴)", ["Grün", "Gelb", "ROT"], index=["Grün", "Gelb", "ROT"].index(current_data["Stufe"]), horizontal=True)
    mangel = st.selectbox("Mangel", ["Stapleranprall", "Sicherungsstift fehlt", "Bodenanker lose", "Überladung", "Verformung", "Sonstiges"])
    kommentar = st.text_input("Zusatz-Kommentar (optional)", value=current_data.get("Mangel", "").split(": ")[-1] if ":" in current_data["Mangel"] else "")
    massnahme = st.selectbox("Maßnahme", ["Beobachten", "Tausch binnen 4 Wo.", "SOFORT SPERREN", "Stift ersetzen", "Anker nachziehen"])

with col3:
    st.write("📸 **Fotos (optional)**")
    f1 = st.camera_input("Foto 1", key="cam1")
    f2 = st.camera_input("Foto 2", key="cam2")

# --- SPEICHER LOGIK ---
b_col1, b_col2 = st.columns(2)

if st.session_state.edit_index is None:
    if b_col1.button("✅ Schaden speichern", use_container_width=True):
        if not regal_nr or not pos:
            st.error("Bitte Regal-Nummer und Position angeben!")
        else:
            current_photos = []
            for f in [f1, f2]:
                if f:
                    img = Image.open(f).convert("RGB")
                    path = f"img_{datetime.now().timestamp()}.jpg"
                    img.save(path)
                    current_photos.append(path)
            
            st.session_state.inspections.append({
                "Regal": regal_nr, "Typ": regal_typ, "Bauteil": bauteil, "Position": pos,
                "Stufe": gefahr, "Mangel": f"{mangel}: {kommentar}", "Massnahme": massnahme, "Fotos": current_photos
            })
            st.success("Gespeichert!")
            st.rerun()
else:
    if b_col1.button("💾 Änderungen übernehmen", use_container_width=True):
        st.session_state.inspections[st.session_state.edit_index].update({
            "Regal": regal_nr, "Typ": regal_typ, "Bauteil": bauteil, "Position": pos,
            "Stufe": gefahr, "Mangel": f"{mangel}: {kommentar}", "Massnahme": massnahme
        })
        st.session_state.edit_index = None
        st.rerun()
    if b_col2.button("🚫 Abbrechen", use_container_width=True):
        st.session_state.edit_index = None
        st.rerun()

# --- LISTE UND PDF ---
if st.session_state.inspections:
    st.divider()
    st.subheader("📋 Erfasste Mängel")
    for idx, item in enumerate(st.session_state.inspections):
        ci, ce = st.columns([8, 2])
        icon = "🟢" if item['Stufe'] == "Grün" else "🟡" if item['Stufe'] == "Gelb" else "🔴"
        ci.write(f"{icon} **#{idx+1} Regal {item['Regal']}** - {item['Bauteil']} ({item['Position']})")
        if ce.button("✏️ Bearbeiten", key=f"edit_{idx}"):
            st.session_state.edit_index = idx
            st.rerun()

    if st.button("📄 PDF-Bericht mit Inhaltsverzeichnis erstellen", type="primary"):
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=20)
        
        # 1. Deckblatt
        pdf.add_page()
        pdf.set_font("Arial", 'B', 26)
        pdf.cell(0, 40, "Inspektionsbericht", ln=True, align='C')
        pdf.set_font("Arial", '', 14)
        pdf.cell(0, 10, f"Kunde: {kunde}", ln=True)
        pdf.cell(0, 10, f"Standort: {standort} | Bereich: {gebaeude}", ln=True)
        pdf.cell(0, 10, f"Prüfer: {inspektor} | Datum: {datetime.now().strftime('%d.%m.%Y')}", ln=True)
        
        # 2. Inhaltsverzeichnis (Seite 2 vorbereiten)
        pdf.add_page()
        pdf.set_font("Arial", 'B', 18)
        pdf.cell(0, 15, "Inhaltsverzeichnis", ln=True)
        pdf.ln(5)
        toc_page = 2
        toc_list = []

        # 3. Details
        for item in st.session_state.inspections:
            pdf.add_page()
            curr_page = pdf.page_no()
            toc_list.append((item['Regal'], item['Stufe'], item['Bauteil'], curr_page))
            
            # Kopfzeile farbig
            if item['Stufe'] == "ROT": pdf.set_fill_color(255, 200, 200)
            elif item['Stufe'] == "Gelb": pdf.set_fill_color(255, 243, 200)
            else: pdf.set_fill_color(200, 255, 200)
            
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(0, 15, f"REGAL: {item['Regal']} - {item['Stufe']}", ln=True, fill=True)
            
            pdf.set_font("Arial", 'B', 13)
            pdf.cell(0, 8, "Bauteil:", ln=True)
            pdf.set_font("Arial", '', 13)
            pdf.cell(0, 8, f"{item['Bauteil']}", ln=True)
            
            pdf.set_font("Arial", 'B', 13)
            pdf.cell(0, 8, "Position / Ebene:", ln=True)
            pdf.set_font("Arial", '', 13)
            pdf.cell(0, 8, f"{item['Position']}", ln=True)
            
            pdf.set_font("Arial", 'B', 13)
            pdf.cell(0, 8, "Mangel & Massnahme:", ln=True)
            pdf.set_font("Arial", '', 12)
            pdf.multi_cell(0, 7, f"{item['Mangel']}\nMassnahme: {item['Massnahme']}")
            
            if item['Fotos']:
                pdf.ln(5)
                y_img = pdf.get_y()
                x_img = 10
                for p in item['Fotos']:
                    pdf.image(p, x=x_img, y=y_img, w=50)
                    x_img += 55
        
        # Inhaltsverzeichnis befüllen
        pdf.page = toc_page
        pdf.set_y(35)
        pdf.set_font("Arial", '', 12)
        for entry in toc_list:
            status_text = "🔴" if entry[1] == "ROT" else "🟡" if entry[1] == "Gelb" else "🟢"
            pdf.cell(0, 10, f"{status_text} Regal {entry[0]} ({entry[2]}) .................... Seite {entry[3]}", ln=True)

        pdf_bytes = pdf.output(dest='S').encode('latin-1', 'replace')
        st.download_button("📥 PDF Bericht laden", data=pdf_bytes, file_name=f"Bericht_{kunde}.pdf")