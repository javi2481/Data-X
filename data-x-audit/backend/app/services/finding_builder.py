import pandas as pd
from uuid import uuid4
from typing import List, Optional
from app.schemas.finding import Finding, Evidence
from app.services.explanation_templates import render_finding_text
import structlog
import time
import math

logger = structlog.get_logger(__name__)

class FindingBuilder:
    def __init__(self):
        pass

    def _get_one_in(self, percent: float) -> str:
        if percent <= 0: return "0"
        val = round(100 / percent)
        return f"1 de cada {val}"

    def detect_high_null_rate(self, df: pd.DataFrame, threshold: float = 0.3) -> List[Finding]:
        findings = []
        total = len(df)
        if total == 0:
            return findings

        null_counts = df.isnull().sum()
        for col, count in null_counts.items():
            percent = (count / total) * 100
            if percent > threshold * 100:
                severity = "critical" if percent > 50 else "important"
                finding_id = f"finding_{uuid4().hex[:8]}"
                
                params = {
                    "column": col,
                    "percent": round(percent, 1),
                    "count": count,
                    "total": total,
                    "one_in": self._get_one_in(percent)
                }
                
                findings.append(Finding(
                    finding_id=finding_id,
                    category="data_gap",
                    severity=severity,
                    title=f"Datos faltantes en {col}",
                    what=render_finding_text("high_null_rate", "what", **params),
                    so_what=render_finding_text("high_null_rate", "so_what", **params),
                    now_what=render_finding_text("high_null_rate", "now_what", **params),
                    affected_columns=[col],
                    evidence=[Evidence(metric="null_percent", value=round(percent, 1), context=f"de {total} registros")],
                    confidence="verified"
                ))
        return findings

    def detect_duplicate_rows(self, df: pd.DataFrame) -> List[Finding]:
        findings = []
        total = len(df)
        if total == 0:
            return findings

        duplicates = df.duplicated().sum()
        if duplicates > 0:
            percent = (duplicates / total) * 100
            severity = "critical" if percent > 20 else "important"
            finding_id = f"finding_{uuid4().hex[:8]}"
            
            params = {
                "count": duplicates,
                "percent": round(percent, 1)
            }
            
            findings.append(Finding(
                finding_id=finding_id,
                category="reliability_risk",
                severity=severity,
                title="Filas duplicadas detectadas",
                what=render_finding_text("duplicate_rows", "what", **params),
                so_what=render_finding_text("duplicate_rows", "so_what", **params),
                now_what=render_finding_text("duplicate_rows", "now_what", **params),
                evidence=[Evidence(metric="duplicate_percent", value=round(percent, 1), context=f"{duplicates} filas")],
                confidence="verified"
            ))
        return findings

    def detect_constant_columns(self, df: pd.DataFrame) -> List[Finding]:
        findings = []
        for col in df.columns:
            unique_values = df[col].nunique()
            if unique_values == 1:
                val = df[col].iloc[0]
                finding_id = f"finding_{uuid4().hex[:8]}"
                
                params = {"column": col, "value": val}
                
                findings.append(Finding(
                    finding_id=finding_id,
                    category="quality_issue",
                    severity="suggestion",
                    title=f"Columna sin variación: {col}",
                    what=render_finding_text("constant_column", "what", **params),
                    so_what=render_finding_text("constant_column", "so_what", **params),
                    now_what=render_finding_text("constant_column", "now_what", **params),
                    affected_columns=[col],
                    evidence=[Evidence(metric="unique_values", value=1)],
                    confidence="verified"
                ))
        return findings

    def detect_high_cardinality(self, df: pd.DataFrame, threshold: float = 0.95) -> List[Finding]:
        findings = []
        total = len(df)
        if total < 10:
            return findings

        for col in df.columns:
            unique_count = df[col].nunique()
            cardinality = unique_count / total
            if cardinality > threshold and df[col].dtype == 'object':
                finding_id = f"finding_{uuid4().hex[:8]}"
                
                params = {
                    "column": col,
                    "unique": unique_count,
                    "total": total,
                    "percent": round(cardinality * 100, 1)
                }
                
                findings.append(Finding(
                    finding_id=finding_id,
                    category="quality_issue",
                    severity="suggestion",
                    title=f"Posible identificador en {col}",
                    what=render_finding_text("high_cardinality", "what", **params),
                    so_what=render_finding_text("high_cardinality", "so_what", **params),
                    now_what=render_finding_text("high_cardinality", "now_what", **params),
                    affected_columns=[col],
                    evidence=[Evidence(metric="cardinality", value=round(cardinality, 3))],
                    confidence="verified"
                ))
        return findings

    def detect_low_cardinality(self, df: pd.DataFrame, threshold: int = 3) -> List[Finding]:
        findings = []
        total = len(df)
        if total < 10:
            return findings

        for col in df.columns:
            unique_count = df[col].nunique()
            if 1 < unique_count <= threshold:
                finding_id = f"finding_{uuid4().hex[:8]}"
                
                params = {"column": col, "unique": unique_count}
                
                findings.append(Finding(
                    finding_id=finding_id,
                    category="opportunity",
                    severity="insight",
                    title=f"Categorías detectadas en {col}",
                    what=render_finding_text("low_cardinality", "what", **params),
                    so_what=render_finding_text("low_cardinality", "so_what", **params),
                    now_what=render_finding_text("low_cardinality", "now_what", **params),
                    affected_columns=[col],
                    evidence=[Evidence(metric="unique_values", value=unique_count)],
                    confidence="verified"
                ))
        return findings

    def generate_column_stats(self, df: pd.DataFrame) -> List[Finding]:
        findings = []
        for col in df.columns:
            dtype = str(df[col].dtype)
            count = int(df[col].count())
            
            params = {"column": col, "dtype": dtype, "count": count}
            
            if pd.api.types.is_numeric_dtype(df[col]):
                params.update({
                    "min": round(float(df[col].min()), 1) if not pd.isna(df[col].min()) else "N/A",
                    "max": round(float(df[col].max()), 1) if not pd.isna(df[col].max()) else "N/A",
                    "median": round(float(df[col].median()), 1) if not pd.isna(df[col].median()) else "N/A"
                })
            else:
                params.update({"min": "N/A", "max": "N/A", "median": "N/A"})

            finding_id = f"finding_{uuid4().hex[:8]}"
            
            findings.append(Finding(
                finding_id=finding_id,
                category="quality_issue",
                severity="insight",
                title=f"Resumen de columna: {col}",
                what=render_finding_text("column_stats", "what", **params),
                so_what=render_finding_text("column_stats", "so_what", **params),
                now_what=render_finding_text("column_stats", "now_what", **params),
                affected_columns=[col],
                confidence="verified"
            ))
        return findings

    def generate_data_quality_summary(self, df: pd.DataFrame, findings_count: int) -> Finding:
        total_rows = len(df)
        total_cols = len(df.columns)
        completeness = round((1 - df.isnull().sum().sum() / (total_rows * total_cols)) * 100, 1) if total_rows > 0 else 0
        
        params = {
            "rows": total_rows,
            "cols": total_cols,
            "completeness": completeness
        }
        
        return Finding(
            finding_id=f"summary_{uuid4().hex[:8]}",
            category="opportunity",
            severity="insight",
            title="Resumen de calidad del dataset",
            what=render_finding_text("data_quality_good", "what", **params),
            so_what=render_finding_text("data_quality_good", "so_what", **params),
            now_what=render_finding_text("data_quality_good", "now_what", **params),
            evidence=[Evidence(metric="completeness", value=completeness)],
            confidence="verified"
        )

    def detect_strong_correlations(self, correlations: dict) -> List[Finding]:
        findings = []
        for corr in correlations.get("strong_correlations", []):
            val = corr.get("correlation", corr.get("value", 0))
            severity = "important" if abs(val) > 0.9 else "insight"
            finding_id = f"finding_{uuid4().hex[:8]}"
            
            params = {
                "col1": corr["col1"],
                "col2": corr["col2"],
                "direction": "positiva" if val > 0 else "negativa",
                "behavior": "también sube" if val > 0 else "baja"
            }
            
            findings.append(Finding(
                finding_id=finding_id,
                category="pattern",
                severity=severity,
                title=f"Relación fuerte entre {corr['col1']} y {corr['col2']}",
                what=render_finding_text("strong_correlation", "what", **params),
                so_what=render_finding_text("strong_correlation", "so_what", **params),
                now_what=render_finding_text("strong_correlation", "now_what", **params),
                affected_columns=[corr["col1"], corr["col2"]],
                evidence=[Evidence(metric="correlation", value=round(val, 2))],
                confidence="verified"
            ))
        return findings

    def detect_outliers_findings(self, outlier_results: list) -> List[Finding]:
        findings = []
        for res in outlier_results:
            percent = res.get("outlier_percent", 0)
            if percent > 5:
                severity = "important" if percent > 10 else "suggestion"
                finding_id = f"finding_{uuid4().hex[:8]}"
                
                params = {
                    "column": res["column"],
                    "count": res["outlier_count"],
                    "percent": round(percent, 1)
                }
                
                findings.append(Finding(
                    finding_id=finding_id,
                    category="reliability_risk",
                    severity=severity,
                    title=f"Valores inusuales en {res['column']}",
                    what=render_finding_text("outlier_detected", "what", **params),
                    so_what=render_finding_text("outlier_detected", "so_what", **params),
                    now_what=render_finding_text("outlier_detected", "now_what", **params),
                    affected_columns=[res["column"]],
                    evidence=[Evidence(metric="outlier_percent", value=round(percent, 1))],
                    confidence="verified"
                ))
        return findings

    def detect_distribution_issues(self, distributions: list) -> List[Finding]:
        findings = []
        for dist in distributions:
            if dist["classification"] != "normal":
                finding_id = f"finding_{uuid4().hex[:8]}"
                
                params = {
                    "column": dist["column"],
                    "direction": "altos" if dist["skewness"] > 0 else "bajos",
                    "opposite": "bajos" if dist["skewness"] > 0 else "altos"
                }
                
                findings.append(Finding(
                    finding_id=finding_id,
                    category="pattern",
                    severity="insight",
                    title=f"Distribución asimétrica en {dist['column']}",
                    what=render_finding_text("skewed_distribution", "what", **params),
                    so_what=render_finding_text("skewed_distribution", "so_what", **params),
                    now_what=render_finding_text("skewed_distribution", "now_what", **params),
                    affected_columns=[dist["column"]],
                    evidence=[Evidence(metric="skewness", value=round(dist["skewness"], 2))],
                    confidence="verified"
                ))
        return findings

    def detect_schema_issues(self, schema_results: list) -> List[Finding]:
        findings = []
        for res in schema_results:
            finding_id = f"finding_{uuid4().hex[:8]}"
            params = {"message": res["message"]}
            
            findings.append(Finding(
                finding_id=finding_id,
                category="quality_issue",
                severity="important",
                title=f"Problema de estructura en {res['column']}",
                what=render_finding_text("schema_warning", "what", **params),
                so_what=render_finding_text("schema_warning", "so_what", **params),
                now_what=render_finding_text("schema_warning", "now_what", **params),
                affected_columns=[res["column"]],
                confidence="verified"
            ))
        return findings

    def detect_statistical_insights(self, test_results: list) -> List[Finding]:
        """Genera findings basados en resultados de tests estadísticos (pingouin)"""
        findings = []
        for res in test_results:
            if "is_normal" in res:
                col = res["column"]
                is_normal = res["is_normal"]
                finding_id = f"stat_{uuid4().hex[:8]}"
                
                findings.append(Finding(
                    finding_id=finding_id,
                    category="pattern",
                    severity="insight",
                    title=f"Análisis de distribución: {col}",
                    what=f"Los datos de '{col}' {'siguen' if is_normal else 'no siguen'} un patrón regular (distribución normal).",
                    so_what="Cuando los datos no son 'normales', el promedio puede verse muy afectado por unos pocos valores extremos.",
                    now_what=f"Es recomendable usar la mediana en lugar del promedio para analizar '{col}'.",
                    affected_columns=[col],
                    evidence=[Evidence(metric="p_value", value=res["p_value"])],
                    confidence="verified"
                ))
            elif "significant" in res and res["significant"]:
                num_col = res["numeric_column"]
                grp_col = res["group_column"]
                finding_id = f"stat_{uuid4().hex[:8]}"
                
                findings.append(Finding(
                    finding_id=finding_id,
                    category="pattern",
                    severity="important",
                    title=f"Diferencia detectada: {num_col} según {grp_col}",
                    what=res["interpretation"],
                    so_what=f"Se confirmó estadísticamente que los valores de '{num_col}' varían dependiendo de la categoría en '{grp_col}'.",
                    now_what=f"Explorá por qué el grupo '{grp_col}' genera estos cambios en '{num_col}' para encontrar oportunidades de optimización.",
                    affected_columns=[num_col, grp_col],
                    evidence=[Evidence(metric="p_value", value=res["p_value"])],
                    confidence="verified"
                ))
        return findings

    def build_all_findings(self, df: pd.DataFrame, eda_results: dict = None, schema_results: list = None, test_results: list = None) -> List[Finding]:
        start_time = time.time()
        logger.info("build_findings_start")
        
        all_findings = []
        if len(df) == 0:
            return all_findings
            
        all_findings.extend(self.detect_high_null_rate(df))
        all_findings.extend(self.detect_duplicate_rows(df))
        all_findings.extend(self.detect_constant_columns(df))
        all_findings.extend(self.detect_high_cardinality(df))
        all_findings.extend(self.detect_low_cardinality(df))
        all_findings.extend(self.generate_column_stats(df))

        if schema_results:
            all_findings.extend(self.detect_schema_issues(schema_results))

        if eda_results:
            if "correlations" in eda_results:
                all_findings.extend(self.detect_strong_correlations(eda_results["correlations"]))
            if "outliers" in eda_results:
                all_findings.extend(self.detect_outliers_findings(eda_results["outliers"]))
            if "distributions" in eda_results:
                all_findings.extend(self.detect_distribution_issues(eda_results["distributions"]))
        
        # Insights estadísticos (pingouin)
        if test_results:
            all_findings.extend(self.detect_statistical_insights(test_results))
        
        # Generar resumen final
        summary = self.generate_data_quality_summary(df, len(all_findings))
        all_findings.append(summary)
        
        duration = time.time() - start_time
        logger.info("build_findings_complete", count=len(all_findings), duration_sec=round(duration, 3))
        return all_findings
