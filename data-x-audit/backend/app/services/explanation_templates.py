TEMPLATES = {
    "high_null_rate": {
        "what": "Faltan datos en la columna '{column}': {percent}% de los registros ({count} de {total}) no tienen valor.",
        "so_what": "Si usás esta columna para tomar decisiones, casi {one_in} de cada registros no aportará información. Esto puede distorsionar promedios, totales y cualquier análisis basado en esta columna.",
        "now_what": "Antes de analizar '{column}', decidí si podés completar los datos faltantes, excluir los registros incompletos, o evitar usar esta columna en decisiones críticas.",
    },
    "duplicate_rows": {
        "what": "Se encontraron {count} filas duplicadas ({percent}% del dataset).",
        "so_what": "Los duplicados inflan los conteos y distorsionan promedios. Si estás midiendo tendencias o totales, los resultados pueden ser engañosos.",
        "now_what": "Revisá si los duplicados son errores de carga o registros legítimos. Si son errores, eliminá los duplicados antes de analizar.",
    },
    "constant_column": {
        "what": "La columna '{column}' tiene un único valor en todos los registros: '{value}'.",
        "so_what": "Una columna con un solo valor no aporta información diferenciadora. No sirve para comparar, filtrar ni segmentar.",
        "now_what": "Podés ignorar esta columna en tu análisis. Si esperabas variación, revisá si los datos se cargaron correctamente.",
    },
    "high_cardinality": {
        "what": "La columna '{column}' tiene {unique} valores distintos de {total} registros ({percent}% son únicos).",
        "so_what": "Esto sugiere que '{column}' podría ser un identificador (como un ID o email) en lugar de una categoría útil para agrupar.",
        "now_what": "Si '{column}' es un identificador, no lo uses para agrupar ni promediar. Si esperabas categorías repetidas, revisá los datos.",
    },
    "low_cardinality": {
        "what": "La columna '{column}' tiene solo {unique} valores distintos.",
        "so_what": "Esto indica que '{column}' es una buena candidata para segmentar o agrupar tus datos. Podés comparar métricas entre estos {unique} grupos.",
        "now_what": "Usá '{column}' como filtro o agrupador para descubrir diferencias entre categorías.",
    },
    "strong_correlation": {
        "what": "Las columnas '{col1}' y '{col2}' tienen una relación fuerte ({direction}): cuando una sube, la otra {behavior}.",
        "so_what": "Esto puede significar que ambas columnas miden algo similar, o que una influye en la otra. Usar ambas en un análisis podría ser redundante.",
        "now_what": "Investigá si la relación tiene sentido para tu negocio. Si son redundantes, elegí la más confiable. Si una causa la otra, es un insight valioso.",
    },
    "outlier_detected": {
        "what": "La columna '{column}' tiene {count} valores inusuales ({percent}%) que se desvían significativamente del patrón general.",
        "so_what": "Estos valores extremos pueden distorsionar promedios y totales. Si son errores, contaminan el análisis. Si son reales, pueden ser los casos más interesantes.",
        "now_what": "Revisá estos {count} valores individualmente. Decidí si son errores (corregir o eliminar) o casos especiales (analizar por separado).",
    },
    "skewed_distribution": {
        "what": "Los datos de '{column}' están concentrados hacia los valores {direction}, con pocos valores {opposite} extremos.",
        "so_what": "El promedio de esta columna puede ser engañoso porque unos pocos valores extremos lo arrastran. La mediana te da una mejor idea del valor 'típico'.",
        "now_what": "Usá la mediana en lugar del promedio para '{column}'. Si necesitás el promedio, mencioná que está influenciado por valores extremos.",
    },
    "schema_warning": {
        "what": "{message}",
        "so_what": "Problemas en la estructura del dataset pueden causar errores en el procesamiento o resultados inesperados.",
        "now_what": "Revisá la estructura del archivo original y corregí los problemas antes de continuar con el análisis.",
    },
    "data_quality_good": {
        "what": "El dataset tiene {rows} registros y {cols} columnas con {completeness}% de completitud general.",
        "so_what": "Los datos están en buena forma para ser analizados. La completitud es suficiente para obtener conclusiones confiables.",
        "now_what": "Podés proceder con confianza al análisis. Los resultados deberían ser representativos.",
    },
    "column_stats": {
        "what": "La columna '{column}' ({dtype}) tiene valores entre {min} y {max}, con un valor típico de {median}.",
        "so_what": "Esto te da el rango y centro de los datos en '{column}'. El rango indica la variabilidad y el valor típico te orienta sobre qué es 'normal'.",
        "now_what": "Usá estos rangos como referencia. Valores fuera de [{min}, {max}] en futuros datos podrían indicar errores o casos especiales.",
    },
}


def render_finding_text(category: str, field: str, **kwargs) -> str:
    """Renderiza un campo (what/so_what/now_what) de un template."""
    template_group = TEMPLATES.get(category, {})
    template = template_group.get(field, "")
    try:
        return template.format(**{k: v for k, v in kwargs.items() if v is not None})
    except (KeyError, IndexError):
        return template
