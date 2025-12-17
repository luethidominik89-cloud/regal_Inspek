import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime
from PIL import Image
import os

# --- KONFIGURATION ---
st.set_page_config(page_title="Regal-Check Profi", layout="wide")

# Google Sheets Anbindung (Fehlertolerant)
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
if 'form_iteration' not in st.session_state:
    st.session_state.form_iteration = 0
if 'temp_customers' not in st.session_state:
    st.session_state.temp_customers = []

def reset_form():
    st.session_state.form_iteration += 1

# --- KUNDENVERWALTUNG ---
st.sidebar.title("🏢 Verwaltung")

# Bestehende Kunden laden
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
# NEUE KUNDEN ERFASSEN (Wieder aktiv)
new_cust_name = st.sidebar.text_input("➕ Neuen Kunden anlegen", placeholder="Name der Firma")
if st.sidebar.button("Kunde speichern"):
    if new_cust_name and new_cust_name not in all_available_customers:
        # Versuch Cloud-Speicherung
        success = False
        if conn:
            try:
                df_c = conn.read(worksheet="Kunden")
                new_df = pd.concat([df_c, pd.DataFrame([{"Kunde": new_cust_name}])], ignore_index=True)
                conn.update(worksheet="Kunden", data=new_df)
                success = True
            except:
                pass
        
        # Immer auch lokal für die Sitzung merken
        st.session_state.temp_customers.append(new_cust_name)
        st.sidebar.success(f"Kunde '{new_cust_name}' ist bereit!")
        st.rerun()

# --- HAUPTSEITE ---
if selected_customer == "---":
    st.title("🛡️ Regal-Check System")
    st.info("Bitte wählen Sie links einen Kunden aus oder legen Sie einen neuen an.")
else:
    tab1, tab2 = st.tabs(["📝 Neue Inspektion", "📁 Archiv (Alte Berichte)"])

    with tab1:
        st.subheader(f"Prüfung für: {selected_customer}")
        with st.expander("📍 Berichts-Kopfdaten", expanded=True):
            c1, c2 = st.columns(2)
            standort = c1.text_input("Standort (Stadt)", placeholder="z.B. Berlin")
            gebaeude = c1.text_input("Gebäude / Halle / Werk", placeholder="z.B. Werk 2, Halle 4")
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
            if st.button("💾 BERICHT ABSCHLIESSEN & ARCHIVIEREN"):
                if conn:
                    try:
                        old_rep = conn.read(worksheet="Berichte")
                        new_data = []
                        for item in st.session_state.inspections:
                            new_data.append({
                                "Datum": datum_heute.strftime("%d.%m.%Y"),
                                "Kunde": selected_customer,
                                "Standort": standort,
                                "Regal": item["Regal"],
                                "Mangel": item["Mangel"],
                                "Status": item["Stufe"]
                            })
                        updated_rep = pd.concat([old_rep, pd.DataFrame(new_data)], ignore_index=True)
                        conn.update(worksheet="Berichte", data=updated_rep)
                        st.success("Bericht wurde im Google Sheet Archiv gespeichert!")
                        st.session_state.inspections = []
                        st.rerun()
                    except:
                        st.error("Archivierung fehlgeschlagen. Bitte Berechtigungen prüfen.")

    with tab2:
        st.subheader(f"Berichts-Historie: {selected_customer}")
        if conn:
            try:
                all_rep = conn.read(worksheet="Berichte", ttl="1m")
                cust_rep = all_rep[all_rep["Kunde"] == selected_customer]
                if not cust_rep.empty:
                    st.dataframe(cust_rep, use_container_width=True, hide_index=True)
                else:
                    st.write("Keine alten Berichte gefunden.")
            except:
                st.write("Verbindung zum Archiv fehlgeschlagen.")