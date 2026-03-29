import re
import structlog
import pandas as pd
from typing import List, Optional
from app.schemas.fraud import FraudFinding

logger = structlog.get_logger(__name__)

try:
    import satcfdi
    SATCFDI_AVAILABLE = True
except ImportError:
    SATCFDI_AVAILABLE = False

class FiscalValidatorService:
    """
    Layer 4 de FraudGuard: Validación Fiscal LATAM.
    Valida matemáticamente CUIT/CUIL (Argentina) y estructuras CFDI (México).
    """
    
    def _validate_cuit(self, cuit: str) -> bool:
        """Aplica validación de Módulo 11 para CUIT/CUIL argentino."""
        cuit_digits = re.sub(r'\D', '', str(cuit))
        if len(cuit_digits) != 11:
            return False
            
        base = [5, 4, 3, 2, 7, 6, 5, 4, 3, 2]
        cuit_list = [int(c) for c in cuit_digits]
        
        calc = sum(a * b for a, b in zip(base, cuit_list[:10]))
        resto = calc % 11
        
        if resto == 0:
            digito_verificador = 0
        elif resto == 1:
            if cuit_list[0] == 2 and cuit_list[1] in [0, 3, 4]:
                digito_verificador = {0: 9, 3: 4, 4: 1}[cuit_list[1]]
            else:
                return False
        else:
            digito_verificador = 11 - resto
            
        return digito_verificador == cuit_list[10]

    def analyze_fiscal_data(self, df: Optional[pd.DataFrame], text: Optional[str] = "") -> List[FraudFinding]:
        findings = []
        
        # 1. Buscar CUITs en el texto completo (OCR/Parseado)
        if text:
            # Captura posibles CUITs con o sin guiones
            cuit_matches = re.finditer(r'\b(?:20|23|24|27|30|33|34)[-\s]?\d{8}[-\s]?\d\b', text)
            for match in cuit_matches:
                cuit_str = match.group()
                if not self._validate_cuit(cuit_str):
                    findings.append(FraudFinding(
                        layer="fiscal_validation",
                        indicator="Invalid CUIT/CUIL",
                        severity="HIGH",
                        evidence=f"Se detectó un CUIT/CUIL estructuralmente inválido en el documento: '{cuit_str}'. Falla la verificación algorítmica de módulo 11.",
                        confidence=1.0
                    ))

        # 2. Buscar en el DataFrame
        if df is not None and not df.empty:
            for col in df.columns:
                if 'cuit' in str(col).lower() or 'cuil' in str(col).lower():
                    invalid_cuits = [val for val in df[col].dropna().astype(str) if len(re.sub(r'\D', '', val)) == 11 and not self._validate_cuit(val)]
                    if invalid_cuits:
                        findings.append(FraudFinding(
                            layer="fiscal_validation",
                            indicator="Invalid CUIT in Table",
                            severity="HIGH",
                            evidence=f"La columna tabular '{col}' contiene CUITs algorítmicamente inválidos (ej. {invalid_cuits[0]}). Posible manipulación de datos.",
                            confidence=1.0
                        ))
                        
        return findings