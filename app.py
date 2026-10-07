import streamlit as st
import pandas as pd
import datetime
import numpy as np
import sqlite3
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
class ClinicPDF(FPDF):
    def header(self):
        self.set_font('helvetica', 'B', 15)
        self.set_text_color(15, 23, 42)
        self.cell(0, 8, 'CLINIC-IA MÉXICO | RECETA Y REPORTE OFICIAL SENASICA', 0, 1, 'C')
        self.set_font('helvetica', 'I', 9)
        self.set_text_color(100, 116, 139)
        self.cell(0, 5, 'Dr. Vet. Alejandro Castañeda Correa — Zootecnia y Sanidad Pecuaria Nacional', 0, 1, 'C')
        self.ln(3)

    def footer(self):
        self.set_y(-15)
        self.set_font('helvetica', 'I', 8)
        self.set_text_color(148, 163, 184)
        self.cell(0, 10, f'Folio de Validación Oficial SINIIGA/SENASICA | Página {self.page_no()}', 0, 0, 'C')

def generate_pdf_report(patient_id, rancho, municipio, estado, species, breed, weight, diagnosis_text, nutritional_text, treatment_text, withdrawal_text, economic_text):
    pdf = ClinicPDF()
    pdf.add_page()
    
    folio = f"MX-CLINIC-2026-{np.random.randint(10000, 99999)}"
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    
    pdf.set_font('helvetica', 'B', 10)
    pdf.set_fill_color(241, 245, 249)
    pdf.cell(0, 7, f" FOLIO ÚNICO NACIONAL: {folio}", 0, 1, 'L', True)
    pdf.cell(0, 7, f" Fecha y Hora de Emisión: {timestamp} (MEX)", 0, 1, 'L', True)
    pdf.ln(3)
    
    pdf.set_font('helvetica', 'B', 11)
    pdf.cell(0, 7, "1. Reseña, Arete SINIIGA y Localización", 0, 1)
    pdf.set_font('helvetica', '', 10)
    pdf.multi_cell(0, 5, f"Predio / Rancho: {rancho} | Municipio: {municipio}, {estado}\nArete SINIIGA / ID: {patient_id}\nEspecie: {species} | Raza: {breed} | Peso Vivo: {weight} kg")
    pdf.ln(2)
    
    pdf.set_font('helvetica', 'B', 11)
    pdf.cell(0, 7, "2. Diagnóstico Clínico y Matriz Regional SENASICA", 0, 1)
    pdf.set_font('helvetica', '', 10)
    pdf.multi_cell(0, 5, diagnosis_text)
    pdf.ln(2)
    
    pdf.set_font('helvetica', 'B', 11)
    pdf.cell(0, 7, "3. Sifoneo Nutricional del Hato", 0, 1)
    pdf.set_font('helvetica', '', 10)
    pdf.multi_cell(0, 5, nutritional_text)
    pdf.ln(2)
    
    pdf.set_font('helvetica', 'B', 11)
    pdf.cell(0, 7, "4. Tratamiento, Periodos de Retiro y Costo-Beneficio", 0, 1)
    pdf.set_font('helvetica', '', 10)
    pdf.multi_cell(0, 5, f"{treatment_text}\n\n{withdrawal_text}\n\n{economic_text}")
    pdf.ln(6)
    
    pdf.set_font('helvetica', 'B', 9)
    pdf.cell(95, 5, "________________________________________", 0, 0, 'C')
    pdf.cell(95, 5, "[ SELLO DIGITAL OFICIAL SENASICA ]", 0, 1, 'C')
    pdf.set_font('helvetica', '', 8)
    pdf.cell(95, 4, "Médico Veterinario Zootecnista Autorizado", 0, 0, 'C')
    pdf.cell(95, 4, f"Folio huella: {folio}-VERIFIED", 0, 1, 'C')
    pdf.cell(95, 4, "Dr. Vet. Alejandro Castañeda Correa", 0, 0, 'C')
    pdf.cell(95, 4, "Trazabilidad y Sanidad Pecuaria en México", 0, 1, 'C')
    
    return pdf.output(dest='S').encode('latin1')


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
        font-size: 4rem;
        background: rgba(255, 255, 255, 0.1);
        padding: 1rem 1.5rem;
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.2);
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
                "focos_rojos": ["Hemoparasitosis (Anaplasmosis y Babesiosis)", "Carbón Sintomático y Edema Maligno", "Estomatitis Vesicular", "Fiebre Porcina Clásica / Vigilancia activa"],
                "restricciones_senasica": "Control estricto del vector (Garrapata *Rhipicephalus microplus*), baños garrapaticidas calendarizados y restricciones de movilización en zonas de erradicación.",
                "manejo_recomendado": "Manejo rotacional de potreros para disminuir carga parasitaria y programas de inmunización contra clostridios antes de la temporada de lluvias."
            },
            "Zona Sur - Sureste y Península": {
                "focos_rojos": ["Tuberculosis bovina en zonas tropicales", "Gusano Barrenador del Ganado (Vigilancia Fronteriza Sur)", "Complejo Respiratorio por estrés de humedad", "Parasitosis gastrointestinal severa"],
                "restricciones_senasica": "Vigilancia epidemiológica activa para prevención de entrada de plagas transfronterizas y certificación de hatos libres.",
                "manejo_recomendado": "Desparasitación estratégica basada en contención coproparasitoscópica y suplementación mineral con alta biodisponibilidad."
            }
        }
        return profiles.get(self.region_macro, profiles["Zona Centro - Occidente / Bajío"])

    def compute_disease_forecast(self, system_affected):
        risk_score = 45
        forecast_alerts = []

        if "Lluvias" in self.season:
            if "Golfo" in self.region_macro or "Sur" in self.region_macro:
                risk_score += 42
                forecast_alerts.append("🔴 **Alerta Roja por Vectores:** Alta probabilidad de brotes de Anaplasmosis y Babesiosis por proliferación de garrapata en temporada de humedad.")
                forecast_alerts.append("⚠️ **Alerta Sanitaria:** Incremento en incidencia de pododermatitis infecciosa por reblandecimiento de pezuñas en lodazales.")
            else:
                risk_score += 25
                forecast_alerts.append("🟡 **Alerta Moderada:** Riesgo de parasitosis gastrointestinales y neumonías por cambios bruscos de temperatura ambiental.")
        elif "Secas" in self.season:
            if "Norte" in self.region_macro:
                risk_score += 35
                forecast_alerts.append("🟡 **Alerta por Estiaje:** Riesgo elevado de botulismo por deficiencia mineral y cuadros respiratorios por inhalación de polvo en corrales.")
            else:
                risk_score += 20
                forecast_alerts.append("🟢 **Riesgo Estacional Bajo-Controlado:** Mantener vigilancia en agua de bebida y calidad de forrajes conservados.")

        if system_affected == "Digestivo / Metabólico" and ("Bajío" in self.region_macro or "Norte" in self.region_macro):
            risk_score += 18
            forecast_alerts.append("📊 **Tendencia Zootécnica:** Incremento estacional de SARA debido a dietas altas en grano por escasez de forraje verde.")

        risk_score = min(98, max(15, risk_score))
        nivel_riesgo = "CRÍTICO" if risk_score > 75 else ("MODERADO" if risk_score > 45 else "BAJO")
        
        return {
            "score": risk_score,
            "nivel": nivel_riesgo,
            "alerts": forecast_alerts
        }


# ==========================================
# PANEL LATERAL DE MÉXICO Y ZONIFICACIÓN
# ==========================================
st.sidebar.markdown("### 🇲🇽 Panel Nacional de Sanidad (México)")
pending_syncs = get_pending_sync_stats()
if pending_syncs > 0:
    st.sidebar.warning(f"🟡 **Modo Offline Rural:** `{pending_syncs}` registros pendientes de sincronizar.")
else:
    st.sidebar.success("🟢 **Modo Sincronizado** (SENASICA Cloud Ready)")

macro_region = st.sidebar.selectbox("🗺️ Macro-Región Ganadera", [
    "Zona Norte (Árida y Semiárida)", 
    "Zona Centro - Occidente / Bajío", 
    "Zona Golfo y Trópico Húmedo", 
    "Zona Sur - Sureste y Península"
])

estados_mexico = {
    "Zona Norte (Árida y Semiárida)": ["Sonora", "Chihuahua", "Coahuila", "Nuevo León", "Durango", "Baja California", "Baja California Sur", "Tamaulipas", "San Luis Potosí", "Zacatecas"],
    "Zona Centro - Occidente / Bajío": ["Jalisco", "Aguascalientes", "Guanajuato", "Michoacán", "Querétaro", "Hidalgo", "Estado de México", "Ciudad de México", "Tlaxcala", "Morelos"],
    "Zona Golfo y Trópico Húmedo": ["Veracruz", "Tabasco", "Oaxaca", "Puebla"],
    "Zona Sur - Sureste y Península": ["Chiapas", "Yucatán", "Quintana Roo", "Campeche", "Guerrero", "Colima", "Nayarit"]
}

estado_seleccionado = st.sidebar.selectbox("🏛️ Estado de la República", estados_mexico.get(macro_region, ["Jalisco"]))
municipio_input = st.sidebar.text_input("📍 Municipio / Localidad", value="Tlaltenango de Sánchez Román")

sb_season = st.sidebar.selectbox("🌦️ Estación Climática Actual", ["Secas / Estiaje prolongado", "Lluvias / Humedad alta / Huracanes", "Transición / Frentes fríos (Nortes)"])
sb_species = st.sidebar.selectbox("Especie", ["Bovino", "Equino", "Porcino", "Ovino", "Caprino", "Canino", "Felino"])

if sb_species in ["Bovino", "Ovino", "Caprino"]:
    sb_breed = st.sidebar.selectbox("Raza / Biotipo", ["Holstein", "Beefmaster", "Angus", "Cebú / Brahman", "Suizo Pardo", "Pelibuey / Boer", "Cruzado"])
    sb_prod_type = "Leche" if st.sidebar.selectbox("Propósito", ["Leche", "Carne", "Doble Propósito"]) == "Leche" else "Carne"
else:
    sb_breed = st.sidebar.text_input("Raza / Biotipo", value="Estándar / Mestizo")
    sb_prod_type = "general"
    
sb_age_group = st.sidebar.selectbox
