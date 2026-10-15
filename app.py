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
# ESTILOS CSS VANGUARDISTAS Y REDISEÑO DE LOGO/HERO
# ==========================================
st.markdown("""
<style>
    .main { background-color: #f8fafc; }
    
    /* Branding Header & Hero Banner */
    .brand-hero {
        background: linear-gradient(135deg, #091e3a 0%, #224066 50%, #132e4f 100%);
        padding: 2.5rem 2rem;
        border-radius: 20px;
        color: white;
        box-shadow: 0 12px 30px -8px rgba(9, 30, 58, 0.3);
        margin-bottom: 2rem;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    .brand-logo-badge {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 70px;
        height: 70px;
        background: rgba(56, 189, 248, 0.15);
        border: 2px solid #38bdf8;
        border-radius: 18px;
        font-size: 2.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 0 20px rgba(56, 189, 248, 0.3);
    }
    .brand-title {
        font-size: 3rem;
        font-weight: 900;
        margin: 0;
        letter-spacing: -0.03em;
        background: linear-gradient(90deg, #ffffff 0%, #38bdf8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .brand-slogan {
        font-size: 1.15rem;
        color: #e2e8f0;
        margin-top: 0.5rem;
        font-weight: 500;
        font-style: italic;
        letter-spacing: 0.01em;
    }
    .brand-author {
        font-size: 0.85rem;
        color: #38bdf8;
        margin-top: 0.85rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }

    /* Tarjetas de Planes y Secciones */
    .plan-card {
        background: #ffffff;
        padding: 2rem 1.5rem;
        border-radius: 16px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 12px -2px rgba(0,0,0,0.05);
        height: 100%;
        transition: all 0.3s ease;
    }
    .plan-card-featured {
        background: #ffffff;
        padding: 2rem 1.5rem;
        border-radius: 16px;
        border: 2px solid #38bdf8;
        box-shadow: 0 8px 25px -5px rgba(56, 189, 248, 0.2);
        height: 100%;
    }
    .card { 
        background-color: #ffffff; 
        padding: 1.5rem; 
        border-radius: 12px; 
        border: 1px solid #e2e8f0; 
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05); 
        margin-bottom: 1rem; 
    }
    .stButton button { border-radius: 10px; font-weight: 600; }
</style>
""", unsafe_allow_html=True)


# ==========================================
# 0. CONTROL DE ESTADO DE SESIÓN Y AUTENTICACIÓN BIOMÉTRICA
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
    st.session_state['selected_plan'] = None
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


def render_brand_header():
    """Encabezado de marca con Logotipo y Eslogan"""
    st.markdown("""
    <div class="brand-hero" style="text-align: center;">
        <div class="brand-logo-badge">🧬🩺</div>
        <h1 class="brand-title">Clinic-IA</h1>
        <p class="brand-slogan">“Zootecnia de Precisión, Trazabilidad e Inteligencia Veterinaria al Servicio del Campo”</p>
        <p class="brand-author">Desarrollada y Creada por: Dr. Alejandro Castañeda Correa</p>
    </div>
    """, unsafe_allow_html=True)


def render_landing_and_subscription_selector():
    """Página de inicio organizada: Branding + Selección de Plan"""
    render_brand_header()
    
    st.markdown("""
    <div style='text-align: center; margin-bottom: 2rem;'>
        <h2>💳 Elige tu Plan de Suscripción</h2>
        <p style='color: #64748b;'>Selecciona la modalidad adecuada para tu operación pecuaria para activar o ingresar a tu cuenta.</p>
    </div>
    """, unsafe_allow_html=True)
    
    col_p1, col_p2, col_p3 = st.columns(3)
    
    with col_p1:
        st.markdown("""
        <div class='plan-card' style='text-align: center;'>
            <span style='font-size: 2rem;'>🌱</span>
            <h3>Plan Productor</h3>
            <h2 style='color: #0284c7;'>$499 <span style='font-size: 1rem; color: #64748b;'>MXN / mes</span></h2>
            <p style='color: #64748b; font-size: 0.9rem;'>Para ranchos independientes y productores individuales.</p>
            <hr style='border: 0; border-top: 1px solid #e2e8f0; margin: 1rem 0;'>
            <div style='text-align: left; font-size: 0.95rem; color: #334155; line-height: 1.8;'>
                ✔️ Hasta 500 aretes SINIIGA activos<br>
                ✔️ Diagnóstico clínico asistido<br>
                ✔️ Recetas y reportes PDF oficiales<br>
                ✔️ Sincronización Mesh P2P básica
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.write("")
        if st.button("Elegir Plan Productor", key="btn_p1", use_container_width=True):
            st.session_state['selected_plan'] = "Productor"
            st.rerun()
            
    with col_p2:
        st.markdown("""
        <div class='plan-card-featured' style='text-align: center;'>
            <span style='font-size: 2rem;'>🩺</span>
            <h3>Plan Pro Veterinario</h3>
            <h2 style='color: #0284c7;'>$1,299 <span style='font-size: 1rem; color: #64748b;'>MXN / mes</span></h2>
            <p style='color: #64748b; font-size: 0.9rem;'>Para Médicos Zootecnistas y asesores técnicos en campo.</p>
            <hr style='border: 0; border-top: 1px solid #e2e8f0; margin: 1rem 0;'>
            <div style='text-align: left; font-size: 0.95rem; color: #334155; line-height: 1.8;'>
                ✔️ Hatos y aretes SINIIGA ilimitados<br>
                ✔️ Vademecum y cálculo costo-beneficio<br>
                ✔️ Alertas IoT y telemetría de hato<br>
                ✔️ Fonofonía y espectrogramas (FFT)
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.write("")
        if st.button("Elegir Plan Pro Vet", key="btn_p2", type="primary", use_container_width=True):
            st.session_state['selected_plan'] = "Pro - Médico Veterinario"
            st.rerun()
            
    with col_p3:
        st.markdown("""
        <div class='plan-card' style='text-align: center;'>
            <span style='font-size: 2rem;'>🏢</span>
            <h3>Plan Corporativo</h3>
            <h2 style='color: #0284c7;'>$3,499 <span style='font-size: 1rem; color: #64748b;'>MXN / mes</span></h2>
            <p style='color: #64748b; font-size: 0.9rem;'>Para asociaciones ganaderas y agroindustrias.</p>
            <hr style='border: 0; border-top: 1px solid #e2e8f0; margin: 1rem 0;'>
            <div style='text-align: left; font-size: 0.95rem; color: #334155; line-height: 1.8;'>
                ✔️ Conexión y trazabilidad SENASICA<br>
                ✔️ Red Mesh rural ilimitada para personal<br>
                ✔️ Múltiples administradores y roles<br>
                ✔️ Soporte técnico prioritario 24/7
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.write("")
        if st.button("Elegir Plan Corporativo", key="btn_p3", use_container_width=True):
            st.session_state['selected_plan'] = "Corporativo"
            st.rerun()


def render_auth_or_register_portal():
    """Portal organizado de autenticación / registro"""
    render_brand_header()
    
    st.markdown(f"""
    <div style='text-align: center; margin-bottom: 1.5rem;'>
        <h2>🛡️ Acceso Seguro y Registro de Cuenta</h2>
        <p style='color: #64748b;'>Plan Seleccionado: <b style='color: #0284c7;'>{st.session_state['selected_plan']}</b> | <a href='#' target='_self' onclick='window.location.reload();'>Cambiar Plan</a></p>
    </div>
    """, unsafe_allow_html=True)
    
    auth_tab1, auth_tab2 = st.tabs(["🔑 Iniciar Sesión Segura", "📝 Registrarse Nueva Cuenta"])
    
    # --- PESTAÑA LOGIN CON BIOMETRÍA Y MFA ---
    with auth_tab1:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            with st.form("login_form"):
                st.markdown("### Credenciales de Acceso")
                username = st.text_input("Usuario o Correo Electrónico", value="alejandro.castaneda")
                password = st.text_input("Contraseña", type="password", value="clinic2026*")
                
                st.markdown("### 🔐 Doble Factor de Autenticación (MFA) & Biometría")
                st.info("💡 Ingrese el token dinámico de 6 dígitos (SMS / WhatsApp). Simulación: `849201`")
                mfa_code = st.text_input("Código Token MFA", value="849201", max_chars=6)
                
                biometric_check = st.checkbox("👆 Validar con Huella Digital / Sensor Biométrico (Passkey FIDO2)")
                
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
                                st.success("¡Autenticación biométrica y MFA exitosas! Ingresando al sistema...")
                                st.rerun()
                            else:
                                st.error("❌ Se requiere la validación de la huella digital / biometría para prevenir fraudes.")
                        else:
                            st.error("❌ Código MFA incorrecto.")
                    else:
                        st.error("❌ Usuario o contraseña incorrectos.")

    # --- PESTAÑA REGISTRO CON DATOS BANCARIOS Y CONTACTO ---
    with auth_tab2:
        col_r1, col_r2, col_r3 = st.columns([1, 2, 1])
        with col_r2:
            with st.form("register_form"):
                st.markdown("### 📋 Registro Comercial y Datos de Facturación")
                
                reg_name = st.text_input("Nombre Completo del Titular")
                reg_email = st.text_input("Correo Electrónico Oficial")
                reg_phone = st.text_input("Número Celular (Para Notificaciones y Tokens SMS)")
                reg_user = st.text_input("Nombre de Usuario")
                reg_pass = st.text_input("Contraseña Segura", type="password")
                
                st.markdown("#### 💳 Información Bancaria (Cobro de Suscripción)")
                reg_bank = st.text_input("Número de Tarjeta / CLABE Interbancaria", placeholder="**** **** **** 1234")
                reg_expiry = st.text_input("Vencimiento (MM/AA)", placeholder="12/28")
                reg_cvv = st.text_input("CVV / Cifra de Seguridad", type="password", max_chars=4)
                
                reg_biometric_consent = st.checkbox("Registrar huella digital / clave biométrica en este equipo")
                
                register_btn = st.form_submit_button("💼 Activar Cuenta y Suscripción", type="primary", use_container_width=True)
                
                if register_btn:
                    if reg_user and reg_pass and reg_email and reg_phone and reg_bank:
                        if reg_user in st.session_state['registered_users_db']:
                            st.error("❌ El usuario ya existe. Intenta con otro.")
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
                            st.success(f"¡Registro completado! Tokens enviados al celular `{reg_phone}`. Inicia sesión en la pestaña adyacente.")
                    else:
                        st.warning("⚠️ Por favor completa todos los campos obligatorios.")


# Control de flujo inicial de la aplicación
if not st.session_state['selected_plan']:
    render_landing_and_subscription_selector()
    st.stop()

if not st.session_state['authenticated'] or not st.session_state['mfa_verified'] or not st.session_state['biometric_verified']:
    render_auth_or_register_portal()
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
# PANEL LATERAL DE CONTROL Y UBICACIÓN
# ==========================================
st.sidebar.markdown(f"### 👤 `{st.session_state['current_user']['name']}`")
st.sidebar.caption(f"Rol: {st.session_state['current_user']['role']}")
st.sidebar.caption(f"Plan Activo: **{st.session_state['selected_plan']}**")
st.sidebar.caption(f"📱 Notificaciones SMS: `{st.session_state['current_user']['phone']}`")

if st.sidebar.button("🚪 Cerrar Sesión / Cambiar Plan"):
    st.session_state['authenticated'] = False
    st.session_state['mfa_verified'] = False
    st.session_state['biometric_verified'] = False
    st.session_state['selected_plan'] = None
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
    "Zona Golfo y Tróp
