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

st.title("🛡️ Regal-Inspektion")

# --- STAMMDATEN ---
with st.expander("📋 Kunden- & Standortdetails"):
    c1, c2 = st.columns(2)
    kunde = c1.text_input("Kunde", key="kunde_val")
    standort = c1.text_input("Standort", key="ort_val")
    gebaeude = c2.text_input("Halle / Bereich", key="halle_val")
    inspektor = c2.text_input("Prüfer", key="name_val")

# --- STATISTIK & DIAGRAMM ---
if st.session_state.inspections:
    st.divider()
    df_stat = pd.DataFrame(st.session_state.inspections)
    stats = df_stat['Stufe'].value_counts()
    
    col_chart, col_met = st.columns([1, 1])
    with col_met:
        st.subheader("📊 Statistik")
        st.metric("Gesamt", len(df_stat))
        st.write(f"🟢 Grün: {stats.get('Grün', 0)} | 🟡 Gelb: {stats.get('Gelb', 0)} | 🔴 ROT: {stats.get('ROT', 0)}")
    
    with col_chart:
        # Ein einfaches Balkendiagramm für die Übersicht
        st.bar_chart(stats)

# --- EINGABEMASKE ---
st.divider()
if st.session_state.edit_index is not None:
    st.warning(f"⚠️ Du bearbeitest gerade Eintrag #{st.session_state.edit_index + 1}")
    edit_data = st.session_state.inspections[st.session_state.edit_index]
else:
    edit_data = {"Regal": "", "Typ": "Palettenregal", "Bauteil": "Stütze", "Position": "", "Stufe": "Grün", "Mangel": "Stapleranprall", "Kommentar": "", "Massnahme": "Beobachten"}

col1, col2, col3 = st.columns([1, 1, 1])

with col1:
    regal_nr = st.text_input("Regal-Nummer", value=edit_data["Regal"])
    regal_typ = st.selectbox("Regalanlage", ["Palettenregal", "Fachbodenregal", "Kragarmregal", "Sonstiges"], index=0)
    bauteil = st.selectbox("Bauteil", ["Stütze", "Traverse", "Rammschutz", "Aussteifung"], index=0)
    pos = st.text_input("Genaue Position", value=edit_data["Position"])

with col2:
    # LÖSUNG FÜR DIE FARBEN: Farbauswahl über Buttons/Radio statt rotem Slider
    st.write("**Gefahrenstufe wählen:**")
    gefahr = st.radio("Status", ["Grün", "Gelb", "ROT"], index=["Grün", "Gelb", "ROT"].index(edit_data["Stufe"]), horizontal=True)
    
    if gefahr == "Grün": st.success("Sicherer Zustand")
    elif gefahr == "Gelb": st.warning("Reparatur erforderlich (4 Wo.)")
    else: st.error("SOFORT SPERREN")

    mangel_auswahl = st.selectbox("Mangel", ["Stapleranprall", "Sicherungsstift fehlt", "Bodenanker lose", "Überladung", "Sonstiges"])
    mangel_detail = st.text_input("Kommentar zum Mangel", value=edit_data["Kommentar"])
    massnahme = st.selectbox("Maßnahme", ["Beobachten", "Tausch binnen 4 Wo.", "SOFORT SPERREN", "Stift ersetzen"])

with col3:
    st.write("📸 **Fotos**")
    f1 = st.camera_input("Detailaufnahme", key="c1")
    f2 = st.camera_input("Übersicht", key="c2")

# Speichern / Update
if st.button("💾 Eintrag speichern / aktualisieren"):
    new_entry = {
        "Regal": regal_nr, "Typ": regal_typ, "Bauteil": bauteil, "Position": pos,
        "Stufe": gefahr, "Mangel": f"{mangel_auswahl}: {mangel_detail}", "Kommentar": mangel_detail,
        "Massnahme": massnahme, "Fotos": edit_data.get("Fotos", [])
    }
    
    # Fotos nur speichern wenn neue gemacht wurden
    if f1 or f2:
        new_photos = []
        for i, f in enumerate([f1, f2]):
            if f:
                img = Image.open(f)
                path = f"img_{datetime.now().timestamp()}.jpg"
                img.save(path)
                new_photos.append(path)
        new_entry["Fotos"] = new_photos

    if st.session_state.edit_index is not None:
        st.session_state.inspections[st.session_state.edit_index] = new_entry
        st.session_state.edit_index = None
    else:
        st.session_state.inspections.append(new_entry)
    st.rerun()

# --- INTERAKTIVE LISTE ---
if st.session_state.inspections:
    st.divider()
    st.subheader("📋 Protokollierte Punkte")
    for idx, item in enumerate(st.session_state.inspections):
        with st.container():
            c_text, c_btn = st.columns([8, 2])
            status_color = "🟢" if item['Stufe'] == "Grün" else "🟡" if item['Stufe'] == "Gelb" else "🔴"
            c_text.write(f"{status_color} **#{idx+1} Regal {item['Regal']}** ({item['Bauteil']})")
            if c_btn.button("✏️ Bearbeiten", key=f"edit_btn_{idx}"):
                st.session_state.edit_index = idx
                st.rerun()

    # PDF Export
    if st.button("📄 PDF-Bericht erstellen"):
        # (PDF Logik bleibt wie gehabt, nutzt nun die gefüllten Daten)
        st.write("PDF wird generiert...")
        # ... (hier den PDF-Code von oben einfügen)