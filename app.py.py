import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from fpdf import FPDF
from datetime import datetime
from PIL import Image
import io
import os

# --- SEITEN-KONFIGURATION ---
st.set_page_config(page_title="Regal-Check Cloud Pro", layout="wide")

# Verbindung zu Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# --- FUNKTIONEN ---
def load_customers():
    try:
        # Versucht das Tabellenblatt "Kunden" zu lesen
        return conn.read(worksheet="Kunden", ttl="1m")
    except:
        return pd.DataFrame(columns=["Kunde"])

def save_customer(name):
    df = load_customers()
    if name not in df["Kunde"].values:
        new_entry = pd.DataFrame([{"Kunde": name}])
        updated_df = pd.concat([df, new_entry], ignore_index=True)
        conn.update(worksheet="Kunden", data=updated_df)
        return True
    return False

# Session State initialisieren
if 'current_inspections' not in st.session_state:
    st.session_state.current_inspections = []
if 'form_iteration' not in st.session_state:
    st.session_state.form_iteration = 0

def reset_form():
    st.session_state.form_iteration += 1

# --- SIDEBAR: KUNDENVERWALTUNG ---
st.sidebar.title("🏢 Kunden-Archiv (Google Sheets)")
df_kunden = load_customers()

new_cust = st.sidebar.text_input("Neuen Kunden anlegen", placeholder="Firma Name")
if st.sidebar.button("➕ Erstellen"):
    if new_cust:
        if save_customer(new_cust):
            st.sidebar.success(f"{new_cust} gespeichert!")
            st.rerun()
        else:
            st.sidebar.warning("Kunde existiert bereits.")

selected_customer = st.sidebar.selectbox("Kunden auswählen", ["---"] + df_kunden["Kunde"].tolist())

# --- HAUPTSEITE ---
if selected_customer == "---":
    st.title("🛡️ Regal-Check Cloud")
    st.info("Bitte wählen Sie links einen Kunden aus oder legen Sie einen neuen an. Ihre Kundenliste wird sicher in Google Sheets gespeichert.")
else:
    st.title(f"Inspektion für: {selected_customer}")
    
    # KOPFDATEN
    with st.expander("📍 Berichts-Kopfdaten", expanded=True):
        c1, c2 = st.columns(2)
        standort = c1.text_input("Standort (Stadt)", placeholder="z.B. Zürich")
        gebaeude = c1.text_input("Gebäude / Werk / Halle", placeholder="z.B. Werk 1, Halle A")
        inspektor = c2.text_input("Prüfer Name", placeholder="Dein Vor- und Nachname")
        datum_heute = c2.date_input("Prüfdatum", datetime.now())

    st.divider()
    
    # EINGABEMASKE
    st.subheader("Neuen Mangel erfassen")
    iter_key = st.session_state.form_iteration
    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        regal_nr = st.text_input("Regal-Nummer", placeholder="z.B. R-22", key=f"r_{iter_key}")
        bauteil = st.selectbox("Bauteil", ["Stütze", "Traverse", "Rammschutz", "Aussteifung"], key=f"b_{iter_key}")
        p_hold = "z.B. Pfosten vorne rechts" if bauteil == "Stütze" else "z.B. Ebene 2, Feld 5"
        pos = st.text_input("Position / Ebene / Feld", placeholder=p_hold, key=f"p_{iter_key}")

    with col2:
        gefahr = st.radio("Gefahrenstufe", ["Grün", "Gelb", "ROT"], horizontal=True, key=f"g_{iter_key}")
        mangel = st.selectbox("Mangel", ["Stapleranprall", "Sicherungsstift fehlt", "Bodenanker lose", "Überladung", "Sonstiges"], key=f"m_{iter_key}")
        kommentar = st.text_input("Zusatz-Info", placeholder="z.B. Delle > 5mm", key=f"k_{iter_key}")
        massnahme = st.selectbox("Maßnahme", ["Beobachten", "Tausch binnen 4 Wo.", "SOFORT SPERREN", "Stift ersetzen"], key=f"ms_{iter_key}")

    with col3:
        f1 = st.camera_input("1. Detail (Schaden)", key=f"f1_{iter_key}")
        f2 = st.camera_input("2. Standort (Übersicht)", key=f"f2_{iter_key}")
        f3 = st.camera_input("3. Traglastschild", key=f"f3_{iter_key}")

    if st.button("✅ Regal zur Liste hinzufügen", use_container_width=True):
        if not regal_nr:
            st.error("Bitte Regal-Nummer eingeben!")
        else:
            fotos = []
            for f in [f1, f2, f3]:
                if f:
                    img = Image.open(f).convert("RGB")
                    fname = f"temp_img_{datetime.now().timestamp()}.jpg"
                    img.save(fname)
                    fotos.append(fname)
            
            st.session_state.current_inspections.append({
                "Regal": regal_nr, "Bauteil": bauteil, "Position": pos,
                "Stufe": gefahr, "Mangel": f"{mangel}: {kommentar}", 
                "Massnahme": massnahme, "Fotos": fotos
            })
            reset_form()
            st.rerun()

    # AKTUELLE LISTE & PDF EXPORT
    if st.session_state.current_inspections:
        st.divider()
        st.subheader("📋 Vorläufige Liste dieser Sitzung")
        for i, item in enumerate(st.session_state.current_inspections):
            st.write(f"**#{i+1} Regal {item['Regal']}** ({item['Stufe']}) - {item['Bauteil']} {item['Position']}")
        
        if st.button("📄 Finalen PDF-Bericht generieren", type="primary", use_container_width=True):
            pdf = FPDF()
            pdf.set_auto_page_break(auto=True, margin=20)
            pdf.add_page()
            
            # Kopfzeilen PDF
            pdf.set_font("Arial", 'B', 24)
            pdf.cell(0, 30, "Inspektionsbericht Regalanlagen", ln=True, align='C')
            pdf.set_font("Arial", '', 12)
            pdf.cell(0, 8, f"Kunde: {selected_customer}", ln=True)
            pdf.cell(0, 8, f"Standort: {standort} | Bereich: {gebaeude}", ln=True)
            pdf.cell(0, 8, f"Prüfer: {inspektor} | Datum: {datum_heute.strftime('%d.%m.%Y')}", ln=True)
            pdf.ln(10)

            for item in st.session_state.current_inspections:
                if pdf.get_y() > 180: pdf.add_page()
                
                # Hintergrundfarbe Gefahrenstufe
                if item['Stufe'] == "ROT": pdf.set_fill_color(255, 200, 200)
                elif item['Stufe'] == "Gelb": pdf.set_fill_color(255, 243, 200)
                else: pdf.set_fill_color(200, 255, 200)
                
                pdf.set_font("Arial", 'B', 13)
                pdf.cell(0, 10, f"REGAL: {item['Regal']} - STATUS: {item['Stufe']}", ln=True, fill=True)
                
                pdf.set_font("Arial", 'B', 11)
                pdf.cell(40, 7, "Bauteil:", ln=0)
                pdf.set_font("Arial", '', 11)
                pdf.cell(0, 7, f"{item['Bauteil']}", ln=True)
                
                pdf.set_font("Arial", 'B', 11)
                pdf.cell(40, 7, "Position:", ln=0)
                pdf.set_font("Arial", '', 11)
                pdf.cell(0, 7, f"{item['Position']}", ln=True)
                
                pdf.set_font("Arial", 'B', 11)
                pdf.cell(0, 7, "Beschreibung & Massnahme:", ln=True)
                pdf.set_font("Arial", '', 11)
                pdf.multi_cell(0, 6, f"{item['Mangel']}\nMassnahme: {item['Massnahme']}")
                
                if item['Fotos']:
                    pdf.ln(2)
                    y_f, x_f = pdf.get_y(), 10
                    for f_p in item['Fotos']:
                        if os.path.exists(f_p):
                            pdf.image(f_p, x=x_f, y=y_f, w=45)
                            x_f += 50
                    pdf.set_y(y_f + 42)
                pdf.ln(5)
                pdf.line(10, pdf.get_y(), 200, pdf.get_y())
                pdf.ln(5)

            pdf_bytes = pdf.output(dest='S').encode('latin-1', 'replace')
            st.download_button("📥 PDF JETZT HERUNTERLADEN", data=pdf_bytes, file_name=f"Bericht_{selected_customer}.pdf")
            
            # WICHTIG: Nach PDF-Download Sitzung leeren
            if st.button("🗑️ Liste für neuen Bericht leeren"):
                st.session_state.current_inspections = []
                st.rerun()