import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime
from PIL import Image
import os
import json

# --- KONFIGURATION ---
st.set_page_config(page_title="Regal-Check Profi Archiv", layout="wide")

# Google Sheets Anbindung
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

# --- DATEN-FUNKTIONEN ---
def get_customers():
    if HAS_GSHEETS:
        try: return conn.read(worksheet="Kunden", ttl="1m")
        except: return pd.DataFrame(columns=["Kunde"])
    return pd.DataFrame(columns=["Kunde"])

def get_all_reports():
    if HAS_GSHEETS:
        try: return conn.read(worksheet="Berichte", ttl="1m")
        except: return pd.DataFrame()
    return pd.DataFrame()

# --- SIDEBAR ---
st.sidebar.title("🏢 Verwaltung")
df_kunden = get_customers()
selected_customer = st.sidebar.selectbox("Kunde auswählen", ["---"] + df_kunden["Kunde"].tolist())

# --- HAUPTSEITE ---
if selected_customer == "---":
    st.title("🛡️ Regal-Check System")
    st.info("Bitte wählen Sie links einen Kunden aus.")
else:
    tab1, tab2 = st.tabs(["📝 Neue Inspektion", "📁 Archiv (Alte Berichte)"])

    with tab1:
        st.subheader(f"Neue Prüfung: {selected_customer}")
        with st.expander("📍 Kopfdaten"):
            c1, c2 = st.columns(2)
            standort = c1.text_input("Standort", key="st_in")
            gebaeude = c1.text_input("Halle / Werk", key="ha_in")
            inspektor = c2.text_input("Prüfer", key="pr_in")
            datum_heute = c2.date_input("Datum", datetime.now())

        # Eingabemaske für Mängel (wie bisher)
        st.divider()
        it = st.session_state.form_iteration
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            regal_nr = st.text_input("Regal-Nr.", key=f"r_{it}")
            bauteil = st.selectbox("Bauteil", ["Stütze", "Traverse", "Rammschutz"], key=f"b_{it}")
        with col2:
            gefahr = st.radio("Status", ["Grün", "Gelb", "ROT"], horizontal=True, key=f"s_{it}")
            mangel = st.text_input("Mangel / Kommentar", key=f"m_{it}")
        with col3:
            f1 = st.camera_input("Foto", key=f"f_{it}")

        if st.button("✅ Mangel hinzufügen"):
            st.session_state.inspections.append({
                "Regal": regal_nr, "Bauteil": bauteil, "Stufe": gefahr, "Mangel": mangel
            })
            reset_form()
            st.rerun()

        # SPEICHERN IN DATENBANK
        if st.session_state.inspections:
            st.write("---")
            if st.button("💾 BERICHT IN DATENBANK SPEICHERN"):
                if HAS_GSHEETS:
                    # Bericht in Zeilenform umwandeln für Google Sheets
                    new_report_data = []
                    for item in st.session_state.inspections:
                        new_report_data.append({
                            "Datum": datum_heute.strftime("%d.%m.%Y"),
                            "Kunde": selected_customer,
                            "Standort": standort,
                            "Prüfer": inspektor,
                            "Regal": item["Regal"],
                            "Mangel": item["Mangel"],
                            "Status": item["Stufe"]
                        })
                    
                    old_reports = get_all_reports()
                    updated_reports = pd.concat([old_reports, pd.DataFrame(new_report_data)], ignore_index=True)
                    conn.update(worksheet="Berichte", data=updated_reports)
                    st.success("Erfolgreich im Archiv gespeichert!")
                    st.session_state.inspections = []
                    st.rerun()

    with tab2:
        st.subheader(f"Historie für {selected_customer}")
        all_reports = get_all_reports()
        if not all_reports.empty:
            # Nur Berichte für den gewählten Kunden filtern
            cust_reports = all_reports[all_reports["Kunde"] == selected_customer]
            if not cust_reports.empty:
                st.dataframe(cust_reports, use_container_width=True)
            else:
                st.write("Keine alten Berichte für diesen Kunden gefunden.")
        else:
            st.write("Datenbank ist leer.")