import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime
from PIL import Image
import io
import os

# Seite konfigurieren
st.set_page_config(page_title="Regal-Check Profi", layout="wide")

# Speicher initialisieren
if 'inspections' not in st.session_state:
    st.session_state.inspections = []
if 'edit_index' not in st.session_state:
    st.session_state.edit_index = None

st.title("🛡️ Regal-Inspektions-Bericht")

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
    st.warning(f"🔄 Bearbeitung: Eintrag #{st.session_state.edit_index + 1}")
    current_data = st.session_state.inspections[st.session_state.edit_index]
else:
    current_data = {"Regal": "", "Typ": "Palettenregal", "Bauteil": "Stütze", "Position": "", "Stufe": "Grün", "Mangel": "Stapleranprall", "Massnahme": "Beobachten", "Fotos": []}

col1, col2, col3 = st.columns([1, 1, 1])

with col1:
    regal_nr = st.text_input("Regal-Nummer", value=current_data["Regal"])
    regal_typ = st.selectbox("Regalanlage", ["Palettenregal", "Fachbodenregal", "Kragarmregal", "Durchlaufregal", "Sonstiges"], index=0)
    bauteil = st.selectbox("Bauteil", ["Stütze", "Traverse", "Rammschutz", "Aussteifung"], index=0)
    pos = st.text_input("Position / Ebene / Feld", value=current_data["Position"])

with col2:
    # Farbwahl über Buttons statt Slider
    st.write("**Gefahrenstufe:**")
    gefahr = st.radio("Status", ["Grün", "Gelb", "ROT"], index=["Grün", "Gelb", "ROT"].index(current_data["Stufe"]), horizontal=True)
    mangel = st.selectbox("Mangel", ["Stapleranprall", "Sicherungsstift fehlt", "Bodenanker lose", "Überladung", "Sonstiges"])
    kommentar = st.text_input("Zusatz-Kommentar", value=current_data.get("Mangel", "").split(": ")[-1] if ":" in current_data["Mangel"] else "")
    massnahme = st.selectbox("Maßnahme", ["Beobachten", "Tausch binnen 4 Wo.", "SOFORT SPERREN", "Stift ersetzen"])

with col3:
    st.write("📸 **Fotos**")
    f1 = st.camera_input("Foto 1", key="cam1")
    f2 = st.camera_input("Foto 2", key="cam2")

# --- SPEICHERN ---
if st.button("✅ Eintrag speichern", use_container_width=True):
    if not regal_nr:
        st.error("Bitte Regal-Nummer angeben!")
    else:
        new_photos = current_data.get("Fotos", [])
        for f in [f1, f2]:
            if f:
                img = Image.open(f).convert("RGB")
                path = f"img_{datetime.now().timestamp()}.jpg"
                img.save(path)
                new_photos.append(path)
        
        entry = {
            "Regal": regal_nr, "Typ": regal_typ, "Bauteil": bauteil, "Position": pos,
            "Stufe": gefahr, "Mangel": f"{mangel}: {kommentar}", "Massnahme": massnahme, "Fotos": new_photos
        }
        
        if st.session_state.edit_index is not None:
            st.session_state.inspections[st.session_state.edit_index] = entry
            st.session_state.edit_index = None
        else:
            st.session_state.inspections.append(entry)
        st.rerun()

# --- AUFZÄHLUNG IN DER APP ---
if st.session_state.inspections:
    st.divider()
    st.subheader("📋 Erfasste Punkte")
    for idx, item in enumerate(st.session_state.inspections):
        c_i, c_e, c_d = st.columns([7, 2, 1])
        icon = "🟢" if item['Stufe'] == "Grün" else "🟡" if item['Stufe'] == "Gelb" else "🔴"
        c_i.write(f"{icon} **#{idx+1} Regal {item['Regal']}** | {item['Bauteil']} ({item['Position']})")
        if c_e.button("✏️", key=f"e_{idx}"):
            st.session_state.edit_index = idx
            st.rerun()
        if c_d.button("🗑️", key=f"d_{idx}"):
            st.session_state.inspections.pop(idx)
            st.rerun()

    # --- PDF GENERIERUNG (OHNE VERZEICHNIS) ---
    if st.button("📄 PDF-Bericht erstellen", type="primary", use_container_width=True):
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=20)
        
        # Deckblatt
        pdf.add_page()
        pdf.set_font("Arial", 'B', 24)
        pdf.cell(0, 40, "Inspektionsbericht Regalanlagen", ln=True, align='C')
        pdf.set_font("Arial", '', 14)
        pdf.cell(0, 10, f"Kunde: {kunde}", ln=True)
        pdf.cell(0, 10, f"Standort: {standort} | Bereich: {gebaeude}", ln=True)
        pdf.cell(0, 10, f"Prüfer: {inspektor} | Datum: {datetime.now().strftime('%d.%m.%Y')}", ln=True)
        pdf.ln(10)
        
        # Aufzählung der Mängel
        for item in st.session_state.inspections:
            # Check für Seitenumbruch
            if pdf.get_y() > 180:
                pdf.add_page()

            # Kopfzeile
            if item['Stufe'] == "ROT": pdf.set_fill_color(255, 200, 200)
            elif item['Stufe'] == "Gelb": pdf.set_fill_color(255, 243, 200)
            else: pdf.set_fill_color(200, 255, 200)
            
            pdf.set_font("Arial", 'B', 14)
            pdf.cell(0, 12, f"REGAL: {item['Regal']} - STATUS: {item['Stufe']}", ln=True, fill=True)
            
            # Details untereinander
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(40, 8, "Bauteil:", ln=0)
            pdf.set_font("Arial", '', 12)
            pdf.cell(0, 8, f"{item['Bauteil']}", ln=True)
            
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(40, 8, "Position:", ln=0)
            pdf.set_font("Arial", '', 12)
            pdf.cell(0, 8, f"{item['Position']}", ln=True)
            
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(0, 8, "Mangel & Massnahme:", ln=True)
            pdf.set_font("Arial", '', 11)
            pdf.multi_cell(0, 7, f"{item['Mangel']}\nMassnahme: {item['Massnahme']}")
            
            # Fotos
            if item['Fotos']:
                pdf.ln(3)
                y_img = pdf.get_y()
                x_img = 10
                for p in item['Fotos']:
                    if os.path.exists(p):
                        pdf.image(p, x=x_img, y=y_img, w=48)
                        x_img += 53
                pdf.set_y(y_img + 42)
            
            pdf.ln(5)
            pdf.line(10, pdf.get_y(), 200, pdf.get_y())
            pdf.ln(10)

        pdf_bytes = pdf.output(dest='S').encode('latin-1', 'replace')
        st.download_button("📥 PDF herunterladen", data=pdf_bytes, file_name=f"Bericht_{kunde}.pdf")