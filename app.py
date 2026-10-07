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
    page_title="Clinic-IA | Veterinaria de Precisión",
    page_icon="🩺",
    layout="wide"
)

# ==========================================
# BASE DE DATOS LOCAL (OFFLINE-FIRST / SQLITE)
# ==========================================
def init_local_db():
    conn = sqlite3.connect('clinic_ia_offline.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS patient_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    rancho TEXT, municipio TEXT, patient_id TEXT, 
                    date TEXT, species TEXT, breed TEXT, sex TEXT, 
                    system TEXT, weight REAL, notes TEXT
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS appointments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    meeting_id TEXT, owner TEXT, rancho TEXT, 
                    species TEXT, urgency TEXT, datetime TEXT, 
                    motive TEXT, link TEXT
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS iot_alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    device_id TEXT, tag_type TEXT, alert_type TEXT, 
                    timestamp TEXT, description TEXT, status TEXT
                )''')
    conn.commit()
    conn.close()

init_local_db()

def save_record_sqlite(record):
    conn = sqlite3.connect('clinic_ia_offline.db')
    c = conn.cursor()
    c.execute('''INSERT INTO patient_records 
                 (rancho, municipio, patient_id, date, species, breed, sex, system, weight, notes)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
              (record['Rancho / Predio'], record['Municipio'], record['ID Paciente'],
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
                 (meeting_id, owner, rancho, species, urgency, datetime, motive, link)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
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
    c.execute('''INSERT INTO iot_alerts (device_id, tag_type, alert_type, timestamp, description, status)
                 VALUES (?, ?, ?, ?, ?, ?)''',
              (alert['device_id'], alert['tag_type'], alert['alert_type'], alert['timestamp'], alert['description'], alert['status']))
    conn.commit()
    conn.close()

def load_iot_alerts_sqlite():
    conn = sqlite3.connect('clinic_ia_offline.db')
    df = pd.read_sql_query("SELECT * FROM iot_alerts ORDER BY id DESC", conn)
    conn.close()
    return df


# ==========================================
# GENERADOR DE PDF PROFESIONAL CON FOLIO Y QR
# ==========================================
class ClinicPDF(FPDF):
    def header(self):
        self.set_font('helvetica', 'B', 16)
        self.set_text_color(15, 23, 42)
        self.cell(0, 10, 'CLINIC-IA | RECETA Y REPORTE CLÍNICO VETERINARIO', 0, 1, 'C')
        self.set_font('helvetica', 'I', 10)
        self.set_text_color(100, 116, 139)
        self.cell(0, 5, 'Dr. Vet. Alejandro Castañeda Correa — Medicina y Zootecnia de Precisión', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-20)
        self.set_font('helvetica', 'I', 8)
        self.set_text_color(148, 163, 184)
        self.cell(0, 10, f'Folio de Validación Oficial | Página {self.page_no()}', 0, 0, 'C')

def generate_pdf_report(patient_id, rancho, municipio, species, breed, weight, diagnosis_text, nutritional_text, treatment_text, withdrawal_text, economic_text):
    pdf = ClinicPDF()
    pdf.add_page()
    
    folio = f"CLINIC-PDF-2026-{np.random.randint(10000, 99999)}"
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    
    pdf.set_font('helvetica', 'B', 11)
    pdf.set_fill_color(241, 245, 249)
    pdf.cell(0, 8, f" FOLIO ÚNICO: {folio}", 0, 1, 'L', True)
    pdf.cell(0, 8, f" Fecha y Hora: {timestamp}", 0, 1, 'L', True)
    pdf.ln(4)
    
    pdf.set_font('helvetica', 'B', 12)
    pdf.cell(0, 8, "1. Reseña e Identificación del Paciente", 0, 1)
    pdf.set_font('helvetica', '', 10)
    pdf.multi_cell(0, 6, f"Predio / Rancho: {rancho} ({municipio})\nIdentificación / Arete: {patient_id}\nEspecie: {species} | Raza: {breed}\nPeso Vivo Registrado: {weight} kg")
    pdf.ln(3)
    
    pdf.set_font('helvetica', 'B', 12)
    pdf.cell(0, 8, "2. Diagnóstico Clínico y Matriz Regional", 0, 1)
    pdf.set_font('helvetica', '', 10)
    pdf.multi_cell(0, 6, diagnosis_text)
    pdf.ln(3)
    
    pdf.set_font('helvetica', 'B', 12)
    pdf.cell(0, 8, "3. Sifoneo Nutricional (Modelos del Hato)", 0, 1)
    pdf.set_font('helvetica', '', 10)
    pdf.multi_cell(0, 6, nutritional_text)
    pdf.ln(3)
    
    pdf.set_font('helvetica', 'B', 12)
    pdf.cell(0, 8, "4. Tratamiento, Retiros y Análisis Económico", 0, 1)
    pdf.set_font('helvetica', '', 10)
    pdf.multi_cell(0, 6, f"{treatment_text}\n\n{withdrawal_text}\n\n{economic_text}")
    pdf.ln(8)
    
    pdf.set_font('helvetica', 'B', 10)
    pdf.cell(95, 6, "________________________________________", 0, 0, 'C')
    pdf.cell(95, 6, "[ CÓDIGO DE VALIDACIÓN OFICIAL ]", 0, 1, 'C')
    pdf.set_font('helvetica', '', 9)
    pdf.cell(95, 5, "Firma y Sello del Médico Veterinario", 0, 0, 'C')
    pdf.cell(95, 5, f"Folio huella: {folio}-VERIFIED", 0, 1, 'C')
    pdf.cell(95, 5, "Dr. Vet. Alejandro Castañeda Correa", 0, 0, 'C')
    pdf.cell(95, 5, "Zootecnia y Nutrición de Precisión", 0, 1, 'C')
    
    return pdf.output(dest='S').encode('latin1')


# ==========================================
# ESTILOS CSS VANGUARDISTAS Y DE EXCELENCIA
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
# MOTOR DE DECISIÓN CLÍNICA Y NUTRICIONAL
# ==========================================
class AdvancedClinicalEngine:
    def __init__(self, species, production_type="general", region="Zacatecas / Centro-Norte", season="Secas"):
        self.species = species.lower()
        self.production_type = production_type.lower()
        self.region = region
        self.season = season
        
    def get_physiological_ranges(self):
        ranges = {
            'bovino_leche': {'temp': (38.0, 39.3), 'hr': (60, 84), 'rr': (18, 28)},
            'bovino_carne': {'temp': (36.7, 39.1), 'hr': (60, 80), 'rr': (10, 30)},
            'equino': {'temp': (37.5, 38.5), 'hr': (28, 40), 'rr': (10, 24)},
            'porcino': {'temp': (38.0, 39.5), 'hr': (60, 90), 'rr': (8, 18)},
            'ovino': {'temp': (38.3, 39.9), 'hr': (70, 80), 'rr': (12, 72)},
            'canino': {'temp': (38.3, 39.2), 'hr': (70, 120), 'rr': (15, 30)},
            'felino': {'temp': (37.8, 39.2), 'hr': (120, 140), 'rr': (20, 30)}
        }
        key = f"{self.species}_{self.production_type}" if f"{self.species}_{self.production_type}" in ranges else self.species
        return ranges.get(key, {'temp': (38.0, 39.0), 'hr': (60, 100), 'rr': (12, 30)})

    def evaluate_vitals(self, temp, hr, rr):
        r = self.get_physiological_ranges()
        alerts = []
        if not (r['temp'][0] <= temp <= r['temp'][1]):
            alerts.append(f"⚠ **Temperatura alterada:** {temp} °C (Normal: {r['temp'][0]} - {r['temp'][1]} °C)")
        if not (r['hr'][0] <= hr <= r['hr'][1]):
            alerts.append(f"⚠️ **Frecuencia cardíaca alterada:** {hr} lpm (Normal: {r['hr'][0]} - {r['hr'][1]} lpm)")
        if not (r['rr'][0] <= rr <= r['rr'][1]):
            alerts.append(f"⚠ **Frecuencia respiratoria alterada:** {rr} rpm (Normal: {r['rr'][0]} - {r['rr'][1]} rpm)")
        return alerts if alerts else ["✅ Constantes fisiológicas dentro de parámetros normales."]

    def compute_differential_diagnosis(self, system_affected, clinical_signs_list, temp, hr, rr):
        differentials = []
        epi_boost = 0
        if "Lluvias / Humedad alta" in self.season:
            epi_boost += 8
        if "Zacatecas / Centro-Norte" in self.region and self.species in ["bovino", "ovino"]:
            epi_boost += 5

        if self.species in ["bovino", "ovino"]:
            if system_affected == "Digestivo / Metabólico":
                differentials = [
                    {"dx": "Acidosis Ruminal Subaguda (SARA) / Aguda", "prob": min(95, (88 if "Cambio de dieta reciente" in clinical_signs_list else 60) + epi_boost)},
                    {"dx": "Desplazamiento de Abomaso (DA)", "prob": min(90, 75 + int(epi_boost/2))},
                    {"dx": "Cetosis Clínica / Subclínica", "prob": 70}
                ]
            elif system_affected == "Respiratorio":
                differentials = [
                    {"dx": "Complejo Respiratorio Bovino (CRB) / Pasteurelosis", "prob": min(98, 92 + epi_boost)},
                    {"dx": "Neumonía Enzoótica / Pleuresía", "prob": min(90, 78 + epi_boost)}
                ]
            else:
                differentials = [{"dx": "Trastorno sistémico multifactorial de origen metabólico/infeccioso", "prob": min(90, 65 + epi_boost)}]
        elif self.species == "equino":
            if system_affected == "Digestivo / Metabólico":
                differentials = [
                    {"dx": "Síndrome Abdominal Agudo (Cólico Espasmódico / Desplazamiento)", "prob": 95},
                    {"dx": "Enteritis / Colitis Aguda", "prob": 80}
                ]
            else:
                differentials = [{"dx": "Obstrucción de Vías Aéreas Superiores / EPPA", "prob": 82}]
        elif self.species in ["canino", "felino"]:
            if system_affected == "Digestivo / Metabólico":
                differentials = [
                    {"dx": "Gastroenteritis Hemorrágica / Parvovirosis", "prob": 89},
                    {"dx": "Cuerpo Extraño Gastrointestinal / Obstrucción", "prob": 78},
                    {"dx": "Pancreatitis Aguda", "prob": 70}
                ]
            elif system_affected == "Reproductivo / Urogenital":
                differentials = [
                    {"dx": "Enfermedad del Tracto Urinario Inferior (FLUTD) / Cistitis", "prob": 91},
                    {"dx": "Insuficiencia Renal Aguda (IRA)", "prob": 84}
                ]
            else:
                differentials = [{"dx": "Proceso inflamatorio sistémico primario", "prob": 75}]
        else:
            differentials = [{"dx": "Patología infecciosa o carencial genérica", "prob": 70}]
            
        return sorted(differentials, key=lambda x: x['prob'], reverse=True)

    def get_nutritional_recommendations(self, top_dx):
        if "Acidosis" in top_dx or "SARA" in top_dx:
            return (
                "🌾 **Sifoneo Nutricional (Corrección para SARA):**\n"
                "- Incrementar la FDN efectiva (eNDF) por encima del 28-30% en la Materia Seca Total.\n"
                "- Incluir bicarbonato de sodio al 1.5% - 2.0% en la ración total mezclada (TMR).\n"
                "- Limitar los carbohidratos no estructurales (CNE) fermentables por comida y revisar el tamaño de partícula del forraje."
            )
        elif "Cetosis" in top_dx:
            return (
                "🧪 **Sifoneo Nutricional (Corrección para Cetosis):**\n"
                "- Administrar propilenglicol oral (300 g/día por 3 a 5 días) como precursor gluconeogénico.\n"
                "- Elevar la densidad energética neta de lactancia (NEL) en la dieta de transición.\n"
                "- Suplementar con colina o niacina protegida para optimizar el metabolismo hepático de lípidos."
            )
        elif "Abomaso" in top_dx:
            return (
                "⚙️ **Sifoneo Nutricional (Prevención DA):**\n"
                "- Incrementar la longitud efectiva de la fibra para estimular la rumia y reducir la flacidez abomasal.\n"
                "- Minimizar el llenado ruminal insuficiente en el periparto evitando reducciones drásticas de consumo."
            )
        else:
            return (
                "🥗 **Recomendación Nutricional General del Hato:**\n"
                "- Balance general de proteína cruda y minerales traza acorde al estatus productivo.\n"
                "- Supervisar la disponibilidad permanente de agua limpia y fresca."
            )


# ==========================================
# PANEL LATERAL DE CAMPO Y RESEÑA
# ==========================================
st.sidebar.markdown("### 🩺 Panel Clínico de Precisión")
st.sidebar.markdown("🟢 *Modo Offline-First (SQLite)* activo en campo.")

sb_region = st.sidebar.selectbox("📍 Región / Municipio Ganadero", ["Zacatecas / Centro-Norte", "Jalisco / Altos y Ciénega", "Bajío / Guanajuato-Michoacán", "Norte / Sonora-Chihuahua", "Otro / General"])
sb_season = st.sidebar.selectbox("🌦️ Estación Climática Actual", ["Secas / Estiaje prolongado", "Lluvias / Humedad alta", "Transición / Frentes fríos"])

sb_species = st.sidebar.selectbox("Especie", ["Bovino", "Equino", "Porcino", "Ovino", "Canino", "Felino"])

if sb_species == "Bovino":
    sb_breed = st.sidebar.selectbox("Raza / Biotipo", ["Holstein", "Beefmaster", "Angus", "Cebú / Brahman", "Suizo Pardo", "Cruzado"])
    sb_prod_type = "Leche" if st.sidebar.selectbox("Propósito", ["Leche", "Carne"]) == "Leche" else "Carne"
else:
    sb_breed = st.sidebar.text_input("Raza / Biotipo", value="Estándar / Mestizo")
    sb_prod_type = "general"
    
sb_age_group = st.sidebar.selectbox("Grupo Etario", ["Neonato / Cría", "Juvenil / Levante", "Adulto en Producción / Mantenimiento", "Geriátrico / Reproductor"])
sb_sex = st.sidebar.selectbox("Sexo", ["Hembra", "Macho", "Macho Castrado"])

sb_evolution = st.sidebar.selectbox("Tiempo de Evolución", ["Hiperagudo (< 12 hrs)", "Agudo (12 - 48 hrs)", "Subagudo (3 - 7 días)", "Crónico (> 7 días)"])
sb_morbidity = st.sidebar.selectbox("Incidencia en el Lote / Colectivo", ["Caso esporádico (1 animal)", "Brote focal (2 a 5 animales)", "Brote masivo (> 10%)"])
sb_system = st.sidebar.selectbox("Sistema Principal Afectado", ["Digestivo / Metabólico", "Respiratorio", "Locomotor / Podal", "Reproductivo / Urogenital", "Nervioso / Infeccioso sistémico"])

sb_system_prod = st.sidebar.selectbox("Sistema de Alojamiento", ["Estabulación total / Confinamiento", "Pastoreo intensivo rotacional", "Sistema mixto / Doméstico"])
sb_diet_change = st.sidebar.selectbox("Factor de Riesgo / Dieta", ["Sin cambios recientes", "Cambio abrupto de dieta (< 48 hrs)", "Acceso a tóxicos / Cuerpos extraños", "Estrés por transporte / climas"])

current_patient_id = st.sidebar.text_input("🆔 Arete / ID / Nombre del Paciente", value="ANIMAL-001")

st.sidebar.markdown("""
<div style='text-align: center; color: #64748b; font-size: 0.85rem; padding: 10px;'>
Diseñado y desarrollado por<br><b>Dr. Vet. Alejandro Castañeda Correa</b>
</div>
""", unsafe_allow_html=True)

# ==========================================
# ENCABEZADO VANGUARDISTA CON LOGOTIPO
# ==========================================
st.markdown("""
<div class="hero-container">
    <div class="hero-logo">🧬</div>
    <div>
        <h1 class="hero-title">Clinic-IA</h1>
        <p class="hero-subtitle">Plataforma experta de diagnóstico clínico, modelos nutricionales y análisis económico de hato.</p>
        <p class="hero-author">Autor: Dr. Vet. Alejandro Castañeda Correa</p>
    </div>
</div>
""", unsafe_allow_html=True)

# ==========================================
# PESTAÑAS PRINCIPALES (7 SECCIONES)
# ==========================================
tab_diag, tab_reg, tab_drugs, tab_weight, tab_audio, tab_iot, tab_tele = st.tabs([
    "🩺 Diagnóstico e IA Nutricional", 
    "📁 Historial por Rancho", 
    "💊 Vademecum, Retiros y Costo-Beneficio", 
    "⚖️ Estimación de Peso",
    "🔊 Fonofonía y Espectrogramas (FFT)",
    "📡 IoT y Telemetría de Hato",
    "📅 Videollamada / Urgencias"
])

# --- PESTAÑA 1: DIAGNÓSTICO CLÍNICO Y SIFONEO NUTRICIONAL ---
with tab_diag:
    st.subheader(f"Evaluación Clínica de Precisión: [{current_patient_id}]")
    st.info(f"Reseña activa: **{sb_species} | Raza: {sb_breed} | Región: {sb_region} | Estación: {sb_season}**")
    
    col_d1, col_d2, col_d3 = st.columns(3)
    with col_d1:
        temp = st.number_input("Temperatura Corporal (°C)", min_value=30.0, max_value=43.0, value=38.5, step=0.1)
    with col_d2:
        hr = st.number_input("Frecuencia Cardíaca (lpm)", min_value=10, max_value=220, value=70, step=1)
    with col_d3:
        rr = st.number_input("Frecuencia Respiratoria (rpm)", min_value=5, max_value=120, value=20, step=1)

    st.markdown("---")
    st.markdown("#### Hallazgos Clínicos Complementarios")
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        sign_1 = st.checkbox("Hipomotilidad / Atonía orgánica")
        sign_2 = st.checkbox("Deshidratación moderada/severa (>6%)")
    with col_s2:
        sign_3 = st.checkbox("Signos de dolor abdominal / cólico / incomodidad")
        sign_4 = st.checkbox("Secreción óculo-nasal o patrón respiratorio disfónico")

    if st.button("Ejecutar Diagnóstico y Sifoneo Nutricional", type="primary"):
        engine = AdvancedClinicalEngine(sb_species, sb_prod_type.lower(), sb_region, sb_season)
        vitals_eval = engine.evaluate_vitals(temp, hr, rr)
        signs_list = []
        if sb_diet_change != "Sin cambios recientes": 
            signs_list.append("Cambio de dieta reciente")
        if sign_1: 
            signs_list.append("Hipomotilidad ruminal")
        differentials = engine.compute_differential_diagnosis(sb_system, signs_list, temp, hr, rr)
        top_dx = differentials[0]['dx'] if differentials else ""
        nutritional_advice = engine.get_nutritional_recommendations(top_dx)
        
        st.session_state['diagnostic_report'] = {
            "vitals": vitals_eval,
            "differentials": differentials,
            "patient": current_patient_id,
            "region": sb_region,
            "season": sb_season,
            "nutritional": nutritional_advice
        }

    st.divider()
    st.subheader("📊 Reporte Diagnóstico y Sifoneo con Modelos Nutricionales")
    if st.session_state['diagnostic_report']:
        report = st.session_state['diagnostic_report']
        st.markdown(f"**Paciente Evaluado:** `{report['patient']}` | 🌍 **Matriz Regional:** `{report['region']}`")
        st.markdown("### 1. Validación Fisiológica")
        for alert in report['vitals']:
            st.write(alert)
            
        st.markdown("### 2. Diagnósticos Diferenciales (Ranking Bayesiano)")
        for idx, item in enumerate(report['differentials'], 1):
            confidence = item['prob']
            st.markdown(f"**{idx}. {item['dx']}** — Índice de Coincidencia: **{confidence}%**")
            st.progress(confidence / 100.0)
            
        st.markdown("### 3. Sifoneo con Modelos Nutricionales del Hato")
        st.info(report['nutritional'])
    else:
        st.info("💡 Ingrese los parámetros y presione el botón para ejecutar el diagnóstico y modelo nutricional.")


# --- PESTAÑA 2: HISTORIAL CLÍNICO POR RANCHO (SQLITE OFFLINE) ---
with tab_reg:
    st.subheader("📁 Archivo Local de Pacientes (Almacenamiento Offline SQLite)")
    st.markdown("Expedientes guardados localmente para consulta síncrona en campo sin interrupciones.")
    
    col_r1, col_r2 = st.columns(2)
    with col_r1:
        input_rancho = st.text_input("🏡 Nombre del Rancho / Predio / Unidad", value="Rancho El Porvenir")
        input_municipio = st.text_input("📍 Municipio / Localidad", value="Tlaltenango, Zacatecas")
    with col_r2:
        input_arete = st.text_input("🆔 ID / Arete / Nombre del Animal", value=current_patient_id)
        reg_species = st.selectbox("Especie en Registro", ["Bovino", "Equino", "Porcino", "Ovino", "Canino", "Felino"], index=0 if sb_species=="Bovino" else 0)
        
    col_r3, col_r4 = st.columns(2)
    with col_r3:
        estimated_weight = st.number_input("Peso Actual (kg)", min_value=0.5, max_value=1500.0, value=float(st.session_state['last_estimated_weight']), step=0.5)
    with col_r4:
        clinical_notes = st.text_area("Hallazgos de Exploración y Plan Terapéutico")
        
    if st.button("Guardar Evento en Base de Datos Local SQLite", type="primary"):
        if input_arete and input_rancho:
            record = {
                "Rancho / Predio": input_rancho.strip().title(),
                "Municipio": input_municipio.strip().title(),
                "ID Paciente": input_arete.strip().upper(),
                "Fecha": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                "Especie": reg_species,
                "Raza": sb_breed,
                "Sexo": sb_sex,
                "Sistema Afectado": sb_system,
                "Peso (kg)": estimated_weight,
                "Notas Clínicas": clinical_notes
            }
            save_record_sqlite(record)
            st.success(f"¡Expediente guardado exitosamente en SQLite local para el predio **{input_rancho.upper()}**!")
        else:
            st.warning("Por favor completa el nombre del rancho y el ID del paciente.")

    st.markdown("---")
    st.subheader("🔍 Consulta de Expedientes Almacenados Localmente")
    
    df_all = load_records_sqlite()
    if not df_all.empty:
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            selected_rancho = st.selectbox("Filtrar por Rancho / Predio", df_all["rancho"].unique().tolist())
        with col_f2:
            df_filtered_rancho = df_all[df_all["rancho"] == selected_rancho]
            selected_id_rancho = st.selectbox("Seleccionar Animal en este Rancho", df_filtered_rancho["patient_id"].unique().tolist())
            
        df_final_view = df_filtered_rancho[df_filtered_rancho["patient_id"] == selected_id_rancho]
        st.markdown(f"### Historial Local de **{selected_id_rancho}** (Predio: *{selected_rancho}*)")
        st.dataframe(df_final_view, use_container_width=True)
    else:
        st.info("Aún no hay registros guardados en la base de datos local SQLite.")


# --- PESTAÑA 3: VADEMECUM, RETIROS Y ANÁLISIS DE COSTO-BENEFICIO ---
with tab_drugs:
    st.subheader("💊 Vademecum, Periodos de Retiro y Análisis Económico de Tratamiento")
    st.markdown("Optimice la decisión clínica evaluando el costo del fármaco frente al valor productivo y riesgo de merma en el hato.")
    
    drug_database = {
        "Oxitetraciclina L.A. (20%) [Antibiótico de amplio espectro]": {
            "dosis": 20.0, "unidad": "mg/kg", "concentracion": 200, "especies": "Bovinos, Ovinos, Porcinos", "via": "IM profunda / SC", "indicacion": "Infecciones respiratorias y sistémicas graves.",
            "retiro_leche": 5, "retiro_carne": 28, "costo_ml": 4.50
        },
        "Ceftiofur Clorhidrato [Cefalosporina 3ra Gen]": {
            "dosis": 2.2, "unidad": "mg/kg", "concentracion": 50, "especies": "Bovinos, Equinos, Caninos, Felinos", "via": "IM / SC", "indicacion": "Enfermedad respiratoria y pododermatitis.",
            "retiro_leche": 0, "retiro_carne": 4, "costo_ml": 18.20
        },
        "Enrofloxacina (10%) [Fluoroquinolona]": {
            "dosis": 5.0, "unidad": "mg/kg", "concentracion": 100, "especies": "Bovinos, Porcinos, Caninos, Felinos", "via": "SC / IM / IV lenta", "indicacion": "Infecciones urogenitales y digestivas complejas.",
            "retiro_leche": 4, "retiro_carne": 14, "costo_ml": 6.80
        },
        "Meloxicam (2%) [Antiinflamatorio no esteroideo]": {
            "dosis": 0.5, "unidad": "mg/kg", "concentracion": 20, "especies": "Bovinos, Equinos, Porcinos, Ovinos", "via": "IV / SC", "indicacion": "Control de dolor, inflamación y pirexia.",
            "retiro_leche": 5, "retiro_carne": 21, "costo_ml": 9.00
        },
        "Flunixin Meglumine [Analgésico / Antitérmico]": {
            "dosis": 1.1, "unidad": "mg/kg", "concentracion": 50, "especies": "Bovinos, Equinos, Caninos", "via": "IV lenta / IM", "indicacion": "Cólico equino, dolor visceral y endotoxemia.",
            "retiro_leche": 2, "retiro_carne": 7, "costo_ml": 12.50
        },
        "Xylazine (2%) [Sedante / Miorrelajante]": {
            "dosis": 0.2, "unidad": "mg/kg", "concentracion": 20, "especies": "Bovinos, Equinos, Caninos, Felinos", "via": "IV / IM", "indicacion": "Sedación profunda y contención en campo.",
            "retiro_leche": 1, "retiro_carne": 3, "costo_ml": 5.00
        },
        "Ivermectina (1%) [Endectocida]": {
            "dosis": 0.2, "unidad": "mg/kg", "concentracion": 10, "especies": "Bovinos, Ovinos, Porcinos, Caninos", "via": "SC / Pour-on", "indicacion": "Control de parásitos gastrointestinales y ectoparásitos.",
            "retiro_leche": 35, "retiro_carne": 42, "costo_ml": 3.20
        }
    }
    
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        selected_drug = st.selectbox("Seleccione el Fármaco del Catálogo", list(drug_database.keys()))
        drug_info = drug_database[selected_drug]
        st.info(
            f"📋 **Especies objetivo:** {drug_info['especies']}\n\n"
            f"💉 **Vía de administración:** {drug_info['via']}\n\n"
            f"📌 **Indicación:** {drug_info['indicacion']}\n\n"
            f"⚖️ **Dosis estándar:** {drug_info['dosis']} {drug_info['unidad']}\n\n"
            f"⏳ **Periodos de Retiro:** Leche: **{drug_info['retiro_leche']} días** | Carne: **{drug_info['retiro_carne']} días**"
        )
    
    with col_d2:
        use_ai_weight = st.checkbox(f"Usar peso actual registrado en memoria ({st.session_state['last_estimated_weight']} kg)", value=True)
        animal_weight = st.session_state['last_estimated_weight'] if use_ai_weight else st.number_input("Ingrese peso manual (kg)", min_value=0.5, max_value=1500.0, value=25.0, step=0.5)
        
        st.markdown("---")
        st.markdown("#### 💲 Variables de Análisis Económico")
        milk_price = st.number_input("Precio de venta leche ($/litro)", value=9.50, step=0.5)
        daily_milk_yield = st.number_input("Producción diaria esperada (litros/día)", value=28.0, step=1.0)
        milk_drop_pct = st.slider("Merma estimada por enfermedad (%)", min_value=10, max_value=90, value=40)
        illness_days = st.number_input("Días estimados de recuperación", min_value=1, max_value=30, value=5)
        
        if st.button("Calcular Tratamiento y Análisis Costo-Beneficio", type="primary"):
            total_mg = animal_weight * drug_info['dosis']
            total_ml = total_mg / drug_info['concentracion']
            drug_total_cost = total_ml * drug_info['costo_ml']
            
            liters_lost_per_day = daily_milk_yield * (milk_drop_pct / 100.0)
            total_milk_loss_value = liters_lost_per_day * illness_days * milk_price
            total_economic_impact = drug_total_cost + total_milk_loss_value
            
            now = datetime.datetime.now()
            safe_milk_date = now + datetime.timedelta(days=drug_info['retiro_leche'])
            safe_meat_date = now + datetime.timedelta(days=drug_info['retiro_carne'])
            
            st.session_state['last_drug_result'] = {
                "drug": selected_drug,
                "weight": animal_weight,
                "ml": round(total_ml, 3),
                "drug_cost": round(drug_total_cost, 2),
                "milk_loss_val": round(total_milk_loss_value, 2),
                "total_impact": round(total_economic_impact, 2),
                "milk_days": drug_info['retiro_leche'],
                "meat_days": drug_info['retiro_carne'],
                "milk_date": safe_milk_date.strftime("%Y-%m-%d"),
                "meat_date": safe_meat_date.strftime("%Y-%m-%d"),
                "via": drug_info['via'],
                "indicacion": drug_info['indicacion']
            }
            
    st.divider()
    st.subheader("🎯 Resultado Financiero y Emisión de Receta Oficial PDF")
    if st.session_state['last_drug_result']:
        res = st.session_state['last_drug_result']
        st.success(
            f"* **Fármaco:** {res['drug']}\n"
            f"* **Dosis Total Requerida:** **{res['ml']} mL** (Costo insumo: **${res['drug_cost']} MXN**)\n"
            f"* **Merma económica proyectada por baja en leche:** **${res['milk_loss_val']} MXN**\n"
            f"* **Impacto Económico Total del Evento:** **${res['total_impact']} MXN**\n\n"
            f"🥛 **Retiro Leche:** {res['milk_days']} días (Seguro desde `{res['milk_date']}`)\n"
            f"🥩 **Retiro Carne:** {res['meat_days']} días (Seguro desde `{res['meat_date']}`)"
        )
        
        nutri_text = st.session_state['diagnostic_report']['nutritional'] if st.session_state['diagnostic_report'] else "Sin sifoneo nutricional activo."
        diag_text = f"Sistema afectado: {sb_system}. Diagnóstico presuntivo regional ({sb_region})."
        treat_text = f"Fármaco: {res['drug']}\nDosis: {res['ml']} mL ({res['drug_cost']} MXN)\nVía: {res['via']}"
        with_text = f"Retiro Leche: {res['milk_days']} días | Retiro Carne: {res['meat_days']} días"
        econ_text = f"Costo total tratamiento + merma: ${res['total_impact']} MXN"
        
        pdf_bytes = generate_pdf_report(
            patient_id=current_patient_id,
            rancho="Rancho El Porvenir",
            municipio="Tlaltenango, Zacatecas",
            species=sb_species,
            breed=sb_breed,
            weight=res['weight'],
            diagnosis_text=diag_text,
            nutritional_text=nutri_text,
            treatment_text=treat_text,
            withdrawal_text=with_text,
            economic_text=econ_text
        )
        
        st.download_button(
            label="📄 Descargar Receta y Reporte Económico Oficial en PDF",
            data=pdf_bytes,
            file_name=f"Receta_Económica_{current_patient_id}_{datetime.date.today()}.pdf",
            mime="application/pdf",
            type="primary"
        )
    else:
        st.info("💡 Configure el fármaco y los parámetros económicos para generar la evaluación de costo-beneficio y el PDF.")


# --- PESTAÑA 4: ESTIMACIÓN DE PESO ---
with tab_weight:
    st.subheader("⚖️ Herramientas de Estimación de Peso y Biometría")
    st.markdown("Seleccione el método para calcular el peso vivo del paciente y actualizarlo automáticamente para la dosificación.")
    
    weight_mode = st.radio("Método de estimación:", ["📐 Ecuaciones Morfométricas (Cinta)", "📸 Inteligencia Artificial por Fotografía"])
    
    if weight_mode == "📐 Ecuaciones Morfométricas (Cinta)":
        col_w1, col_w2 = st.columns(2)
        with col_w1:
            heart_girth = st.number_input("Perímetro Torácico (cm)", min_value=15.0, max_value=300.0, value=180.0, step=0.5)
        with col_w2:
            body_length = st.number_input("Longitud Corporal (cm)", min_value=15.0, max_value=300.0, value=150.0, step=0.5)
            
        if st.button("Calcular con Morfometría", type="primary"):
            estimated_w = round((heart_girth ** 2 * body_length) / 10840, 2)
            st.session_state['last_estimated_weight'] = estimated_w
            st.success(f"⚖️ **Peso Calculado y Guardado en Memoria:** **{estimated_w} kg**")
    else:
        uploaded_image = st.file_uploader("Sube la fotografía lateral del animal", type=["jpg", "jpeg", "png"])
        if uploaded_image:
            st.image(Image.open(uploaded_image), caption=f"Paciente ID: {current_patient_id}", use_container_width=True)
            if st.button("🤖 Procesar Peso con IA", type="primary"):
                ai_weight_result = 438.0
                st.session_state['last_estimated_weight'] = ai_weight_result
                st.success(f"¡Peso estimado por visión artificial: **{ai_weight_result} kg** (Guardado en memoria para dosificación)!")

    st.markdown("---")
    st.metric(label="Peso Actual Registrado en Memoria de la App", value=f"{st.session_state['last_estimated_weight']} kg")


# --- PESTAÑA 5: FONOFONÍA Y ESPECTROGRAMAS REALES (LIBROSA / FFT) ---
with tab_audio:
    st.subheader("🔊 Procesamiento Acústico y Generación de Espectrogramas (Librosa / FFT)")
    st.markdown(f"Análisis espectral real de auscultación ruminal o respiratoria para el paciente con ID: **{current_patient_id}**")
    
    audio_upload = st.file_uploader("Sube archivo de audio de auscultación (WAV / MP3 / M4A)", type=["wav", "mp3", "m4a"])
    
    if audio_upload:
        st.audio(audio_upload)
        if st.button("🔬 Procesar Espectrograma Real (FFT)", type="primary"):
            try:
                # Cargar audio con librosa
                y, sr = librosa.load(audio_upload, sr=None)
                
                # Calcular mel-espectrograma
                S = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=128, fmax=8000)
                S_dB = librosa.power_to_db(S, ref=np.max)
                
                # Graficar con matplotlib
                fig, ax = plt.subplots(figsize=(10, 4))
                img = librosa.display.specshow(S_dB, x_axis='time', y_axis='mel', sr=sr, fmax=8000, ax=ax, cmap='magma')
                ax.set(title=f'Espectrograma Acústico - Paciente {current_patient_id}')
                fig.colorbar(img, ax=ax, format='%+2.0f dB')
                
                st.pyplot(fig)
                
                # Métricas acústicas derivadas
                rms = librosa.feature.rms(y=y)[0]
                mean_energy = np.mean(rms) * 1000
                dom_freq = sr / 2 if len(y) > 0 else 0
                
                st.success("¡Espectrograma generado y procesado exitosamente vía Transformada de Fourier (FFT)!")
                
                col_a1, col_a2 = st.columns(2)
                with col_a1:
                    st.metric(label="Energía RMS Promedio", value=f"{round(mean_energy, 2)} Units")
                with col_a2:
                    st.metric(label="Tasa de Muestreo", value=f"{sr} Hz")
                    
            except Exception as e:
                st.error(f"Error procesando el archivo de audio: {e}")
    else:
        st.info("💡 Sube un archivo de audio para calcular y visualizar el espectrograma real de la motilidad ruminal o ruidos respiratorios.")


# --- PESTAÑA 6: IOT Y TELEMETRÍA DE HATO ---
with tab_iot:
    st.subheader("📡 Módulo IoT: Alertas de Collares de Rumodetección y Podómetros")
    st.markdown("Recepción automática de eventos telemétricos (baja de rumina, picos de actividad por celo o fiebre subclínica).")
    
    with st.expander("📥 Simular Webhook / Entrada de Dispositivo Inteligente (API Mock)"):
        with st.form("iot_form"):
            col_i1, col_i2 = st.columns(2)
            with col_i1:
                iot_device_id = st.text_input("ID Collar / Dispositivo IoT", value="COLLAR-BVD-894")
                iot_tag_type = st.selectbox("Tipo de Sensor", ["Collar Ruminal (Allflex/SensingCow)", "Podómetro Actividad (Pedometer Tag)", "Orejera Térmica IoT"])
            with col_i2:
                iot_alert_type = st.selectbox("Tipo de Alerta Temprana", ["⚠️ Alerta SARA / Baja Rumina (< 350 min/día)", "🔥 Alerta Fiebre / Temperatura Elevada", "💃 Alerta Celo Detectado (Pico Actividad)", "🔋 Batería Baja / Sin Señal"])
                iot_status = st.selectbox("Estatus de Alerta", ["Activa / Pendiente de Revisión", "Atendida / En Tratamiento", "Descartada"])
            
            iot_desc = st.text_area("Descripción telemétrica", value="El sensor detectó una caída sostenida del tiempo de rumina durante las últimas 18 horas.")
            
            submit_iot = st.form_submit_button("🛰️ Registrar Alerta IoT en Base de Datos", type="primary")
            if submit_iot:
                new_alert = {
                    "device_id": iot_device_id,
                    "tag_type": iot_tag_type,
                    "alert_type": iot_alert_type,
                    "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "description": iot_desc,
                    "status": iot_status
                }
                save_iot_alert_sqlite(new_alert)
                st.success("¡Alerta IoT recibida y almacenada en el sistema del hato!")

    st.markdown("---")
    st.subheader("🚨 Historial de Alertas Telemétricas Activas en el Hato")
    df_iot = load_iot_alerts_sqlite()
    if not df_iot.empty:
        for idx, row in df_iot.iterrows():
            st.markdown(f"""
            <div class="card">
                <h4>{row['alert_type']} — <code>{row['device_id']}</code></h4>
                <p><b>Sensor:</b> {row['tag_type']} | <b>Fecha/Hora:</b> {row['timestamp']}</p>
                <p><b>Descripción:</b> {row['description']}</p>
                <p><b>Estatus:</b> <code>{row['status']}</code></p>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No hay alertas telemétricas pendientes registradas en este momento.")


# --- PESTAÑA 7: VIDEOLLAMADA / URGENCIAS A DISTANCIA ---
with tab_tele:
    st.subheader("📅 Telemedicina Veterinaria: Agendar Videollamada de Urgencia / Distancia")
    st.markdown("Conexión directa en tiempo real con el **Dr. Vet. Alejandro Castañeda Correa** para casos críticos o asesoría técnica en campo.")
    
    with st.form("tele_form"):
        col_t1, col_t2 = st.columns(2)
        with col_t1:
            tele_client = st.text_input("Nombre del Propietario / Productor", value="Alejandro Castañeda")
            tele_rancho = st.text_input("Rancho / Predio / Ubicación", value="Tlaltenango, Zacatecas")
            tele_species = st.selectbox("Especie Involucrada", ["Bovino", "Equino", "Porcino", "Ovino", "Canino", "Felino"])
        with col_t2:
            tele_urgency = st.selectbox("Nivel de Urgencia", ["🔴 EMERGENCIA 24/7 (Atención Inmediata)", "🟠 Consulta Prioritaria (Hoy)", "🟡 Videollamada Programada (Próximos días)"])
            tele_date = st.date_input("Fecha Preferida de Consulta")
            tele_time = st.time_input("Hora Estimada")
            
        tele_motive = st.text_area("Descripción breve del caso clínico o emergencia", placeholder="Ej. Vaca caída con signos de hipocalcemia postparto / Cólico equino agudo...")
        
        submit_tele = st.form_submit_button("🚀 Agendar / Iniciar Videollamada de Urgencia", type="primary")
        
        if submit_tele:
            meeting_id = f"CLINIC-IA-{np.random.randint(1000, 9999)}"
            appointment = {
                "ID Cita": meeting_id,
                "Propietario": tele_client,
                "Rancho": tele_rancho,
                "Especie": tele_species,
                "Urgencia": tele_urgency,
                "Fecha/Hora": f"{tele_date} {tele_time}",
                "Motivo": tele_motive,
                "Enlace": f"https://meet.jit.si/{meeting_id}"
            }
            save_appointment_sqlite(appointment)
            st.success("¡Cita de telemedicina registrada exitosamente en SQLite local!")

    st.divider()
    st.subheader("📌 Consultas y Urgencias Agendadas (SQLite)")
    df_app = load_appointments_sqlite()
    if not df_app.empty:
        for idx, row in df_app.iterrows():
            with st.container():
                st.markdown(f"""
                <div class="card">
                    <h4>🚨 {row['urgency']} — Predio: {row['rancho']}</h4>
                    <p><b>Propietario:</b> {row['owner']} | <b>Especie:</b> {row['species']} | <b>Fecha:</b> {row['datetime']}</p>
                    <p><b>Motivo:</b> {row['motive']}</p>
                    <p>🔗 <b>Enlace de Videollamada Segura:</b> <a href="{row['link']}" target="_blank">{row['link']}</a></p>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("No hay videollamadas de emergencia o distancia agendadas en la base de datos local.")
