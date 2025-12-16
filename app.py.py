import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime
from PIL import Image
import io
import os

# Konfiguration der Seite
st.set_page_config(page_title="Regal-Check Profi", layout="wide")

# Speicher für die Sitzung initialisieren
if 'inspections' not in st.session_state:
    st.session_state.inspections = []
if 'edit_index' not in st.session_state:
    st.session_state.edit_index = None

st.title("🛡️ Regal-Inspektions-System")

# --- STAMMDATEN ---
with st.expander("📋 Kunden- & Standortdetails", expanded=True):
    c1, c2 = st.columns(2)
    with c1:
        kunde = st.text_input("Kunde / Firma", key="k_name")
        standort = st.text_input("Standort / Werk", key="k_ort")
    with c2:
        gebaeude = st.text_input("Halle / Bereich", key="k_halle")
        inspektor = st.text_input("Prüfer Name", key="k_pruefer")

# --- STATISTIK ---
if st.session_state.inspections:
    df_stat = pd.DataFrame(st.session_state.inspections)
    stats = df_stat['Stufe'].value_counts()
    st.divider()
    st.subheader("📊 Aktuelle Statistik")
    s1, s2, s3, s4 = st.columns(4)
    s1.metric("Gesamt", len(df_stat))
    s2.metric("🟢 Grün", stats.get("Grün", 0))
    s3.metric("🟡 Gelb", stats.get("Gelb", 0))
    s4.metric("🔴 ROT", stats.get("ROT", 0))

# --- EINGABEMASKE ---
st.divider()
if st.session_state.edit_index is not None:
    st.info(f"🔄 Bearbeite Eintrag #{st.session_state.edit_index + 1}")
    data = st.session_state.inspections[st.session_state.edit_index]
else:
    data = {"Regal": "", "Typ": "Palettenregal", "Bauteil": "Stütze", "Position": "", "Stufe": "Grün", "Mangel": "Stapleranprall", "Massnahme": "Beobachten", "Fotos": []}

col1, col2, col3 = st.columns([1, 1, 1])

with col1:
    regal_nr = st.text_input("Regal-Nummer", value=data["Regal"])
    regal_typ = st.selectbox("Regalanlage", ["Palettenregal", "Fachbodenregal", "Kragarmregal", "Durchlaufregal", "Sonstiges"], index=0)
    
    # Bauteil Auswahl
    bauteil_liste = ["Stütze", "Traverse", "Rammschutz", "Aussteifung", "Fachboden"]
    bauteil_index = bauteil_liste.index(data["Bauteil"]) if data["Bauteil"] in bauteil_liste else 0
    bauteil = st.selectbox("Bauteil", bauteil_liste, index=bauteil_index)
    
    # DYNAMISCHE POSITIONSEINGABE basierend auf Bauteil
    if bauteil == "Stütze":
        pos_label = "Position (z.B. vorne links, 3. Pfosten)"
        pos_placeholder = "vorne rechts"
    elif bauteil == "Traverse":
        pos_label = "Ebene und Feld (z.B. Ebene 3, Feld 12)"
        pos_placeholder = "E3, F12"
    elif bauteil == "Rammschutz":
        pos_label = "Position (z.B. Ecke links, Regal-Stirnseite)"
        pos_placeholder = "Ecke vorne"
    else:
        pos_label = "Genaue Position"
        pos_placeholder = "z.B. Bodenzone"
        
    pos = st.text_input(pos_label, value=data["Position"], placeholder=pos_placeholder)

with col2:
    st.write("**Gefahrenstufe:**")
    gefahr = st.radio("Status wählen", ["Grün", "Gelb", "ROT"], index=["Grün", "Gelb", "ROT"].index(data["Stufe"]), horizontal=True)
    
    mangel = st.selectbox("Mangel", ["Stapleranprall", "Sicherungsstift fehlt", "Bodenanker lose", "Überladung", "Verformung", "Sonstiges"])
    kommentar = st.text_input("Zusatz-Kommentar", value=data.get("Mangel", "").split(": ")[-1] if ":" in data["Mangel"] else "")
    massnahme = st.selectbox("Maßnahme", ["Beobachten", "Tausch binnen 4 Wo.", "SOFORT SPERREN", "Stift ersetzen", "Anker nachziehen"])

with col3:
    st.write("📸 **Dokumentation**")
    f1 = st.camera_input("1. Detailaufnahme", key="cam_1")
    f2 = st.camera_input("2. Übersicht", key="cam_2")
    f3 = st.camera_input("3. Zusatzfoto", key="cam_3")

# Buttons für Speichern / Korrigieren
btn_col1, btn_col2 = st.columns(2)
if st.session_state.edit_index is None:
    if btn_col1.button("✅ Schaden speichern"):
        current_photos = []
        for i, f in enumerate([f1, f2, f3]):
            if f:
                img = Image.open(f).convert("RGB")
                path = f"img_{datetime.now().timestamp()}_{i}.jpg"
                img.save(path)
                current_photos.append(path)
        
        st.session_state.inspections.append({
            "Regal": regal_nr, "Typ": regal_typ, "Bauteil": bauteil, "Position": pos,
            "Stufe": gefahr, "Mangel": f"{mangel}: {kommentar}", "Massnahme": massnahme, "Fotos": current_photos
        })
        st.rerun()
else:
    if btn_col1.button("💾 Änderungen übernehmen"):
        st.session_state.inspections[st.session_state.edit_index].update({
            "Regal": regal_nr, "Typ": regal_typ, "Bauteil": bauteil, "Position": pos,
            "Stufe": gefahr, "Mangel": f"{mangel}: {kommentar}", "Massnahme": massnahme
        })
        st.session_state.edit_index = None
        st.rerun()
    if btn_col2.button("🚫 Abbrechen"):
        st.session_state.edit_index = None
        st.rerun()

# --- LISTE UND PDF EXPORT ---
if st.session_state.inspections:
    st.divider()
    st.subheader("📋 Erfasste Mängel")
    for idx, item in enumerate(st.session_state.inspections):
        c_info, c_edit = st.columns([8, 2])
        status_icon = "🟢" if item['Stufe'] == "Grün" else "🟡" if item['Stufe'] == "Gelb" else "🔴"
        c_info.write(f"{status_icon} **#{idx+1} Regal {item['Regal']}** - {item['Bauteil']} ({item['Position']})")
        if c_edit.button("✏️ Bearbeiten", key=f"btn_edit_{idx}"):
            st.session_state.edit_index = idx
            st.rerun()

    if st.button("📄 Finalen PDF-Bericht generieren"):
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        
        # --- SEITE 1: DECKBLATT ---
        pdf.add_page()
        pdf.set_font("Arial", 'B', 22)
        pdf.cell(0, 30, "Inspektionsbericht Regalanlagen", ln=True, align='C')
        pdf.set_font("Arial", '', 12)
        pdf.cell(0, 10, f"Kunde: {kunde}", ln=True)
        pdf.cell(0, 10, f"Standort: {standort} | Bereich: {gebaeude}", ln=True)
        pdf.cell(0, 10, f"Prüfer: {inspektor} | Datum: {datetime.now().strftime('%d.%m.%Y')}", ln=True)
        pdf.ln(15)
        
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 10, "Zusammenfassung der Ergebnisse:", ln=True)
        pdf.set_font("Arial", '', 12)
        stats_data = pd.DataFrame(st.session_state.inspections)['Stufe'].value_counts()
        pdf.cell(0, 8, f"- Gesamtanzahl der Prüfpunkte: {len(st.session_state.inspections)}", ln=True)
        pdf.set_text_color(0, 100, 0)
        pdf.cell(0, 8, f"- Grüne Gefahrenstufe: {stats_data.get('Grün', 0)}", ln=True)
        pdf.set_text_color(200, 120, 0)
        pdf.cell(0, 8, f"- Gelbe Gefahrenstufe: {stats_data.get('Gelb', 0)}", ln=True)
        pdf.set_text_color(200, 0, 0)
        pdf.cell(0, 8, f"- ROTE GEFAHRENSTUFE: {stats_data.get('ROT', 0)}", ln=True)
        pdf.set_text_color(0, 0, 0)
        
        # --- SEITE 2ff: DETAILS ---
        pdf.add_page()
        for item in st.session_state.inspections:
            if item['Stufe'] == "ROT": pdf.set_fill_color(255, 200, 200)
            elif item['Stufe'] == "Gelb": pdf.set_fill_color(255, 243, 200)
            else: pdf.set_fill_color(200, 255, 200)
            
            pdf.set_font("Arial", 'B', 11)
            pdf.cell(0, 10, f"REGAL: {item['Regal']} ({item['Typ']}) - STATUS: {item['Stufe']}", ln=True, fill=True)
            pdf.set_font("Arial", '', 10)
            pdf.multi_cell(0, 6, f"Bauteil: {item['Bauteil']} | Position: {item['Position']}\nMangel: {item['Mangel']}\nMassnahme: {item['Massnahme']}")
            
            if item['Fotos']:
                pdf.ln(2)
                y_img_start = pdf.get_y()
                x_img_pos = 10
                for p_path in item['Fotos']:
                    if os.path.exists(p_path):
                        pdf.image(p_path, x=x_img_pos, y=y_img_start, w=40)
                        x_img_pos += 45
                pdf.set_y(y_img_start + 32)

            pdf.ln(5)
            pdf.line(10, pdf.get_y(), 200, pdf.get_y())
            pdf.ln(5)

        pdf_bytes = pdf.output(dest='S').encode('latin-1', 'replace')
        st.download_button("📥 PDF Bericht jetzt herunterladen", data=pdf_bytes, file_name=f"Inspektion_{kunde}.pdf")