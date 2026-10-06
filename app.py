import streamlit as st

# Configuración de la página optimizada para vista móvil
st.set_page_config(
    page_title="Diagnóstico Clínico de Campo",
    page_icon="🩺",
    layout="centered"
)

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
            alerts.append(f"⚠️️ **Temperatura alterada:** {temp} °C (Rango: {r['temp'][0]} - {r['temp'][1]} °C)")
        if not (r['hr'][0] <= hr <= r['hr'][1]):
            alerts.append(f"⚠️ **Frecuencia cardíaca alterada:** {hr} lpm (Rango: {r['hr'][0]} - {r['hr'][1]} lpm)")
        if not (r['rr'][0] <= rr <= r['rr'][1]):
            alerts.append(f"⚠️ **Frecuencia respiratoria alterada:** {rr} rpm (Rango: {r['rr'][0]} - {r['rr'][1]} rpm)")
            
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

# Interfaz de Usuario
st.title("🩺 Diagnóstico Clínico Veterinario")
st.markdown("Herramienta de apoyo en campo para evaluación de constantes y grado de deshidratación.")

with st.form("diagnostic_form"):
    st.subheader("1. Selección de Paciente")
    species_options = {
        "Bovino": "bovino",
        "Equino": "equino",
        "Porcino": "porcino",
        "Ovino / Borrego": "ovino"
    }
    selected_species_label = st.selectbox("Especie", list(species_options.keys()))
    species = species_options[selected_species_label]
    
    production_type = "general"
    if species == "bovino":
        prod_options = {"Leche": "leche", "Carne": "carne"}
        production_type = prod_options[st.selectbox("Propósito Zootécnico", list(prod_options.keys()))]

    st.subheader("2. Constantes Fisiológicas")
    col1, col2, col3 = st.columns(3)
    with col1:
        temp = st.number_input("Temp (°C)", min_value=30.0, max_value=45.0, value=38.5, step=0.1)
    with col2:
        hr = st.number_input("FC (lpm)", min_value=10, max_value=150, value=70, step=1)
    with col3:
        rr = st.number_input("FR (rpm)", min_value=5, max_value=120, value=20, step=1)

    st.subheader("3. Evaluación de Hidratación")
    skin_tent = st.slider("Tiempo de pliegue cutáneo (segundos)", min_value=0.0, max_value=10.0, value=1.0, step=0.5)
    mucosa = st.selectbox("Humedad de mucosas", ["Húmeda/Normal", "Pegajosa", "Seca"])
    eye_sunken = st.checkbox("Depresión del globo ocular (ojos hundidos)")

    submit_button = st.form_submit_button(label="Ejecutar Diagnóstico")

if submit_button:
    evaluator = FieldDiagnostics(species, production_type)
    
    st.divider()
    st.subheader("📋 Resultados del Análisis")
    
    # Evaluar constantes
    vitals_results = evaluator.evaluate_vitals(temp, hr, rr)
    st.markdown("### Constantes Fisiológicas")
    for alert in vitals_results:
        st.write(alert)
        
    # Evaluar deshidratación
    dehydration_result = evaluator.assess_dehydration(skin_tent, mucosa, eye_sunken)
    st.markdown("### Estado de Hidratación")
    st.write(dehydration_result)
