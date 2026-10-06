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
            alerts.append(f"Temperatura corporal alterada: {temp} °C (Rango: {r['temp'][0]} - {r['temp'][1]} °C)")
        if not (r['hr'][0] <= hr <= r['hr'][1]):
            alerts.append(f"Frecuencia cardiaca alterada: {hr} lpm (Rango: {r['hr'][0]} - {r['hr'][1]} lpm)")
        if not (r['rr'][0] <= rr <= r['rr'][1]):
            alerts.append(f"Frecuencia respiratoria alterada: {rr} rpm (Rango: {r['rr'][0]} - {r['rr'][1]} rpm)")
            
        return alerts if alerts else ["Constantes fisiológicas dentro de parámetros normales."]

    def assess_dehydration(self, skin_tent_seconds, mucous_membrane_status, eye_sunken_bool):
        score = 0
        if skin_tent_seconds > 5:
            score += 3
        elif skin_tent_seconds > 2:
            score += 2
        elif skin_tent_seconds > 1:
            score += 1
            
        if mucous_membrane_status == 'seca':
            score += 2
        elif mucous_membrane_status == 'pegajosa':
            score += 1
            
        if eye_sunken_bool:
            score += 2
            
        if score >= 5:
            return "Deshidratación severa (> 8-10%). Urgente: Fluidoterapia intravenosa."
        elif score >= 3:
            return "Deshidratación moderada (6-8%)."
        elif score >= 1:
            return "Deshidratación leve (4-6%)."
        return "Estado de hidratación normal (< 4%)."
