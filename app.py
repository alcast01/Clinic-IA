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
if 'appointments' not in st.session_state:
    st.session_state['appointments'] = []

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
# PESTAÑAS PRINCIPALES (6 SECCIONES)
# ==========================================
tab_diag, tab_reg, tab
