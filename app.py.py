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

def reset_form():
    st.session_state.form_iteration += 1

# --- KUNDENVERWALTUNG ---
st.sidebar.title("🏢 Verwaltung")

# Bestehende Kunden laden (Lesen ist erlaubt)
cloud_customers = []
if conn:
    try:
        df_c = conn.read(worksheet="Kunden", ttl="1m")
        cloud_customers = df_c["Kunde"].tolist()
    except:
        pass

all_available_customers = sorted(list(set(cloud_customers + st.session_state.temp_customers)))
selected_customer = st.sidebar.selectbox("Kunde wählen", ["---"] + all_available_customers)

st.sidebar.divider()
new_cust_name = st.sidebar.text_input("➕ Neuen Kunden anlegen")
if st.sidebar.button("Kunde für Sitzung merken"):
    if new_cust_name and new_cust_name not in all_available_customers:
        st.session_state.temp_customers.append(new_cust_name)
        st.sidebar.success(f"Kunde '{new_cust_name}' bereit!")
        st.rerun()

# --- HAUPTSEITE ---
if selected_customer == "---":
    st.title("🛡️ Regal-Check System")
    st.info("Bitte wählen Sie links einen Kunden aus.")
else:
    tab1, tab2 = st.tabs(["📝 Neue Inspektion", "📁 Sitzungs-Archiv"])

    with tab1:
        st.subheader(f"Prüfung für: {selected_customer}")
        with st.expander("📍 Berichts-Kopfdaten", expanded=True):
            c1, c2 = st.columns(2)
            standort = c1.text_input("Standort (Stadt)", placeholder="z.B. Berlin")
            gebaeude = c1.text_input("Gebäude / Halle / Werk", placeholder="z.B. Halle 4")
            inspektor = c2.text_input("Prüfer Name", placeholder="Dein Name")
            datum_heute = c2.date_input("Prüfdatum", datetime.now())

        st.divider()
        it = st.session_state.form_iteration
        col1, col2, col3 = st.columns([1, 1, 1])

        with col1:
            regal_nr = st.text_input("Regal-Nummer", placeholder="z.B. R-01", key=f"r_{it}")
            bauteil = st.selectbox("Bauteil", ["Stütze", "Traverse", "Rammschutz", "Aussteifung"], key=f"b_{it}")
            pos = st.text_input("Position / Ebene / Feld", placeholder="z.B. Feld 5, E3", key=f"p_{it}")

        with col2:
            st.write("**Gefahrenstufe:**")
            gefahr = st.radio("Status", ["Grün", "Gelb", "ROT"], horizontal=True, key=f"s_{it}")
            mangel = st.selectbox("Mangel", ["Stapleranprall", "Sicherungsstift fehlt", "Bodenanker lose", "Überladung", "Sonstiges"], key=f"m_{it}")
            kommentar = st.text_input("Zusatz-Info", placeholder="Details zum Schaden", key=f"k_{it}")
            massnahme = st.selectbox("Maßnahme", ["Beobachten", "Tausch binnen 4 Wo.", "SOFORT SPERREN", "Anker nachziehen"], key=f"ms_{it}")

        with col3:
            f1 = st.camera_input("1. Detail (Schaden)", key=f"f1_{it}")
            f2 = st.camera_input("2. Standort (Übersicht)", key=f"f2_{it}")
            f3 = st.camera_input("3. Traglastschild", key=f"f3_{it}")

        if st.button("✅ Regal zur Liste hinzufügen", use_container_width=True):
            if not regal_nr:
                st.error("Bitte Regal-Nummer angeben!")
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
                    "Stufe": gefahr, "Mangel": f"{mangel}: {kommentar}", 
                    "Massnahme": massnahme, "Fotos": fotos
                })
                reset_form()
                st.rerun()

        if st.session_state.inspections:
            st.divider()
            if st.button("💾 BERICHT ABSCHLIESSEN & IM ARCHIV ABLEGEN"):
                new_report = {
                    "Datum": datum_heute.strftime("%d.%m.%Y"),
                    "Kunde": selected_customer,
                    "Standort": standort,
                    "Mängel": len(st.session_state.inspections),
                    "Details": st.session_state.inspections.copy()
                }
                st.session_state.report_archive.append(new_report)
                st.session_state.inspections = []
                st.success("Bericht wurde erfolgreich in das Sitzungs-Archiv verschoben!")
                st.rerun()

    with tab2:
        st.subheader(f"Berichts-Historie dieser Sitzung: {selected_customer}")
        if st.session_state.report_archive:
            for idx, rep in enumerate(reversed(st.session_state.report_archive)):
                if rep["Kunde"] == selected_customer:
                    with st.expander(f"📅 Bericht vom {rep['Datum']} ({rep['Mängel']} Mängel)"):
                        st.write(f"**Standort:** {rep['Standort']}")
                        
                        if st.button(f"📄 PDF für Bericht #{idx} generieren", key=f"pdf_{idx}"):
                            pdf = FPDF()
                            pdf.set_auto_page_break(auto=True, margin=20)
                            
                            # Deckblatt
                            pdf.add_page()
                            pdf.set_font("Arial", 'B', 24)
                            pdf.cell(0, 40, "Inspektionsbericht", ln=True, align='C')
                            pdf.set_font("Arial", '', 14)
                            pdf.cell(0, 10, f"Kunde: {rep['Kunde']}", ln=True)
                            pdf.cell(0, 10, f"Datum: {rep['Datum']}", ln=True)
                            
                            # Inhaltsverzeichnis
                            pdf.add_page()
                            pdf.set_font("Arial", 'B', 18)
                            pdf.cell(0, 15, "Inhaltsverzeichnis", ln=True)
                            pdf.ln(5)
                            toc_entries = []

                            # Details
                            pdf.add_page()
                            for item in rep["Details"]:
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
                                    y_f, x_f = pdf.get_y(), 10
                                    for f in item['Fotos']:
                                        if os.path.exists(f):
                                            pdf.image(f, x=x_f, y=y_f, w=45)
                                            x_f += 50
                                    pdf.set_y(y_f + 42)
                                pdf.ln(5); pdf.line(10, pdf.get_y(), 200, pdf.get_y()); pdf.ln(5)

                            # Inhaltsverzeichnis füllen
                            pdf.page = 2
                            pdf.set_y(35)
                            pdf.set_font("Arial", '', 11)
                            for t in toc_entries:
                                pdf.cell(0, 10, f"Regal {t[0]}: {t[2]} ({t[3]})", ln=False)
                                pdf.set_x(170)
                                pdf.cell(0, 10, f"Seite {t[4]}", ln=True)

                            pdf_out = pdf.output(dest='S').encode('latin-1', 'replace')
                            st.download_button("📥 PDF JETZT LADEN", data=pdf_out, file_name=f"Bericht_{rep['Kunde']}.pdf", key=f"dl_{idx}")
        else:
            st.write("Noch keine Berichte in dieser Sitzung abgeschlossen.")