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

st.title("🛡️ Regal-Inspektions-System")

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
    st.warning(f"🔄 BEARBEITUNGS-MODUS: Eintrag #{st.session_state.edit_index + 1} anpassen")
    current_data = st.session_state.inspections[st.session_state.edit_index]
else:
    current_data = {"Regal": "", "Typ": "Palettenregal", "Bauteil": "Stütze", "Position": "", "Stufe": "Grün", "Mangel": "Stapleranprall", "Massnahme": "Beobachten", "Fotos": []}

col1, col2, col3 = st.columns([1, 1, 1])

with col1:
    regal_nr = st.text_input("Regal-Nummer", value=current_data["Regal"])
    regal_typ = st.selectbox("Regalanlage", ["Palettenregal", "Fachbodenregal", "Kragarmregal", "Durchlaufregal", "Sonstiges"], 
                             index=["Palettenregal", "Fachbodenregal", "Kragarmregal", "Durchlaufregal", "Sonstiges"].index(current_data["Typ"]))
    
    bauteil_liste = ["Stütze", "Traverse", "Rammschutz", "Aussteifung"]
    b_idx = bauteil_liste.index(current_data["Bauteil"]) if current_data["Bauteil"] in bauteil_liste else 0
    bauteil = st.selectbox("Bauteil", bauteil_liste, index=b_idx)
    
    if bauteil == "Stütze":
        pos_label = "Position (Stütze)"
    elif bauteil == "Traverse":
        pos_label = "Ebene und Feld"
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
    st.write("📸 **Fotos aufnehmen**")
    f1 = st.camera_input("Foto 1", key="cam1")
    f2 = st.camera_input("Foto 2", key="cam2")

# --- SPEICHER-BUTTONS ---
b_col1, b_col2 = st.columns(2)
if st.session_state.edit_index is None:
    if b_col1.button("✅ Schaden in Liste speichern", use_container_width=True):
        if not regal_nr:
            st.error("Bitte Regal-Nummer angeben!")
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

# --- DIE AUFZÄHLUNG (ZURÜCKKEHREN & BEARBEITEN) ---
if st.session_state.inspections:
    st.divider()
    st.subheader("📋 Erfasste Mängel (Klicken zum Bearbeiten)")
    
    # Tabelle für Übersicht
    for idx, item in enumerate(st.session_state.inspections):
        with st.container():
            c_info, c_edit, c_del = st.columns([7, 2, 1])
            status_color = "🟢" if item['Stufe'] == "Grün" else "🟡" if item['Stufe'] == "Gelb" else "🔴"
            
            # Anzeige in der App-Liste
            c_info.write(f"{status_color} **#{idx+1} Regal {item['Regal']}** | {item['Bauteil']} ({item['Position']})")
            
            # Button um zum Eintrag zurückzukehren
            if c_edit.button("✏️ Bearbeiten", key=f"edit_btn_{idx}"):
                st.session_state.edit_index = idx
                st.rerun()
            
            # Button zum Löschen falls nötig
            if c_del.button("🗑️", key=f"del_btn_{idx}"):
                st.session_state.inspections.pop(idx)
                st.rerun()

    # --- PDF GENERATOR ---
    st.divider()
    if st.button("📄 Finalen PDF-Bericht generieren", type="primary", use_container_width=True):
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=20)
        
        # Deckblatt
        pdf.add_page()
        pdf.set_font("Arial", 'B', 26)
        pdf.cell(0, 40, "Inspektionsbericht", ln=True, align='C')
        pdf.set_font("Arial", '', 14)
        pdf.cell(0, 10, f"Kunde: {kunde}", ln=True)
        pdf.cell(0, 10, f"Standort: {standort} | Prüfer: {inspektor}", ln=True)
        
        # Inhaltsverzeichnis Seite
        pdf.add_page()
        pdf.set_font("Arial", 'B', 18)
        pdf.cell(0, 15, "Inhaltsverzeichnis", ln=True)
        pdf.ln(5)
        toc_data = []

        # Details pro Seite
        for item in st.session_state.inspections:
            pdf.add_page()
            toc_data.append((item['Regal'], item['Stufe'], item['Bauteil'], item['Position'], pdf.page_no()))
            
            if item['Stufe'] == "ROT": pdf.set_fill_color(255, 200, 200)
            elif item['Stufe'] == "Gelb": pdf.set_fill_color(255, 243, 200)
            else: pdf.set_fill_color(200, 255, 200)
            
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(0, 15, f"REGAL: {item['Regal']} - {item['Stufe']}", ln=True, fill=True)
            
            pdf.ln(5)
            pdf.set_font("Arial", 'B', 13)
            pdf.cell(0, 8, "Bauteil:", ln=True)
            pdf.set_font("Arial", '', 13)
            pdf.cell(0, 8, f"{item['Bauteil']}", ln=True)
            
            pdf.ln(2)
            pdf.set_font("Arial", 'B', 13)
            pdf.cell(0, 8, "Position / Ebene:", ln=True)
            pdf.set_font("Arial", '', 13)
            pdf.cell(0, 8, f"{item['Position']}", ln=True)
            
            pdf.ln(2)
            pdf.set_font("Arial", 'B', 13)
            pdf.cell(0, 8, "Mangel & Massnahme:", ln=True)
            pdf.set_font("Arial", '', 12)
            pdf.multi_cell(0, 7, f"{item['Mangel']}\nMassnahme: {item['Massnahme']}")
            
            if item['Fotos']:
                pdf.ln(5)
                y_img = pdf.get_y()
                x_img = 10
                for p in item['Fotos']:
                    if os.path.exists(p):
                        pdf.image(p, x=x_img, y=y_img, w=50)
                        x_img += 55
                pdf.set_y(y_img + 45)

        # Inhaltsverzeichnis ausfüllen
        pdf.page = 2
        pdf.set_y(35)
        pdf.set_font("Arial", '', 11)
        for entry in toc_data:
            if entry[1] == "ROT": pdf.set_fill_color(255, 0, 0)
            elif entry[1] == "Gelb": pdf.set_fill_color(255, 243, 0)
            else: pdf.set_fill_color(0, 255, 0)
            pdf.ellipse(10, pdf.get_y()+2, 4, 4, style='F')
            pdf.set_x(18)
            pdf.cell(0, 10, f"Regal {entry[0]}: {entry[2]} ({entry[3]})", ln=False)
            pdf.set_x(165)
            pdf.cell(0, 10, f"Seite {entry[4]}", ln=True)

        pdf_bytes = pdf.output(dest='S').encode('latin-1', 'replace')
        st.download_button("📥 PDF Bericht herunterladen", data=pdf_bytes, file_name=f"Inspektion_{kunde}.pdf")