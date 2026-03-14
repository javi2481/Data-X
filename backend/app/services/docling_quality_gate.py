from typing import Any

class DoclingQualityGate:
    def evaluate(self, conversion_result: dict[str, Any]) -> dict[str, Any]:
        """
        Evalúa la calidad de la conversión de Docling.
        Decide si el resultado es usable (pass/warn/fail).
        """
        status = "pass"
        warnings = []
        method = conversion_result.get("method", "unknown")
        confidence = conversion_result.get("confidence")
        
        # Lógica de evaluación basada en confianza si existe
        if confidence is not None:
            if confidence < 0.5:
                status = "fail"
                warnings.append(f"Confianza muy baja en la conversión ({confidence:.2f})")
            elif confidence < 0.8:
                status = "warn"
                warnings.append(f"Confianza moderada en la conversión ({confidence:.2f})")
        
        # Si no hay tablas extraídas y el método fue docling, podría ser un warning o fail
        if method == "docling" and not conversion_result.get("tables_found", True):
            status = "warn"
            warnings.append("No se detectaron tablas estructuradas claras en el documento")

        # Si se usó fallback, marcamos como warn por defecto si queremos avisar
        if method == "fallback":
            status = "warn"
            warnings.append("Se utilizó el motor de respaldo (pandas) en lugar del pipeline de Docling")

        return {
            "status": status,
            "confidence": confidence,
            "warnings": warnings,
            "method": method
        }
