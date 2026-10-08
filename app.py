import streamlit as st
import pandas as pd
import datetime
import numpy as np
import sqlite3
import re
from PIL import Image
from fpdf import FPDF
import librosa
import librosa.display
import matplotlib.pyplot as plt

# Configuración de la página
st.set_page_config(
    page_title="Clinic-IA | Veterinaria de Precisión (México)",
    page_icon="🩺",
    layout="wide"
)

# ==========================================
# BASE DE DATOS LOCAL Y GESTIÓN OFFLINE-FIRST (SQLITE)
# ==========================================
def init_local_db():
    conn = sqlite3.connect('clinic_ia_offline.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS patient_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    rancho TEXT, municipio TEXT, estado TEXT, patient_id TEXT, 
                    date TEXT, species TEXT, breed TEXT, sex TEXT, 
                    system TEXT, weight REAL, notes TEXT,
                    sync_status TEXT DEFAULT 'pending'
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS appointments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    meeting_id TEXT, owner TEXT, rancho TEXT, 
                    species TEXT, urgency TEXT, datetime TEXT, 
                    motive TEXT, link TEXT,
                    sync_status TEXT DEFAULT 'pending'
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS iot_alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    device_id TEXT, tag_type TEXT, alert_type TEXT, 
                    timestamp TEXT, description TEXT, status TEXT,
                    sync_status TEXT DEFAULT 'pending'
                )''')
    conn.commit()
    conn.close()

init_local_db()

def save_record_sqlite(record):
    conn = sqlite3.connect('clinic_ia_offline.db')
    c = conn.cursor()
    c.execute('''INSERT INTO patient_records 
                 (rancho, municipio, estado, patient_id, date, species, breed, sex, system, weight, notes, sync_status)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending')''',
              (record['Rancho / Predio'], record['Municipio'], record['Estado'], record['ID Paciente'],
               record['Fecha'], record['Especie'], record['Raza'], record['Sexo'],
               record['Sistema Afectado'], record['Peso (kg)'], record['Notas Clínicas']))
    conn.commit()
    conn.close()

def load_records_sqlite():
    conn = sqlite3.connect('clinic_ia_offline.db')
    df = pd.read_sql_query("SELECT * FROM patient_records", conn)
    conn.close()
    return df

def save_appointment_sqlite(app):
    conn = sqlite3.connect('clinic_ia_offline.db')
    c = conn.cursor()
    c.execute('''INSERT INTO appointments 
                 (meeting_id, owner, rancho, species, urgency, datetime, motive, link, sync_status)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending')''',
              (app['ID Cita'], app['Propietario'], app['Rancho'], app['Especie'],
               app['Urgencia'], app['Fecha/Hora'], app['Motivo'], app['Enlace']))
    conn.commit()
    conn.close()

def load_appointments_sqlite():
    conn = sqlite3.connect('clinic_ia_offline.db')
    df = pd.read_sql_query("SELECT * FROM appointments", conn)
    conn.close()
    return df

def save_iot_alert_sqlite(alert):
    conn = sqlite3.connect('clinic_ia_offline.db')
    c = conn.cursor()
    c.execute('''INSERT INTO iot_alerts (device_id, tag_type, alert_type, timestamp, description, status, sync_status)
                 VALUES (?, ?, ?, ?, ?, ?, 'pending')''',
              (alert['device_id'], alert['tag_type'], alert['alert_type'], alert['timestamp'], alert['description'], alert['status']))
    conn.commit()
    conn.close()

def load_iot_alerts_sqlite():
    conn = sqlite3.connect('clinic_ia_offline.db')
    df = pd.read_sql_query("SELECT * FROM iot_alerts ORDER BY id DESC", conn)
    conn.close()
    return df

def get_pending_sync_stats():
    conn = sqlite3.connect('clinic_ia_offline.db')
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM patient_records WHERE sync_status = 'pending'")
    p = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM appointments WHERE sync_status = 'pending'")
    a = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM iot_alerts WHERE sync_status = 'pending'")
    i = c.fetchone()[0]
    conn.close()
    return p + a + i

def sync_local_to_cloud_mock():
    conn = sqlite3.connect('clinic_ia_offline.db')
    c = conn.cursor()
    c.execute("UPDATE patient_records SET sync_status = 'synced' WHERE sync_status = 'pending'")
    c.execute("UPDATE appointments SET sync_status = 'synced' WHERE sync_status = 'pending'")
    c.execute("UPDATE iot_alerts SET sync_status = 'synced' WHERE sync_status = 'pending'")
    conn.commit()
    conn.close()


# ==========================================
# GENERADOR DE PDF PROFESIONAL CON FOLIO
# ==========================================
def clean_for_pdf(text):
    if not text:
        return ""
    text = re.sub(r'[\*`_#]', '', str(text))
    return text.encode('latin-1', 'ignore').decode('latin-1')

class ClinicPDF(FPDF):
    def header(self):
        self.set_font('helvetica', 'B', 15)
        self.set_text_color(15, 23, 42)
        self.cell(0, 8, 'CLINIC-IA MEXICO | RECETA Y REPORTE OFICIAL SENASICA', 0, 1, 'C')
        self.set_font('helvetica', 'I', 9)
        self.set_text_color(100, 116, 139)
        self.cell(0, 5, 'Dr. Vet. Alejandro Castaneda Correa - Zootecnia y Sanidad Pecuaria Nacional', 0, 1, 'C')
        self.ln(3)

    def footer(self):
        self.set_y(-15)
        self.set_font('helvetica', 'I', 8)
        self.set_text_color(148, 163, 184)
        self.cell(0, 10, f'Folio de Validacion Oficial SINIIGA/SENASICA | Pagina {self.page_no()}', 0, 0, 'C')

def generate_pdf_report(patient_id, rancho, municipio, estado, species, breed, weight, diagnosis_text, nutritional_text, treatment_text, withdrawal_text, economic_text):
    pdf = ClinicPDF()
    pdf.add_page()
    
    folio = f"MX-CLINIC-2026-{np.random.randint(10000, 99999)}"
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    
    pdf.set_font('helvetica', 'B', 10)
    pdf.set_fill_color(241, 245, 249)
    pdf.cell(0, 7, f" FOLIO UNICO NACIONAL: {folio}", 0, 1, 'L', True)
    pdf.cell(0, 7, f" Fecha y Hora de Emision: {timestamp} (MEX)", 0, 1, 'L', True)
    pdf.ln(3)
    
    pdf.set_font('helvetica', 'B', 11)
    pdf.cell(0, 7, "1. Resena, Arete SINIIGA y Localizacion", 0, 1)
    pdf.set_font('helvetica', '', 10)
    pdf.multi_cell(0, 5, clean_for_pdf(f"Predio / Rancho: {rancho} | Municipio: {municipio}, {estado}\nArete SINIIGA / ID: {patient_id}\nEspecie: {species} | Raza: {breed} | Peso Vivo: {weight} kg"))
    pdf.ln(2)
    
    pdf.set_font('helvetica', 'B', 11)
    pdf.cell(0, 7, "2. Diagnostico Clinico y Matriz Regional SENASICA", 0, 1)
    pdf.set_font('helvetica', '', 10)
    pdf.multi_cell(0, 5, clean_for_pdf(diagnosis_text))
    pdf.ln(2)
    
    pdf.set_font('helvetica', 'B', 11)
    pdf.cell(0, 7, "3. Sifoneo Nutricional del Hato", 0, 1)
    pdf.set_font('helvetica', '', 10)
    pdf.multi_cell(0, 5, clean_for_pdf(nutritional_text))
    pdf.ln(2)
    
    pdf.set_font('helvetica', 'B', 11)
    pdf.cell(0, 7, "4. Tratamiento, Periodos de Retiro y Costo-Beneficio", 0, 1)
    pdf.set_font('helvetica', '', 10)
    pdf.multi_cell(0, 5, clean_for_pdf(f"{treatment_text}\n\n{withdrawal_text}\n\n{economic_text}"))
    pdf.ln(6)
    
    pdf.set_font('helvetica', 'B', 9)
    pdf.cell(95, 5, "________________________________________", 0, 0, 'C')
    pdf.cell(95, 5, "[ SELLO DIGITAL OFICIAL SENASICA ]", 0, 1, 'C')
    pdf.set_font('helvetica', '', 8)
    pdf.cell(95, 4, "Medico Veterinario Zootecnista Autorizado", 0, 0, 'C')
    pdf.cell(95, 4, f"Folio huella: {folio}-VERIFIED", 0, 1, 'C')
    pdf.cell(95, 4, "Dr. Vet. Alejandro Castaneda Correa", 0, 0, 'C')
    pdf.cell(95, 4, "Trazabilidad y Sanidad Pecuaria en Mexico", 0, 1, 'C')
    
    return bytes(pdf.output())


# ==========================================
# ESTILOS CSS VANGUARDISTAS
# ==========================================
st.markdown("""
<style>
    .main { background-color: #f8fafc; }
    .hero-container {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        padding: 2.5rem;
        border-radius: 16px;
        color: white;
        box-shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.2);
        margin-bottom: 2rem;
        display: flex;
        align-items: center;
        gap: 2rem;
    }
    .hero-logo {
        font-size: 3.5rem;
        background: rgba(255, 255, 255, 0.1);
        padding: 1rem 1.25rem;
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.2);
        text-align: center;
    }
    .hero-title { font-size: 2.75rem; font-weight: 800; margin: 0; color: #ffffff; letter-spacing: -0.025em; }
    .hero-subtitle { font-size: 1.1rem; color: #94a3b8; margin-top: 0.5rem; font-weight: 400; }
    .hero-author { font-size: 0.85rem; color: #38bdf8; margin-top: 0.75rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; }
    .card { background-color: #ffffff; padding: 1.5rem; border-radius: 12px; border: 1px solid #e2e8f0; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05); margin-bottom: 1rem; }
    .stButton button { border-radius: 8px; font-weight: 600; transition: all 0.3s ease; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# INICIALIZACIÓN DE ESTADO DE SESIÓN
# ==========================================
if 'last_estimated_weight' not in st.session_state:
    st.session_state['last_estimated_weight'] = 450.0
if 'last_drug_result' not in st.session_state:
    st.session_state['last_drug_result'] = None
if 'diagnostic_report' not in st.session_state:
    st.session_state['diagnostic_report'] = None

# ==========================================
# MOTOR DE ZONIFICACIÓN Y PRONÓSTICO MÉXICO
# ==========================================
class MexicanZoningAndForecastEngine:
    def __init__(self, region_macro, estado, season, species, system_prod):
        self.region_macro = region_macro
        self.estado = estado
        self.season = season
        self.species = species.lower()
        self.system_prod = system_prod.lower()

    def get_regional_sanitary_profile(self):
        profiles = {
            "Zona Norte (Árida y Semiárida)": {
                "focos_rojos": ["Tuberculosis Bovina (TB)", "Brucelosis (B. abortus)", "Queratoconjuntivitis Infecciosa Bovina", "Anaplasmosis marginalis"],
                "restricciones_senasica": "Control riguroso de movilización (Pruebas negativas de TB y Brucelosis vigentes para tránsito interestatal. Arete SINIIGA obligatorio).",
                "manejo_recomendado": "Suplementación mineral estratégica en épocas de estiaje y control estricto de ectoparásitos por polvo y sequía."
            },
            "Zona Centro - Occidente / Bajío": {
                "focos_rojos": ["Acidosis Ruminal Subaguda (SARA)", "Mastitis bovina subclínica/clínica", "Rabia Paralítica Bovina (Derriengue por murciélago)", "Leptospirosis"],
                "restricciones_senasica": "Campañas de vacunación obligatoria contra Derriengue en zonas endémicas y control de mastitis en sistemas lecheros especializados.",
                "manejo_recomendado": "Monitoreo constante de FDN efectiva en raciones TMR y vacunación anual contra clostridiosis y leptospirosis."
            },
            "Zona Golfo y Trópico Húmedo": {
                "focos_rojos": ["Hemoparasitosis (Anaplasmosis y Babesiosis)", "
