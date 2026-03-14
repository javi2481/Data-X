from typing import Any

class DoclingQualityGate:
    def evaluate(self, conversion_result: dict[str, Any]) -> dict[str, Any]:
        """
        Evalúa la calidad de la conversión de Docling.
        Decide si el resultado es usable (accept/warning/reject).
        """
        status = "accept"
        warnings = []
        method = conversion_result.get("method", "unknown")
        confidence_raw = conversion_result.get("confidence")
        
        # Extraer valor numérico si es un objeto de confianza (Docling 2.x)
        confidence = 1.0
        if confidence_raw is not None:
            if hasattr(confidence_raw, "value"):
                confidence = float(confidence_raw.value)
            elif hasattr(confidence_raw, "score"):
                confidence = float(confidence_raw.score)
            else:
                try:
                    confidence = float(confidence_raw)
                except (ValueError, TypeError):
                    confidence = 0.95 # Valor por defecto razonable
        
        # Lógica de evaluación basada en confianza si existe
        if confidence_raw is not None:
            if confidence < 0.5:
                status = "reject"
                warnings.append(f"Confianza muy baja en la conversión ({confidence:.2f})")
            elif confidence < 0.8:
                status = "warning"
                warnings.append(f"Confianza moderada en la conversión ({confidence:.2f})")
        
        # Si no hay tablas extraídas y el método fue docling, podría ser un warning o reject
        if method == "docling" and not conversion_result.get("tables_found", True):
            status = "warning"
            warnings.append("No se detectaron tablas estructuradas claras en el documento")

        # Si se usó fallback, marcamos como warning por defecto si queremos avisar
        if method == "fallback":
            status = "warning"
            warnings.append("Se utilizó el motor de respaldo (pandas) en lugar del pipeline de Docling")

        return {
            "status": status,
            "confidence": confidence,
            "warnings": warnings,
            "method": method
        }
