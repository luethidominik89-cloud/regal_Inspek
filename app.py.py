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
    
    pos = st.text_input("Genaue Position / Ebene / Feld", value=current_data["Position"])

with col2:
    gefahr = st.radio("Gefahrenstufe wählen", ["Grün", "Gelb", "ROT"], 
                      index=["Grün", "Gelb", "ROT"].index(current_data["Stufe"]), horizontal=True)
    
    mangel_opt = ["Stapleranprall", "Sicherungsstift fehlt", "Bodenanker lose", "Überladung", "Sonstiges"]
    mangel = st.selectbox("Mangel", mangel_opt)
    kommentar = st.text_input("Zusatz-Kommentar", value=current_data.get("Mangel", "").split(": ")[-1] if ":" in current_data["Mangel"] else "")
    massnahme = st.selectbox("Maßnahme", ["Beobachten", "Tausch binnen 4 Wo.", "SOFORT SPERREN", "Stift ersetzen"])

with col3:
    st.write("📸 **Fotos**")
    f1 = st.camera_input("Foto 1", key="cam1")
    f2 = st.camera_input("Foto 2", key="cam2")

# --- SPEICHER-BUTTONS ---
b_col1, b_col2 = st.columns(2)
if st.session_state.edit_index is None:
    if b_col1.button("✅ In Liste speichern", use_container_width=True):
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

# --- LISTE IN DER APP ---
if st.session_state.inspections:
    st.divider()
    st.subheader("📋 Erfasste Mängel")
    for idx, item in enumerate(st.session_state.inspections):
        c_info, c_edit, c_del = st.columns([7, 2, 1])
        icon = "🟢" if item['Stufe'] == "Grün" else "🟡" if item['Stufe'] == "Gelb" else "🔴"
        c_info.write(f"{icon} **#{idx+1} Regal {item['Regal']}** | {item['Bauteil']} - {item['Position']}")
        if c_edit.button("✏️", key=f"e_{idx}"):
            st.session_state.edit_index = idx
            st.rerun()
        if c_del.button("🗑️", key=f"d_{idx}"):
            st.session_state.inspections.pop(idx)
            st.rerun()

    # --- PDF GENERATOR ---
    if st.button("📄 PDF-Bericht generieren", type="primary", use_container_width=True):
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=20)
        
        # 1. Deckblatt
        pdf.add_page()
        pdf.set_font("Arial", 'B', 26)
        pdf.cell(0, 40, "Inspektionsbericht", ln=True, align='C')
        pdf.set_font("Arial", '', 14)
        pdf.cell(0, 10, f"Kunde: {kunde}", ln=True)
        pdf.cell(0, 10, f"Standort: {standort}", ln=True)
        pdf.cell(0, 10, f"Prüfer: {inspektor}", ln=True)
        pdf.cell(0, 10, f"Datum: {datetime.now().strftime('%d.%m.%Y')}", ln=True)
        
        # 2. Inhaltsverzeichnis (Wird später befüllt)
        pdf.add_page()
        pdf.set_font("Arial", 'B', 18)
        pdf.cell(0, 15, "Inhaltsverzeichnis", ln=True)
        pdf.ln(5)
        toc_page_index = 2
        toc_entries = []

        # 3. Mängel-Details (Fortlaufend)
        pdf.add_page()
        for item in st.session_state.inspections:
            # Merken der Position für das Inhaltsverzeichnis
            toc_entries.append((item['Regal'], item['Stufe'], item['Bauteil'], item['Position'], pdf.page_no()))
            
            # Seitenumbruch-Check
            if pdf.get_y() > 180:
                pdf.add_page()

            # Balken-Header
            if item['Stufe'] == "ROT": pdf.set_fill_color(255, 200, 200)
            elif item['Stufe'] == "Gelb": pdf.set_fill_color(255, 243, 200)
            else: pdf.set_fill_color(200, 255, 200)
            
            pdf.set_font("Arial", 'B', 14)
            pdf.cell(0, 12, f"REGAL-NR: {item['Regal']} - STATUS: {item['Stufe']}", ln=True, fill=True)
            
            # --- DETAILS UNTEREINANDER ---
            pdf.set_font("Arial", 'B', 11)
            pdf.cell(40, 8, "Bauteil:", ln=0)
            pdf.set_font("Arial", '', 11)
            pdf.cell(0, 8, f"{item['Bauteil']}", ln=True)
            
            pdf.set_font("Arial", 'B', 11)
            pdf.cell(40, 8, "Genaue Position:", ln=0)
            pdf.set_font("Arial", '', 11)
            pdf.cell(0, 8, f"{item['Position']}", ln=True)
            
            pdf.set_font("Arial", 'B', 11)
            pdf.cell(0, 8, "Mangel & Massnahme:", ln=True)
            pdf.set_font("Arial", '', 11)
            pdf.multi_cell(0, 6, f"{item['Mangel']}\nEmpfohlene Massnahme: {item['Massnahme']}")
            
            # Fotos
            if item['Fotos']:
                pdf.ln(2)
                y_imgs = pdf.get_y()
                x_imgs = 10
                for p in item['Fotos']:
                    if os.path.exists(p):
                        pdf.image(p, x=x_imgs, y=y_imgs, w=48)
                        x_imgs += 53
                pdf.set_y(y_imgs + 42)
            
            pdf.ln(5)
            pdf.line(10, pdf.get_y(), 200, pdf.get_y())
            pdf.ln(8)

        # Inhaltsverzeichnis Seite nachträglich beschreiben
        pdf.page = toc_page_index
        pdf.set_y(35)
        pdf.set_font("Arial", '', 11)
        for entry in toc_entries:
            if entry[1] == "ROT": pdf.set_fill_color(255, 0, 0)
            elif entry[1] == "Gelb": pdf.set_fill_color(255, 243, 0)
            else: pdf.set_fill_color(0, 255, 0)
            
            pdf.ellipse(10, pdf.get_y()+2, 4, 4, style='F')
            pdf.set_x(18)
            # HIER STEHT JETZT REGAL, BAUTEIL UND POSITION IM VERZEICHNIS
            pdf.cell(0, 10, f"Regal {entry[0]}: {entry[2]} ({entry[3]})", ln=False)
            pdf.set_x(165)
            pdf.cell(0, 10, f"Seite {entry[4]}", ln=True)

        pdf_bytes = pdf.output(dest='S').encode('latin-1', 'replace')
        st.download_button("📥 PDF herunterladen", data=pdf_bytes, file_name=f"Bericht_{kunde}.pdf")