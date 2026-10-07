import streamlit as st
import pandas as pd
import datetime
import numpy as np
from PIL import Image

# Configuración de la página
st.set_page_config(
    page_title="Clinic-IA | Veterinaria de Precisión",
    page_icon="🩺",
    layout="wide"
)

# ==========================================
# ESTILOS CSS VANGUARDISTAS Y DE EXCELENCIA
# ==========================================
st.markdown("""
<style>
    /* Estilo general de la aplicación */
    .main {
        background-color: #f8fafc;
    }
    
    /* Tarjeta de Encabezado Principal */
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
    .hero-title {
        font-size: 2.75rem;
        font-weight: 800;
        margin: 0;
        letter-spacing: -0.025em;
        color: #ffffff;
    }
    .hero-subtitle {
        font-size: 1.1rem;
        color: #94a3b8;
        margin-top: 0.5rem;
        font-weight: 400;
    }
    .hero-author {
        font-size: 0.85rem;
        color: #38bdf8;
        margin-top: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    /* Estilización de Contenedores y Tarjetas */
    .card {
        background-color: #ffffff;
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        margin-bottom: 1rem;
    }
    
    /* Botones personalizados */
    .stButton button {
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
</style>
""", unsafe_allow_html=True)

# Inicializar almacenamiento en sesión
if 'patient_records' not in st.session_state:
    st.session_state['patient_records'] = []
if 'last_estimated_weight' not in st.session_state:
    st.session_state['last_estimated_weight'] = 400.0

class FieldDiagnostics:
    def __init__(self, species, production_type="general"):
        self.species = species.lower()
        self.production_type = production_type.lower()
        
    def evaluate_vitals(self, temp, hr, rr):
        ranges = {
            'bovino_leche': {'temp': (38.0, 39.3), 'hr': (60, 84), 'rr': (18, 28)},
            'bovino_carne': {'temp': (36.7, 39.1), 'hr': (60, 80), 'rr': (10, 30)},
            'equino': {'temp': (37.5, 38.5), 'hr': (28, 40), 'rr': (10, 24)},
            'porcino': {'temp': (38.0, 39.5), 'hr': (60, 90), 'rr': (8, 18)},
            'ovino': {'temp': (38.3, 39.9), 'hr': (70, 80), 'rr': (12, 72)}
        }
        
        key = f"{self.species}_{self.production_type}" if f"{self.species}_{self.production_type}" in ranges else self.species
        if key not in ranges:
            return ["Especie o tipo productivo no soportado en la base de datos."]
        
        r = ranges[key]
        alerts = []
        
        if not (r['temp'][0] <= temp <= r['temp'][1]):
            alerts.append(f"⚠ **Temperatura alterada:** {temp} °C (Rango: {r['temp'][0]} - {r['temp'][1]} °C)")
        if not (r['hr'][0] <= hr <= r['hr'][1]):
            alerts.append(f"⚠️ **Frecuencia cardíaca alterada:** {hr} lpm (Rango: {r['hr'][0]} - {r['hr'][1]} lpm)")
        if not (r['rr'][0] <= rr <= r['rr'][1]):
            alerts.append(f"⚠ **Frecuencia respiratoria alterada:** {rr} rpm (Rango: {r['rr'][0]} - {r['rr'][1]} rpm)")
            
        return alerts if alerts else ["✅ Constantes fisiológicas dentro de parámetros normales."]

    def assess_dehydration(self, skin_tent_seconds, mucous_membrane_status, eye_sunken_bool):
        score = 0
        if skin_tent_seconds > 5:
            score += 3
        elif skin_tent_seconds > 2:
            score += 2
        elif skin_tent_seconds > 1:
            score += 1
            
        if mucous_membrane_status == 'Seca':
            score += 2
        elif mucous_membrane_status == 'Pegajosa':
            score += 1
            
        if eye_sunken_bool:
            score += 2
            
        if score >= 5:
            return "🔴 **Deshidratación severa (> 8-10%).** Urgente: Fluidoterapia intravenosa."
        elif score >= 3:
            return "🟠 **Deshidratación moderada (6-8%).**"
        elif score >= 1:
            return "🟡 **Deshidratación leve (4-6%).**"
        return "🟢 **Estado de hidratación normal (< 4%).**"

    @staticmethod
    def estimate_weight_biometric(species, heart_girth, body_length):
        if species == "bovino":
            weight = (heart_girth ** 2 * body_length) / 10840
        elif species == "equino":
            weight = (heart_girth ** 2 * body_length) / 11877
        elif species == "porcino":
            weight = (heart_girth ** 2 * body_length) / 14200
        else:
            weight = (heart_girth ** 2 * body_length) / 10000
        return round(weight, 2)


# ==========================================
# PANEL LATERAL: VARIABLES CLÍNICAS Y ANAMNESIS
# ==========================================
st.sidebar.markdown("### 🩺 Panel Clínico de Campo")
st.sidebar.markdown("Parámetros inteligentes para anamnesis integral.")

with st.sidebar.expander("🏷️ 1. Reseña y Señalamiento", expanded=True):
    sb_species = st.selectbox("Especie", ["Bovino", "Equino", "Porcino", "Ovino"])
    sb_breed = st.selectbox("Raza / Biotipo", ["Holstein", "Beefmaster", "Angus", "Cebú / Brahman", "Suizo Pardo", "Cruzado / Comercial", "Otro"])
    sb_age_group = st.selectbox("Grupo Etario", ["Cría / Ternero (< 6 meses)", "Levante / Recría", "Vaca en Producción / Adulto", "Toro reproductor"])
    sb_sex = st.selectbox("Sexo", ["Hembra", "Macho", "Macho Castrado"])
    sb_prod_type = "Leche" if sb_species == "Bovino" and st.selectbox("Propósito", ["Leche", "Carne"]) == "Leche" else "Carne"

with st.sidebar.expander("📋 2. Anamnesis y Evolución"):
    sb_evolution = st.selectbox("Tiempo de Evolución", ["Hiperagudo (< 12 hrs)", "Agudo (12 - 48 hrs)", "Subagudo (3 - 7 días)", "Crónico (> 7 días)"])
    sb_morbidity = st.selectbox("Incidencia en el Lote", ["Caso esporádico (1 animal)", "Brote focal (2 a 5 animales)", "Brote masivo (> 10% del lote)"])
    sb_system = st.selectbox("Sistema Principal Afectado", ["Digestivo / Metabólico", "Respiratorio", "Locomotor / Podal", "Reproductivo / Urogenital", "Nervioso / Infeccioso sistémico"])

with st.sidebar.expander("🌾 3. Nutrición y Ambiente"):
    sb_system_prod = st.selectbox("Sistema de Producción", ["Estabulación total (Confinamiento / TMR)", "Pastoreo intensivo rotacional", "Sistema mixto (Silvopastoril / Suplementado)"])
    sb_diet_change = st.selectbox("Cambio de Dieta Reciente", ["No hay cambios", "Sí (Últimos 7 días)", "Sí (Últimas 24-48 horas - Alerta acidosis)"])
    sb_water_source = st.selectbox("Calidad / Fuente de Agua", ["Bebedero automático / Limpio", "Estanque / Jagüey", "Pozo profundo", "Agua corriente / Río"])

with st.sidebar.expander("💉 4. Manejo Sanitario Reciente"):
    sb_vaccination = st.selectbox("Historial de Vacunación", ["Al día (Calendario completo)", "Incompleto / Desconocido", "Ninguna aplicación reciente"])
    sb_deworming = st.selectbox("Última Desparasitación", ["Menos de 30 días", "De 1 a 3 meses", "Más de 3 meses / Desconocido"])

st.sidebar.markdown("---")
current_patient_id = st.sidebar.text_input("🆔 Arete / ID Activo para Consulta", value="ARETE-001")

st.sidebar.markdown("---")
st.sidebar.markdown(
    "<div style='text-align: center; color: #64748b; font-size: 0.85rem; padding: 10px;'>"
    "Diseñado y desarrollado por<br><b>Dr. Vet. Alejandro Castañeda Correa</b>"
    "</div>", 
    unsafe_allow_html=True
)


# ==========================================
# ENCABEZADO VANGUARDISTA CON LOGOTIPO
# ==========================================
st.markdown("""
<div class="hero-container">
    <div class="hero-logo">🧬</div>
    <div>
        <h1 class="hero-title">Clinic-IA</h1>
        <p class="hero-subtitle">Precisión diagnóstica e inteligencia artificial avanzada para la clínica veterinaria de campo.</p>
        <p class="hero-author">Autor: Dr. Vet. Alejandro Castañeda Correa</p>
    </div>
</div>
""", unsafe_allow_html=True)


# ==========================================
# INTERFAZ DE PESTAÑAS PRINCIPALES
# ==========================================
tab_diag, tab_reg, tab_drugs, tab_weight, tab_audio = st.tabs([
    "🩺 Diagnóstico Clínico", 
    "📁 Historial por Arete", 
    "💊 Fármacos y Dosificación", 
    "⚖️ Estimación de Peso (IA)",
    "🔊 Fonofonía Ruminal (IA)"
])

# --- PESTAÑA 1: DIAGNÓSTICO CLÍNICO ---
with tab_diag:
    st.subheader(f"Evaluación Clínica para Paciente: ID [{current_patient_id}]")
    st.info(f"Reseña actual cargada desde el panel lateral: **{sb_species} | Raza: {sb_breed} | Etapa: {sb_age_group}**")
    
    with st.form("diagnostic_form"):
        c1, c2, c3 = st.columns(3)
        with c1:
            temp = st.number_input("Temp (°C)", min_value=30.0, max_value=45.0, value=38.5, step=0.1)
        with c2:
            hr = st.number_input("FC (lpm)", min_value=10, max_value=150, value=70, step=1)
        with c3:
            rr = st.number_input("FR (rpm)", min_value=5, max_value=120, value=20, step=1)

        st.markdown("---")
        skin_tent = st.slider("Tiempo de pliegue cutáneo (segundos)", min_value=0.0, max_value=10.0, value=1.0, step=0.5)
        mucosa = st.selectbox("Humedad de mucosas", ["Húmeda/Normal", "Pegajosa", "Seca"])
        eye_sunken = st.checkbox("Depresión del globo ocular (ojos hundidos)")

        submit_button = st.form_submit_button(label="Ejecutar Diagnóstico Clínico")

    if submit_button:
        evaluator = FieldDiagnostics(sb_species, sb_prod_type.lower())
        st.divider()
        st.subheader("📋 Resultados del Análisis y Diagnóstico Diferencial")
        
        vitals_results = evaluator.evaluate_vitals(temp, hr, rr)
        st.markdown("### Constantes Fisiológicas")
        for alert in vitals_results:
            st.write(alert)
            
        dehydration_result = evaluator.assess_dehydration(skin_tent, mucosa, eye_sunken)
        st.markdown("### Estado de Hidratación")
        st.write(dehydration_result)
        
        st.markdown("### 🔍 Factores de Riesgo Integrados (Anamnesis)")
        st.write(f"- **Evolución del cuadro:** {sb_evolution} ({sb_morbidity})")
        st.write(f"- **Sistema afectado:** {sb_system}")
        st.write(f"- **Alerta nutricional/ambiente:** Dieta reciente: *{sb_diet_change}* | Sistema: *{sb_system_prod}*")


# --- PESTAÑA 2: HISTORIAL CLÍNICO Y REGISTRO ---
with tab_reg:
    st.subheader("📁 Historial Clínico Longitudinal por Número de Arete / ID")
    
    with st.form("patient_form"):
        col1, col2 = st.columns(2)
        with col1:
            input_arete = st.text_input("Número de Arete / ID del Paciente", value=current_patient_id)
            reg_species = st.selectbox("Especie", ["Bovino", "Equino", "Porcino", "Ovino"], index=0 if sb_species=="Bovino" else 0)
        with col2:
            estimated_weight = st.number_input("Peso Actual (kg)", min_value=1.0, max_value=1500.0, value=st.session_state['last_estimated_weight'])
            clinical_notes = st.text_area("Hallazgos de Exploración y Plan Terapéutico")
            
        save_btn = st.form_submit_button("Guardar Evento en el Historial del Arete")
        
        if save_btn:
            if input_arete:
                record = {
                    "Arete/ID": input_arete.strip().upper(),
                    "Fecha": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "Especie": reg_species,
                    "Raza": sb_breed,
                    "Sistema Afectado": sb_system,
                    "Peso (kg)": estimated_weight,
                    "Notas Clínicas": clinical_notes
                }
                st.session_state['patient_records'].append(record)
                st.success(f"¡Evento clínico guardado exitosamente para el arete: {input_arete.upper()}!")
            else:
                st.warning("Por favor ingresa un número de arete válido.")

    st.markdown("---")
    st.subheader("🔍 Consulta de Historial Clínico por Arete")
    
    if st.session_state['patient_records']:
        df_all = pd.DataFrame(st.session_state['patient_records'])
        unique_aretes = df_all["Arete/ID"].unique().tolist()
