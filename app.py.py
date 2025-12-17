import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime
from PIL import Image
import os

# --- KONFIGURATION ---
st.set_page_config(page_title="Regal-Check Profi", layout="wide")

# Google Sheets Anbindung versuchen
try:
    from streamlit_gsheets import GSheetsConnection
    conn = st.connection("gsheets", type=GSheetsConnection)
    HAS_GSHEETS = True
except Exception:
    HAS_GSHEETS = False

# Session State initialisieren
if 'inspections' not in st.session_state:
    st.session_state.inspections = []
if 'form_iteration' not in st.session_state:
    st.session_state.form_iteration = 0

def reset_form():
    st.session_state.form_iteration += 1

# --- KUNDENVERWALTUNG (GOOGLE SHEETS ODER LOKAL) ---
st.sidebar.title("🏢 Kundenverwaltung")

if HAS_GSHEETS:
    try:
        df_kunden = conn.read(worksheet="Kunden", ttl="1m")
    except:
        df_kunden = pd.DataFrame(columns=["Kunde"])
    
    new_cust = st.sidebar.text_input("Neuen Kunden anlegen")
    if st.sidebar.button("➕ Kunde speichern"):
        if new_cust and new_cust not in df_kunden["Kunde"].values:
            new_entry = pd.DataFrame([{"Kunde": new_cust}])
            updated_df = pd.concat([df_kunden, new_entry], ignore_index=True)
            # Hier passiert der Schreibvorgang (benötigt "Editor"-Rechte im Link!)
            try:
                conn.update(worksheet="Kunden", data=updated_df)
                st.sidebar.success("Kunde gespeichert!")
                st.rerun()
            except Exception as e:
                st.sidebar.error("Fehler beim Speichern. Prüfe, ob das Google Sheet auf 'Editor' steht!")
    
    selected_customer = st.sidebar.selectbox("Kunde wählen", ["---"] + df_kunden["Kunde"].tolist())
else:
    # Fallback falls Google Sheets nicht konfiguriert ist
    selected_customer = st.sidebar.text_input("Kunde / Firma manuell", placeholder="z.B. Muster GmbH")

# --- HAUPTSEITE ---
if not selected_customer or selected_customer == "---":
    st.title("🛡️ Regal-Check System")
    st.info("Bitte wählen Sie einen Kunden aus oder legen Sie einen neuen an.")
else:
    st.title(f"Inspektion: {selected_customer}")
    
    with st.expander("📍 Standort & Kopfdaten", expanded=True):
        c1, c2 = st.columns(2)
        standort = c1.text_input("Standort (Stadt)", placeholder="z.B. Berlin")
        gebaeude = c1.text_input("Gebäude / Werk / Halle", placeholder="z.B. Halle 4")
        inspektor = c2.text_input("Prüfer Name", placeholder="Dein Name")
        datum_heute = c2.date_input("Prüfdatum", datetime.now())

    st.divider()

    # --- EINGABEMASKE ---
    st.subheader("Neuen Mangel erfassen")
    it = st.session_state.form_iteration
    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        regal_nr = st.text_input("Regal-Nummer", placeholder="z.B. R-001", key=f"r_{it}")
        bauteil = st.selectbox("Bauteil", ["Stütze", "Traverse", "Rammschutz", "Aussteifung"], key=f"b_{it}")
        pos = st.text_input("Position / Ebene / Feld", placeholder="z.B. Feld 5", key=f"p_{it}")

    with col2:
        # Kein Slider, sondern klare Auswahl (Status-Fix)
        st.write("**Gefahrenstufe:**")
        gefahr = st.radio("Status", ["Grün", "Gelb", "ROT"], horizontal=True, key=f"s_{it}")
        mangel = st.selectbox("Mangel", ["Stapleranprall", "Sicherungsstift fehlt", "Bodenanker lose", "Überladung", "Sonstiges"], key=f"m_{it}")
        kommentar = st.text_input("Zusatz-Info", placeholder="Details zum Schaden", key=f"k_{it}")
        massnahme = st.selectbox("Maßnahme", ["Beobachten", "Tausch binnen 4 Wo.", "SOFORT SPERREN", "Anker nachziehen"], key=f"ms_{it}")

    with col3:
        f1 = st.camera_input("1. Detail (Schaden)", key=f"f1_{it}")
        f2 = st.camera_input("2. Standort (Übersicht)", key=f"f2_{it}")
        f3 = st.camera_input("3. Sonstiges", key=f"f3_{it}")

    if st.button("✅ Regal zur Liste hinzufügen", use_container_width=True):
        if not regal_nr:
            st.error("Regal-Nummer fehlt!")
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

    # --- BERICHT & PDF ---
    if st.session_state.inspections:
        st.divider()
        st.subheader("📋 Aktuelle Mängelliste")
        for idx, item in enumerate(st.session_state.inspections):
            icon = "🟢" if item['Stufe'] == "Grün" else "🟡" if item['Stufe'] == "Gelb" else "🔴"
            st.write(f"{icon} **Regal {item['Regal']}** - {item['Bauteil']} ({item['Position']})")

        if st.button("📄 PDF-Bericht erstellen", type="primary", use_container_width=True):
            pdf = FPDF()
            pdf.set_auto_page_break(auto=True, margin=20)
            
            # Deckblatt
            pdf.add_page()
            pdf.set_font("Arial", 'B', 24)
            pdf.cell(0, 40, "Inspektionsbericht", ln=True, align='C')
            pdf.set_font("Arial", '', 14)
            pdf.cell(0, 10, f"Kunde: {selected_customer}", ln=True)
            pdf.cell(0, 10, f"Standort: {standort} | Bereich: {gebaeude}", ln=True)
            pdf.cell(0, 10, f"Datum: {datum_heute.strftime('%d.%m.%Y')}", ln=True)
            
            # Inhaltsverzeichnis (Fix für Bild 2/3)
            pdf.add_page()
            pdf.set_font("Arial", 'B', 18)
            pdf.cell(0, 15, "Inhaltsverzeichnis", ln=True)
            pdf.ln(5)
            toc_data = []

            # Details
            for item in st.session_state.inspections:
                pdf.add_page()
                toc_data.append((item['Regal'], item['Stufe'], pdf.page_no()))
                
                if item['Stufe'] == "ROT": pdf.set_fill_color(255, 200, 200)
                elif item['Stufe'] == "Gelb": pdf.set_fill_color(255, 243, 200)
                else: pdf.set_fill_color(200, 255, 200)
                
                pdf.set_font("Arial", 'B', 16)
                pdf.cell(0, 12, f"Regal: {item['Regal']} - Status: {item['Stufe']}", ln=True, fill=True)
                pdf.set_font("Arial", '', 12)
                pdf.cell(0, 8, f"Bauteil: {item['Bauteil']} | Position: {item['Position']}", ln=True)
                pdf.multi_cell(0, 7, f"Mangel: {item['Mangel']}\nMassnahme: {item['Massnahme']}")
                
                if item['Fotos']:
                    pdf.ln(5)
                    y, x = pdf.get_y(), 10
                    for f in item['Fotos']:
                        if os.path.exists(f):
                            pdf.image(f, x=x, y=y, w=55)
                            x += 60
                
            # Inhaltsverzeichnis füllen
            pdf.page = 2
            pdf.set_y(35)
            pdf.set_font("Arial", '', 12)
            for t in toc_data:
                pdf.cell(0, 10, f"Regal {t[0]} ({t[1]})", ln=False)
                pdf.set_x(170)
                pdf.cell(0, 10, f"Seite {t[2]}", ln=True)

            pdf_out = pdf.output(dest='S').encode('latin-1', 'replace')
            st.download_button("📥 PDF Herunterladen", data=pdf_out, file_name=f"Bericht_{selected_customer}.pdf")