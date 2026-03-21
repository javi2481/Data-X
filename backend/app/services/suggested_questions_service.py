"""
SuggestedQuestionsService: Generates contextual questions based on document structure.

Sprint 2: Analyzes findings, chunks, and document metadata to suggest relevant questions.
"""
from __future__ import annotations

from typing import Any, List, Dict, Optional
import structlog

logger = structlog.get_logger(__name__)


class SuggestedQuestionsService:
    """
    Generates suggested questions based on document structure and findings.
    
    Uses:
    - Finding categories and severity to suggest investigative questions
    - Document chunks and headings to suggest navigational questions
    - Table metadata to suggest data exploration questions
    """

    def __init__(self):
        self._question_templates = self._load_question_templates()

    def _load_question_templates(self) -> Dict[str, List[str]]:
        """Load question templates by category."""
        return {
            # Based on finding categories
            "data_gap": [
                "¿Qué columnas tienen más datos faltantes?",
                "¿Cómo puedo completar los valores nulos en {column}?",
                "¿Qué impacto tienen los datos faltantes en el análisis?",
            ],
            "reliability_risk": [
                "¿Qué problemas de confiabilidad detectaste?",
                "¿Cómo puedo mejorar la calidad de los datos?",
                "¿Hay valores atípicos que deba revisar?",
            ],
            "pattern": [
                "¿Qué patrones interesantes encontraste?",
                "¿Hay correlaciones entre las columnas?",
                "¿Qué tendencias se observan en los datos?",
            ],
            "opportunity": [
                "¿Qué oportunidades de mejora identificaste?",
                "¿Cómo puedo aprovechar estos datos?",
            ],
            "quality_issue": [
                "¿Qué problemas de calidad hay en el dataset?",
                "¿Cómo puedo limpiar estos datos?",
            ],
            # Based on document structure
            "document_overview": [
                "¿De qué trata este documento?",
                "¿Cuáles son los puntos principales?",
                "Dame un resumen ejecutivo",
            ],
            "tables": [
                "¿Qué tablas contiene el documento?",
                "¿Qué información hay en la tabla {table_id}?",
                "Compara las tablas del documento",
            ],
            "sections": [
                "¿Qué secciones tiene el documento?",
                "Explícame la sección '{heading}'",
            ],
            # Generic exploration
            "exploration": [
                "¿Qué es lo más importante que debo saber?",
                "¿Hay algo inusual en estos datos?",
                "¿Qué recomendaciones tienes?",
            ],
        }

    def generate_questions(
        self,
        findings: List[Dict[str, Any]] | None = None,
        chunks: List[Dict[str, Any]] | None = None,
        document_metadata: Dict[str, Any] | None = None,
        tables: List[Dict[str, Any]] | None = None,
        max_questions: int = 8,
    ) -> List[Dict[str, Any]]:
        """
        Generate suggested questions based on available context.
        
        Args:
            findings: List of finding dicts with category, severity, affected_columns
            chunks: List of chunk dicts with source_type, location
            document_metadata: Document metadata dict
            tables: List of table metadata dicts
            max_questions: Maximum number of questions to return
            
        Returns:
            List of question dicts with text, category, priority, context
        """
        questions: List[Dict[str, Any]] = []
        
        # 1. Generate questions from findings
        if findings:
            questions.extend(self._questions_from_findings(findings))
        
        # 2. Generate questions from document structure
        if chunks:
            questions.extend(self._questions_from_chunks(chunks))
        
        # 3. Generate questions from tables
        if tables:
            questions.extend(self._questions_from_tables(tables))
        
        # 4. Add generic exploration questions
        questions.extend(self._generic_questions())
        
        # Deduplicate and prioritize
        questions = self._deduplicate_questions(questions)
        questions = sorted(questions, key=lambda q: q.get("priority", 5))
        
        return questions[:max_questions]

    def _questions_from_findings(
        self, findings: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Generate questions based on findings."""
        questions = []
        
        # Count findings by category
        category_counts: Dict[str, int] = {}
        severity_max: Dict[str, str] = {}
        columns_by_category: Dict[str, List[str]] = {}
        
        for f in findings:
            cat = f.get("category", "unknown")
            sev = f.get("severity", "suggestion")
            cols = f.get("affected_columns", [])
            
            category_counts[cat] = category_counts.get(cat, 0) + 1
            
            # Track highest severity per category
            severity_order = {"critical": 0, "important": 1, "suggestion": 2, "insight": 3}
            if cat not in severity_max or severity_order.get(sev, 5) < severity_order.get(severity_max[cat], 5):
                severity_max[cat] = sev
            
            if cols:
                if cat not in columns_by_category:
                    columns_by_category[cat] = []
                columns_by_category[cat].extend(cols)
        
        # Generate questions for top categories
        for cat, count in sorted(category_counts.items(), key=lambda x: -x[1])[:3]:
            templates = self._question_templates.get(cat, [])
            priority = 1 if severity_max.get(cat) == "critical" else 2 if severity_max.get(cat) == "important" else 3
            
            for template in templates[:2]:  # Max 2 per category
                # Try to fill in column names
                text = template
                if "{column}" in template and columns_by_category.get(cat):
                    text = template.format(column=columns_by_category[cat][0])
                
                questions.append({
                    "text": text,
                    "category": cat,
                    "priority": priority,
                    "context": f"{count} hallazgo(s) de tipo {cat}",
                })
        
        return questions

    def _questions_from_chunks(
        self, chunks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Generate questions based on document chunks."""
        questions = []
        
        # Find unique headings
        headings = set()
        for chunk in chunks:
            loc = chunk.get("location") or {}
            if loc.get("heading"):
                headings.add(loc["heading"])
            if loc.get("section_path"):
                for h in loc["section_path"]:
                    headings.add(h)
        
        # Add document overview question
        questions.append({
            "text": "¿De qué trata este documento?",
            "category": "document_overview",
            "priority": 1,
            "context": f"{len(chunks)} fragmentos indexados",
        })
        
        # Add section-specific questions for top headings
        for heading in list(headings)[:3]:
            if len(heading) > 5:  # Skip very short headings
                questions.append({
                    "text": f"Explícame la sección '{heading[:50]}'",
                    "category": "sections",
                    "priority": 3,
                    "context": f"Sección: {heading[:50]}",
                })
        
        return questions

    def _questions_from_tables(
        self, tables: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Generate questions based on table metadata."""
        questions = []
        
        if not tables:
            return questions
        
        if len(tables) == 1:
            table = tables[0]
            headers = table.get("headers", [])
            if headers:
                questions.append({
                    "text": f"¿Qué información contiene la columna '{headers[0]}'?",
                    "category": "tables",
                    "priority": 2,
                    "context": f"Tabla con {len(headers)} columnas",
                })
        else:
            questions.append({
                "text": f"¿Qué diferencias hay entre las {len(tables)} tablas?",
                "category": "tables",
                "priority": 2,
                "context": f"{len(tables)} tablas detectadas",
            })
        
        # Add generic table question
        questions.append({
            "text": "¿Cuáles son las métricas clave en estos datos?",
            "category": "tables",
            "priority": 3,
            "context": "Exploración de datos",
        })
        
        return questions

    def _generic_questions(self) -> List[Dict[str, Any]]:
        """Return generic exploration questions."""
        return [
            {
                "text": "¿Qué es lo más importante que debo saber?",
                "category": "exploration",
                "priority": 4,
                "context": "Pregunta general",
            },
            {
                "text": "¿Qué recomendaciones tienes para mejorar estos datos?",
                "category": "exploration",
                "priority": 5,
                "context": "Recomendaciones",
            },
        ]

    def _deduplicate_questions(
        self, questions: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Remove duplicate questions based on text similarity."""
        seen_texts = set()
        unique = []
        
        for q in questions:
            # Normalize text for comparison
            normalized = q["text"].lower().strip()
            if normalized not in seen_texts:
                seen_texts.add(normalized)
                unique.append(q)
        
        return unique


# Singleton instance
_suggested_questions_service: Optional[SuggestedQuestionsService] = None


def get_suggested_questions_service() -> SuggestedQuestionsService:
    """Get or create the SuggestedQuestionsService singleton."""
    global _suggested_questions_service
    if _suggested_questions_service is None:
        _suggested_questions_service = SuggestedQuestionsService()
    return _suggested_questions_service
