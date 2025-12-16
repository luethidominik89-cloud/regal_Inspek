import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime
from PIL import Image
import os

st.set_page_config(page_title="Regal-Check Profi Plus", layout="wide")

# Speicher für die Inspektionen initialisieren
if 'inspections' not in st.session_state:
    st.session_state.inspections = []

st.title("🛡️ Professionelle Regal-Inspektion")

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
    pos = st.text_input("Genaue Position (z.B. Ebene 2, von links gezählt)")

with col2:
    gefahr = st.select_slider("Gefahrenstufe", options=["Grün", "Gelb", "ROT"], value="Grün")
    mangel_auswahl = st.selectbox("Art des Mangels", ["Stapleranprall", "Sicherungsstift fehlt", "Bodenanker lose", "Überladung", "Schweißnaht defekt", "Sonstiges"])
    mangel_detail = st.text_input("Kommentar zum Mangel")
    
    massnahmen_liste = ["Beobachten", "Tausch innerhalb 4 Wochen", "SOFORT SPERREN / ENTLADEN", "Sicherungsstift ersetzen", "Bodenanker nachziehen"]
    massnahme = st.selectbox("Maßnahme", massnahmen_liste)

with col3:
    st.write("📸 **Dokumentation**")
    f1 = st.camera_input("1. Detailaufnahme (Schaden)", key="f1")
    f2 = st.camera_input("2. Übersicht (Standort/Gang)", key="f2")
    f3 = st.camera_input("3. Zusatzfoto", key="f3")

# Speichern Button
if st.button("Schaden zur Liste hinzufügen"):
    if not regal_nr or not pos:
        st.error("Bitte Regal-Nummer und Position angeben!")
    else:
        saved_photos = []
        for i, f in enumerate([f1, f2, f3]):
            if f:
                img = Image.open(f)
                if img.mode in ("RGBA", "P"): img = img.convert("RGB")
                path = f"temp_{len(st.session_state.inspections)}_{i}.jpg"
                img.save(path)
                saved_photos.append(path)

        st.session_state.inspections.append({
            "Regal": regal_nr, "Typ": regal_typ, "Bauteil": bauteil,
            "Position": pos, "Stufe": gefahr, "Mangel": f"{mangel_auswahl}: {mangel_detail}",
            "Massnahme": massnahme, "Fotos": saved_photos
        })
        st.success("Eintrag gespeichert!")

# --- VERWALTUNG DER LISTE (RÜCKGÄNGIG FUNKTION) ---
if st.session_state.inspections:
    st.divider()
    st.subheader("Vorschau & Korrektur")
    
    col_del1, col_del2 = st.columns(2)
    if col_del1.button("⬅️ Letzten Eintrag löschen (Rückgängig)"):
        st.session_state.inspections.pop()
        st.rerun()
    if col_del2.button("🗑️ Ganze Liste leeren"):
        st.session_state.inspections = []
        st.rerun()

    df = pd.DataFrame(st.session_state.inspections).drop(columns=['Fotos'])
    st.table(df)

    # --- PDF GENERIERUNG ---
    if st.button("📄 Finalen PDF-Bericht generieren"):
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        
        # Header
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, "Regal-Inspektionsprotokoll", ln=True, align='C')
        pdf.set_font("Arial", '', 10)
        pdf.cell(0, 7, f"Kunde: {kunde} | Standort: {standort} | Prüfer: {inspektor}", ln=True, align='C')
        pdf.ln(10)

        for item in st.session_state.inspections:
            # Hintergrundfarbe für den Balken setzen
            if item['Stufe'] == "ROT":
                pdf.set_fill_color(255, 200, 200) # Hellrot
                pdf.set_text_color(150, 0, 0)     # Dunkelrot für Text
            elif item['Stufe'] == "Gelb":
                pdf.set_fill_color(255, 243, 200) # Hellgelb/Orange
                pdf.set_text_color(150, 100, 0)
            else:
                pdf.set_fill_color(200, 255, 200) # Hellgrün
                pdf.set_text_color(0, 100, 0)

            pdf.set_font("Arial", 'B', 11)
            pdf.cell(0, 10, f"REGAL: {item['Regal']} ({item['Typ']}) - STATUS: {item['Stufe']}", ln=True, fill=True)
            
            pdf.set_text_color(0, 0, 0)
            pdf.set_font("Arial", size=10)
            pdf.multi_cell(0, 6, f"Bauteil/Pos: {item['Bauteil']} - {item['Position']}\nMangel: {item['Mangel']}\nMassnahme: {item['Massnahme']}")
            
            # Fotos nebeneinander
            if item['Fotos']:
                pdf.ln(2)
                x_start = 10
                for img_p in item['Fotos']:
                    pdf.image(img_p, x=x_start, w=40)
                    x_start += 45
                pdf.ln(32)
            
            pdf.ln(5)
            pdf.line(10, pdf.get_y(), 200, pdf.get_y())
            pdf.ln(5)

        pdf_bytes = pdf.output(dest='S').encode('latin-1', 'replace')
        st.download_button("📥 PDF Bericht herunterladen", data=pdf_bytes, file_name=f"Inspektion_{kunde}.pdf")