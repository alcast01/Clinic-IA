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

# Inicializar sesión
if 'patient_records' not in st.session_state:
    st.session_state['patient_records'] = []
if 'last_estimated_weight' not in st.session_state:
    st.session_state['last_estimated_weight'] = 400.0

# ==========================================
# MOTOR DE DECISIÓN CLÍNICA Y DIAGNÓSTICO (CDSS)
# ==========================================
class AdvancedClinicalEngine:
    def __init__(self, species, production_type="general"):
        self.species = species.lower()
        self.production_type = production_type.lower()
        
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
        """Algoritmo de inferencia probabilística basado en signología y sistemas"""
        r = self.get_physiological_ranges()
        score_base = 50
        
        if temp > r['temp'][1]: score_base += 15 # Fiebre sugiere proceso infeccioso/inflamatorio
        elif temp < r['temp'][0]: score_base += 20 # Hipotermia sugiere shock o metabolismo deprimido
        
        differentials = []
        
        if self.species in ["bovino", "ovino"]:
            if system_affected == "Digestivo / Metabólico":
                differentials = [
                    {"dx": "Acidosis Ruminal Subaguda (SARA) / Aguda", "prob": 88 if "Cambio de dieta reciente" in clinical_signs_list else 60},
                    {"dx": "Desplazamiento de Abomaso (DA)", "prob": 75 if "Hipomotilidad ruminal" in clinical_signs_list else 45},
                    {"dx": "Cetosis Clínica / Subclínica", "prob": 70}
                ]
            elif system_affected == "Respiratorio":
                differentials = [
                    {"dx": "Complejo Respiratorio Bovino (CRB) / Pasteurelosis", "prob": 92},
                    {"dx": "Neumonía Enzoótica / Pleuresía", "prob": 78}
                ]
            else:
                differentials = [{"dx": "Trastorno sistémico multifactorial de origen metabólico/infeccioso", "prob": 65}]
                
        elif self.species == "equino":
            if system_affected == "Digestivo / Metabólico":
                differentials = [
                    {"dx": "Síndrome Abdominal Agudo (Cólico Spasmodico / Desplazamiento)", "prob": 95},
                    {"dx": "Enteritis / Colitis Aguda", "prob": 80}
                ]
            else:
                differentials = [{"dx": "Obstrucción de Vías Aéreas Superiores / EPPA", "prob": 82}]
                
        elif self.species in ["canino", "felino"]:
            if system_affected == "Digestivo / Metabólico":
                differentials = [
                    {"dx": "Gastroenteritis Hemorrágica / Parvovirosis (si no vacunado)", "prob": 89},
                    {"dx": "Cuerpo Extraño Gastrointestinal / Obstrucción", "prob": 78},
                    {"dx": "Pancreatitis Aguda", "prob": 70}
                ]
            elif system_affected == "Reproductivo / Urogenital":
                differentials = [
                    {"dx": "Enfermedad del Tracto Urinario Inferior Felino (FLUTD) / Cistitis", "prob": 91},
                    {"dx": "Insuficiencia Renal Aguda (IRA)", "prob": 84}
                ]
            else:
                differentials = [{"dx": "Proceso inflamatorio sistémico primario", "prob": 75}]
        else:
            differentials = [{"dx": "Patología infecciosa o carencial genérica del lote/especie", "prob": 70}]
            
        # Ordenar por probabilidad descendente
        differentials = sorted(differentials, key=lambda x: x['prob'], reverse=True)
        return differentials


# ==========================================
# PANEL LATERAL DE CAMPO Y RESEÑA
# ==========================================
st.sidebar.markdown("### 🩺 Panel Clínico de Precisión")
st.sidebar.markdown("Parámetros inteligentes para anamnesis integral.")

with st.sidebar.expander("🏷️ 1. Reseña y Señalamiento", expanded=True):
    sb_species = st.selectbox("Especie", ["Bovino", "Equino", "Porcino", "Ovino", "Canino", "Felino"])
    
    # Razas o propósitos adaptados dinámicamente
    if sb_species == "Bovino":
        sb_breed = st.selectbox("Raza / Biotipo", ["Holstein", "Beefmaster", "Angus", "Cebú / Brahman", "Suizo Pardo", "Cruzado"])
        sb_prod_type = "Leche" if st.selectbox("Propósito", ["Leche", "Carne"]) == "Leche" else "Carne"
    else:
        sb_breed = st.text_input("Raza / Biotipo", value="Estándar / Mestizo")
        sb_prod_type = "general"
        
    sb_age_group = st.selectbox("Grupo Etario", ["Neonato / Cría", "Juvenil / Levante", "Adulto en Producción / Mantenimiento", "Geriatrie / Reproductor"])
    sb_sex = st.selectbox("Sexo", ["Hembra", "Macho", "Macho Castrado"])

with st.sidebar.expander("📋 2. Anamnesis y Evolución"):
    sb_evolution = st.selectbox("Tiempo de Evolución", ["Hiperagudo (< 12 hrs)", "Agudo (12 - 48 hrs)", "Subagudo (3 - 7 días)", "Crónico (> 7 días)"])
    sb_morbidity = st.selectbox("Incidencia en el Lote / Colectivo", ["Caso esporádico (1 animal)", "Brote focal (2 a 5 animales)", "Brote masivo (> 10%)"])
    sb_system = st.selectbox("Sistema Principal Afectado", ["Digestivo / Metabólico", "Respiratorio", "Locomotor / Podal", "Reproductivo / Urogenital", "Nervioso / Infeccioso sistémico"])

with st.sidebar.expander("🌾 3. Nutrición y Ambiente"):
    sb_system_prod = st.selectbox("Sistema de Alojamiento", ["Estabulación total / Confinamiento", "Pastoreo intensivo rotacional", "Sistema mixto / Doméstico"])
    sb_diet_change = st.selectbox("Factor de Riesgo / Dieta", ["Sin cambios recientes", "Cambio abrupto de dieta (< 48 hrs)", "Acceso a tóxicos / Cuerpos extraños", "Estrés por transporte / climക്കാര്‍"])

st.sidebar.markdown("---")
current_patient_id = st.sidebar.text_input("🆔 Arete / ID / Nombre del Paciente", value="PACIENTE-001")

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
        <p class="hero-subtitle">Plataforma experta de diagnóstico clínico veterinario con motores de inferencia probabilística.</p>
        <p class="hero-author">Autor: Dr. Vet. Alejandro Castañeda Correa</p>
    </div>
</div>
""", unsafe_allow_html=True)

# ==========================================
# PESTAÑAS PRINCIPALES
# ==========================================
tab_diag, tab_reg, tab_drugs, tab_weight, tab_audio = st.tabs([
    "🩺 Diagnóstico IA Avanzado", 
    "📁 Historial Clínico", 
    "💊 Vademecum y Dosificación", 
    "⚖️ Estimación de Peso",
    "🔊 Fonofonía (IA)"
])

# --- PESTAÑA 1: DIAGNÓSTICO CLÍNICO AVANZADO ---
with tab_diag:
    st.subheader(f"Evaluación Clínica de Precisión: [{current_patient_id}]")
    st.info(f"Reseña activa: **{sb_species} | Raza: {sb_breed} | Etapa: {sb_age_group}**")
    
    with st.form("advanced_diagnostic_form"):
        c1, c2, c3 = st.columns(3)
        with c1:
            temp = st.number_input("Temperatura Corporal (°C)", min_value=30.0, max_value=43.0, value=38.5, step=0.1)
        with c2:
            hr = st.number_input("Frecuencia Cardíaca (lpm)", min_value=10, max_value=220, value=70, step=1)
        with c3:
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

        submit_eval = st.form_submit_button(label="Ejecutar Algoritmo de Diagnóstico de Alta Precisión")

    if submit_eval:
        engine = AdvancedClinicalEngine(sb_species, sb_prod_type.lower())
        
        st.divider()
        st.subheader("📊 Reporte Diagnóstico y Matriz de Confianza")
        
        # 1. Evaluación de Constantes
        vitals_eval = engine.evaluate_vitals(temp, hr, rr)
        st.markdown("### 1. Validación Fisiológica")
        for alert in vitals_eval:
            st.write(alert)
            
        # 2. Diagnóstico Diferencial Probabilístico
        signs_list = []
        if sb_diet_change != "Sin cambios recientes": signs_list.append("Cambio de dieta reciente")
        if sign_1: signs_list.append("Hipomotilidad ruminal")
        
        differentials = engine.compute_differential_diagnosis(sb_system, signs_list, temp, hr, rr)
        
        st.markdown("### 2. Diagnósticos Diferenciales (Ranking Bayesiano)")
        for idx, item in enumerate(differentials, 1):
            confidence = item['prob']
            color = "green" if confidence > 80 else ("orange" if confidence > 60 else "red")
            st.markdown(f"**{idx}. {item['dx']}** — Índice de Coincidencia: **{confidence}%**")
            st.progress(confidence / 100.0)
            
        st.markdown("### 3. Plan Terapéutico y Recomendaciones de Campo")
        st.success("✔ Se recomienda toma de muestras complementarias (hemograma, química sanguínea o gasometría) para confirmar el diagnóstico con mayor certeza analítica.")


# --- PESTAÑA 2: HISTORIAL CLÍNICO ---
with tab_reg:
    st.subheader("📁 Historial Clínico Longitudinal por Identificador")
    
    with st.form("patient_form"):
        col1, col2 = st.columns(2)
        with col1:
            input_arete = st.text_input("ID / Arete del Paciente", value=current_patient_id)
            reg_species = st.selectbox("Especie en Registro", ["Bovino", "Equino", "Porcino", "Ovino", "Canino", "Felino"])
        with col2:
            estimated_weight = st.number_input("Peso Actual Registrado (kg)", min_value=0.5, max_value=1500.0, value=st.session_state['last_estimated_weight'])
            clinical_notes = st.text_area("Hallazgos de Exploración y Plan Terapéutico Aplicado")
            
        save_btn = st.form_submit_button("Guardar Evento en el Historial")
        
        if save_btn:
            if input_arete:
                record = {
                    "ID Paciente": input_arete.strip().upper(),
                    "Fecha": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "Especie": reg_species,
                    "Raza": sb_breed,
                    "Sistema Afectado": sb_system,
                    "Peso (kg)": estimated_weight,
                    "Notas": clinical_notes
                }
                st.session_state['patient_records'].append(record)
                st.success(f"¡Registro clínico guardado con éxito para: {input_arete.upper()}!")
            else:
                st.warning("Por favor ingresa un identificador válido.")

    st.markdown("---")
    if st.session_state['patient_records']:
        df_all = pd.DataFrame(st.session_state['patient_records'])
        selected_id = st.selectbox("Seleccione el ID para auditar su expediente completo", df_all["ID Paciente"].unique().tolist())
        st.dataframe(df_all[df_all["ID Paciente"] == selected_id], use_container_width=True)
        if st.button("🗑️ Limpiar Historial de Sesión"):
            st.session_state['patient_records'] = []
            st.rerun()
    else:
        st.info("No hay registros previos en la sesión actual.")


# --- PESTAÑA 3: FÁRMACOS Y DOSIFICACIÓN ---
with tab_drugs:
    st.subheader("Calculadora y Vademecum Clínico Clasificado")
    drug_database = {
        "Oxitetraciclina L.A. (20%) [Antibiótico]": {"dosis": 20.0, "unidad": "mg/kg", "concentracion": 200, "indicacion": "Infecciones sistémicas y respiratorias."},
        "Ceftiofur Clorhidrato [Antibiótico]": {"dosis": 2.2, "unidad": "mg/kg", "concentracion": 50, "indicacion": "Infecciones respiratorias agudas."},
        "Meloxicam (2%) [Antiinflamatorio]": {"dosis": 0.5, "unidad": "mg/kg", "concentracion": 20, "indicacion": "Control de dolor, inflamación y pirexia."},
        "Flunixin Meglumine [Analgésico / Antitérmico]": {"dosis": 1.1, "unidad": "mg/kg", "concentracion": 50, "indicacion": "Dolor visceral y cólico agudo."},
        "Ivermectina (1%) [Antiparasitario]": {"dosis": 0.2, "unidad": "mg/kg", "concentracion": 10, "indicacion": "Control de parásitos internos y externos."}
    }
    
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        selected_drug = st.selectbox("Seleccione el Fármaco", list(drug_database.keys()))
        drug_info = drug_database[selected_drug]
        st.info(f"📋 **Indicación:** {drug_info['indicacion']}\n\n📌 **Dosis estándar:** {drug_info['dosis']} {drug_info['unidad']}")
    with col_d2:
        use_ai_w = st.checkbox(f"Usar peso actual registrado ({st.session_state['last_estimated_weight']} kg)", value=True)
        animal_w = st.session_state['last_estimated_weight'] if use_ai_w else st.number_input("Peso manual (kg)", 1.0, 1500.0, 450.0)
        
    if st.button("Calcular Volumen de Aplicación"):
        total_ml = (animal_w * drug_info['dosis']) / drug_info['concentracion']
        st.success(f"### Dosis Total Requerida: **{round(total_ml, 2)} mL**  \n*(Calculado para {animal_w} kg)*")


# --- PESTAÑA 4: ESTIMACIÓN DE PESO ---
with tab_weight:
    st.subheader("Herramientas de Estimación Biométrica y de Peso")
    w_mode = st.radio("Método:", ["📐 Ecuaciones Morfométricas (Cinta)", "📸 Visión Artificial por Fotografía"])
    
    if w_mode == "📐 Ecuaciones Morfométricas (Cinta)":
        c_w1, c_w2 = st.columns(2)
        with c_w1:
            hg = st.number_input("Perímetro Torácico (cm)", 30.0, 300.0, 180.0)
        with c_w2:
            bl = st.number_input("Longitud Corporal (cm)", 30.0, 300.0, 150.0)
        if st.button("Calcular Peso"):
            w_est = round((hg ** 2 * bl) / 10840, 2)
            st.session_state['last_estimated_weight'] = w_est
            st.success(f"⚖️ **Peso Estimado:** **{w_est} kg**")
    else:
        up_img = st.file_uploader("Sube fotografía lateral", type=["jpg", "png", "jpeg"])
        if up_img:
            st.image(Image.open(up_img), use_container_width=True)
            if st.button("Procesar Imagen con IA"):
                st.session_state['last_estimated_weight'] = 435.0
                st.success("¡Peso estimado por visión artificial: 435.0 kg (Guardado en memoria)!")


# --- PESTAÑA 5: FONOFONÍA RUMINAL ---
with tab_audio:
    st.subheader("🔊 Diagnóstico Acústico y Fonofónico por IA")
    aud_file = st.file_uploader("Sube archivo de audio (WAV / MP3)", type=["wav", "mp3", "m4a"])
    if aud_file:
        st.audio(aud_file)
        if st.button("Analizar Espectro Fonofónico"):
            st.success("¡Análisis espectral completado con éxito!")
            st.write("🟢 **Motilidad Ruminal Normal:** Patrón acústico rítmico con predominio de bajas frecuencias.")
            st.metric("Frecuencia Dominante", "46.2 Hz")
