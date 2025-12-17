import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime
from PIL import Image
import os
import json

# --- SEITEN-KONFIGURATION ---
st.set_page_config(page_title="Regal-Check Profi DB", layout="wide")

# Pfad für die lokale Datenbank (Hinweis: In Streamlit Cloud ist dies temporär)
DB_FILE = "regal_datenbank.json"

# --- DATENBANK FUNKTIONEN ---
def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_db(db):
    with open(DB_FILE, "w") as f:
        json.dump(db, f, indent=4)

# Session State initialisieren
if 'db' not in st.session_state:
    st.session_state.db = load_db()
if 'current_inspections' not in st.session_state:
    st.session_state.current_inspections = []
if 'form_iteration' not in st.session_state:
    st.session_state.form_iteration = 0

def reset_form():
    st.session_state.form_iteration += 1

# --- SIDEBAR: KUNDEN-NAVIGATION ---
st.sidebar.title("🏢 Kunden-Archiv")
new_cust = st.sidebar.text_input("Neuen Kunden anlegen", placeholder="Name der Firma")
if st.sidebar.button("➕ Kunde erstellen"):
    if new_cust and new_cust not in st.session_state.db:
        st.session_state.db[new_cust] = {"berichte": []}
        save_db(st.session_state.db)
        st.rerun()

all_customers = sorted(list(st.session_state.db.keys()))
selected_customer = st.sidebar.selectbox("Kunden auswählen", ["---"] + all_customers)

# --- HAUPTSEITE ---
if selected_customer == "---":
    st.title("🛡️ Regal-Check Inspektions-System")
    st.info("Bitte wählen Sie links einen Kunden aus oder legen Sie einen neuen an.")
else:
    st.title(f"Prüfung für: {selected_customer}")
    
    tab1, tab2 = st.tabs(["📝 Neue Inspektion erfassen", "📁 Abgeschlossene Berichte"])

    # --- TAB 1: NEUE INSPEKTION ---
    with tab1:
        with st.expander("📍 Bericht-Details (Kopfdaten)", expanded=True):
            c1, c2 = st.columns(2)
            # Standort ohne "Werk" (Werk kommt in das nächste Feld)
            standort = c1.text_input("Standort (Stadt)", placeholder="z.B. Berlin")
            gebaeude = c1.text_input("Gebäude / Werk / Halle", placeholder="z.B. Werk 2, Halle 4")
            inspektor = c2.text_input("Name des Prüfers", placeholder="Dein Name")
            datum_heute = c2.date_input("Prüfdatum", datetime.now())

        st.divider()
        st.subheader("Neues Regal / Mangel aufnehmen")
        
        # Reset-Logik via iteration_key
        iter_key = st.session_state.form_iteration
        col1, col2, col3 = st.columns([1, 1, 1])

        with col1:
            regal_nr = st.text_input("Regal-Nummer", placeholder="z.B. R-01", key=f"reg_{iter_key}")
            regal_typ = st.selectbox("Regalanlage", ["Palettenregal", "Fachbodenregal", "Kragarmregal", "Durchlaufregal", "Sonstiges"], key=f"typ_{iter_key}")
            bauteil = st.selectbox("Bauteil", ["Stütze", "Traverse", "Rammschutz", "Aussteifung"], key=f"bt_{iter_key}")
            
            # Dynamischer Platzhalter für Position
            p_hold = "z.B. Pfosten vorne links" if bauteil == "Stütze" else "z.B. Ebene 3, Feld 10" if bauteil == "Traverse" else "Genaue Lage"
            pos = st.text_input("Position / Ebene / Feld", placeholder=p_hold, key=f"pos_{iter_key}")

        with col2:
            st.write("**Gefahrenstufe:**")
            gefahr = st.radio("Status", ["Grün", "Gelb", "ROT"], horizontal=True, key=f"st_{iter_key}")
            mangel_main = st.selectbox("Hauptmangel", ["Stapleranprall", "Sicherungsstift fehlt", "Bodenanker lose", "Überladung", "Verformung", "Sonstiges"], key=f"ma_{iter_key}")
            kommentar = st.text_input("Zusatz-Kommentar", placeholder="z.B. Delle > 3mm", key=f"ko_{iter_key}")
            massnahme = st.selectbox("Maßnahme", ["Beobachten", "Tausch binnen 4 Wo.", "SOFORT SPERREN", "Stift ersetzen", "Anker nachziehen"], key=f"ms_{iter_key}")

        with col3:
            st.write("📸 **3 Fotos aufnehmen**")
            f1 = st.camera_input("1. Detailaufnahme (Schaden)", key=f"c1_{iter_key}")
            f2 = st.camera_input("2. Standortaufnahme (Übersicht)", key=f"c2_{iter_key}")
            f3 = st.camera_input("3. Traglastschild / Sonstiges", key=f"c3_{iter_key}")

        if st.button("✅ Regal zur Liste hinzufügen & Formular leeren", use_container_width=True):
            if not regal_nr:
                st.error("Bitte Regal-Nummer angeben!")
            else:
                fotos = []
                for f in [f1, f2, f3]:
                    if f:
                        img = Image.open(f).convert("RGB")
                        fname = f"img_{datetime.now().timestamp()}.jpg"
                        img.save(fname)
                        fotos.append(fname)
                
                st.session_state.current_inspections.append({
                    "Regal": regal_nr, "Typ": regal_typ, "Bauteil": bauteil, "Position": pos,
                    "Stufe": gefahr, "Mangel": f"{mangel_main}: {kommentar}", 
                    "Massnahme": massnahme, "Fotos": fotos
                })
                reset_form()
                st.rerun()

        # Aktuelle Liste anzeigen
        if st.session_state.current_inspections:
            st.divider()
            st.subheader("📋 Liste der aktuell aufgenommenen Mängel")
            for i, item in enumerate(st.session_state.current_inspections):
                icon = "🟢" if item['Stufe'] == "Grün" else "🟡" if item['Stufe'] == "Gelb" else "🔴"
                st.text(f"{icon} #{i+1} Regal {item['Regal']} - {item['Bauteil']} ({item['Position']})")
            
            if st.button("💾 KOMPLETTEN BERICHT ABSCHLIESSEN & ARCHIVIEREN", type="primary", use_container_width=True):
                neuer_bericht = {
                    "datum": datum_heute.strftime("%d.%m.%Y"),
                    "standort": standort,
                    "bereich": gebaeude,
                    "pruefer": inspektor,
                    "mangel_liste": st.session_state.current_inspections.copy()
                }
                st.session_state.db[selected_customer]["berichte"].append(neuer_bericht)
                save_db(st.session_state.db)
                st.session_state.current_inspections = [] 
                st.success("Bericht erfolgreich im Archiv gespeichert!")
                st.rerun()

    # --- TAB 2: ARCHIV / HISTORIE ---
    with tab2:
        st.subheader(f"Gespeicherte Berichte für {selected_customer}")
        berichte = st.session_state.db[selected_customer].get("berichte", [])
        
        if not berichte:
            st.write("Noch keine Berichte für diesen Kunden vorhanden.")
        else:
            for idx, b in enumerate(reversed(berichte)):
                with st.expander(f"📅 Bericht vom {b['datum']} - Bereich: {b['bereich']}"):
                    st.write(f"**Prüfer:** {b['pruefer']} | **Mängel:** {len(b['mangel_liste'])}")
                    
                    if st.button(f"📄 PDF für Bericht am {b['datum']} erstellen", key=f"pdf_{idx}"):
                        pdf = FPDF()
                        pdf.set_auto_page_break(auto=True, margin=20)
                        
                        # Deckblatt
                        pdf.add_page()
                        pdf.set_font("Arial", 'B', 24)
                        pdf.cell(0, 40, "Inspektionsbericht Regalanlagen", ln=True, align='C')
                        pdf.set_font("Arial", '', 14)
                        pdf.cell(0, 10, f"Kunde: {selected_customer}", ln=True)
                        pdf.cell(0, 10, f"Standort: {b['standort']} | Bereich: {b['bereich']}", ln=True)
                        pdf.cell(0, 10, f"Prüfer: {b['pruefer']} | Datum: {b['datum']}", ln=True)
                        pdf.ln(20)

                        # Mängel-Aufzählung
                        for item in b['mangel_liste']:
                            if pdf.get_y() > 180: pdf.add_page()
                            
                            if item['Stufe'] == "ROT": pdf.set_fill_color(255, 200, 200)
                            elif item['Stufe'] == "Gelb": pdf.set_fill_color(255, 243, 200)
                            else: pdf.set_fill_color(200, 255, 200)
                            
                            pdf.set_font("Arial", 'B', 14)
                            pdf.cell(0, 12, f"REGAL: {item['Regal']} - STATUS: {item['Stufe']}", ln=True, fill=True)
                            
                            pdf.set_font("Arial", 'B', 12)
                            pdf.cell(45, 8, "Bauteil:", ln=0)
                            pdf.set_font("Arial", '', 12)
                            pdf.cell(0, 8, f"{item['Bauteil']}", ln=True)
                            
                            pdf.set_font("Arial", 'B', 12)
                            pdf.cell(45, 8, "Position:", ln=0)
                            pdf.set_font("Arial", '', 12)
                            pdf.cell(0, 8, f"{item['Position']}", ln=True)
                            
                            pdf.set_font("Arial", 'B', 12)
                            pdf.cell(0, 8, "Beschreibung:", ln=True)
                            pdf.set_font("Arial", '', 11)
                            pdf.multi_cell(0, 7, f"{item['Mangel']}\nMassnahme: {item['Massnahme']}")
                            
                            if item['Fotos']:
                                pdf.ln(3)
                                y_f, x_f = pdf.get_y(), 10
                                for f_path in item['Fotos']:
                                    if os.path.exists(f_path):
                                        pdf.image(f_path, x=x_f, y=y_f, w=45)
                                        x_f += 50
                                pdf.set_y(y_f + 42)
                            pdf.ln(5)
                            pdf.line(10, pdf.get_y(), 200, pdf.get_y())
                            pdf.ln(5)
                        
                        pdf_out = pdf.output(dest='S').encode('latin-1', 'replace')
                        st.download_button("📥 PDF Herunterladen", data=pdf_out, file_name=f"Bericht_{selected_customer}.pdf", key=f"dl_{idx}")