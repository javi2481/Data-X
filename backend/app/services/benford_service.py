import pandas as pd
import numpy as np
from scipy.stats import chisquare
import structlog
from typing import List, Optional
from app.schemas.fraud import FraudFinding

logger = structlog.get_logger(__name__)

try:
    import benford as bf
    BENFORD_AVAILABLE = True
except ImportError:
    BENFORD_AVAILABLE = False

class BenfordService:
    """
    Layer 3 de FraudGuard: Análisis Numérico y Semántico.
    Aplica la Ley de Benford a columnas financieras para detectar anomalías o números fabricados.
    """
    def analyze_benford(self, df: pd.DataFrame, financial_columns: Optional[List[str]] = None) -> List[FraudFinding]:
        findings = []
        if df is None or df.empty:
            return findings

        # Auto-detectar columnas financieras si no se proporcionan
        if not financial_columns:
            keywords = ["total", "amount", "precio", "price", "monto", "subtotal", "iva", "tax", "cost", "costo", "salary", "salario"]
            financial_columns = [
                col for col in df.columns 
                if any(keyword in col.lower() for keyword in keywords)
                and pd.api.types.is_numeric_dtype(df[col])
            ]

        # Probabilidades teóricas de Benford para los dígitos del 1 al 9
        benford_probs = np.log10(1 + 1 / np.arange(1, 10))

        for col in financial_columns:
            try:
                series = df[col].dropna()
                # Ignorar ceros y negativos para Benford
                series = series[series > 0]
                
                # Se requiere un tamaño de muestra decente para que la estadística tenga sentido
                if len(series) < 100:
                    continue

                # 1. Extraer el primer dígito significativo de cada número
                first_digits = series.astype(str).str.extract(r'([1-9])').astype(float).dropna()[0]
                
                # 2. Contar frecuencias del 1 al 9
                counts = first_digits.value_counts().reindex(range(1, 10), fill_value=0)
                total = counts.sum()
                
                if total < 100:
                    continue
                    
                # 3. Frecuencias esperadas
                expected = total * benford_probs
                
                # 4. Prueba de Chi-Cuadrado
                chi2, p_val = chisquare(f_obs=counts, f_exp=expected)
                
                # Un p_value < 0.05 significa que la distribución NO sigue a Benford (rechaza H0)
                if p_val < 0.05:
                    findings.append(FraudFinding(
                        layer="numeric_semantic",
                        indicator="Benford Law Deviation",
                        severity="HIGH" if p_val < 0.01 else "MEDIUM",
                        evidence=f"Los datos de '{col}' muestran una desviación significativa de la distribución natural de números (Ley de Benford, p-value: {p_val:.4f}). Posible manipulación manual o invención de datos.",
                        confidence=round(1 - p_val, 2)
                    ))
                    
            except Exception as e:
                logger.error("benford_analysis_failed", column=col, error=str(e))
                
        return findings