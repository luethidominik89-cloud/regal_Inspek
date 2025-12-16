import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime
from PIL import Image

st.set_page_config(page_title="Regal-Check Profi", layout="wide")

if 'inspections' not in st.session_state:
    st.session_state.inspections = []

st.title("🛡️ Präzise Regal-Inspektion")

# --- STAMMDATEN ---
with st.expander("📋 Stammdaten"):
    c1, c2 = st.columns(2)
    kunde = c1.text_input("Kunde")
    inspektor = c2.text_input("Prüfer")

# --- ERWEITERTE SCHADENSAUFNAHME ---
st.divider()
st.subheader("⚠️ Detail-Erfassung")
col1, col2, col3 = st.columns([1, 1, 1])

with col1:
    regal_nr = st.text_input("Regal-Nummer (z.B. R-01)")
    bauteil = st.selectbox("Bauteil", ["Stütze", "Traverse", "Rammschutz", "Aussteifung"])
    
    # DYNAMISCHE FELDER je nach Bauteil
    detail_position = ""
    if bauteil == "Stütze":
        detail_position = st.text_input("Genaue Stütze", placeholder="z.B. Vorne rechts / 3. Stütze von links")
    elif bauteil == "Traverse":
        detail_position = st.text_input("Ebene / Position", placeholder="z.B. Ebene 2, zwischen Ständer A und B")
    else:
        detail_position = st.text_input("Zusatz-Info zur Position")

with col2:
    gefahr = st.select_slider("Gefahrenstufe", options=["Grün", "Gelb", "ROT"], value="Grün")
    ursache = st.text_input("Mangel / Ursache")
    massnahme = st.text_area("Maßnahme")

with col3:
    foto = st.camera_input("Schaden fotografieren")

if st.button("Eintrag speichern"):
    if not regal_nr or not detail_position:
        st.error("Bitte Regal-Nummer und genaue Position angeben!")
    else:
        img_path = None
        if foto:
            img = Image.open(foto)
            img_path = f"temp_{len(st.session_state.inspections)}.jpg"
            img.save(img_path)

        st.session_state.inspections.append({
            "Regal": regal_nr,
            "Bauteil": bauteil,
            "Position": detail_position,
            "Stufe": gefahr,
            "Mangel": ursache,
            "Massnahme": massnahme,
            "Foto": img_path
        })
        st.success(f"Eintrag für {bauteil} an Position {detail_position} gespeichert.")

# --- BERICHTS-VORSCHAU & PDF ---
if st.session_state.inspections:
    st.divider()
    df = pd.DataFrame(st.session_state.inspections).drop(columns=['Foto'])
    st.table(df)

    if st.button("📄 PDF mit Details generieren"):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, f"Prüfbericht: {kunde}", ln=True, align='C')
        pdf.ln(5)

        for item in st.session_state.inspections:
            pdf.set_fill_color(240, 240, 240)
            pdf.set_font("Arial", 'B', 11)
            
            # Farb-Logik
            color = (255, 0, 0) if item['Stufe'] == "ROT" else (200, 150, 0) if item['Stufe'] == "Gelb" else (0, 128, 0)
            pdf.set_text_color(*color)
            
            pdf.cell(0, 10, f"REGAL: {item['Regal']} | {item['Bauteil']} ({item['Stufe']})", ln=True, fill=True)
            
            pdf.set_text_color(0, 0, 0)
            pdf.set_font("Arial", size=10)
            pdf.multi_cell(0, 6, txt=(f"GENAUE POSITION: {item['Position']}\n"
                                     f"MANGEL: {item['Mangel']}\n"
                                     f"MASSNAHME: {item['Massnahme']}"))
            
            if item['Foto']:
                pdf.image(item['Foto'], x=150, w=45)
            
            pdf.ln(10)
            pdf.line(10, pdf.get_y(), 200, pdf.get_y())
            pdf.ln(5)

        pdf_bytes = pdf.output(dest='S').encode('latin-1', 'replace')
        st.download_button("📥 PDF Herunterladen", data=pdf_bytes, file_name=f"Bericht_{kunde}.pdf")