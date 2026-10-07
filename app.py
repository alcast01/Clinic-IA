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

# ==========================================
# INICIALIZACIÓN DE ESTADO DE SESIÓN (PERSISTENCIA)
# ==========================================
if 'patient_records' not in st.session_state:
    st.session_state['patient_records'] = []
if 'last_estimated_weight' not in st.session_state:
    st.session_state['last_estimated_weight'] = 450.0
if 'last_drug_result' not in st.session_state:
    st.session_state['last_drug_result'] = None
if 'diagnostic_report' not in st.session_state:
    st.session_state['diagnostic_report'] = None
if 'audio_result' not in st.session_state:
    st.session_state['audio_result'] = None

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


# ==========================================
# PANEL LATERAL DE CAMPO Y RESEÑA
# ==========================================
st.sidebar.markdown("### 🩺 Panel Clínico de Precisión")
st.sidebar.markdown("Parámetros inteligentes para anamnesis integral.")

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
    "📁 Historial por Rancho", 
    "💊 Vademecum Multiespecie", 
    "⚖️ Estimación de Peso",
    "🔊 Fonofonía (IA)"
])

# --- PESTAÑA 1: DIAGNÓSTICO CLÍNICO AVANZADO ---
with tab_diag:
    st.subheader(f"Evaluación Clínica de Precisión: [{current_patient_id}]")
    st.info(f"Reseña activa: **{sb_species} | Raza: {sb_breed} | Sexo: {sb_sex} | Etapa: {sb_age_group}**")
    
    temp = st.number_input("Temperatura Corporal (°C)", min_value=30.0, max_value=43.0, value=38.5, step=0.1)
    hr = st.number_input("Frecuencia Cardíaca (lpm)", min_value=10, max_value=220, value=70, step=1)
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

    if st.button("Ejecutar Algoritmo de Diagnóstico de Alta Precisión", type="primary"):
        engine = AdvancedClinicalEngine(sb_species, sb_prod_type.lower())
        vitals_eval = engine.evaluate_vitals(temp, hr, rr)
        signs_list = []
        if sb_diet_change != "Sin cambios recientes": signs_list.append("Cambio de dieta reciente")
        if sign_1: signs_list.append("Hipomotilidad ruminal")
        differentials = engine.compute_differential_diagnosis(sb_system, signs_list, temp, hr, rr)
        
        st.session_state['diagnostic_report'] = {
            "vitals": vitals_eval,
            "differentials": differentials,
            "patient": current_patient_id
        }

    if st.session_state['diagnostic_report']:
        report = st.session_state['diagnostic_report']
        st.divider()
        st.subheader(f"📊 Reporte Diagnóstico y Matriz de Confianza [{report['patient']}]")
        
        st.markdown("### 1. Validación Fisiológica")
        for alert in report['vitals']:
            st.write(alert)
            
        st.markdown("### 2. Diagnósticos Diferenciales (Ranking Bayesiano)")
        for idx, item in enumerate(report['differentials'], 1):
            confidence = item['prob']
            st.markdown(f"**{idx}. {item['dx']}** — Índice de Coincidencia: **{confidence}%**")
            st.progress(confidence / 100.0)
            
        st.markdown("### 3. Plan Terapéutico y Recomendaciones de Campo")
        st.success("✔ Se recomienda toma de muestras complementarias y seguimiento clínico en el expediente del rancho.")


# --- PESTAÑA 2: HISTORIAL CLÍNICO POR RANCHO Y MUNICIPIO ---
with tab_reg:
    st.subheader("📁 Archivo de Pacientes por Rancho Ganadero y Municipio")
    st.markdown("Organice y audite el historial longitudinal agrupado por unidad de producción y localidad.")
    
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
        
    if st.button("Guardar Evento en el Archivo del Rancho", type="primary"):
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
            st.session_state['patient_records'].append(record)
            st.success(f"¡Expediente guardado exitosamente para el predio **{input_rancho.upper()}** ({input_municipio})!")
        else:
            st.warning("Por favor completa el nombre del rancho y el ID del animal.")

    st.markdown("---")
    st.subheader("🔍 Filtro y Consulta por Rancho / Municipio")
    
    if st.session_state['patient_records']:
        df_all = pd.DataFrame(st.session_state['patient_records'])
        
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            selected_rancho = st.selectbox("Filtrar por Rancho / Predio", df_all["Rancho / Predio"].unique().tolist())
        with col_f2:
            df_filtered_rancho = df_all[df_all["Rancho / Predio"] == selected_rancho]
            selected_id_rancho = st.selectbox("Seleccionar Animal en este Rancho", df_filtered_rancho["ID Paciente"].unique().tolist())
            
        df_final_view = df_filtered_rancho[df_filtered_rancho["ID Paciente"] == selected_id_rancho]
        st.markdown(f"### Historial Clínico de **{selected_id_rancho}** (Predio: *{selected_rancho}*)")
        st.dataframe(df_final_view, use_container_width=True)
        
        if st.button("🗑️ Limpiar Todos los Registros de Sesión"):
            st.session_state['patient_records'] = []
            st.rerun()
    else:
        st.info("Aún no hay expedientes clínicos registrados en la sesión actual.")


# --- PESTAÑA 3: VADEMECUM MULTIESPECIE ---
with tab_drugs:
    st.subheader("💊 Vademecum Clínico y Calculadora de Dosificación Multiespecie")
    st.markdown("Catálogo ampliado de fármacos adaptado desde pequeños animales hasta grandes rumiantes y equinos.")
    
    drug_database = {
        "Oxitetraciclina L.A. (20%) [Antibiótico de amplio espectro]": {
            "dosis": 20.0, "unidad": "mg/kg", "concentracion": 200, "especies": "Bovinos, Ovinos, Porcinos", "via": "IM profunda / SC", "indicacion": "Infecciones respiratorias y sistémicas graves."
        },
        "Ceftiofur Clorhidrato [Cefalosporina 3ra Gen]": {
            "dosis": 2.2, "unidad": "mg/kg", "concentracion": 50, "especies": "Bovinos, Equinos, Caninos, Felinos", "via": "IM / SC", "indicacion": "Enfermedad respiratoria y pododermatitis."
        },
        "Enrofloxacina (10%) [Fluoroquinolona]": {
            "dosis": 5.0, "unidad": "mg/kg", "concentracion": 100, "especies": "Bovinos, Porcinos, Caninos, Felinos", "via": "SC / IM / IV lenta", "indicacion": "Infecciones urogenitales y digestivas complejas."
        },
        "Meloxicam (2%) [Antiinflamatorio no esteroideo]": {
            "dosis": 0.5, "unidad": "mg/kg", "concentracion": 20, "especies": "Bovinos, Equinos, Porcinos, Ovinos", "via": "IV / SC", "indicacion": "Control de dolor, inflamación y pirexia."
        },
        "Meloxicam (0.5% - Suspensión/Inyectable) [AINE Pequeñas Especies]": {
            "dosis": 0.2, "unidad": "mg/kg", "concentracion": 5, "especies": "Caninos, Felinos", "via": "SC / Oral", "indicacion": "Control de dolor osteoarticular y postquirúrgico."
        },
        "Flunixin Meglumine [Analgésico / Antitérmico]": {
            "dosis": 1.1, "unidad": "mg/kg", "concentracion": 50, "especies": "Bovinos, Equinos, Caninos", "via": "IV lenta / IM", "indicacion": "Cólico equino, dolor visceral y endotoxemia."
        },
        "Xylazine (2%) [Sedante / Miorrelajante]": {
            "dosis": 0.2, "unidad": "mg/kg", "concentracion": 20, "especies": "Bovinos, Equinos, Caninos, Felinos", "via": "IV / IM", "indicacion": "Sedación profunda y contención en campo."
        },
        "Ivermectina (1%) [Endectocida]": {
            "dosis": 0.2, "unidad": "mg/kg", "concentracion": 10, "especies": "Bovinos, Ovinos, Porcinos, Caninos", "via": "SC / Pour-on", "indicacion": "Control de parásitos gastrointestinales y ectoparásitos."
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
            f"⚖️ **Dosis estándar:** {drug_info['dosis']} {drug_info['unidad']}"
        )
    
    with col_d2:
        use_ai_weight = st.checkbox(f"Usar peso actual registrado en memoria ({st.session_state['last_estimated_weight']} kg)", value=True)
        animal_weight = st.session_state['last_estimated_weight'] if use_ai_weight else st.number_input("Ingrese peso manual (kg)", min_value=0.5, max_value=1500.0, value=25.0, step=0.5)
        
        if st.button("Calcular Dosis Total de Aplicación", type="primary"):
            total_mg = animal_weight * drug_info['dosis']
            total_ml = total_mg / drug_info['concentracion']
            st.session_state['last_drug_result'] = {
