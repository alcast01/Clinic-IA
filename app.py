import streamlit as st
import numpy as np
from PIL import Image
import io

# --- CLASES DEL SISTEMA CLÍNICO DE CAMPO ---
class PacienteBovino:
    def __init__(self, arete, especie_tipo, etapa, peso_kg, propietario):
        self.arete = arete
        self.especie_tipo = especie_tipo  # "Carne" o "Leche"
        self.etapa = etapa  # "Ternero", "Recría", "Engorda", "Vaca en Lactancia"
        self.peso_kg = peso_kg
        self.propietario = propietario
        self.historial = []

    def agregar_evento(self, fecha, sintomas, temperatura, fc, fr, diagnostico, tratamiento, calculo_dosis, pronostico):
        evento = {
            "fecha": fecha,
            "sintomas": sintomas,
            "temperatura": temperatura,
            "fc": fc,
            "fr": fr,
            "diagnostico": diagnostico,
            "tratamiento": tratamiento,
            "calculo_dosis": calculo_dosis,
            "pronostico": pronostico
        }
        self.historial.append(evento)


class SistemaClinicoCampo:
    def __init__(self):
        if 'pacientes' not in st.session_state:
            st.session_state.pacientes = {}
        
        if 'inventario_farmacos' not in st.session_state:
            st.session_state.inventario_farmacos = {
                "florfenicol": {
                    "nombre": "Florfenicol 300 mg/mL (30%)",
                    "concentracion_mg_ml": 300,
                    "dosis_recomendada_mg_kg": 20,
                    "costo_por_ml": 3.50,
                    "via": "IM"
                },
                "oxitetraciclina_la": {
                    "nombre": "Oxitetraciclina L.A. 200 mg/mL",
                    "concentracion_mg_ml": 200,
                    "dosis_recomendada_mg_kg": 20,
                    "costo_por_ml": 1.20,
                    "via": "IM / SC"
                },
                "flunixin": {
                    "nombre": "Flunixin Meglumine 50 mg/mL",
                    "concentracion_mg_ml": 50,
                    "dosis_recomendada_mg_kg": 2.2,
                    "costo_por_ml": 4.00,
                    "via": "IV / IM"
                },
                "calcio": {
                    "nombre": "Gluconato de Calcio 23%",
                    "concentracion_mg_ml": 230,
                    "volumen_fijo_ml": 500,
                    "costo_por_ml": 0.45,
                    "via": "IV lenta"
                },
                "sulfadiazina_trimetoprim": {
                    "nombre": "Sulfadiazina + Trimetoprim",
                    "concentracion_mg_ml": 240,
                    "dosis_recomendada_mg_kg": 24,
                    "costo_por_ml": 1.80,
                    "via": "Oral / IM"
                }
            }

    def registrar_paciente(self, arete, especie_tipo, etapa, peso_kg, propietario):
        if arete in st.session_state.pacientes:
            return False, f"El paciente con arete {arete} ya está registrado."
        st.session_state.pacientes[arete] = PacienteBovino(arete, especie_tipo, etapa, peso_kg, propietario)
        return True, f"Paciente {arete} registrado exitosamente."

    def calcular_dosis_y_costo(self, peso_kg, key_farmaco):
        if key_farmaco not in st.session_state.inventario_farmacos:
            return None
        
        farmaco = st.session_state.inventario_farmacos[key_farmaco]
        
        if "volumen_fijo_ml" in farmaco:
            volumen_ml = farmaco["volumen_fijo_ml"]
            dosis_total_mg = volumen_ml * farmaco["concentracion_mg_ml"]
        else:
            dosis_total_mg = peso_kg * farmaco["dosis_recomendada_mg_kg"]
            volumen_ml = dosis_total_mg / farmaco["concentracion_mg_ml"]
            
        costo_total = volumen_ml * farmaco["costo_por_ml"]
        
        return {
            "farmaco": farmaco["nombre"],
            "via": farmaco["via"],
            "dosis_total_mg": round(dosis_total_mg, 2),
            "volumen_ml": round(volumen_ml, 2),
            "costo_estimado": round(costo_total, 2)
        }

    def estimar_peso_por_imagen(self, imagen_bytes, etapa_bovino):
        """
        Función de visión artificial en campo: procesa la foto lateral del bovino 
        para estimar su biomasa y evitar sub- o sobredosificación de fármacos.
        """
        img = Image.open(imagen_bytes).convert("L")
        arr = np.array(img)
        altura_px, ancho_px = arr.shape
        
        factores_etapa = {
            "Ternero": 0.35,
            "Recría": 0.85,
            "Engorda": 1.45,
            "Vaca en Lactancia": 1.60
        }
        factor = factores_etapa.get(etapa_bovino, 1.0)
        pixel_density = np.mean(arr < 200)
        peso_estimado = (ancho_px * altura_px / 15000) * factor * (0.8 + 0.4 * pixel_density)
        
        if etapa_bovino == "Ternero":
            peso_estimado = max(35.0, min(140.0, peso_estimado))
        elif etapa_bovino == "Vaca en Lactancia":
            peso_estimado = max(400.0, min(800.0, peso_estimado))
        elif etapa_bovino == "Engorda":
            peso_estimado = max(250.0, min(650.0, peso_estimado))
        else:
            peso_estimado = max(150.0, min(450.0, peso_estimado))
            
        return round(peso_estimado, 2)

# --- CONFIGURACIÓN DE LA INTERFAZ STREAMLIT ---
st.set_page_config(page_title="Sistema Clínico Bovino de Campo", page_icon="🐄", layout="wide")

sistema = SistemaClinicoCampo()

st.title("🐄 Sistema Clínico Veterinario de Campo (CDSS Bovinos)")
st.markdown("Herramienta de diagnóstico sindrómico, cálculo exacto de dosis por peso (evitando sub/sobredosificación) y gestión de inventario para condiciones restrictivas.")

tab_registro, tab_peso_foto, tab_diagnostico, tab_farmacos, tab_historial = st.tabs([
    "📋 Registro de Pacientes", 
    "📸 Estimación Peso (Foto)", 
    "🩺 Diagnóstico y Dosis", 
    "💊 Fármacos e Inventario", 
    "📜 Historial Clínico"
])

with tab_registro:
    st.header("Registro de Nuevo Paciente Bovino")
    col1, col2 = st.columns(2)
    with col1:
        reg_arete = st.text_input("Número de Arete / Identificación")
        reg_especie = st.selectbox("Propósito Productivo", ["Carne", "Leche"])
        reg_etapa = st.selectbox("Etapa Fisiológica", ["Ternero", "Recría", "Engorda", "Vaca en Lactancia"])
    with col2:
        reg_peso = st.number_input("Peso Vivo Estimado / Real (kg)", min_value=20.0, max_value=1200.0, value=450.0, step=10.0)
        reg_propietario = st.text_input("Nombre del Propietario / Rancho")
        
    if st.button("Registrar Paciente"):
        if reg_arete.strip() == "":
            st.error("Por favor ingrese un número de arete válido.")
        else:
            success, msg = sistema.registrar_paciente(reg_arete, reg_especie, reg_etapa, reg_peso, reg_propietario)
            if success:
                st.success(msg)
            else:
                st.warning(msg)

with tab_peso_foto:
    st.header("📸 Estimación de Peso por Fotografía en Campo")
    st.markdown("Tome o suba una fotografía lateral del bovino para calcular automáticamente su peso y evitar errores críticos de subdosificación o intoxicación por sobredosis.")
    
    col_foto1, col_foto2 = st.columns(2)
    with col_foto1:
        etapa_foto = st.selectbox("Seleccione la Etapa del Animal para Calibrar el Algoritmo", ["Ternero", "Recría", "Engorda", "Vaca en Lactancia"], key="etapa_foto_sel")
        tipo_captura = st.radio("Método de captura", ["Tomar con Cámara", "Subir Imagen"])
        
        imagen_cargada = None
        if tipo_captura == "Tomar con Cámara":
            imagen_cargada = st.camera_input("Capturar foto lateral del bovino")
        else:
            imagen_cargada = st.file_uploader("Subir archivo de imagen (JPG/PNG)", type=["jpg", "jpeg", "png"])
            
    with col_foto2:
        if imagen_cargada is not None:
            st.image(imagen_cargada, caption="Fotografía del Paciente en Campo", use_column_width=True)
            if st.button("Calcular Peso por Visión Artificial"):
                peso_calculado = sistema.estimar_peso_por_imagen(imagen_cargada, etapa_foto)
                st.success(f"⚖️ Peso Estimado por Fotografía: **{peso_calculado} kg**")
                st.info("💡 Consejo clínico: Puede usar este valor directamente en la pestaña de Diagnóstico y Dosis para garantizar la precisión farmacológica.")
        else:
            st.info("Capture o cargue una imagen para habilitar el análisis morfométrico.")

with tab_diagnostico:
    st.header("🩺 Motor de Diagnóstico Sindrómico y Dosificación")
    
    if not st.session_state.pacientes:
        st.warning("No hay pacientes registrados. Por favor registre al menos un animal en la pestaña 'Registro de Pacientes'.")
    else:
        lista_aretes = list(st.session_state.pacientes.keys())
        diag_arete = st.selectbox("Seleccione el Paciente (Arete)", lista_aretes)
        paciente_actual = st.session_state.pacientes[diag_arete]
        
        st.write(f"**Propietario:** {paciente_actual.propietario} | **Etapa:** {paciente_actual.etapa} | **Peso Registrado:** {paciente_actual.peso_kg} kg")
        
        col_d1, col_d2, col_d3 = st.columns(3)
        with col_d1:
            diag_fecha = st.date_input("Fecha de Visita")
            diag_temp = st.number_input("Temperatura (°C)", min_value=35.0, max_value=43.0, value=39.0, step=0.1)
        with col_d2:
            diag_fc = st.number_input("Frecuencia Cardíaca (lpm)", min_value=30, max_value=120, value=65)
            diag_fr = st.number_input("Frecuencia Respiratoria (rpm)", min_value=10, max_value=80, value=24)
        with col_d3:
            sintomas_opciones = ["Tos", "Descarga nasal", "Diarrea", "Deshidratación", "Caída / Postración", "Inmóvil", "Hipotermia", "Fiebre alta", "Timpanismo"]
            diag_sintomas = st.multiselect("Signos Clínicos Observados en Campo", sintomas_opciones)
            
        if st.button("Ejecutar Diagnóstico y Calcular Tratamiento"):
            sintomas_lower = [s.lower() for s in diag_sintomas]
            diagnostico = ""
            tratamiento_desc = ""
            farmacos_sugeridos = []
            pronostico = ""
            
            if "tos" in sintomas_lower or "descarga nasal" in sintomas_lower or diag_fr > 35:
                diagnostico = "Enfermedad Respiratoria Bovina (ERB) / Neumonía"
                if diag_temp > 39.5:
                    farmacos_sugeridos = ["florfenicol", "flunixin"]
                    tratamiento_desc = "Florfenicol + Flunixin Meglumine (AINE)."
                    pronostico = "Reservado a Favorable (tratamiento temprano)."
                else:
                    farmacos_sugeridos = ["oxitetraciclina_la"]
                    tratamiento_desc = "Oxitetraciclina de Larga Acción (dosis única)."
                    pronostico = "Favorable."
            elif "diarrea" in sintomas_lower or "deshidratacion" in sintomas_lower:
                diagnostico = "Diarrea Neonatal / Enteritis Infecciosa"
                if paciente_actual.etapa.lower() == "ternero":
                    farmacos_sugeridos = ["sulfadiazina_trimetoprim"]
                    tratamiento_desc = "Electrolitos orales + Sulfadiazina con Trimetoprim."
                    pronostico = "Reservado."
                else:
                    farmacos_sugeridos = ["oxitetraciclina_la", "flunixin"]
                    tratamiento_desc = "Rehidratación + Oxitetraciclina + AINEs."
                    pronostico = "Favorable."
            elif "caída / postración" in sintomas_lower or "hipotermia" in sintomas_lower or "inmóvil" in sintomas_lower:
                diagnostico = "Fiebre de Leche (Hipocalcemia Clínica)"
                farmacos_sugeridos = ["calcio"]
                tratamiento_desc = "Gluconato de Calcio al 23% (IV lenta controlando FC)."
                pronostico = "Favorable si se aplica antes de 24 horas."
            else:
                diagnostico = "Síndrome Febril Inespecífico / Evaluación Adicional"
                farmacos_sugeridos = ["flunixin"]
                tratamiento_desc = "Antipirético (Flunixin) + Complejo Vitamínico B."
                pronostico = "Reservado."
                
            calculo_dosis_resultados = []
            for f_key in farmacos_sugeridos:
                res_dosis = sistema.calcular_dosis_y_costo(paciente_actual.peso_kg, f_key)
                if res_dosis:
                    calculo_dosis_resultados.append(res_dosis)
                    
            paciente_actual.agregar_evento(str(diag_fecha), diag_sintomas, diag_temp, diag_fc, diag_fr, diagnostico, tratamiento_desc, calculo_dosis_resultados, pronostico)
            
            st.success("¡Diagnóstico generado y guardado en el historial del paciente!")
            st.markdown(f"### 📋 Reporte Clínico")
            st.write(f"**Diagnóstico:** {diagnostico}")
            st.write(f"**Tratamiento Sugerido:** {tratamiento_desc}")
            st.write(f"**Pronóstico:** {pronostico}")
            
            st.markdown("### 🧮 Dosificación Exacta y Costos para el Rancho")
            for item in calculo_dosis_resultados:
                st.info(f"**Fármaco:** {item['farmaco']} (Vía: {item['via']})\n\n"
                        f"- Dosis Total: **{item['dosis_total_mg']} mg**\n"
                        f"- Volumen a Aplicar: **{item['volumen_ml']} mL**\n"
                        f"- Costo Estimado
