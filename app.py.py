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
if 'form_iteration' not in st.session_state:
    st.session_state.form_iteration = 0

def reset_form():
    st.session_state.form_iteration += 1
    st.session_state.edit_index = None

st.title("🛡️ Regal-Inspektion")

# --- STAMMDATEN ---
with st.expander("📋 Kunden- & Standortdetails", expanded=True):
    c_head1, c_head2 = st.columns(2)
    kunde = c_head1.text_input("Kunde / Firma", placeholder="z.B. Muster GmbH")
    standort = c_head1.text_input("Standort (Stadt)", placeholder="z.B. Berlin")
    gebaeude = c_head2.text_input("Gebäude / Werk / Halle", placeholder="z.B. Halle 4")
    inspektor = c_head2.text_input("Prüfer Name", placeholder="Dein Name")

# --- EINGABEMASKE ---
st.divider()
iter_key = st.session_state.form_iteration
col1, col2, col3 = st.columns([1, 1, 1])

with col1:
    regal_nr = st.text_input("Regal-Nummer", placeholder="z.B. R-001", key=f"reg_{iter_key}")
    bauteil = st.selectbox("Bauteil", ["Stütze", "Traverse", "Rammschutz", "Aussteifung"], key=f"bt_{iter_key}")
    pos = st.text_input("Position / Ebene / Feld", placeholder="z.B. Ebene 2, Feld 5", key=f"pos_{iter_key}")

with col2:
    # ERSATZ FÜR DEN ROTEN SLIDER: Klare Buttons
    st.write("**Gefahrenstufe wählen:**")
    gefahr = st.radio("Status", ["Grün", "Gelb", "ROT"], horizontal=True, key=f"st_{iter_key}")
    
    mangel = st.selectbox("Mangel", ["Stapleranprall", "Sicherungsstift fehlt", "Bodenanker lose", "Überladung", "Sonstiges"], key=f"ma_{iter_key}")
    kommentar = st.text_input("Zusatz-Kommentar", placeholder="z.B. Delle > 3mm", key=f"ko_{iter_key}")
    massnahme = st.selectbox("Maßnahme", ["Beobachten", "Tausch binnen 4 Wo.", "SOFORT SPERREN", "Stift ersetzen"], key=f"ms_{iter_key}")

with col3:
    st.write("📸 **Fotos**")
    f1 = st.camera_input("1. Detail (Schaden)", key=f"c1_{iter_key}")
    f2 = st.camera_input("2. Standort (Übersicht)", key=f"c2_{iter_key}")
    f3 = st.camera_input("3. Traglastschild", key=f"c3_{iter_key}")

# --- SPEICHERN ---
if st.button("✅ Regal speichern", use_container_width=True):
    if not regal_nr:
        st.error("Bitte Regal-Nummer angeben!")
    else:
        fotos = []
        for f in [f1, f2, f3]:
            if f:
                img = Image.open(f).convert("RGB")
                path = f"img_{datetime.now().timestamp()}.jpg"
                img.save(path)
                fotos.append(path)
        
        st.session_state.inspections.append({
            "Regal": regal_nr, "Bauteil": bauteil, "Position": pos,
            "Stufe": gefahr, "Mangel": f"{mangel}: {kommentar}", "Massnahme": massnahme, "Fotos": fotos
        })
        reset_form()
        st.rerun()

# --- AUFZÄHLUNG & PDF ---
if st.session_state.inspections:
    st.divider()
    st.subheader("📋 Erfasste Mängel")
    for idx, item in enumerate(st.session_state.inspections):
        c_i, c_d = st.columns([9, 1])
        icon = "🟢" if item['Stufe'] == "Grün" else "🟡" if item['Stufe'] == "Gelb" else "🔴"
        c_i.write(f"{icon} **#{idx+1} Regal {item['Regal']}** | {item['Bauteil']} ({item['Position']})")
        if c_d.button("🗑️", key=f"del_{idx}"):
            st.session_state.inspections.pop(idx)
            st.rerun()

    if st.button("📄 PDF mit Inhaltsverzeichnis generieren", type="primary", use_container_width=True):
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=20)
        
        # 1. Deckblatt
        pdf.add_page()
        pdf.set_font("Arial", 'B', 24)
        pdf.cell(0, 40, "Inspektionsbericht", ln=True, align='C')
        pdf.set_font("Arial", '', 14)
        pdf.cell(0, 10, f"Kunde: {kunde}", ln=True)
        pdf.cell(0, 10, f"Standort: {standort} | Bereich: {gebaeude}", ln=True)
        pdf.cell(0, 10, f"Datum: {datetime.now().strftime('%d.%m.%Y')}", ln=True)
        
        # 2. Inhaltsverzeichnis (Seite 2)
        pdf.add_page()
        pdf.set_font("Arial", 'B', 18)
        pdf.cell(0, 15, "Inhaltsverzeichnis", ln=True)
        pdf.ln(5)
        toc_entries = []

        # 3. Details (Fortlaufend)
        pdf.add_page()
        for item in st.session_state.inspections:
            # Position merken
            toc_entries.append((item['Regal'], item['Stufe'], item['Bauteil'], item['Position'], pdf.page_no()))
            
            if pdf.get_y() > 180: pdf.add_page()

            if item['Stufe'] == "ROT": pdf.set_fill_color(255, 200, 200)
            elif item['Stufe'] == "Gelb": pdf.set_fill_color(255, 243, 200)
            else: pdf.set_fill_color(200, 255, 200)
            
            pdf.set_font("Arial", 'B', 14)
            pdf.cell(0, 12, f"REGAL: {item['Regal']} - {item['Stufe']}", ln=True, fill=True)
            pdf.set_font("Arial", '', 11)
            pdf.cell(0, 8, f"Bauteil: {item['Bauteil']} | Position: {item['Position']}", ln=True)
            pdf.multi_cell(0, 6, f"Mangel: {item['Mangel']}\nMassnahme: {item['Massnahme']}")
            
            if item['Fotos']:
                pdf.ln(2)
                y_img, x_img = pdf.get_y(), 10
                for p in item['Fotos']:
                    if os.path.exists(p):
                        pdf.image(p, x=x_img, y=y_img, w=45)
                        x_img += 50
                pdf.set_y(y_img + 42)
            pdf.ln(5); pdf.line(10, pdf.get_y(), 200, pdf.get_y()); pdf.ln(5)

        # Inhaltsverzeichnis füllen
        pdf.page = 2
        pdf.set_y(35)
        pdf.set_font("Arial", '', 11)
        for entry in toc_entries:
            # Punktfarbe zeichnen
            if entry[1] == "ROT": pdf.set_fill_color(255, 0, 0)
            elif entry[1] == "Gelb": pdf.set_fill_color(255, 243, 0)
            else: pdf.set_fill_color(0, 255, 0)
            pdf.ellipse(10, pdf.get_y()+2, 4, 4, style='F')
            pdf.set_x(18)
            pdf.cell(0, 10, f"Regal {entry[0]}: {entry[2]} ({entry[3]})", ln=False)
            pdf.set_x(165)
            pdf.cell(0, 10, f"Seite {entry[4]}", ln=True)

        pdf_bytes = pdf.output(dest='S').encode('latin-1', 'replace')
        st.download_button("📥 PDF Bericht laden", data=pdf_bytes, file_name=f"Bericht_{kunde}.pdf")