import pandas as pd
from uuid import uuid4
from typing import List
from app.schemas.finding import Finding, Evidence
from app.services.explanation_templates import render_explanation

class FindingBuilder:
    def __init__(self):
        pass

    def detect_high_null_rate(self, df: pd.DataFrame, threshold: float = 0.3) -> List[Finding]:
        findings = []
        total = len(df)
        if total == 0:
            return findings

        null_counts = df.isnull().sum()
        for col, count in null_counts.items():
            percent = count / total
            if percent > threshold:
                severity = "critical" if percent > 0.8 else "warning"
                finding_id = f"finding_{uuid4().hex[:8]}"
                explanation = render_explanation(
                    "high_null_rate", 
                    column=col, 
                    percent=round(percent * 100, 2), 
                    count=count, 
                    total=total
                )
                findings.append(Finding(
                    finding_id=finding_id,
                    category="high_null_rate",
                    severity=severity,
                    title=f"Alta tasa de nulos en {col}",
                    technical_summary=f"La columna {col} tiene {count} nulos ({percent:.1%})",
                    explanation=explanation,
                    affected_columns=[col],
                    evidence=[Evidence(metric="null_percent", value=percent, threshold=threshold)]
                ))
        return findings

    def detect_duplicate_rows(self, df: pd.DataFrame) -> List[Finding]:
        findings = []
        total = len(df)
        if total == 0:
            return findings

        duplicates = df.duplicated().sum()
        if duplicates > 0:
            percent = duplicates / total
            severity = "critical" if percent > 0.2 else "warning"
            finding_id = f"finding_{uuid4().hex[:8]}"
            explanation = render_explanation(
                "duplicate_rows", 
                count=duplicates, 
                percent=round(percent * 100, 2)
            )
            findings.append(Finding(
                finding_id=finding_id,
                category="duplicate_rows",
                severity=severity,
                title="Filas duplicadas detectadas",
                technical_summary=f"Se encontraron {duplicates} filas duplicadas ({percent:.1%})",
                explanation=explanation,
                evidence=[Evidence(metric="duplicate_percent", value=percent)]
            ))
        return findings

    def detect_constant_columns(self, df: pd.DataFrame) -> List[Finding]:
        findings = []
        for col in df.columns:
            unique_values = df[col].nunique()
            if unique_values == 1:
                val = df[col].iloc[0]
                finding_id = f"finding_{uuid4().hex[:8]}"
                explanation = render_explanation("constant_column", column=col, value=val)
                findings.append(Finding(
                    finding_id=finding_id,
                    category="constant_column",
                    severity="info",
                    title=f"Columna constante: {col}",
                    technical_summary=f"La columna {col} solo contiene el valor '{val}'",
                    explanation=explanation,
                    affected_columns=[col],
                    evidence=[Evidence(metric="unique_count", value=1)]
                ))
        return findings

    def detect_high_cardinality(self, df: pd.DataFrame, threshold: float = 0.95) -> List[Finding]:
        findings = []
        total = len(df)
        if total < 10: # No tiene sentido con muy pocos datos
            return findings

        for col in df.columns:
            unique_count = df[col].nunique()
            cardinality = unique_count / total
            if cardinality > threshold and df[col].dtype == 'object':
                finding_id = f"finding_{uuid4().hex[:8]}"
                explanation = render_explanation(
                    "high_cardinality", 
                    column=col, 
                    unique=unique_count, 
                    total=total, 
                    percent=round(cardinality * 100, 2)
                )
                findings.append(Finding(
                    finding_id=finding_id,
                    category="high_cardinality",
                    severity="info",
                    title=f"Alta cardinalidad en {col}",
                    technical_summary=f"La columna {col} tiene {unique_count} valores únicos ({cardinality:.1%})",
                    explanation=explanation,
                    affected_columns=[col],
                    evidence=[Evidence(metric="cardinality", value=cardinality, threshold=threshold)]
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
                explanation = render_explanation("low_cardinality", column=col, unique=unique_count)
                findings.append(Finding(
                    finding_id=finding_id,
                    category="low_cardinality",
                    severity="info",
                    title=f"Baja cardinalidad en {col}",
                    technical_summary=f"La columna {col} tiene solo {unique_count} valores únicos",
                    explanation=explanation,
                    affected_columns=[col],
                    evidence=[Evidence(metric="unique_count", value=unique_count, threshold=threshold)]
                ))
        return findings

    def generate_column_stats(self, df: pd.DataFrame) -> List[Finding]:
        findings = []
        for col in df.columns:
            dtype = str(df[col].dtype)
            count = int(df[col].count())
            
            kwargs = {"column": col, "dtype": dtype, "count": count}
            
            if pd.api.types.is_numeric_dtype(df[col]):
                kwargs.update({
                    "min": round(float(df[col].min()), 2) if not pd.isna(df[col].min()) else None,
                    "max": round(float(df[col].max()), 2) if not pd.isna(df[col].max()) else None,
                    "mean": round(float(df[col].mean()), 2) if not pd.isna(df[col].mean()) else None
                })
            else:
                kwargs.update({"min": "N/A", "max": "N/A", "mean": "N/A"})

            finding_id = f"finding_{uuid4().hex[:8]}"
            explanation = render_explanation("column_stats", **kwargs)
            
            findings.append(Finding(
                finding_id=finding_id,
                category="column_stats",
                severity="info",
                title=f"Estadísticas de {col}",
                technical_summary=f"Perfil básico de la columna {col}",
                explanation=explanation,
                affected_columns=[col]
            ))
        return findings

    def build_all_findings(self, df: pd.DataFrame) -> List[Finding]:
        all_findings = []
        all_findings.extend(self.detect_high_null_rate(df))
        all_findings.extend(self.detect_duplicate_rows(df))
        all_findings.extend(self.detect_constant_columns(df))
        all_findings.extend(self.detect_high_cardinality(df))
        all_findings.extend(self.detect_low_cardinality(df))
        all_findings.extend(self.generate_column_stats(df))
        return all_findings
