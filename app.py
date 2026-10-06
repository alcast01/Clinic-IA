class PacienteBovino:
    def __init__(self, arete, especie_tipo, etapa, peso_kg, propietario):
        self.arete = arete
        self.especie_tipo = especie_tipo  # "Carne" o "Leche"
        self.etapa = etapa  # "Ternero", "Vaca en Lactancia", "Engorda", etc.
        self.peso_kg = peso_kg
        self.propietario = propietario
        self.historial = []

    def agregar_evento(self, fecha, sintomas, temperatura, fc, fr, diagnostico, tratamiento, pronostico):
        evento = {
            "fecha": fecha,
            "sintomas": sintomas,
            "temperatura": temperatura,
            "fc": fc,
            "fr": fr,
            "diagnostico": diagnostico,
            "tratamiento": tratamiento,
            "pronostico": pronostico
        }
        self.historial.append(evento)


class SistemaClinicoCampo:
    def __init__(self):
        self.pacientes = {}

    def registrar_paciente(self, arete, especie_tipo, etapa, peso_kg, propietario):
        if arete in self.pacientes:
            return f"El paciente con arete {arete} ya está registrado."
        self.pacientes[arete] = PacienteBovino(arete, especie_tipo, etapa, peso_kg, propietario)
        return f"Paciente {arete} registrado exitosamente."

    def diagnosticar_y_tratar(self, arete, fecha, sintomas, temperatura, fc, fr):
        if arete not in self.pacientes:
            return "Error: Paciente no encontrado. Registre el paciente primero."
        
        paciente = self.pacientes[arete]
        diagnostico = ""
        tratamiento = ""
        pronostico = ""

        # --- MOTOR DE DIAGNÓSTICO SINDRÓMICO PARA CAMPO ---
        sintomas_lower = [s.lower() for s in sintomas]

        # 1. Síndrome Respiratorio (ERB / Neumonía)
        if "tos" in sintomas_lower or "descarga nasal" in sintomas_lower or fr > 35:
            diagnostico = "Enfermedad Respiratoria Bovina (ERB) / Neumonía de Campo"
            if temperatura > 39.5:
                tratamiento = "Florfenicol (20 mg/kg IM) + Flunixin Meglumine (AINE, 2.2 mg/kg). Ajustar por costo: Oxitetraciclina de larga acción si el presupuesto es muy ajustado."
                pronostico = "Reservado a Favorable (si se trata en fase temprana)."
            else:
                tratamiento = "Oxitetraciclina LA (20 mg/kg IM dosis única) + Vitamina A+D+E."
                pronostico = "Favorable."

        # 2. Síndrome Entérico / Diarrea (Común en terneros)
        elif "diarrea" in sintomas_lower or "deshidratacion" in sintomas_lower:
            diagnostico = "Diarrea Neonatal / Enteritis Infecciosa"
            if paciente.etapa.lower() == "ternero":
                tratamiento = "Electrolitos orales (mínimo 4L/día) + Sulfadiazina con Trimetoprim oral o Gentamicina oral + Protector de mucosa (Caolín/Pectina)."
                pronostico = "Reservado (depende del grado de acidosis y debilidad)."
            else:
                tratamiento = "Rehidratación oral/IV + Probióticos ruminales + AINEs."
                pronostico = "Favorable."

        # 3. Síndrome Metabólico / Hipocalcemia (Vacas lecheras en transición)
        elif "caida" in sintomas_lower or "hipotermia" in sintomas_lower or "inmovil" in sintomas_lower:
            diagnostico = "Fiebre de Leche (Hipocalcemia Clínica)"
            tratamiento = "Gluconato de Calcio al 23% (500 ml IV lenta controlando frecuencia cardíaca) + Calcio subcutáneo/oral de soporte."
            pronostico = "Favorable si se aplica antes de las 24 horas de postración."

        # 4. Caso general por defecto
        else:
            diagnostico = "Síndrome Febril Inespecífico / Evaluación Adicional Requerida"
            tratamiento = "Pลงl. Antipirético (Dipirona o Flunixin) + Vitamínico estimulante del apetito (B-Complex)."
            pronostico = "Reservado."

        # Guardar en el historial del paciente
        paciente.agregar_evento(fecha, sintomas, temperatura, fc, fr, diagnostico, tratamiento, pronostico)

        return {
            "arete": arete,
            "etapa": paciente.etapa,
            "diagnostico": diagnostico,
            "tratamiento_sugerido": tratamiento,
            "pronostico": pronostico
        }


# --- EJEMPLO DE USO ---
app = SistemaClinicoCampo()

# 1. Registrar una Vaca Lechera en transición con Hipocalcemia
print(app.registrar_paciente("A-102", "Leche", "Vaca en Lactancia", 600, "Rancho El Trébol"))

# 2. Diagnosticar en campo ingresando variables clínicas
resultado = app.diagnosticar_y_tratar(
    arete="A-102",
    fecha="2026-10-06",
    sintomas=["caida", "inmovil", "hipotermia"],
    temperatura=37.8, # Típica baja en hipocalcemia
    fc=70,
    fr=24
)

print("\n--- REPORTE CLÍNICO DE CAMPO ---")
for k, v in resultado.items():
    print(f"{k.capitalize()}: {v}")
