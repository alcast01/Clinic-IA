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
st.sidebar.markdown("### 🧬🩺 Clinic-IA | Sanidad y Precisión")
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
    
sb_age_group = st.sidebar.selectbox("Grupo Etario", ["Neonato / Cría", "Juvenil / Levante", "Adulto en Producción / Mantenimiento", "Geriátrico / Reproductor"])
sb_sex = st.sidebar.selectbox("Sexo", ["Hembra", "Macho", "Macho Castrado"])

sb_evolution = st.sidebar.selectbox("Tiempo de Evolución", ["Hiperagudo (< 12 hrs)", "Agudo (12 - 48 hrs)", "Subagudo (3 - 7 días)", "Crónico (> 7 días)"])
sb_morbidity = st.sidebar.selectbox("Incidencia en el Hato / Lote", ["Caso esporádico (1 animal)", "Brote focal (2 a 5 animales)", "Brote masivo (> 10%)"])
sb_system = st.sidebar.selectbox("Sistema Principal Afectado", ["Digestivo / Metabólico", "Respiratorio", "Locomotor / Podal", "Reproductivo / Urogenital", "Nervioso / Infeccioso sistémico"])

sb_system_prod = st.sidebar.selectbox("Sistema de Alojamiento", ["Estabulación total / Confinamiento", "Pastoreo rotacional intensivo", "Sistema extensivo / Agostadero"])
sb_diet_change = st.sidebar.selectbox("Factor de Riesgo / Sanitario", ["Sin cambios recientes", "Cambio abrupto de dieta / Forraje", "Ingreso de animales sin cuarentena (SINIIGA)", "Exposición a vectores / garrapatas / murciélagos"])

current_patient_id = st.sidebar.text_input("🆔 Arete SINIIGA / ID / Nombre", value="MX-849201")

st.sidebar.markdown("""
<div style='text-align: center; color: #64748b; font-size: 0.85rem; padding: 10px;'>
Plataforma Nacional Clinic-IA México<br><b>Dr. Vet. Alejandro Castañeda Correa</b>
</div>
""", unsafe_allow_html=True)

# ==========================================
# ENCABEZADO VANGUARDISTA CON LOGOTIPO TECNOLÓGICO-VETERINARIO
# ==========================================
st.markdown("""
<div class="hero-container">
    <div class="hero-logo">🧬🩺</div>
    <div>
        <h1 class="hero-title">Clinic-IA México</h1>
        <p class="hero-subtitle">Sistema experto de diagnóstico veterinario, zonificación sanitaria SENASICA y pronóstico epidemiológico predictivo.</p>
        <p class="hero-author">Autor: Dr. Vet. Alejandro Castañeda Correa | Cobertura Nacional</p>
    </div>
</div>
""", unsafe_allow_html=True)

# ==========================================
# PESTAÑAS PRINCIPALES (8 SECCIONES)
# ==========================================
tab_diag, tab_zone, tab_reg, tab_drugs, tab_weight, tab_audio, tab_iot, tab_tele = st.tabs([
    "🩺 Diagnóstico e IA Nutricional", 
    "🗺️ Zonificación SENASICA y Pronóstico",
    "📁 Historial por Rancho", 
    "💊 Vademecum, Retiros y Costo-Beneficio", 
    "⚖️ Estimación de Peso",
    "🔊 Fonofonía y Espectrogramas (FFT)",
    "📡 IoT y Telemetría de Hato",
    "📅 Videollamada / Urgencias"
])

# --- PESTAÑA 1: DIAGNÓSTICO CLÍNICO Y SIFONEO NUTRICIONAL ---
with tab_diag:
    st.subheader(f"Evaluación Clínica de Precisión: Arete SINIIGA `[{current_patient_id}]`")
    st.info(f"Ubicación activa: **{estado_seleccionado}, {municipio_input} ({macro_region})** | Estación: **{sb_season}**")
    
    col_d1, col_d2, col_d3 = st.columns(3)
    with col_d1:
        temp = st.number_input("Temperatura Corporal (°C)", min_value=30.0, max_value=43.0, value=38.5, step=0.1)
    with col_d2:
        hr = st.number_input("Frecuencia Cardíaca (lpm)", min_value=10, max_value=220, value=70, step=1)
    with col_d3:
        rr = st.number_input("Frecuencia Respiratoria (rpm)", min_value=5, max_value=120, value=20, step=1)

    st.markdown("---")
    st.markdown("#### Hallazgos Clínicos y Factores de Riesgo")
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        sign_1 = st.checkbox("Hipomotilidad / Atonía orgánica")
        sign_2 = st.checkbox("Deshidratación moderada/severa (>6%)")
    with col_s2:
        sign_3 = st.checkbox("Signos de dolor abdominal / cólico / incomodidad")
        sign_4 = st.checkbox("Secreción óculo-nasal o descarga hemorrágica / disfonia")

    if st.button("Ejecutar Diagnóstico y Modelo Predictivo Nacional", type="primary"):
        engine = MexicanZoningAndForecastEngine(macro_region, estado_seleccionado, sb_season, sb_species, sb_prod_type)
        vitals_eval = engine.get_regional_sanitary_profile()
        
        differentials = [
            {"dx": "Acidosis Ruminal Subaguda (SARA) / Trastorno Metabólico", "prob": 92 if "Digestivo" in sb_system else 65},
            {"dx": "Complejo Infeccioso Endémico Regional (SENASICA Foco Rojo)", "prob": 84},
            {"dx": "Proceso inflamatorio sistémico secundario por estrés ambiental", "prob": 72}
        ]
        
        nutri_advice = (
            "🌾 **Sifoneo Nutricional Adaptado a México:**\n"
            f"- Ajustar niveles de proteína y FDN acorde a la disponibilidad de forrajes en `{estado_seleccionado}` durante la temporada de `{sb_season}`.\n"
            "- Suplementación mineral con bloques multinutricionales para prevenir caídas metabólicas."
        )
        
        forecast_data = engine.compute_disease_forecast(sb_system)

        st.session_state['diagnostic_report'] = {
            "differentials": differentials,
            "patient": current_patient_id,
            "region": f"{estado_seleccionado}, {macro_region}",
            "season": sb_season,
            "nutritional": nutri_advice,
            "forecast": forecast_data
        }

    st.divider()
    st.subheader("📊 Reporte Diagnóstico y Matriz de Riesgo Nacional")
    if st.session_state['diagnostic_report']:
        report = st.session_state['diagnostic_report']
        st.markdown(f"**Paciente Arete:** `{report['patient']}` | 📍 **Región:** `{report['region']}`")
        
        st.markdown("### 1. Diagnósticos Diferenciales Ponderados")
        for idx, item in enumerate(report['differentials'], 1):
            confidence = item['prob']
            st.markdown(f"**{idx}. {item['dx']}** — Probabilidad Coincidencia: **{confidence}%**")
            st.progress(confidence / 100.0)
            
        st.markdown("### 2. Pronóstico Epidemiológico Predictivo para el Hato")
        fc = report['forecast']
        st.warning(f"⚠️ **Índice de Riesgo de Brote en Zona:** `{fc['score']}%` (Nivel de Alerta: **{fc['nivel']}**)")
        for alert in fc['alerts']:
            st.write(alert)

        st.markdown("### 3. Sifoneo Nutricional")
        st.info(report['nutritional'])
    else:
        st.info("💡 Ingrese los datos clínicos y presione el botón para ejecutar el diagnóstico experto adaptado a México.")


# --- PESTAÑA 2: ZONIFICACIÓN SENASICA Y PRONÓSTICO ---
with tab_zone:
    st.subheader("🗺️ Zonificación Sanitaria SENASICA y Pronóstico de Enfermedades en México")
    st.markdown("Consulte las restricciones oficiales de movilización, las enfermedades de notificación obligatoria y el pronóstico de brotes para su estado.")

    engine_zone = MexicanZoningAndForecastEngine(macro_region, estado_seleccionado, sb_season, sb_species, sb_prod_type)
    sanitary_profile = engine_zone.get_regional_sanitary_profile()
    forecast_current = engine_zone.compute_disease_forecast(sb_system)

    col_z1, col_z2 = st.columns(2)
    with col_z1:
        st.markdown(f"### 📍 Perfil Sanitario: `{estado_seleccionado}`")
        
        sanitary_info_text = (
            f"**Macro-Región:** {macro_region}\n\n"
            "**Restricciones y Campañas SENASICA / SADER:**\n"
            f"{sanitary_profile['restricciones_senasica']}"
        )
        st.info(sanitary_info_text)
        
        st.markdown("#### 🔴 Focos Rojos Epidemiológicos en la Zona")
        for fr in sanitary_profile['focos_rojos']:
            st.markdown(f"- ⚠️ {fr}")
            
    with col_z2:
        st.markdown("### 🔮 Pronóstico y Alerta Epidemiológica Predictiva")
        st.metric(label="Índice de Riesgo Predictivo de Brote", value=f"{forecast_current['score']}%", delta=forecast_current['nivel'], delta_color="inverse")
        st.markdown(f"**Estacionalidad analizada:** `{sb_season}`")
        
        st.markdown("#### 📋 Recomendaciones de Manejo Preventivo:")
        st.success(sanitary_profile['manejo_recomendado'])
        for fa in forecast_current['alerts']:
            st.write(fa)


# --- PESTAÑA 3: HISTORIAL POR RANCHO (SQLITE) ---
with tab_reg:
    st.subheader("📁 Archivo Local de Pacientes y Sincronización Rural (Lazy Sync)")
    st.markdown("Gestión offline-first de expedientes con control de estado y transmisión asíncrona hacia la nube.")
    
    col_sync1, col_sync2 = st.columns([3, 1])
    with col_sync1:
        pending_count = get_pending_sync_stats()
        st.info(f"📊 Estado de Cola Local: **{pending_count} registros pendientes** de sincronizar con el servidor central.")
    with col_sync2:
        if st.button("🔄 Sincronizar con la Nube", type="secondary"):
            sync_local_to_cloud_mock()
            st.success("¡Sincronización completada con éxito!")
            st.rerun()

    st.divider()
    
    col_r1, col_
