import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime
from PIL import Image
import os

# --- KONFIGURATION ---
st.set_page_config(page_title="Regal-Check Profi", layout="wide")

# Google Sheets (Nur zum LESEN der Kundenliste)
def get_conn():
    try:
        from streamlit_gsheets import GSheetsConnection
        return st.connection("gsheets", type=GSheetsConnection)
    except:
        return None

conn = get_conn()

# Session State initialisieren
if 'inspections' not in st.session_state:
    st.session_state.inspections = []
if 'report_archive' not in st.session_state:
    st.session_state.report_archive = []
if 'form_iteration' not in st.session_state:
    st.session_state.form_iteration = 0
if 'temp_customers' not in st.session_state:
    st.session_state.temp_customers = []

def reset_form():
    st.session_state.form_iteration += 1

# --- SIDEBAR: KUNDEN ---
st.sidebar.title("🏢 Verwaltung")
cloud_customers = []
if conn:
    try:
        df_c = conn.read(worksheet="Kunden", ttl="1m")
        cloud_customers = df_c["Kunde"].tolist()
    except:
        pass

all_customers = sorted(list(set(cloud_customers + st.session_state.temp_customers)))
selected_customer = st.sidebar.selectbox("Kunde wählen", ["---"] + all_customers)

new_cust = st.sidebar.text_input("➕ Neuen Kunden anlegen")
if st.sidebar.button("Kunde für Sitzung merken"):
    if new_cust and new_cust not in all_customers:
        st.session_state.temp_customers.append(new_cust)
        st.rerun()

# --- HAUPTSEITE ---
if selected_customer == "---":
    st.title("🛡️ Regal-Check System")
    st.info("Bitte wählen Sie einen Kunden aus.")
else:
    tab1, tab2 = st.tabs(["📝 Neue Inspektion", "📁 Archiv (Sitzung)"])

    with tab1:
        st.subheader(f"Prüfung für: {selected_customer}")
        with st.expander("📍 Berichts-Kopfdaten", expanded=True):
            c1, c2 = st.columns(2)
            standort = c1.text_input("Standort", placeholder="Stadt")
            gebaeude = c1.text_input("Halle / Werk", placeholder="Halle 4")
            inspektor = c2.text_input("Prüfer", placeholder="Dein Name")
            datum_heute = c2.date_input("Datum", datetime.now())

        st.divider()
        it = st.session_state.form_iteration
        col1, col2, col3 = st.columns([1, 1, 1])

        with col1:
            regal_nr = st.text_input("Regal-Nr.", placeholder="z.B. R-01", key=f"r_{it}")
            bauteil = st.selectbox("Bauteil", ["Stütze", "Traverse", "Rammschutz", "Aussteifung"], key=f"b_{it}")
            pos = st.text_input("Position", placeholder="Ebene/Feld", key=f"p_{it}")

        with col2:
            gefahr = st.radio("Gefahrenstufe", ["Grün", "Gelb", "ROT"], horizontal=True, key=f"s_{it}")
            mangel = st.selectbox("Mangel", ["Stapleranprall", "Stift fehlt", "Anker lose", "Überladung", "Sonstiges"], key=f"m_{it}")
            komm = st.text_input("Zusatz-Info", key=f"k_{it}")
            massn = st.selectbox("Maßnahme", ["Beobachten", "Tausch 4 Wo.", "SOFORT SPERREN", "Anker ziehen"], key=f"ms_{it}")

        with col3:
            f1 = st.camera_input("Foto 1", key=f"f1_{it}")
            f2 = st.camera_input("Foto 2", key=f"f2_{it}")
            f3 = st.camera_input("Foto 3", key=f"f3_{it}")

        if st.button("✅ Regal zur Liste hinzufügen", use_container_width=True):
            if not regal_nr: st.error("Regal-Nr. fehlt!")
            else:
                fotos = []
                for f in [f1, f2, f3]:
                    if f:
                        img = Image.open(f).convert("RGB")
                        p = f"temp_{datetime.now().timestamp()}.jpg"
                        img.save(p)
                        fotos.append(p)
                st.session_state.inspections.append({
                    "Regal": regal_nr, "Bauteil": bauteil, "Position": pos,
                    "Stufe": gefahr, "Mangel": f"{mangel}: {komm}", "Massn": massn, "Fotos": fotos
                })
                reset_form()
                st.rerun()

        # --- ZURÜCK-FUNKTION / LISTE ---
        if st.session_state.inspections:
            st.divider()
            st.subheader("📋 Erfasste Mängel (Liste)")
            for idx, item in enumerate(st.session_state.inspections):
                c_text, c_del = st.columns([9, 1])
                icon = "🟢" if item['Stufe'] == "Grün" else "🟡" if item['Stufe'] == "Gelb" else "🔴"
                c_text.write(f"{icon} **Regal {item['Regal']}** - {item['Bauteil']} ({item['Position']})")
                # ZURÜCK / LÖSCHEN BUTTON
                if c_del.button("🗑️", key=f"del_{idx}"):
                    st.session_state.inspections.pop(idx)
                    st.rerun()

            if st.button("💾 BERICHT ABSCHLIESSEN"):
                st.session_state.report_archive.append({
                    "Datum": datum_heute.strftime("%d.%m.%Y"),
                    "Kunde": selected_customer,
                    "Details": st.session_state.inspections.copy()
                })
                st.session_state.inspections = []
                st.success("Bericht archiviert!")
                st.rerun()

    with tab2:
        st.subheader("Archivierte Berichte")
        for idx, rep in enumerate(reversed(st.session_state.report_archive)):
            if rep["Kunde"] == selected_customer:
                with st.expander(f"Bericht {rep['Datum']}"):
                    if st.button(f"📥 PDF laden", key=f"pdf_{idx}"):
                        pdf = FPDF()
                        pdf.set_auto_page_break(auto=True, margin=20)
                        pdf.add_page()
                        pdf.set_font("Arial", 'B', 20)
                        pdf.cell(0, 30, f"Bericht: {rep['Kunde']}", ln=True, align='C')
                        pdf.set_font("Arial", '', 12)
                        pdf.cell(0, 10, f"Datum: {rep['Datum']}", ln=True)
                        pdf.ln(10)

                        for item in rep["Details"]:
                            if pdf.get_y() > 200: pdf.add_page()
                            # Farb-Status
                            if item['Stufe'] == "ROT": pdf.set_fill_color(255, 200, 200)
                            elif item['Stufe'] == "Gelb": pdf.set_fill_color(255, 243, 200)
                            else: pdf.set_fill_color(200, 255, 200)
                            
                            pdf.set_font("Arial", 'B', 14)
                            pdf.cell(0, 10, f"Regal {item['Regal']} - {item['Stufe']}", ln=True, fill=True)
                            pdf.set_font("Arial", '', 11)
                            pdf.cell(0, 8, f"{item['Bauteil']} | {item['Position']}", ln=True)
                            pdf.multi_cell(0, 6, f"Mangel: {item['Mangel']}\nMassnahme: {item['Massn']}")
                            
                            if item['Fotos']:
                                pdf.ln(2); y, x = pdf.get_y(), 10
                                for f in item['Fotos']:
                                    if os.path.exists(f):
                                        pdf.image(f, x=x, y=y, w=45)
                                        x += 50
                                pdf.set_y(y + 42)
                            pdf.ln(5); pdf.line(10, pdf.get_y(), 200, pdf.get_y()); pdf.ln(5)

                        pdf_bytes = pdf.output(dest='S').encode('latin-1', 'replace')
                        st.download_button("Datei speichern", pdf_bytes, f"Bericht_{idx}.pdf", key=f"dl_{idx}")