class PacienteBovino:
    def __init__(self, arete, especie_tipo, etapa, peso_kg, propietario):
        self.arete = arete
        self.especie_tipo = especie_tipo  # "Carne" o "Leche"
        self.etapa = etapa  # "Ternero", "Vaca en Lactancia", "Engorda", etc.
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
        self.pacientes = {}
        
        # Base de datos de fármacos comunes en campo con concentración y costo unitario estimado por mL
        self.inventario_farmacos = {
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
                "volumen_fijo_ml": 500, # Manejo por volumen estándar para vacas adultas
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
        if arete in self.pacientes:
            return f"El paciente con arete {arete} ya está registrado."
        self.pacientes[arete] = PacienteBovino(arete, especie_tipo, etapa, peso_kg, propietario)
        return f"Paciente {arete} registrado exitosamente."

    def calcular_dosis_y_costo(self, peso_kg, key_farmaco):
        if key_farmaco not in self.inventario_farmacos:
            return None
        
        farmaco = self.inventario_farmacos[key_farmaco]
        
        # Cálculo matemático automatizado
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

    def diagnosticar_y_tratar(self, arete, fecha, sintomas, temperatura, fc, fr):
        if arete not in self.pacientes:
            return "Error: Paciente no encontrado. Registre el paciente primero."
        
        paciente = self.pacientes[arete]
        diagnostico = ""
        tratamiento_desc = ""
        farmacos_sugeridos = []
        pronostico = ""

        # --- MOTOR DE DIAGNÓSTICO SINDRÓMICO PARA CAMPO ---
        sintomas_lower = [s.lower() for s in sintomas]

        # 1. Síndrome Respiratorio (ERB / Neumonía)
        if "tos" in sintomas_lower or "descarga nasal" in sintomas_lower or fr > 35:
            diagnostico = "Enfermedad Respiratoria Bovina (ERB) / Neumonía de Campo"
            if temperatura > 39.5:
                farmacos_sugeridos = ["florfenicol", "flunixin"]
                tratamiento_desc = "Florfenicol + Flunixin Meglumine (AINE)."
                pronostico = "Reservado a Favorable (tratamiento temprano)."
            else:
                farmacos_sugeridos = ["oxitetraciclina_la"]
                tratamiento_desc = "Oxitetraciclina de Larga Acción (dosis única)."
                pronostico = "Favorable."

        # 2. Síndrome Entérico / Diarrea (Común en terneros)
        elif "diarrea" in sintomas_lower or "deshidratacion" in sintomas_lower:
            diagnostico = "Diarrea Neonatal / Enteritis Infecciosa"
            if paciente.etapa.lower() == "ternero":
                farmacos_sugeridos = ["sulfadiazina_trimetoprim"]
                tratamiento_desc = "Electrolitos orales + Sulfadiazina con Trimetoprim oral."
                pronostico = "Reservado (depende del grado de deshidratación)."
            else:
                farmacos_sugeridos = ["oxitetraciclina_la", "flunixin"]
                tratamiento_desc = "Rehidratación + Oxitetraciclina + AINEs."
                pronostico = "Favorable."

        # 3. Síndrome Metabólico / Hipocalcemia (Vacas lecheras en transición)
        elif "caida" in sintomas_lower or "hipotermia" in sintomas_lower or "inmovil" in sintomas_lower:
            diagnostico = "Fiebre de Leche (Hipocalcemia Clínica)"
            farmacos_sugeridos = ["calcio"]
            tratamiento_desc = "Gluconato de Calcio al 23% (IV lenta controlando frecuencia cardíaca)."
            pronostico = "Favorable si se aplica antes de las 24 horas de postración."

        # 4. Caso general por defecto
        else:
            diagnostico = "Síndrome Febril Inespecífico / Evaluación Adicional"
            farmacos_sugeridos = ["flunixin"]
            tratamiento_desc = "Antipirético (Flunixin) + Complejo Vitamínico B."
            pronostico = "Reservado."

        # Calcular dosis y costos automáticos para los fármacos seleccionados
        calculo_dosis_resultados = []
        for f_key in farmacos_sugeridos:
            res_dosis = self.calcular_dosis_y_costo(paciente.peso_kg, f_key)
            if res_dosis:
                calculo_dosis_resultados.append(res_dosis)

        # Guardar en el historial del paciente
        paciente.agregar_evento(fecha, sintomas, temperatura, fc, fr, diagnostico, tratamiento_desc, calculo_dosis_resultados, pronostico)

        return {
            "arete": arete,
            "etapa": paciente.etapa,
            "peso_kg": paciente.peso_kg,
            "diagnostico": diagnostico,
            "tratamiento_sugerido": tratamiento_desc,
            "calculo_dosis_y_costos": calculo_dosis_resultados,
            "pronostico": pronostico
        }


if __name__ == "__main__":
    # --- EJEMPLO DE USO ---
    app = SistemaClinicoCampo()

    # 1. Registrar una Vaca Lechera en transición con Hipocalcemia y 600 kg
    print(app.registrar_paciente("A-102", "Leche", "Vaca en Lactancia", 600, "Rancho El Trébol"))

    # 2. Diagnosticar en campo ingresando variables clínicas
    resultado = app.diagnosticar_y_tratar(
        arete="A-102",
        fecha="2026-10-06",
        sintomas=["caida", "inmovil", "hipotermia"],
        temperatura=37.8,
        fc=70,
        fr=24
    )

    print("\n--- REPORTE CLÍNICO Y DOSIFICACIÓN DE CAMPO ---")
    print(f"Arete: {resultado['arete']} | Etapa: {resultado['etapa']} | Peso: {resultado['peso_kg']} kg")
    print(f"Diagnóstico: {resultado['diagnostico']}")
    print(f"Tratamiento: {resultado['tratamiento_sugerido']}")
    print("\nCálculo Automatizado de Dosis e Inventario:")
    for item in resultado['calculo_dosis_y_costos']:
        print(f" - Fármaco: {item['farmaco']} (Vía: {item['via']})")
        print(f"   * Dosis Total: {item['dosis_total_mg']} mg")
        print(f"   * Volumen exacto a aplicar: {item['volumen_ml']} mL")
        print(f"   * Costo estimado: ${item['costo_estimado']} unidades")
    print(f"Pronóstico: {resultado['pronostico']}")
