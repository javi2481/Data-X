TEMPLATES = {
    "high_null_rate": "La columna '{column}' tiene {percent}% de valores nulos ({count} de {total}). Esto puede afectar la calidad del análisis.",
    "duplicate_rows": "Se detectaron {count} filas duplicadas ({percent}% del dataset). Considerar deduplicación.",
    "constant_column": "La columna '{column}' tiene un único valor ('{value}'). No aporta información diferenciadora.",
    "high_cardinality": "La columna '{column}' tiene {unique} valores únicos de {total} ({percent}% cardinalidad). Posiblemente sea un identificador.",
    "low_cardinality": "La columna '{column}' tiene solo {unique} valores únicos. Posiblemente sea categórica.",
    "strong_correlation": "Las columnas '{col1}' y '{col2}' tienen una correlación de {value} ({classification}). Esto puede indicar redundancia o dependencia.",
    "outlier_detected": "La columna '{column}' tiene {count} outliers ({percent}%) usando método {method}. Rango esperado: [{lower}, {upper}].",
    "skewed_distribution": "La columna '{column}' muestra una distribución {classification} (skewness: {value}). Considerar transformación logarítmica.",
    "column_stats": "Columna '{column}': tipo {dtype}, {count} valores, rango [{min}, {max}], media {mean}.",
    "data_quality_warning": "{message}",
    "schema_warning": "{message}",
}

def render_explanation(category: str, **kwargs) -> str:
    template = TEMPLATES.get(category, "{message}")
    return template.format(**{k: v for k, v in kwargs.items() if v is not None})
