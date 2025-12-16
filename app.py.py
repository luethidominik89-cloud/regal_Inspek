import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime
from PIL import Image
import io

st.set_page_config(page_title="Regal-Check Profi", layout="wide")

# Speicher initialisieren
if 'inspections' not in st.session_state:
    st.session_state.inspections = []
if 'edit_index' not in st.session_state:
    st.session_state.edit_index = None

st.title("🛡️ Regal-Inspektion mit Statistik & Editor")

# --- STAMMDATEN ---
with st.expander("📋 Kunden- & Standortdetails", expanded=True):
    c1, c2 = st.columns(2)
    kunde = c1.text_input("Kunde / Firma", key="kunde")
    standort = c1.text_input("Standort", key="standort")
    gebaeude = c2.text_input("Gebäudeteil / Halle", key="gebaeude")
    inspektor = c2.text_input("Prüfer", key="inspektor")

# --- STATISTIK (DYNAMISCH) ---
if st.session_state.inspections:
    st.divider()
    st.subheader("📊 Inspektions-Zusammenfassung")
    df_stat = pd.DataFrame(st.session_state.inspections)
    stats = df_stat['Stufe'].value_counts()
    
    s_col1, s_col2, s_col3, s_col4 = st.columns(4)
    s_col1.metric("Gesamt", len(df_stat))
    s_col2.metric("🟢 Grün", stats.get("Grün", 0))
    s_col3.metric("🟡 Gelb", stats.get("Gelb", 0))
    s_col4.metric("🔴 ROT", stats.get("ROT", 0))

# --- EINGABEMASKE ---
st.divider()
mode_label = "📝 Eintrag bearbeiten" if st.session_state.edit_index is not None else "⚠️ Neuen Mangel erfassen"
st.subheader(mode_label)

# Werte für Bearbeitungsmodus vorladen
if st.session_state.edit_index is not None:
    edit_data = st.session_state.inspections[st.session_state.edit_index]
else:
    edit_data = {"Regal": "", "Typ": "Palettenregal", "Bauteil": "Stütze", "Position": "", "Stufe": "Grün", "Mangel": "Stapleranprall", "Kommentar": "", "Massnahme": "Beobachten"}

col1, col2, col3 = st.columns([1, 1, 1])

with col1:
    regal_nr = st.text_input("Regal-Nummer", value=edit_data["Regal"])
    regal_typ = st.selectbox("Regalanlage", ["Palettenregal", "Fachbodenregal", "Kragarmregal", "Einfahrregal", "Sonstiges"], index=["Palettenregal", "Fachbodenregal", "Kragarmregal", "Einfahrregal", "Sonstiges"].index(edit_data["Typ"]))
    bauteil = st.selectbox("Bauteil", ["Stütze", "Traverse", "Rammschutz", "Aussteifung"], index=["Stütze", "Traverse", "Rammschutz", "Aussteifung"].index(edit_data["Bauteil"]))
    pos = st.text_input("Genaue Position", value=edit_data["Position"])

with col2:
    # Der Slider-Farben Hinweis
    st.write("Gefahrenstufe: 🟢 → 🟡 → 🔴")
    gefahr = st.select_slider("Stufe wählen", options=["Grün", "Gelb", "ROT"], value=edit_data["Stufe"])
    
    mangel_auswahl = st.selectbox("Mangel", ["Stapleranprall", "Sicherungsstift fehlt", "Bodenanker lose", "Überladung", "Sonstiges"], index=["Stapleranprall", "Sicherungsstift fehlt", "Bodenanker lose", "Überladung", "Sonstiges"].index(edit_data["Mangel"].split(":")[0] if ":" in edit_data["Mangel"] else "Stapleranprall"))
    mangel_detail = st.text_input("Kommentar", value=edit_data.get("Kommentar", ""))
    massnahme = st.selectbox("Maßnahme", ["Beobachten", "Tausch binnen 4 Wo.", "SOFORT SPERREN", "Stift ersetzen"], index=["Beobachten", "Tausch binnen 4 Wo.", "SOFORT SPERREN", "Stift ersetzen"].index(edit_data["Massnahme"]))

with col3:
    st.write("📸 **Fotos**")
    f1 = st.camera_input("1. Detailaufnahme", key="cam1")
    f2 = st.camera_input("2. Übersicht", key="cam2")

# Buttons für Speichern / Abbrechen
b_col1, b_col2 = st.columns(2)
if st.session_state.edit_index is None:
    if b_col1.button("✅ Schaden speichern"):
        # Logik für neuen Eintrag
        photos = []
        for i, f in enumerate([f1, f2]):
            if f:
                img = Image.open(f)
                path = f"img_{datetime.now().timestamp()}_{i}.jpg"
                img.save(path)
                photos.append(path)
        
        st.session_state.inspections.append({
            "Regal": regal_nr, "Typ": regal_typ, "Bauteil": bauteil, "Position": pos,
            "Stufe": gefahr, "Mangel": f"{mangel_auswahl}: {mangel_detail}", "Kommentar": mangel_detail,
            "Massnahme": massnahme, "Fotos": photos
        })
        st.rerun()
else:
    if b_col1.button("💾 Änderungen übernehmen"):
        st.session_state.inspections[st.session_state.edit_index].update({
            "Regal": regal_nr, "Typ": regal_typ, "Bauteil": bauteil, "Position": pos,
            "Stufe": gefahr, "Mangel": f"{mangel_auswahl}: {mangel_detail}", "Kommentar": mangel_detail,
            "Massnahme": massnahme
        })
        st.session_state.edit_index = None
        st.rerun()
    if b_col2.button("🚫 Abbrechen"):
        st.session_state.edit_index = None
        st.rerun()

# --- TABELLE DER EINTRÄGE MIT BEARBEITEN-FUNKTION ---
if st.session_state.inspections:
    st.divider()
    st.subheader("📋 Erfasste Mängel (Klicken zum Bearbeiten)")
    for idx, item in enumerate(st.session_state.inspections):
        c_idx, c_info, c_edit = st.columns([1, 8, 2])
        color = "🔴" if item['Stufe'] == "ROT" else "🟡" if item['Stufe'] == "Gelb" else "🟢"
        c_idx.write(f"#{idx+1}")
        c_info.write(f"{color} **Regal {item['Regal']}** - {item['Bauteil']} ({item['Position']})")
        if c_edit.button("✏️ Bearbeiten", key=f"edit_{idx}"):
            st.session_state.edit_index = idx
            st.rerun()

    # --- PDF EXPORT MIT STATISTIK ---
    if st.button("📄 Finalen PDF-Bericht generieren"):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, "Regal-Inspektionsprotokoll", ln=True, align='C')
        
        # Statistik im PDF
        pdf.set_font("Arial", 'B', 12)
        pdf.ln(5)
        pdf.cell(0, 10, "Zusammenfassung der Prüfung:", ln=True)
        pdf.set_font("Arial", '', 10)
        pdf.cell(0, 7, f"Anzahl Mängel Gesamt: {len(st.session_state.inspections)}", ln=True)
        pdf.cell(0, 7, f"ROT: {stats.get('ROT', 0)} | Gelb: {stats.get('Gelb', 0)} | Grün: {stats.get('Grün', 0)}", ln=True)
        pdf.ln(5)

        for item in st.session_state.inspections:
            if item['Stufe'] == "ROT": pdf.set_fill_color(255, 200, 200)
            elif item['Stufe'] == "Gelb": pdf.set_fill_color(255, 243, 200)
            else: pdf.set_fill_color(200, 255, 200)
            
            pdf.set_font("Arial", 'B', 11)
            pdf.cell(0, 10, f"REGAL: {item['Regal']} - STATUS: {item['Stufe']}", ln=True, fill=True)
            pdf.set_font("Arial", '', 10)
            pdf.multi_cell(0, 6, f"Position: {item['Bauteil']} {item['Position']}\nMangel: {item['Mangel']}\nMassnahme: {item['Massnahme']}")
            
            if item['Fotos']:
                pdf.ln(2)
                x_pos = 10
                for p in item['Fotos']:
                    pdf.image(p, x=x_pos, w=40)
                    x_pos += 45
                pdf.ln(35)
            pdf.ln(5)

        pdf_bytes = pdf.output(dest='S').encode('latin-1', 'replace')
        st.download_button("📥 PDF Bericht laden", data=pdf_bytes, file_name=f"Bericht_{kunde}.pdf")