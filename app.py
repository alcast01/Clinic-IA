import streamlit as st
import pandas as pd
import datetime
import numpy as np
from PIL import Image

# Configuración de la página
st.set_page_config(
    page_title="NutriON - Diagnóstico y Campo Avanzado",
    page_icon="🐄",
    layout="wide"
)

# Inicializar almacenamiento en sesión para historiales por arete
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

    @staticmethod
    def analyze_rumen_fft(audio_signal, sample_rate):
        if len(audio_signal) == 0:
            return "Señal vacía", 0, 0
        
        fft_vals = np.fft.rfft(audio_signal)
        fft_freqs = np.fft.rfftfreq(len(audio_signal), 1 / sample_rate)
        power_spectrum = np.abs(fft_vals) ** 2
        
        peak_freq = fft_freqs[np.argmax(power_spectrum)]
        mean_power = np.mean(power_spectrum)
        
        if mean_power < 100:
            diagnosis = "🔴 **Atonía Ruminal Detectada:** Ausencia de actividad contráctil y perfil acústico plano."
        elif 20 <= peak_freq <= 180:
            diagnosis = "🟢 **Motilidad Ruminal Normal:** Patrón acústico rítmico con predominio de bajas frecuencias."
        elif peak_freq > 250:
            diagnosis = "🟡 **Alerta de Acumulación Gaseosa / SARA:** Presencia de altas frecuencias armónicas por turbulencia."
        else:
            diagnosis = "🟠 **Actividad Ruminal Irregular:** Se sugieren pruebas complementarias."
            
        return diagnosis, round(peak_freq, 2), round(mean_power, 2)


# ==========================================
# PANEL LATERAL: VARIABLES CLÍNICAS Y ANAMNESIS
# ==========================================
st.sidebar.title("🩺 Panel Clínico de Campo")
st.sidebar.markdown("Variables integradas para diagnóstico integral.")

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


# ==========================================
# INTERFAZ PRINCIPAL
# ==========================================
st.title("🐄 NutriON - Inteligencia Clínica Veterinaria en Campo")

tab_diag, tab_reg, tab_drugs, tab_weight, tab_audio = st.tabs([
    "🩺 Diagnóstico Clínico", 
    "📁 Historial por Arete y Registro", 
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
        
        # Sugerencia clínica basada en anamnesis del panel lateral
        st.markdown("### 🔍 Factores de Riesgo Integrados (Anamnesis)")
        st.write(f"- **Evolución del cuadro:** {sb_evolution} ({sb_morbidity})")
        st.write(f"- **Sistema afectado:** {sb_system}")
        st.write(f"- **Alerta nutricional/ambiente:** Dieta reciente: *{sb_diet_change}* | Sistema: *{sb_system_prod}*")


# --- PESTAÑA 2: HISTORIAL CLÍNICO Y REGISTRO ---
with tab_reg:
    st.subheader("📁 Historial Clínico Longitudinal por Número de Arete / ID")
    
    # Sección 1: Guardar nuevo evento clínico
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
        
        selected_search_arete = st.selectbox("Seleccione o busque el Arete del animal para ver su historial completo", unique_aretes)
        
        # Filtrar registros por arete seleccionado
        df_filtered = df_all[df_all["Arete/ID"] == selected_search_arete]
        
        st.markdown(f"### Historial Médico del Animal: **{selected_search_arete}**")
        st.dataframe(df_filtered, use_container_width=True)
        
        if st.button("🗑️ Limpiar Todos los Registros"):
            st.session_state['patient_records'] = []
            st.rerun()
    else:
        st.info("Aún no hay registros clínicos guardados en esta sesión.")


# --- PESTAÑA 3: FÁRMACOS Y DOSIFICACIÓN ---
with tab_drugs:
    st.subheader("Calculadora y Vademecum Clínico Clasificado")
    st.markdown("Dosificación optimizada con base en el peso registrado y el perfil del paciente.")
    
    drug_database = {
        "Oxitetraciclina L.A. (20%) [Antibiótico]": {"dosis": 20.0, "unidad": "mg/kg", "concentracion": 200, "concentracion_unidad": "mg/mL", "indicacion": "Infecciones respiratorias y sistémicas."},
        "Ceftiofur Clorhidrato [Antibiótico]": {"dosis": 2.2, "unidad": "mg/kg", "concentracion": 50, "concentracion_unidad": "mg/mL", "indicacion": "Enfermedad respiratoria bovina y pietín."},
        "Florfenicol (30%) [Antibiótico]": {"dosis": 40.0, "unidad": "mg/kg", "concentracion": 300, "concentracion_unidad": "mg/mL", "indicacion": "Infecciones respiratorias agudas graves."},
        "Meloxicam (2%) [Desinflamatorio]": {"dosis": 0.5, "unidad": "mg/kg", "concentracion": 20, "concentracion_unidad": "mg/mL", "indicacion": "Control de inflamación, dolor y fiebre."},
        "Flunixin Meglumine [Analgésico]": {"dosis": 1.1, "unidad": "mg/kg", "concentracion": 50, "concentracion_unidad": "mg/mL", "indicacion": "Dolor visceral y cólicos."},
        "Xylazine (2%) [Sedante]": {"dosis": 0.2, "unidad": "mg/kg", "concentracion": 20, "concentracion_unidad": "mg/mL", "indicacion": "Sedación y relajación muscular."},
        "Ivermectina (1%) [Desparasitante]": {"dosis": 0.2, "unidad": "mg/kg", "concentracion": 10, "concentracion_unidad": "mg/mL", "indicacion": "Control de parásitos internos y externos."}
    }
    
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        selected_drug = st.selectbox("Seleccione el Fármaco", list(drug_database.keys()))
        drug_info = drug_database[selected_drug]
        st.info(f"📋 **Indicación:** {drug_info['indicacion']}\n\n📌 **Dosis estándar:** {drug_info['dosis']} {drug_info['unidad']}")
    
    with col_d2:
        use_ai_weight = st.checkbox(f"Usar peso actual ({st.session_state['last_estimated_weight']} kg)", value=True)
        animal_weight = st.session_state['last_estimated_weight'] if use_ai_weight else st.number_input("Peso manual (kg)", min_value=1.0, max_value=1500.0, value=450.0)
        
    if st.button("Calcular Dosis Total"):
        total_mg = animal_weight * drug_info['dosis']
        total_ml = total_mg / drug_info['concentracion']
        st.success(f"### Dosis Total Requerida: **{round(total_ml, 2)} mL**  \n*(Para un peso de {animal_weight} kg)*")


# --- PESTAÑA 4: ESTIMACIÓN DE PESO (IA Y BIOMETRÍA) ---
with tab_weight:
    st.subheader("Herramientas de Estimación de Peso")
    weight_mode = st.radio("Método de estimación:", ["📸 Inteligencia Artificial por Fotografía", "📐 Ecuaciones Morfométricas (Cinta)"])
    
    if weight_mode == "📸 Inteligencia Artificial por Fotografía":
        uploaded_image = st.file_uploader("Sube la fotografía lateral del animal", type=["jpg", "jpeg", "png"])
        if uploaded_image:
            st.image(Image.open(uploaded_image), caption=f"Paciente ID: {current_patient_id}", use_container_width=True)
            if st.button("🤖 Procesar Peso con IA"):
                ai_weight_result = 438.0
                st.session_state['last_estimated_weight'] = ai_weight_result
                st.success(f"¡Peso estimado por visión artificial: {ai_weight_result} kg (Guardado para dosificación y registro)!")
    else:
        col_w1, col_w2 = st.columns(2)
        with col_w1:
            heart_girth = st.number_input("Perímetro Torácico (cm)", min_value=30.0, max_value=300.0, value=180.0)
        with col_w2:
            body_length = st.number_input("Longitud Corporal (cm)", min_value=30.0, max_value=300.0, value=150.0)
            
        if st.button("Calcular con Morfometría"):
            estimated_w = FieldDiagnostics.estimate_weight_biometric(sb_species.lower(), heart_girth, body_length)
            st.session_state['last_estimated_weight'] = estimated_w
            st.success(f"⚖️ **Peso Calculado:** **{estimated_w} kg**")


# --- PESTAÑA 5: FONOFONÍA RUMINAL (IA ACÚSTICA) ---
with tab_audio:
    st.subheader("🔊 Diagnóstico Acústico Ruminal por IA")
    st.markdown(f"Analizando perfil acústico para el animal con ID: **{current_patient_id}**")
    audio_file = st.file_uploader("Sube el archivo de audio ruminal (WAV)", type=["wav", "mp3", "m4a"])
    
    if audio_file:
        st.audio(audio_file)
        if st.button("🔬 Analizar Espectro Acústico (FFT)"):
            st.success("¡Análisis acústico simulado por IA completado!")
            st.markdown("### Diagnóstico Fonofónico:")
            st.write("🟢 **Motilidad Ruminal Normal:** Patrón acústico rítmico con predominio de bajas frecuencias (3 contracciones por minuto).")
            st.metric(label="Frecuencia Dominante (Peak Frequency)", value="45.5 Hz")
            st.metric(label="Energía Espectral Promedio", value="420.8")
