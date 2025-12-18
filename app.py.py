import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime
from PIL import Image
import os

# --- KONFIGURATION ---
st.set_page_config(page_title="Regal-Check Profi", layout="wide")

# Google Sheets Anbindung (Nur zum LESEN der Kundenliste)
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
if 'edit_data' not in st.session_state:
    st.session_state.edit_data = None

def reset_form():
    st.session_state.form_iteration += 1
    st.session_state.edit_data = None

# --- SIDEBAR ---
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

new_cust = st.sidebar.text_input("➕ Neuen Kunden anlegen", placeholder="z.B. Muster AG")
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
            standort = c1.text_input("Standort", placeholder="z.B. Zürich / Werk 1")
            gebaeude = c1.text_input("Halle / Gebäude", placeholder="z.B. Halle A / Hochregal")
            inspektor = c2.text_input("Prüfer Name", placeholder="Dein Name")
            datum_heute = c2.date_input("Prüfdatum", datetime.now())

        st.divider()
        
        # Logik für Bearbeitung vs. Placeholder
        edit = st.session_state.edit_data
        it = st.session_state.form_iteration
        col1, col2, col3 = st.columns([1, 1, 1])

        with col1:
            # Regal-Nr
            regal_nr = st.text_input("Regal-Nr.", 
                                    value=edit["Regal"] if edit else "", 
                                    placeholder="z.B. R-01 / Feld 10", 
                                    key=f"r_{it}")
            
            # Bauteil
            b_list = ["Stütze", "Traverse", "Rammschutz", "Aussteifung"]
            b_idx = b_list.index(edit["Bauteil"]) if edit else 0
            bauteil = st.selectbox("Bauteil", b_list, index=b_idx, key=f"b_{it}")
            
            # Position
            pos = st.text_input("Position / Ebene", 
                               value=edit["Position"] if edit else "", 
                               placeholder="z.B. Ebene 3 / Pfosten vorn", 
                               key=f"p_{it}")

        with col2:
            # Gefahrenstufe
            s_list = ["Grün", "Gelb", "ROT"]
            s_idx = s_list.index(edit["Stufe"]) if edit else 0
            gefahr = st.radio("Status", s_list, index=s_idx, horizontal=True, key=f"s_{it}")
            
            # Mangel
            m_list = ["Stapleranprall", "Sicherungsstift fehlt", "Bodenanker lose", "Überladung", "Sonstiges"]
            m_main = edit["Mangel"].split(":")[0] if edit else "Stapleranprall"
            m_idx = m_list.index(m_main) if m_main in m_list else 0
            mangel_sel = st.selectbox("Hauptmangel", m_list, index=m_idx, key=f"m_{it}")
            
            # Zusatz-Kommentar
            k_val = edit["Mangel"].split(":")[1].strip() if edit and ":" in edit["Mangel"] else ""
            komm = st.text_input("Zusatz-Info", 
                                value=k_val, 
                                placeholder="z.B. Delle > 3mm / Verformung", 
                                key=f"k_{it}")
            
            # Maßnahme
            ms_list = ["Beobachten", "Tausch binnen 4 Wo.", "SOFORT SPERREN", "Stift ersetzen", "Anker nachziehen"]
            ms_idx = ms_list.index(edit["Massn"]) if edit else 0
            massn = st.selectbox("Maßnahme", ms_list, index=ms_idx, key=f"ms_{it}")

        with col3:
            st.write("📸 **Fotos**")
            f1 = st.camera_input("1. Detail (Schaden)", key=f"f1_{it}")
            f2 = st.camera_input("2. Übersicht", key=f"f2_{it}")
            f3 = st.camera_input("3. Typenschild", key=f"f3_{it}")

        if st.button("✅ Regal zur Liste hinzufügen", use_container_width=True):
            if not regal_nr: st.error("Regal-Nr. fehlt!")
            else:
                fotos = edit["Fotos"] if edit else []
                new_f = [f for f in [f1, f2, f3] if f]
                if new_f:
                    fotos = []
                    for f in new_f:
                        img = Image.open(f).convert("RGB")
                        p = f"temp_{datetime.now().timestamp()}.jpg"
                        img.save(p)
                        fotos.append(p)
                
                st.session_state.inspections.append({
                    "Regal": regal_nr, "Bauteil": bauteil, "Position": pos,
                    "Stufe": gefahr, "Mangel": f"{mangel_sel}: {komm}", "Massn": massn, "Fotos": fotos
                })
                reset_form()
                st.rerun()

        # --- UNTEN: LISTE & RÜCKGÄNGIG ---
        if st.session_state.inspections:
            st.divider()
            if st.button("↩️ Letzten Eintrag sofort löschen (Undo)", use_container_width=True):
                st.session_state.inspections.pop()
                st.rerun()

            st.subheader("📋 Aktuelle Liste")
            for idx, item in enumerate(st.session_state.inspections):
                c_t, c_e, c_d = st.columns([8, 1, 1])
                icon = "🟢" if item['Stufe'] == "Grün" else "🟡" if item['Stufe'] == "Gelb" else "🔴"
                c_t.write(f"{icon} **Regal {item['Regal']}** - {item['Bauteil']} ({item['Position']})")
                
                if c_e.button("✏️", key=f"ed_{idx}"):
                    st.session_state.edit_data = st.session_state.inspections.pop(idx)
                    st.rerun()
                if c_d.button("🗑️", key=f"del_{idx}"):
                    st.session_state.inspections.pop(idx)
                    st.rerun()

            st.write("---")
            if st.button("💾 BERICHT ABSCHLIESSEN", type="primary", use_container_width=True):
                st.session_state.report_archive.append({
                    "Datum": datum_heute.strftime("%d.%m.%Y"),
                    "Kunde": selected_customer, "Details": st.session_state.inspections.copy(),
                    "Standort": standort, "Bereich": gebaeude
                })
                st.session_state.inspections = []
                st.success("Archiviert!")
                st.rerun()

    with tab2:
        # Archiv (Ohne Inhaltsverzeichnis)
        st.subheader("📁 Sitzungs-Archiv")
        for idx, rep in enumerate(reversed(st.session_state.report_archive)):
            if rep["Kunde"] == selected_customer:
                with st.expander(f"Bericht vom {rep['Datum']} - {rep.get('Bereich','')}"):
                    if st.button(f"📥 PDF Bericht laden", key=f"pdf_{idx}"):
                        pdf = FPDF()
                        pdf.set_auto_page_break(auto=True, margin=20)
                        pdf.add_page()
                        pdf.set_font("Arial", 'B', 20)
                        pdf.cell(0, 30, f"Bericht: {rep['Kunde']}", ln=True, align='C')
                        pdf.set_font("Arial", '', 12)
                        pdf.cell(0, 10, f"Datum: {rep['Datum']} | Standort: {rep.get('Standort','')}", ln=True)
                        pdf.ln(10)
                        for item in rep["Details"]:
                            if pdf.get_y() > 200: pdf.add_page()
                            if item['Stufe'] == "ROT": pdf.set_fill_color(255, 200, 200)
                            elif item['Stufe'] == "Gelb": pdf.set_fill_color(255, 243, 200)
                            else: pdf.set_fill_color(200, 255, 200)
                            pdf.set_font("Arial", 'B', 14)
                            pdf.cell(0, 10, f"Regal {item['Regal']} - {item['Stufe']}", ln=True, fill=True)
                            pdf.set_font("Arial", '', 11)
                            pdf.multi_cell(0, 6, f"{item['Bauteil']} ({item['Position']})\n{item['Mangel']}\nMassnahme: {item['Massn']}")
                            if item['Fotos']:
                                pdf.ln(2); y, x = pdf.get_y(), 10
                                for f in item['Fotos']:
                                    if os.path.exists(f):
                                        pdf.image(f, x=x, y=y, w=45); x += 50
                                pdf.set_y(y + 42)
                            pdf.ln(5); pdf.line(10, pdf.get_y(), 200, pdf.get_y()); pdf.ln(5)
                        pdf_bytes = pdf.output(dest='S').encode('latin-1', 'replace')
                        st.download_button("Speichern", pdf_bytes, f"Bericht.pdf", key=f"dl_{idx}")