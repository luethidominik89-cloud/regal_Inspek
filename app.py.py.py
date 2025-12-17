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

# Funktion zum Zurücksetzen der Felder (indem man den Key-Counter erhöht)
if 'form_iteration' not in st.session_state:
    st.session_state.form_iteration = 0

def reset_form():
    st.session_state.edit_index = None
    st.session_state.form_iteration += 1

st.title("🛡️ Professionelle Regal-Inspektion")

# --- STAMMDATEN ---
with st.expander("📋 Kunden- & Standortdetails", expanded=True):
    c_head1, c_head2 = st.columns(2)
    kunde = c_head1.text_input("Kunde / Firma", placeholder="z.B. Muster GmbH")
    standort = c_head1.text_input("Standort / Werk", placeholder="z.B. Berlin Werk 2")
    gebaeude = c_head2.text_input("Halle / Bereich", placeholder="z.B. Halle 4 / Wareneingang")
    inspektor = c_head2.text_input("Prüfer Name", placeholder="Dein Name")

# --- EINGABEMASKE ---
st.divider()
if st.session_state.edit_index is not None:
    st.warning(f"🔄 Bearbeitung: Eintrag #{st.session_state.edit_index + 1}")
    current_data = st.session_state.inspections[st.session_state.edit_index]
else:
    # Standardwerte für ein leeres Formular
    current_data = {"Regal": "", "Typ": "Palettenregal", "Bauteil": "Stütze", "Position": "", "Stufe": "Grün", "Mangel": "Stapleranprall", "Massnahme": "Beobachten", "Fotos": []}

# Nutze den iteration_key um Felder nach dem Speichern zu leeren
iter_key = st.session_state.form_iteration

col1, col2, col3 = st.columns([1, 1, 1])

with col1:
    regal_nr = st.text_input("Regal-Nummer", value=current_data["Regal"], placeholder="z.B. R-001", key=f"regal_{iter_key}")
    regal_typ = st.selectbox("Regalanlage", ["Palettenregal", "Fachbodenregal", "Kragarmregal", "Durchlaufregal", "Sonstiges"], 
                             index=["Palettenregal", "Fachbodenregal", "Kragarmregal", "Durchlaufregal", "Sonstiges"].index(current_data["Typ"]), 
                             key=f"typ_{iter_key}")
    bauteil = st.selectbox("Bauteil", ["Stütze", "Traverse", "Rammschutz", "Aussteifung"], 
                           index=["Stütze", "Traverse", "Rammschutz", "Aussteifung"].index(current_data["Bauteil"]),
                           key=f"bt_{iter_key}")
    
    # Dynamische Platzhalter
    p_hold = "z.B. Pfosten vorne links" if bauteil == "Stütze" else "z.B. Ebene 3, Feld 10" if bauteil == "Traverse" else "Genaue Lage"
    pos = st.text_input("Position / Ebene / Feld", value=current_data["Position"], placeholder=p_hold, key=f"pos_{iter_key}")

with col2:
    st.write("**Gefahrenstufe:**")
    gefahr = st.radio("Status", ["Grün", "Gelb", "ROT"], 
                      index=["Grün", "Gelb", "ROT"].index(current_data["Stufe"]), 
                      horizontal=True, key=f"stufe_{iter_key}")
    mangel = st.selectbox("Hauptmangel", ["Stapleranprall", "Sicherungsstift fehlt", "Bodenanker lose", "Überladung", "Verformung", "Sonstiges"], key=f"mangel_{iter_key}")
    kommentar = st.text_input("Zusatz-Kommentar (Vorschlag)", placeholder="z.B. Delle > 3mm", key=f"kommentar_{iter_key}")
    massnahme = st.selectbox("Maßnahme", ["Beobachten", "Tausch binnen 4 Wo.", "SOFORT SPERREN", "Stift ersetzen", "Anker nachziehen"], key=f"mass_{iter_key}")

with col3:
    st.write("📸 **Dokumentation**")
    f1 = st.camera_input("1. Detailaufnahme (Schaden)", key=f"cam1_{iter_key}")
    f2 = st.camera_input("2. Standortaufnahme (Übersicht)", key=f"cam2_{iter_key}")
    f3 = st.camera_input("3. Traglastschild / Sonstiges", key=f"cam3_{iter_key}")

# --- SPEICHERN ---
if st.button("✅ Eintrag speichern & Formular leeren", use_container_width=True):
    if not regal_nr:
        st.error("Bitte Regal-Nummer angeben!")
    else:
        new_photos = []
        # Wenn wir bearbeiten, behalten wir alte Fotos, falls keine neuen gemacht wurden
        if st.session_state.edit_index is not None:
            new_photos = current_data.get("Fotos", [])
            
        for f in [f1, f2, f3]:
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
        else:
            st.session_state.inspections.append(entry)
        
        reset_form()
        st.rerun()

# --- AUFZÄHLUNG ---
if st.session_state.inspections:
    st.divider()
    st.subheader("📋 Aktuelle Mängelliste")
    for idx, item in enumerate(st.session_state.inspections):
        c_i, c_e, c_d = st.columns([7, 2, 1])
        icon = "🟢" if item['Stufe'] == "Grün" else "🟡" if item['Stufe'] == "Gelb" else "🔴"
        c_i.write(f"{icon} **#{idx+1} Regal {item['Regal']}** | {item['Bauteil']} ({item['Position']})")
        if c_e.button("✏️", key=f"edit_btn_{idx}"):
            st.session_state.edit_index = idx
            st.rerun()
        if c_d.button("🗑️", key=f"del_btn_{idx}"):
            st.session_state.inspections.pop(idx)
            st.rerun()

    # --- PDF ---
    if st.button("📄 PDF-Bericht erstellen", type="primary", use_container_width=True):
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=20)
        pdf.add_page()
        pdf.set_font("Arial", 'B', 24)
        pdf.cell(0, 40, "Inspektionsbericht Regalanlagen", ln=True, align='C')
        pdf.set_font("Arial", '', 14)
        pdf.cell(0, 10, f"Kunde: {kunde}", ln=True)
        pdf.cell(0, 10, f"Standort: {standort} | Prüfer: {inspektor}", ln=True)
        pdf.ln(10)
        
        for item in st.session_state.inspections:
            if pdf.get_y() > 160: pdf.add_page()
            if item['Stufe'] == "ROT": pdf.set_fill_color(255, 200, 200)
            elif item['Stufe'] == "Gelb": pdf.set_fill_color(255, 243, 200)
            else: pdf.set_fill_color(200, 255, 200)
            
            pdf.set_font("Arial", 'B', 14)
            pdf.cell(0, 12, f"REGAL: {item['Regal']} - STATUS: {item['Stufe']}", ln=True, fill=True)
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(45, 8, "Bauteil:", ln=0); pdf.set_font("Arial", '', 12); pdf.cell(0, 8, f"{item['Bauteil']}", ln=True)
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(45, 8, "Position:", ln=0); pdf.set_font("Arial", '', 12); pdf.cell(0, 8, f"{item['Position']}", ln=True)
            pdf.set_font("Arial", 'B', 12); pdf.cell(0, 8, "Beschreibung:", ln=True)
            pdf.set_font("Arial", '', 11); pdf.multi_cell(0, 7, f"{item['Mangel']}\nMassnahme: {item['Massnahme']}")
            
            if item['Fotos']:
                pdf.ln(3)
                y_imgs, x_imgs = pdf.get_y(), 10
                for p in item['Fotos'][:3]:
                    if os.path.exists(p):
                        pdf.image(p, x=x_imgs, y=y_imgs, w=45)
                        x_imgs += 50
                pdf.set_y(y_imgs + 42)
            pdf.ln(5); pdf.line(10, pdf.get_y(), 200, pdf.get_y()); pdf.ln(10)

        pdf_bytes = pdf.output(dest='S').encode('latin-1', 'replace')
        st.download_button("📥 PDF Herunterladen", data=pdf_bytes, file_name=f"Bericht_{kunde}.pdf")