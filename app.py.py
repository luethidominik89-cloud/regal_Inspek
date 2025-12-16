import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime
from PIL import Image
import io

# Konfiguration der Seite
st.set_page_config(page_title="Regal-Check Profi Plus", layout="wide")

# Initialisierung des Speichers für die Sitzung
if 'inspections' not in st.session_state:
    st.session_state.inspections = []

st.title("🛡️ Professionelle Regal-Inspektion")

# --- ERWEITERTE STAMMDATEN ---
with st.expander("📋 Kunden- & Standortdetails", expanded=True):
    c1, c2 = st.columns(2)
    with c1:
        kunde = st.text_input("Kunde / Firma")
        standort = st.text_input("Standort (Stadt / Werk)")
    with c2:
        gebaeude = st.text_input("Gebäudeteil / Halle (z.B. Halle A, OG)")
        inspektor = st.text_input("Prüfer")

# --- SCHADENSAUFNAHME ---
st.divider()
st.subheader("⚠️ Mängel-Erfassung")
col1, col2, col3 = st.columns([1, 1, 1])

with col1:
    regal_nr = st.text_input("Regal-Nummer (z.B. R-01)")
    
    # Auswahl der Regalanlage
    regal_typ = st.selectbox("Regalanlage", [
        "Palettenregal", 
        "Fachbodenregal", 
        "Kragarmregal", 
        "Einfahrregal", 
        "Durchlaufregal", 
        "Verschieberegal",
        "Sonstiges"
    ])
    
    bauteil = st.selectbox("Bauteil", ["Stütze", "Traverse", "Rammschutz", "Aussteifung", "Fachboden"])
    
    # Abfrage der genauen Position basierend auf dem Bauteil
    if bauteil == "Stütze":
        pos = st.text_input("Genaue Stütze", placeholder="z.B. vorne links / 2. Pfosten")
    elif bauteil == "Traverse":
        pos = st.text_input("Ebene / Position", placeholder="z.B. Ebene 3, Feld 2")
    else:
        pos = st.text_input("Zusatz-Info Position", placeholder="z.B. Bodenzone")

with col2:
    gefahr = st.select_slider("Gefahrenstufe", options=["Grün", "Gelb", "ROT"], value="Grün")
    
    # Dropdown für gängige Mängel
    mangel_liste = [
        "Stapleranprall / Verformung",
        "Fehlender Sicherungsstift",
        "Riss in Schweißnaht",
        "Lockerung der Bodenanker",
        "Überladung / Durchbiegung",
        "Sicherheitshinweis fehlt",
        "Sonstiges (siehe Kommentar)"
    ]
    mangel_auswahl = st.selectbox("Art des Mangels", mangel_liste)
    mangel_detail = st.text_input("Zusatzkommentar (optional)")

    # Dropdown für gängige Maßnahmen
    massnahmen_liste = [
        "Keine sofortige Maßnahme (Beobachtung)",
        "Sicherungstifte ersetzen",
        "Bauteil innerhalb 4 Wochen austauschen",
        "SOFORTIGE SPERRUNG & Entladung",
        "Bodenanker nachziehen",
        "Belastung reduzieren",
        "Prüfplakette anbringen"
    ]
    gewaehlte_massnahme = st.selectbox("Erforderliche Maßnahme", massnahmen_liste)

with col3:
    foto = st.camera_input("Foto aufnehmen")

# Button zum Speichern
if st.button("Schaden speichern"):
    if not regal_nr or not pos:
        st.error("Bitte Regal-Nr. und Position angeben!")
    else:
        img_path = None
        if foto:
            img = Image.open(foto)
            # Konvertierung zu RGB falls nötig (für PDF Export)
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            img_path = f"temp_{len(st.session_state.inspections)}.jpg"
            img.save(img_path)

        st.session_state.inspections.append({
            "Regal": regal_nr,
            "Typ": regal_typ,
            "Bauteil": bauteil,
            "Position": pos,
            "Stufe": gefahr,
            "Mangel": f"{mangel_auswahl} {mangel_detail}".strip(),
            "Massnahme": gewaehlte_massnahme,
            "Foto": img_path
        })
        st.success(f"Eintrag für {regal_typ} (Nr. {regal_nr}) gespeichert.")

# --- BERICHT & PDF ---
if st.session_state.inspections:
    st.divider()
    st.subheader("Aktuelle Liste")
    df = pd.DataFrame(st.session_state.inspections).drop(columns=['Foto'])
    st.dataframe(df, use_container_width=True)

    if st.button("📄 PDF-Prüfbericht generieren"):
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        
        # Titel
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, "Regal-Inspektionsprotokoll", ln=True, align='C')
        
        # Stammdaten im PDF
        pdf.set_font("Arial", size=10)
        pdf.cell(0, 8, f"Kunde: {kunde} | Standort: {standort} | Bereich: {gebaeude}", ln=True, align='C')
        pdf.ln(10)

        for item in st.session_state.inspections:
            # Kopfzeile für jeden Mangel (Hintergrundfarbe)
            pdf.set_fill_color(240, 240, 240)
            pdf.set_font("Arial", 'B', 11)
            
            # Textfarbe basierend auf Gefahr
            if item['Stufe'] == "ROT":
                pdf.set_text_color(255, 0, 0)
            elif item['Stufe'] == "Gelb":
                pdf.set_text_color(200, 150, 0)
            else:
                pdf.set_text_color(0, 128, 0)
            
            pdf.cell(0, 10, f"REGAL NR: {item['Regal']} ({item['Typ']}) - Status: {item['Stufe']}", ln=True, fill=True)
            
            # Details zum Mangel
            pdf.set_text_color(0, 0, 0)
            pdf.set_font("Arial", size=10)
            content = (f"Bauteil/Position: {item['Bauteil']} - {item['Position']}\n"
                       f"Mangel: {item['Mangel']}\n"
                       f"Massnahme: {item['Massnahme']}")
            pdf.multi_cell(0, 6, content)
            
            # Foto einbetten
            if item['Foto']:
                try:
                    pdf.image(item['Foto'], x=150, w=45)
                except:
                    pdf.cell(0, 10, "Foto konnte nicht geladen werden.", ln=True)
            
            pdf.ln(5)
            pdf.line(10, pdf.get_y(), 200, pdf.get_y())
            pdf.ln(5)

        # PDF zum Download anbieten
        pdf_bytes = pdf.output(dest='S').encode('latin-1', 'replace')
        st.download_button("📥 PDF-Bericht herunterladen", data=pdf_bytes, file_name=f"Bericht_{kunde}_{standort}.pdf")