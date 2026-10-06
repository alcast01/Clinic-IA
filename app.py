import streamlit as st
import pandas as pd
import datetime

# Configuración de la página
st.set_page_config(
    page_title="NutriON - Diagnóstico y Campo",
    page_icon="🐄",
    layout="wide"
)

# Inicializar almacenamiento en sesión para pacientes registrados
if 'patient_records' not in st.session_state:
    st.session_state['patient_records'] = []

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
            alerts.append(f"⚠️️ **Frecuencia respiratoria alterada:** {rr} rpm (Rango: {r['rr'][0]} - {r['rr'][1]} rpm)")
            
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
        # Modelos predictivos biométricos por regresión geométrica
        if species == "bovino":
            # Fórmula de Crevat / Schaeffer modificada para bovinos (Resultado en kg)
            weight = (heart_girth ** 2 * body_length) / 10840
        elif species == "equino":
            # Fórmula de Murlin para equinos
            weight = (heart_girth ** 2 * body_length) / 11877
        elif species == "porcino":
            weight = (heart_girth ** 2 * body_length) / 14200
        else: # Ovino
            weight = (heart_girth ** 2 * body_length) / 10000
        return round(weight, 2)

# Interfaz Principal con Pestañas
st.title("🐄 NutriON - Módulo Clínico de Campo")

tab_diag, tab_reg, tab_drugs, tab_weight = st.tabs([
    "🩺 Diagnóstico Clínico", 
    "📁 Registro de Pacientes", 
    "💊 Fármacos y Dosificación", 
    "⚖️ Estimación de Peso (IA)"
])

# --- PESTAÑA 1: DIAGNÓSTICO CLÍNICO ---
with tab_diag:
    st.subheader("Evaluación de Constantes y Estado Hídrico")
    
    with st.form("diagnostic_form"):
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            species_options = {"Bovino": "bovino", "Equino": "equino", "Porcino": "porcino", "Ovino / Borrego": "ovino"}
            selected_species_label = st.selectbox("Especie", list(species_options.keys()), key="diag_species")
            species = species_options[selected_species_label]
        with col_s2:
            production_type = "general"
            if species == "bovino":
                prod_options = {"Leche": "leche", "Carne": "carne"}
                production_type = prod_options[st.selectbox("Propósito Zootécnico", list(prod_options.keys()))]

        st.markdown("---")
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

        submit_button = st.form_submit_button(label="Ejecutar Diagnóstico")

    if submit_button:
        evaluator = FieldDiagnostics(species, production_type)
        st.divider()
        st.subheader("📋 Resultados del Análisis")
        
        vitals_results = evaluator.evaluate_vitals(temp, hr, rr)
        st.markdown("### Constantes Fisiológicas")
        for alert in vitals_results:
            st.write(alert)
            
        dehydration_result = evaluator.assess_dehydration(skin_tent, mucosa, eye_sunken)
        st.markdown("### Estado de Hidratación")
        st.write(dehydration_result)

# --- PESTAÑA 2: REGISTRO DE PACIENTES ---
with tab_reg:
    st.subheader("Bitácora de Pacientes en Campo")
    
    with st.form("patient_form"):
        col1, col2 = st.columns(2)
        with col1:
            patient_id = st.text_input("Identificación del Animal (Arete / Nombre)")
            reg_species = st.selectbox("Especie", ["Bovino", "Equino", "Porcino", "Ovino"], key="reg_sp")
        with col2:
            estimated_weight = st.number_input("Peso Estimado / Real (kg)", min_value=1.0, max_value=1500.0, value=400.0)
            clinical_notes = st.text_area("Observaciones Clínicas / Diagnóstico preliminar")
            
        save_btn = st.form_submit_button("Guardar en el Registro de la Sesión")
        
        if save_btn:
            if patient_id:
                record = {
                    "Fecha": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "Arete/ID": patient_id,
                    "Especie": reg_species,
                    "Peso (kg)": estimated_weight,
                    "Notas": clinical_notes
                }
                st.session_state['patient_records'].append(record)
                st.success(f"¡Paciente {patient_id} registrado exitosamente!")
            else:
                st.warning("Por favor ingresa un identificador válido para el paciente.")

    if st.session_state['patient_records']:
        st.markdown("### Pacientes Registrados en la Visita Actual")
        df_patients = pd.DataFrame(st.session_state['patient_records'])
        st.dataframe(df_patients, use_container_width=True)
        
        if st.button("Limpiar Registro"):
            st.session_state['patient_records'] = []
            st.rerun()

# --- PESTAÑA 3: FÁRMACOS Y DOSIFICACIÓN ---
with tab_drugs:
    st.subheader("Calculadora de Dosificación de Fármacos")
    
    drug_database = {
        "Oxitetraciclina L.A. (20%)": {"dosis": 20.0, "unidad": "mg/kg", "concentracion": 200, "concentracion_unidad": "mg/mL"},
        "Meloxicam (2%)": {"dosis": 0.5, "unidad": "mg/kg", "concentracion": 20, "concentracion_unidad": "mg/mL"},
        "Ivermectina (1%)": {"dosis": 0.2, "unidad": "mg/kg", "concentracion": 10, "concentracion_unidad": "mg/mL"},
        "Ceftiofur": {"dosis": 2.2, "unidad": "mg/kg", "concentracion": 50, "concentracion_unidad": "mg/mL"}
    }
    
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        selected_drug = st.selectbox("Seleccione el Fármaco", list(drug_database.keys()))
        drug_info = drug_database[selected_drug]
        st.info(f"Dosis estándar recomendada: **{drug_info['dosis']} {drug_info['unidad']}**\n\nConcentración del producto: **{drug_info['concentracion']} {drug_info['concentracion_unidad']}**")
    
    with col_d2:
        animal_weight = st.number_input("Peso del animal para cálculo (kg)", min_value=1.0, max_value=1500.0, value=450.0, step=10.0)
        
    if st.button("Calcular Dosis Total"):
        total_mg = animal_weight * drug_info['dosis']
        total_ml = total_mg / drug_info['concentracion']
        st.success(f"### Dosis Total Requerida: **{round(total_ml, 2)} mL**  \n*(Equivalente a {total_mg} mg totales)*")

# --- PESTAÑA 4: ESTIMACIÓN DE PESO (IA / BIOMETRÍA) ---
with tab_weight:
    st.subheader("Módulo de Estimación Predictiva de Peso por Morfometría")
    st.markdown("Utiliza ecuaciones de regresión biométrica para calcular el peso vivo en campo midiendo el perímetro torácico y la longitud corporal.")
    
    col_w1, col_w2 = st.columns(2)
    with col_w1:
        w_species_label = st.selectbox("Especie", ["Bovino", "Equino", "Porcino", "Ovino"], key="weight_sp")
        w_species_map = {"Bovino": "bovino", "Equino": "equino", "Porcino": "porcino", "Ovino": "ovino"}
        w_species = w_species_map[w_species_label]
        
    with col_w2:
        heart_girth = st.number_input("Perímetro Torácico (cm)", min_value=30.0, max_value=300.0, value=180.0, step=1.0)
        body_length = st.number_input("Longitud Corporal (cm)", min_value=30.0, max_value=300.0, value=150.0, step=1.0)
        
    if st.button("Estimar Peso con Algoritmo Predictivo"):
        estimated_w = FieldDiagnostics.estimate_weight_biometric(w_species, heart_girth, body_length)
        st.success(f"⚖️ **Peso Estimado Calculado:** **{estimated_w} kg**")
        st.caption("Nota: El cálculo utiliza modelos matemáticos estándar de estimación morfométrica adaptados para optimizar el manejo zootécnico en campo.")
