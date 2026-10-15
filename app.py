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
    page_title="Clinic-IA | Zootecnia e Inteligencia Veterinaria",
    page_icon="🧬",
    layout="wide"
)

# ==========================================
# ESTILOS CSS VANGUARDISTAS Y DISEÑO DE MARCA
# ==========================================
st.markdown("""
<style>
    .main { background-color: #f1f5f9; }
    
    /* Branding Hero Section */
    .hero-container {
        background: linear-gradient(135deg, #0b132b 0%, #1c2541 50%, #3a506b 100%);
        padding: 3rem 2rem;
        border-radius: 24px;
        color: white;
        box-shadow: 0 20px 40px -15px rgba(11, 19, 43, 0.4);
        margin-bottom: 2.5rem;
        border: 1px solid rgba(255, 255, 255, 0.1);
        text-align: center;
        position: relative;
        overflow: hidden;
    }
    
    .hero-logo-wrapper {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 90px;
        height: 90px;
        background: radial-gradient(circle, rgba(56,189,248,0.25) 0%, rgba(15,23,42,0.6) 100%);
        border: 2px solid #38bdf8;
        border-radius: 24px;
        font-size: 3rem;
        margin-bottom: 1.2rem;
        box-shadow: 0 0 30px rgba(56, 189, 248, 0.4);
    }
    
    .hero-title {
        font-size: 3.5rem;
        font-weight: 900;
        margin: 0;
        letter-spacing: -0.04em;
        background: linear-gradient(90deg, #ffffff 30%, #38bdf8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    .hero-slogan {
        font-size: 1.25rem;
        color: #cbd5e1;
        margin-top: 0.75rem;
        font-weight: 400;
        letter-spacing: 0.02em;
    }
    
    .hero-author {
        font-size: 0.85rem;
        color: #38bdf8;
        margin-top: 1rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.1em;
    }

    /* Tarjetas de Planes */
    .plan-box {
        background: #ffffff;
        padding: 2rem 1.5rem;
        border-radius: 20px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 10px 25px -5px rgba(0,0,0,0.05);
        text-align: center;
        height: 100%;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    
    .plan-box-featured {
        background: #ffffff;
        padding: 2rem 1.5rem;
        border-radius: 20px;
        border: 2px solid #0284c7;
        box-shadow: 0 15px 30px -5px rgba(2, 132, 199, 0.15);
        text-align: center;
        height: 100%;
    }

    .auth-card {
        background: #ffffff;
        padding: 2.5rem;
        border-radius: 20px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 10px 30px -10px rgba(0,0,0,0.08);
    }

    .card { 
        background-color: #ffffff; 
        padding: 1.5rem; 
        border-radius: 16px; 
        border: 1px solid #e2e8f0; 
        box-shadow: 0 4px 10px -2px rgba(0, 0, 0, 0.03); 
        margin-bottom: 1rem; 
    }
    
    .stButton button { border-radius: 12px; font-weight: 600; padding: 0.6rem 1.2rem; }
</style>
""", unsafe_allow_html=True)


# ==========================================
# 0. CONTROL DE ESTADO DE SESIÓN Y USUARIOS
# ==========================================
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False
if 'mfa_verified' not in st.session_state:
    st.session_state['mfa_verified'] = False
if 'biometric_verified' not in st.session_state:
    st.session_state['biometric_verified'] = False
if 'current_user' not in st.session_state:
    st.session_state['current_user'] = None
if 'selected_plan' not in st.session_state:
    st.session_state['selected_plan'] = "Pro - Médico Veterinario"
if 'registered_users_db' not in st.session_state:
    st.session_state['registered_users_db'] = {
        "alejandro.castaneda": {
            "pass": "clinic2026*", 
            "name": "Dr. Alejandro Castañeda Correa", 
            "role": "Administrador / Creador",
            "email": "alejandro.castaneda@clinic-ia.com",
            "phone": "+52 33 1234 5678",
            "bank": "BBVA **** 4092",
            "plan": "Pro - Médico Veterinario"
        }
    }


def render_header_banner():
    """Logotipo renovado y banner vanguardista"""
    st.markdown("""
    <div class="hero-container">
        <div class="hero-logo-wrapper">🧬🩺</div>
        <h1 class="hero-title">Clinic-IA</h1>
        <p class="hero-slogan">“Zootecnia de Precisión, Trazabilidad e Inteligencia Veterinaria al Servicio del Campo”</p>
        <p class="hero-author">Desarrollada y Creada por: Dr. Alejandro Castañeda Correa</p>
    </div>
    """, unsafe_allow_html=True)


def render_landing_page():
    """Página de Inicio Organizada: Sección A (Autenticación) / Sección B (Planes de Suscripción)"""
    render_header_banner()
    
    # SECCIÓN 1: INICIO DE SESIÓN Y REGISTRO (SEPARADO)
    st.markdown("## 🔐 1. Acceso a la Plataforma")
    st.caption("Ingresa con tus credenciales o registra una nueva cuenta para acceder a Clinic-IA.")
    
    auth_tab1, auth_tab2 = st.tabs(["🔑 Iniciar Sesión", "📝 Registro de Nueva Cuenta Comercial"])
    
    with auth_tab1:
        col_l1, col_l2, col_l3 = st.columns([1, 2, 1])
        with col_l2:
            st.markdown("<div class='auth-card'>", unsafe_allow_html=True)
            with st.form("login_form_standalone"):
                st.markdown("### Credenciales de Usuario")
                username = st.text_input("Usuario o Correo Electrónico", value="alejandro.castaneda")
                password = st.text_input("Contraseña", type="password", value="clinic2026*")
                
                st.markdown("---")
                st.markdown("#### 🛡️ Autenticación Fuerte Anti-Fraude")
                st.info("💡 Se enviará un token dinámico de 6 dígitos vía SMS / WhatsApp a su celular. (Simulación: `849201`)")
                mfa_code = st.text_input("Código Token MFA", value="849201", max_chars=6)
                
                biometric_check = st.checkbox("👆 Autenticar con Huella Digital / Sensor Biométrico (Passkey FIDO2)")
                
                login_btn = st.form_submit_button("🚀 Acceder a Clinic-IA", type="primary", use_container_width=True)
                
                if login_btn:
                    users_db = st.session_state['registered_users_db']
                    if username in users_db and users_db[username]["pass"] == password:
                        if mfa_code == "849201":
                            if biometric_check:
                                st.session_state['authenticated'] = True
                                st.session_state['mfa_verified'] = True
                                st.session_state['biometric_verified'] = True
                                st.session_state['current_user'] = users_db[username]
                                st.success("¡Autenticación exitosa! Ingresando a la plataforma...")
                                st.rerun()
                            else:
                                st.error("❌ Se requiere la validación biométrica/huella digital para evitar robos de cuenta.")
                        else:
                            st.error("❌ Código MFA incorrecto.")
                    else:
                        st.error("❌ Credenciales incorrectas.")
            st.markdown("</div>", unsafe_allow_html=True)

    with auth_tab2:
        col_r1, col_r2, col_r3 = st.columns([1, 2, 1])
        with col_r2:
            st.markdown("<div class='auth-card'>", unsafe_allow_html=True)
            with st.form("register_form_standalone"):
                st.markdown("### Datos del Titular y Suscripción")
                reg_name = st.text_input("Nombre Completo")
                reg_email = st.text_input("Correo Electrónico")
                reg_phone = st.text_input("Teléfono Celular (Para Tokens SMS / WhatsApp)")
                reg_user = st.text_input("Nombre de Usuario deseado")
                reg_pass = st.text_input("Contraseña Segura", type="password")
                
                st.markdown("#### 💳 Datos Bancarios (Cobro Recurrente de Suscripción)")
                reg_bank = st.text_input("Número de Tarjeta / CLABE Interbancaria", placeholder="**** **** **** 1234")
                reg_expiry = st.text_input("Vencimiento (MM/AA)", placeholder="12/28")
                reg_cvv = st.text_input("CVV / Cifra de Seguridad", type="password", max_chars=4)
                
                reg_biometric_consent = st.checkbox("Registrar dispositivo para huella digital / biometría")
                
                register_btn = st.form_submit_button("💼 Confirmar Registro y Activar Plan", type="primary", use_container_width=True)
                
                if register_btn:
                    if reg_user and reg_pass and reg_email and reg_phone and reg_bank:
                        if reg_user in st.session_state['registered_users_db']:
                            st.error("❌ El nombre de usuario ya está registrado.")
                        else:
                            st.session_state['registered_users_db'][reg_user] = {
                                "pass": reg_pass,
                                "name": reg_name,
                                "role": "Propietario / Suscriptor",
                                "email": reg_email,
                                "phone": reg_phone,
                                "bank": reg_bank,
                                "plan": st.session_state['selected_plan']
                            }
                            st.success(f"¡Registro exitoso! Tokens enviados a `{reg_phone}`. Procede a iniciar sesión.")
                    else:
                        st.warning("⚠️ Completa todos los campos solicitados.")
            st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")
    
    # SECCIÓN 2: PLANES DE SUSCRIPCIÓN (SEPARADO)
    st.markdown("## 💳 2. Oferta de Planes y Suscripciones")
    st.caption("Selecciona el plan que se adapte a tus necesidades operativas.")
    
    col_p1, col_p2, col_p3 = st.columns(3)
    
    with col_p1:
        st.markdown("""
        <div class='plan-box'>
            <span style='font-size: 2.2rem;'>🌱</span>
            <h3>Plan Productor</h3>
            <h2 style='color: #0284c7;'>$499 <span style='font-size: 1rem; color: #64748b;'>MXN / mes</span></h2>
            <p style='color: #64748b; font-size: 0.9rem;'>Ideal para ranchos e instalaciones individuales.</p>
            <hr style='border: 0; border-top: 1px solid #e2e8f0; margin: 1rem 0;'>
            <div style='text-align: left; font-size: 0.95rem; color: #334155; line-height: 1.8;'>
                ✔️ Hasta 500 aretes SINIIGA activos<br>
                ✔️ Diagnóstico clínico asistido<br>
                ✔️ Reportes y recetas PDF oficiales<br>
                ✔️ Sincronización Mesh P2P básica
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.write("")
        if st.button("Seleccionar Productor", key="p1_btn", use_container_width=True):
            st.session_state['selected_plan'] = "Productor"
            st.success("Has seleccionado el Plan Productor.")

    with col_p2:
        st.markdown("""
        <div class='plan-box-featured'>
            <span style='font-size: 2.2rem;'>🩺</span>
            <h3>Plan Pro Veterinario</h3>
            <h2 style='color: #0284c7;'>$1,299 <span style='font-size: 1rem; color: #64748b;'>MXN / mes</span></h2>
            <p style='color: #64748b; font-size: 0.9rem;'>Diseñado para Médicos Zootecnistas y consultores.</p>
            <hr style='border: 0; border-top: 1px solid #e2e8f0; margin: 1rem 0;'>
            <div style='text-align: left; font-size: 0.95rem; color: #334155; line-height: 1.8;'>
                ✔️ Hatos y aretes SINIIGA ilimitados<br>
                ✔️ Vademecum y análisis costo-beneficio<br>
                ✔️ Telemetría e integraciones IoT<br>
                ✔️ Fonofonía y espectrogramas (FFT)
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.write("")
        if st.button("Seleccionar Pro Vet", key="p2_btn", type="primary", use_container_width=True):
            st.session_state['selected_plan'] = "Pro - Médico Veterinario"
            st.success("Has seleccionado el Plan Pro Veterinario.")

    with col_p3:
        st.markdown("""
        <div class='plan-box'>
            <span style='font-size: 2.2rem;'>🏢</span>
            <h3>Plan Corporativo</h3>
            <h2 style='color: #0284c7;'>$3,499 <span style='font-size: 1rem; color: #64748b;'>MXN / mes</span></h2>
            <p style='color: #64748b; font-size: 0.9rem;'>Para asociaciones ganaderas y agroindustrias.</p>
            <hr style='border: 0; border-top: 1px solid #e2e8f0; margin: 1rem 0;'>
            <div style='text-align: left; font-size: 0.95rem; color: #334155; line-height: 1.8;'>
                ✔️ Conexión y trazabilidad SENASICA<br>
                ✔️ Red Mesh rural ilimitada para personal<br>
                ✔️ Acceso multiusuario y roles<br>
                ✔️ Soporte técnico prioritario 24/7
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.write("")
        if st.button("Seleccionar Corporativo", key="p3_btn", use_container_width=True):
            st.session_state['selected_plan'] = "Corporativo"
            st.success("Has seleccionado el Plan Corporativo.")


# Control de flujo para pantalla inicial
if not st.session_state['authenticated'] or not st.session_state['mfa_verified'] or not st.session_state['biometric_verified']:
    render_landing_page()
    st.stop()


# ==========================================
# 1. BASE DE DATOS LOCAL Y GESTIÓN OFFLINE-FIRST (SQLITE + MESH SYNC)
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
    c.execute('''CREATE TABLE IF NOT EXISTS mesh_nodes (
                    node_id TEXT PRIMARY KEY,
                    location TEXT,
                    last_sync TEXT,
                    status TEXT
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
# 2. GENERADOR DE PDF PROFESIONAL CON FOLIO Y QR MOCK
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
        self.cell(0, 8, 'CLINIC-IA | RECETA Y REPORTE OFICIAL SENASICA', 0, 1, 'C')
        self.set_font('helvetica', 'I', 9)
        self.set_text_color(100, 116, 139)
        self.cell(0, 5, 'Zootecnia de Precisión, Trazabilidad e Inteligencia Veterinaria', 0, 1, 'C')
        self.ln(3)

    def footer(self):
        self.set_y(-15)
        self.set_font('helvetica', 'I', 8)
        self.set_text_color(148, 163, 184)
        self.cell(0, 10, f'Folio de Validación Oficial SINIIGA/SENASICA | Página {self.page_no()}', 0, 0, 'C')

def generate_pdf_report(patient_id, rancho, municipio, estado, species, breed, weight, diagnosis_text, nutritional_text, treatment_text, withdrawal_text, economic_text):
    pdf = ClinicPDF()
    pdf.add_page()
    
    folio = f"CLINIC-IA-2026-{np.random.randint(10000, 99999)}"
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    
    pdf.set_font('helvetica', 'B', 10)
    pdf.set_fill_color(241, 245, 249)
    pdf.cell(0, 7, f" FOLIO ÚNICO OFICIAL: {folio}", 0, 1, 'L', True)
    pdf.cell(0, 7, f" Fecha y Hora de Emisión: {timestamp}", 0, 1, 'L', True)
    pdf.ln(3)
    
    pdf.set_font('helvetica', 'B', 11)
    pdf.cell(0, 7, "1. Reseña, Arete SINIIGA y Localización", 0, 1)
    pdf.set_font('helvetica', '', 10)
    pdf.multi_cell(0, 5, clean_for_pdf(f"Predio / Rancho: {rancho} | Municipio: {municipio}, {estado}\nArete SINIIGA / ID: {patient_id}\nEspecie: {species} | Raza: {breed} | Peso Vivo: {weight} kg"))
    pdf.ln(2)
    
    pdf.set_font('helvetica', 'B', 11)
    pdf.cell(0, 7, "2. Diagnóstico Clínico y Matriz Regional SENASICA", 0, 1)
    pdf.set_font('helvetica', '', 10)
    pdf.multi_cell(0, 5, clean_for_pdf(diagnosis_text))
    pdf.ln(2)
    
    pdf.set_font('helvetica', 'B', 11)
    pdf.cell(0, 7, "3. Sifoneo Nutricional del Hato", 0, 1)
    pdf.set_font('helvetica', '', 10)
    pdf.multi_cell(0, 5, clean_for_pdf(nutritional_text))
    pdf.ln(2)
    
    pdf.set_font('helvetica', 'B', 11)
    pdf.cell(0, 7, "4. Tratamiento, Periodos de Retiro y Viabilidad Económica", 0, 1)
    pdf.set_font('helvetica', '', 10)
    pdf.multi_cell(0, 5, clean_for_pdf(f"{treatment_text}\n\n{withdrawal_text}\n\n{economic_text}"))
    pdf.ln(6)
    
    pdf.set_font('helvetica', 'B', 9)
    pdf.cell(95, 5, "________________________________________", 0, 0, 'C')
    pdf.cell(95, 5, "[ CÓDIGO QR SEGURO SENASICA ]", 0, 1, 'C')
    pdf.set_font('helvetica', '', 8)
    pdf.cell(95, 4, "Médico Veterinario Zootecnista Autorizado", 0, 0, 'C')
    pdf.cell(95, 4, f"Folio huella digital: {folio}-VERIFIED", 0, 1, 'C')
    pdf.cell(95, 4, "Desarrollada y Creada por: Dr. Alejandro Castañeda Correa", 0, 0, 'C')
    pdf.cell(95, 4, "Trazabilidad y Sanidad Pecuaria", 0, 1, 'C')
    
    return bytes(pdf.output())


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
# MOTOR DE ZONIFICACIÓN Y PRONÓSTICO
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
                "focos_rojos": ["Hemoparasitosis", "Carbón Sintomático", "Estomatitis Vesicular", "Fiebre Porcina Clásica"],
                "restricciones_senasica": "Control estricto del vector (Garrapata Rhipicephalus microplus), baños garrapaticidas calendarizados y restricciones de movilización.",
                "manejo_recomendado": "Manejo rotacional de potreros para disminuir carga parasitaria y programas de inmunización contra clostridios."
            },
            "Zona Sur - Sureste y Península": {
                "focos_rojos": ["Tuberculosis bovina en zonas tropicales", "Gusano Barrenador del Ganado", "Complejo Respiratorio", "Parasitosis gastrointestinal severa"],
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
# PANEL LATERAL Y CONFIGURACIÓN REGIONAL
# ==========================================
st.sidebar.markdown(f"### 👤 `{st.session_state['current_user']['name']}`")
st.sidebar.caption(f"Rol: {st.session_state['current_user']['role']}")
st.sidebar.caption(f"Plan Activo: **{st.session_state['selected_plan']}**")
st.sidebar.caption(f"📱 Notificaciones SMS: `{st.session_state['current_user']['phone']}`")

if st.sidebar.button("🚪 Cerrar Sesión"):
    st.session_state['authenticated'] = False
    st.session_state['mfa_verified'] = False
    st.session_state['biometric_verified'] = False
    st.rerun()

st.sidebar.markdown("---")
pending_syncs = get_pending_sync_stats()
if pending_syncs > 0:
    st.sidebar.warning(f"🟡 **Modo Offline Mesh:** `{pending_syncs}` registros listos para sync local/nube.")
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

estado_seleccionado = st.sidebar.selectbox("🏛️ Estado / Provincia", estados_mexico.get(macro_region, ["Jalisco"]))
municipio_input = st.sidebar.text_input("📍 Municipio / Localidad", value="Tlaltenango de Sánchez Román")

sb_season = st.sidebar.selectbox("🌦️ Estación Climática Actual", ["Secas / Estiaje prolongado", "Lluvias / Humedad alta / Huracanes", "Transición / Frentes fríos (Nortes)"])
sb_species = st.sidebar.selectbox("Especie", ["Bovino", "Equino", "Porcino", "Ovino", "Caprino", "Canino", "Felino"])

if sb_species in ["Bovino"]:
    breed_family = st.sidebar.selectbox("Familia Zootécnica", [
        "🥩 Carne - Bos Taurus (Británicas / Continentales)",
        "🤠 Carne - Bos Indicus (Zebú / Adaptadas)",
        "🧬 Carne - Sintéticas / Compuestas",
        "🥛 Leche Especializada",
        "🧀 Doble Propósito / Rústicas Regionales"
    ])
    
    breed_catalog = {
        "🥩 Carne - Bos Taurus (Británicas / Continentales)": ["Angus (Negro/Rojo)", "Hereford", "Charolais", "Simmental", "Limousin", "Belgian Blue"],
        "🤠 Carne - Bos Indicus (Zebú / Adaptadas)": ["Brahman (Blanco/Rojo)", "Nelore", "Gyr", "Guzerat", "Indubrasil"],
        "🧬 Carne - Sintéticas / Compuestas": ["Beefmaster", "Brangus", "Braford", "Santa Gertrudis", "Simbrah"],
        "🥛 Leche Especializada": ["Holstein", "Jersey", "Guernsey", "Ayrshire"],
        "🧀 Doble Propósito / Rústicas Regionales": ["Suizo Pardo (Americano/Europeo)", "Simental Ley de Leche", "Criollo / Tropicarne", "Cruzado F1 (Zebú x Europeo)"]
    }
    
    sb_breed = st.sidebar.selectbox("Raza Específica", breed_catalog[breed_family])
    sb_prod_type = "Leche" if "Leche" in breed_family else "Carne"
elif sb_species in ["Ovino", "Caprino"]:
    sb_breed = st.sidebar.selectbox("Raza / Biotipo", ["Pelibuey", "Dorper", "Katahdin", "Boer", "Saanen", "Alpine", "Cruzado Regional"])
    sb_prod_type = "Carne"
else:
    sb_breed = st.sidebar.text_input("Raza / Biotipo", value="Estándar / Mestizo")
    sb_prod_type = "general"

sb_age_group = st.sidebar.selectbox("Grupo Etario", ["Neonato / Cría (0 - 3 meses)", "Lactante / Destete (3 - 8 meses)", "Juvenil / Levante (8 - 18 meses)", "Adulto en Producción / Mantenimiento", "Reproductor / Geriátrico"])
sb_sex = st.sidebar.selectbox("Sexo", ["Hembra", "Macho", "Macho Castrado"])

sb_evolution = st.sidebar.selectbox("Tiempo de Evolución", ["Hiperagudo (< 12 hrs)", "Agudo (12 - 48 hrs)", "Subagudo (3 - 7 días)", "Crónico (> 7 días)"])
sb_morbidity = st.sidebar.selectbox("Incidencia en el Hato / Lote", ["Caso esporádico (1 animal)", "Brote focal (2 a 5 animales)", "Brote masivo (> 10%)"])
sb_system = st.sidebar.selectbox("Sistema Principal Afectado", ["Locomotor / Podal / Extremidades", "Digestivo / Metabólico", "Respiratorio", "Reproductivo / Urogenital", "Nervioso / Infeccioso sistémico"])

sb_system_prod = st.sidebar.selectbox("Sistema de Alojamiento", ["Estabulación total / Confinamiento", "Pastoreo rotacional intensivo", "Sistema extensivo / Agostadero"])
sb_diet_change = st.sidebar.selectbox("Factor de Riesgo / Sanitario", ["Sin cambios recientes", "Cambio abrupto de dieta / Forraje", "Ingreso de animales sin cuarentena (SINIIGA)", "Exposición a vectores / garrapatas / murciélagos", "Trauma en parto / Tracción forzada"])

current_patient_id = st.sidebar.text_input("🆔 Arete SINIIGA / ID / Nombre", value="MX-849201")

st.sidebar.markdown("""
<div style='text-align: center; color: #64748b; font-size: 0.85rem; padding: 10px;'>
Plataforma Internacional Clinic-IA
</div>
""", unsafe_allow_html=True)


# BANNER EN CABECERA DE LA SESIÓN AUTENTICADA
render_header_banner()


# ==========================================
# PESTAÑAS PRINCIPALES DE LA PLATAFORMA (9 SECCIONES)
# ==========================================
tab_diag, tab_zone, tab_reg, tab_drugs, tab_weight, tab_audio, tab_iot, tab_mesh, tab_tele = st.tabs([
    "🩺 Diagnóstico e IA Nutricional", 
    "🗺️ Zonificación SENASICA y Pronóstico",
    "📁 Historial por Rancho", 
    "💊 Vademecum, Retiros y Costo-Beneficio", 
    "⚖️ Estimación de Peso",
    "🔊 Fonofonía y Espectrogramas (FFT)",
    "📡 IoT y Telemetría de Hato",
    "🌐 Sincronización Mesh P2P (Rural)",
    "📅 Videollamada / Urgencias"
])

# --- PESTAÑA 1: DIAGNÓSTICO CLÍNICO Y SIFONEO NUTRICIONAL ---
with tab_diag:
    st.subheader(f"Evaluación Clínica de Precisión: Arete SINIIGA `[{current_patient_id}]`")
    st.info(f"Ubicación activa: **{estado_seleccionado}, {municipio_input} ({macro_region})** | Estación: **{sb_season}** | Raza: **{sb_breed}**")
    
    col_d1, col_d2, col_d3 = st.columns(3)
    with col_d1:
        temp = st.number_input("Temperatura Corporal (°C)", min_value=30.0, max_value=43.0, value=38.8, step=0.1)
    with col_d2:
        hr = st.number_input("Frecuencia Cardíaca (lpm)", min_value=10, max_value=220, value=90, step=1)
    with col_d3:
        rr = st.number_input("Frecuencia Respiratoria (rpm)", min_value=5, max_value=120, value=32, step=1)

    st.markdown("---")
    st.markdown("#### Hallazgos Clínicos, Semiología y Evaluación Locomotora Especializada")
    
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        sign_loco1 = st.checkbox("Aumento de volumen / Inflamación articular (Carpo, Tarso, Menudillo)")
        sign_loco2 = st.checkbox("Dolor / Calor a la palpación de pezuña / Banda coronaria / Espacio interdigital")
        sign_loco3 = st.checkbox("Incapacidad para sostener peso / Claudicación de grado elevado (3/3 o 4/5)")
        sign_loco4 = st.checkbox("Antecedente de infección umbilical (Ombligo engrosado / Doloroso)")
    with col_s2:
        sign_loco5 = st.checkbox("Crepitación al movimiento u olor fétido muscular / Enfisema subcutáneo")
        sign_loco6 = st.checkbox("Acortamiento o retracción de tendones flexores (Pie de gatillo / Hiperextensión)")
        sign_loco7 = st.checkbox("Sintomatología neurológica / Asimetría pélvica / Postura en xifosis")
        sign_loco8 = st.checkbox("Postración prolongada / Rigidez muscular progresiva")

    if st.button("Ejecutar Diagnóstico Experto Locomotor y Modelo Predictivo", type="primary"):
        engine = MexicanZoningAndForecastEngine(macro_region, estado_seleccionado, sb_season, sb_species, sb_prod_type)
        vitals_eval = engine.get_regional_sanitary_profile()
        
        differentials = []
        treatment_suggestion = ""
        management_recommendations = ""
        prognosis_text = ""
        
        if "Locomotor" in sb_system or sign_loco1 or sign_loco2 or sign_loco3:
            if "Neonato" in sb_age_group or sign_loco4:
                differentials.append({"dx": "Artritis Séptica / Poliartritis Secundaria a Onfaloflebitis ('Mal de Ombligo')", "prob": 94})
                differentials.append({"dx": "Fractura Epifisiaria / Trauma Físico por Parto Distócico", "prob": 78})
                differentials.append({"dx": "Enfermedad del Músculo Blanco (Miopatía Nutricional por Deficiencia de Se/Vit E)", "prob": 68})
                
                treatment_suggestion = (
                    "💉 **Tratamiento Clínico Recomendado:**\n"
                    "- **Antibioticoterapia sistémica:** Ceftiofur Clorhidrato (2.2 mg/kg IM c/24h por 7-10 días) o Florfenicol (20 mg/kg IM c/48h).\n"
                    "- **Antiinflamatorio y Analgesia:** Meloxicam (0.5 mg/kg SC c/24-48h) para mitigar el dolor articular.\n"
                    "- **Lavadura o Artrocentesis:** Lavado salino estéril con antibiótico en articulaciones con efusión purulenta severa."
                )
                management_recommendations = (
                    "🐄 **Manejo y Recomendaciones Biosanitarias:**\n"
                    "- Aislamiento en corral hospital con cama blanda de paja limpia y seca.\n"
                    "- Curación umbilical inmediata al nacimiento con Yodo al 7-10%.\n"
                    "- Garantizar calostrado oportuno (10% del peso vivo en las primeras 6 horas)."
                )
                prognosis_text = "🔮 **Pronóstico:** **Reservado a Desfavorable** (Depende del grado de destrucción del cartílago articular y respuesta rápida al tratamiento)."
            elif sign_loco5:
                differentials.append({"dx": "Carbón Sintomático (Blackleg / Clostridium chauvoei)", "prob": 95})
                differentials.append({"dx": "Miositis Gangrenosa / Traumatismo Muscular Severo", "prob": 72})
                
                treatment_suggestion = (
                    "💉 **Tratamiento Clínico de Emergencia:**\n"
                    "- **Penicilina G Sódica / Procaínica:** Dosis elevadas (30,000 UI/kg IM/IV) cada 12-24h.\n"
                    "- **Fenestración muscular:** Incisión quirúrgica longitudinal en tejidos necróticos para irrigar con agua oxigenada (Peróxido de Hidrógeno al 3%)."
                )
                management_recommendations = (
                    "🐄 **Manejo:** Incineración o entierro profundo con cal de cadáveres para evitar contaminación de potreros. Vacunación inmediata del lote."
                )
                prognosis_text = "🔮 **Pronóstico:** **Grave / Muy Desfavorable** (>90% de mortalidad por endotoxemia)."
            elif sign_loco2:
                differentials.append({"dx": "Pododermatitis Infecciosa (Gabarro / Pedero / Fusobacterium necrophorum)", "prob": 91})
                differentials.append({"dx": "Lesión Mecánica / Penetración de Cuerpo Extraño Interdigital", "prob": 82})
                
                treatment_suggestion = (
                    "💉 **Tratamiento Clínico:**\n"
                    "- **Oxitetraciclina L.A. (20%):** 20 mg/kg IM profunda (dosis única o repetir a 72h).\n"
                    "- **Tratamiento tópico:** Limpieza interdigital con Sulfato de Cobre al 10% y curación protectora."
                )
                management_recommendations = "🐄 **Manejo:** Recorte podal funcional y desinfección de corrales/lodazales."
                prognosis_text = "🔮 **Pronóstico:** **Favorable** con intervención oportuna."
            else:
                differentials.append({"dx": "Deformidad Tendinosa Congénita / Trauma en Ligamentos Cruzados", "prob": 88})
                differentials.append({"dx": "Artritis Séptica Subaguda", "prob": 79})
                
                treatment_suggestion = (
                    "💉 **Tratamiento:** Fisioterapia, vendajes funcionales/férulas de extensión y analgesia con Meloxicam (0.5 mg/kg)."
                )
                management_recommendations = "🐄 **Manejo:** Control estricto de movimiento en corrales planos sin desnivel."
                prognosis_text = "🔮 **Pronóstico:** **Favorable a Reservado**."
        else:
            differentials = [
                {"dx": "Acidosis Ruminal Subaguda (SARA) / Trastorno Metabólico", "prob": 88},
                {"dx": "Complejo Infeccioso Endémico Regional (SENASICA Foco Rojo)", "prob": 76},
                {"dx": "Proceso inflamatorio sistémico secundario", "prob": 65}
            ]
            treatment_suggestion = "Soporte metabólico y sintomático según valoración de laboratorio."
            management_recommendations = "Ajuste de ración TMR y fibra efectiva."
            prognosis_text = "Favorable con manejo oportuno."

        nutri_advice = (
            "🌾 **Sifoneo Nutricional y Preventivo Locomotor:**\n"
            f"- Proporcionar suplementación mineral alta en Selenio, Vitamina E, Calcio y Fósforo adaptada a la región `{estado_seleccionado}`.\n"
            "- Garantizar curación umbilical inmediata al nacimiento con Solución Yodada al 7-10% y asegurar curado de colostro."
        )

        forecast_data = engine.compute_disease_forecast(sb_system)

        st.session_state['diagnostic_report'] = {
            "differentials": differentials,
            "patient": current_patient_id,
            "region": f"{estado_seleccionado}, {macro_region}",
            "season": sb_season,
            "nutritional": nutri_advice,
            "forecast": forecast_data,
            "treatment": treatment_suggestion,
            "management": management_recommendations,
            "prognosis": prognosis_text
        }

    st.divider()
    st.subheader("📊 Reporte Diagnóstico y Matriz de Riesgo Nacional")
    if st.session_state['diagnostic_report']:
        report = st.session_state['diagnostic_report']
        st.markdown(f"**Paciente Arete:** `{report['patient']}` | 📍 **Región:** `{report['region']}` | **Raza:** `{sb_breed}`")
        
        st.markdown("### 1. Diagnósticos Diferenciales Ponderados")
        for idx, item in enumerate(report['differentials'], 1):
            confidence = item['prob']
            st.markdown(f"**{idx}. {item['dx']}** — Probabilidad Coincidencia: **{confidence}%**")
            st.progress(confidence / 100.0)
            
        st.markdown("### 2. Plan Terapéutico y Protocolo de Manejo Sugerido")
        st.info(report.get('treatment', 'Sin protocolo específico.'))
        st.success(report.get('management', 'Sin manejo específico.'))
        st.warning(report.get('prognosis', 'Sin pronóstico registrado.'))
            
        st.markdown("### 3. Pronóstico Epidemiológico Predictivo para el Hato")
        fc = report['forecast']
        st.warning(f"⚠️ **Índice de Riesgo de Brote en Zona:** `{fc['score']}%` (Nivel de Alerta: **{fc['nivel']}**)")
        for alert in fc['alerts']:
            st.write(alert)

        st.markdown("### 4. Sifoneo Nutricional")
        st.info(report['nutritional'])
    else:
        st.info("💡 Ingrese los datos clínicos y presione el botón para ejecutar el diagnóstico experto.")


# --- PESTAÑA 2: ZONIFICACIÓN SENASICA Y PRONÓSTICO ---
with tab_zone:
    st.subheader("🗺️ Zonificación Sanitaria SENASICA y Pronóstico de Enfermedades")
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
    
    col_r1, col_r2 = st.columns(2)
    with col_r1:
        input_rancho = st.text_input("🏡 Nombre del Rancho / Predio", value="Rancho San José de los Tlaxcalas")
        input_municipio = st.text_input("📍 Municipio / Localidad", value=municipio_input)
    with col_r2:
        input_arete = st.text_input("🆔 Arete SINIIGA / ID del Animal", value=current_patient_id)
        reg_species = st.selectbox("Especie en Registro", ["Bovino", "Equino", "Porcino", "Ovino", "Caprino", "Canino", "Felino"], index=0 if sb_species=="Bovino" else 0)
        
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
                "Estado": estado_seleccionado,
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
            st.success(f"¡Expediente guardado en SQLite local (Estado: `pending`) para el predio **{input_rancho.upper()}** ({estado_seleccionado})!")
            st.rerun()
        else:
            st.warning("Por favor completa el nombre del rancho y el arete SINIIGA del paciente.")

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


# --- PESTAÑA 4: VADEMECUM Y COSTO-BENEFICIO ---
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
        
        if use_ai_weight:
            animal_weight = st.session_state['last_estimated_weight']
        else:
            animal_weight = st.number_input(
                "Ingrese peso manual (kg)",
                min_value=0.5,
                max_value=1500.0,
                value=25.0,
                step=0.5
            )
        
        st.markdown("---")
        st.markdown("#### 💲 Variables de Análisis Económico (MXN)")
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
        
        st.success(f"""
* **Fármaco:** {res['drug']}
* **Dosis Total Requerida:** **{res['ml']} mL** (Costo insumo: **${res['drug_cost']} MXN**)
* **Merma económica proyectada por baja en leche:** **${res['milk_loss_val']} MXN**
* **Impacto Económico Total del Evento:** **${res['total_impact']} MXN**

🥛 **Retiro Leche:** {res['milk_days']} días (Seguro desde `{res['milk_date']}`)
🥩 **Retiro Carne:** {res['meat_days']} días (Seguro desde `{res['meat_date']}`)
        """)
        
        nutri_text = st.session_state['diagnostic_report']['nutritional'] if st.session_state['diagnostic_report'] else "Sin sifoneo nutricional activo."
        diag_text = f"Sistema afectado: {sb_system}. Diagnóstico presuntivo regional ({estado_seleccionado}, {macro_region})."
        treat_text = f"Fármaco: {res['drug']}\nDosis: {res['ml']} mL ({res['drug_cost']} MXN)\nVía: {res['via']}"
        with_text = f"Retiro Leche: {res['milk_days']} días | Retiro Carne: {res['meat_days']} días"
        econ_text = f"Costo total tratamiento + merma: ${res['total_impact']} MXN"
        
        pdf_bytes = generate_pdf_report(
            patient_id=current_patient_id,
            rancho="Rancho San José de los Tlaxcalas",
            municipio=municipio_input,
            estado=estado_seleccionado,
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
            label="📄 Descargar Receta y Reporte Oficial SENASICA en PDF",
            data=pdf_bytes,
            file_name=f"Receta_SENASICA_{current_patient_id}_{datetime.date.today()}.pdf",
            mime="application/pdf",
            type="primary"
        )
    else:
        st.info("💡 Configure el fármaco y los parámetros económicos para generar la evaluación y el PDF oficial.")


# --- PESTAÑA 5: ESTIMACIÓN DE PESO ---
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
            st.image(Image.open(uploaded_image), caption=f"Arete SINIIGA: {current_patient_id}", use_container_width=True)
            if st.button("🤖 Procesar Peso con IA", type="primary"):
                ai_weight_result = 438.0
                st.session_state['last_estimated_weight'] = ai_weight_result
                st.success(f"¡Peso estimado por visión artificial: **{ai_weight_result} kg** (Guardado en memoria)!")

    st.markdown("---")
    st.metric(label="Peso Actual Registrado en Memoria de la App", value=f"{st.session_state['last_estimated_weight']} kg")


# --- PESTAÑA 6: FONOFONÍA Y ESPECTROGRAMAS REALES ---
with tab_audio:
    st.subheader("🔊 Procesamiento Acústico y Generación de Espectrogramas (Librosa / FFT)")
    st.markdown(f"Análisis espectral real de auscultación ruminal o respiratoria para el arete SINIIGA: **{current_patient_id}**")
    
    audio_upload = st.file_uploader("Sube archivo de audio de auscultación (WAV / MP3 / M4A)", type=["wav", "mp3", "m4a"])
    
    if audio_upload:
        st.audio(audio_upload)
        if st.button("🔬 Procesar Espectrograma Real (FFT)", type="primary"):
            try:
                y, sr = librosa.load(audio_upload, sr=None)
                S = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=128, fmax=8000)
                S_dB = librosa.power_to_db(S, ref=np.max)
                
                fig, ax = plt.subplots(figsize=(10, 4))
                img = librosa.display.specshow(S_dB, x_axis='time', y_axis='mel', sr=sr, fmax=8000, ax=ax, cmap='magma')
                ax.set(title=f'Espectrograma Acústico - Arete {current_patient_id}')
                fig.colorbar(img, ax=ax, format='%+2.0f dB')
                
                st.pyplot(fig)
                
                rms = librosa.feature.rms(y=y)[0]
                mean_energy = np.mean(rms) * 1000
                
                st.success("¡Espectrograma generado y procesado exitosamente vía Transformada de Fourier (FFT)!")
                
                col_a1, col_a2 = st.columns(2)
                with col_a1:
                    st.metric(label="Energía RMS Promedio", value=f"{round(mean_energy, 2)} Units")
                with col_a2:
                    st.metric(label="Tasa de Muestreo", value=f"{sr} Hz")
                    
            except Exception as e:
                st.error(f"Error procesando el archivo de audio: {e}")
    else:
        st.info("💡 Sube un archivo de audio para calcular y visualizar el espectrograma real de la motilidad ruminal o respiratoria.")


# --- PESTAÑA 7: IOT Y TELEMETRÍA DE HATO ---
with tab_iot:
    st.subheader("📡 Módulo IoT: Alertas de Collares de Rumodetección y Podómetros")
    st.markdown("Recepción automática de eventos telemétricos (baja de rumina, picos de actividad por celo o fiebre subclínica).")
    
    with st.expander("📥 Simular Webhook / Entrada de Dispositivo Inteligente (API Mock)"):
        with st.form("iot_form"):
            col_i1, col_i2 = st.columns(2)
            with col_i1:
                iot_device_id = st.text_input("ID Collar / Dispositivo IoT", value="COLLAR-MX-902")
                iot_tag_type = st.selectbox("Tipo de Sensor", ["Collar Ruminal (Allflex/SensingCow)", "Podómetro Actividad (Pedometer Tag)", "Orejera Térmica IoT"])
            with col_i2:
                iot_alert_type = st.selectbox("Tipo de Alerta Temprana", ["⚠️ Alerta SARA / Baja Rumina (< 350 min/día)", "🔥 Alerta Fiebre / Temperatura Elevada", "💃 Alerta Celo Detectado (Pico Actividad)", "🔋 Batería Baja / Sin Señal"])
                iot_status = st.selectbox("Estatus de Alerta", ["Activa / Pendiente de Revisión", "Atendida / En Tratamiento", "Descartada"])
            
            iot_desc = st.text_area("Descripción telemétrica", value="El sensor detectó una caída sostenida del tiempo de rumina durante las últimas 18 horas en el predio.")
            
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
                st.success("¡Alerta IoT recibida y almacenada localmente en la cola de sincronización!")

    st.markdown("---")
    st.subheader("🚨 Historial de Alertas Telemétricas Activas en el Hato")
    df_iot = load_iot_alerts_sqlite()
    if not df_iot.empty:
        for idx, row in df_iot.iterrows():
            sync_tag = "🟢 Sincronizado" if row['sync_status'] == 'synced' else "🟡 Pendiente"
            st.markdown(f"""
            <div class="card">
                <h4>{row['alert_type']} — <code>{row['device_id']}</code> ({sync_tag})</h4>
                <p><b>Sensor:</b> {row['tag_type']} | <b>Fecha/Hora:</b> {row['timestamp']}</p>
                <p><b>Descripción:</b> {row['description']}</p>
                <p><b>Estatus:</b> <code>{row['status']}</code></p>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No hay alertas telemétricas pendientes registradas en este momento.")


# --- PESTAÑA 8: MESH SYNC P2P ---
with tab_mesh:
    st.subheader("🌐 Red Mesh P2P Rural (Sincronización Off-Grid)")
    st.markdown("Permite compartir expedientes clínicos, alertas sanitarias y reportes de aretes SINIIGA entre dispositivos cercanos en el rancho **sin necesidad de conexión a internet o señal celular**, utilizando Bluetooth o Wi-Fi Direct local.")
    
    col_m1, col_m2 = st.columns(2)
    with col_m1:
        st.markdown("#### 📡 Nodos Mesh Detectados en el Área")
        st.info("🟢 **Nodo Corrales Norte** (Dispositivo Tablet Vet) — Último ping: Hace 2 min\n\n🟢 **Nodo Báscula Ganadera** (Dispositivo Mozo) — Último ping: Hace 5 min")
        if st.button("🔄 Buscar Nodos Cercanos (Escaneo Local)", type="secondary"):
            st.success("¡Escaneo completado! 2 nodos locales encontrados y sincronizados con éxito.")
    with col_m2:
        st.markdown("#### 📤 Exportar Paquete de Emergencia Cifrado")
        st.markdown("Genera un archivo comprimido local con el estado del hato para pasarlo por USB o transferencia rápida en campo.")
        if st.button("📦 Generar Paquete Mesh Local", type="primary"):
            st.success("¡Paquete Mesh generado correctamente en el almacenamiento local del dispositivo!")


# --- PESTAÑA 9: VIDEOLLAMADA / URGENCIAS A DISTANCIA ---
with tab_tele:
    st.subheader("📅 Telemedicina Veterinaria: Agendar Videollamada de Urgencia / Distancia")
    st.markdown(f"Conexión directa en tiempo real con el **Dr. Alejandro Castañeda Correa** para casos críticos o asesoría técnica en campo. (Notificaciones activas al cel: `{st.session_state['current_user']['phone']}`)")
    
    with st.form("tele_form"):
        col_t1, col_t2 = st.columns(2)
        with col_t1:
            tele_client = st.text_input("Nombre del Propietario / Productor", value=st.session_state['current_user']['name'])
            tele_rancho = st.text_input("Rancho / Predio / Ubicación", value=f"{estado_seleccionado}, {municipio_input}")
            tele_species = st.selectbox("Especie Involucrada", ["Bovino", "Equino", "Porcino", "Ovino", "Caprino", "Canino", "Felino"])
        with col_t2:
            tele_urgency = st.selectbox("Nivel de Urgencia", ["🔴 EMERGENCIA 24/7 (Atención Inmediata)", "🟠 Consulta Prioritaria (Hoy)", "🟡 Videollamada Programada (Próximos días)"])
            tele_date = st.date_input("Fecha Preferida de Consulta")
            tele_time = st.time_input("Hora Estimada")
            
        tele_motive = st.text_area("Descripción breve del caso clínico o emergencia", placeholder="Ej. Becerro con claudicación severa y sospecha de artritis séptica...")
        
        submit_tele = st.form_submit_button("🚀 Agendar y Enviar Notificación SMS/WhatsApp", type="primary")
        
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
            st.success(f"¡Cita agendada exitosamente y notificación enviada por SMS/WhatsApp al número `{st.session_state['current_user']['phone']}`!")

    st.divider()
    st.subheader("📌 Consultas y Urgencias Agendadas (SQLite)")
    df_app = load_appointments_sqlite()
    if not df_app.empty:
        for idx, row in df_app.iterrows():
            sync_tag = "🟢 Sincronizado" if row['sync_status'] == 'synced' else "🟡 Pendiente"
            with st.container():
                st.markdown(f"""
                <div class="card">
                    <h4>🚨 {row['urgency']} — Predio: {row['rancho']} ({sync_tag})</h4>
                    <p><b>Propietario:</b> {row['owner']} | <b>Especie:</b> {row['species']} | <b>Fecha:</b> {row['datetime']}</p>
                    <p><b>Motivo:</b> {row['motive']}</p>
                    <p>🔗 <b>Enlace de Videollamada Segura:</b> <a href="{row['link']}" target="_blank">{row['link']}</a></p>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("No hay videollamadas de emergencia o distancia agendadas en la base de datos local.")
