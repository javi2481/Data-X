import structlog
import asyncio
from datetime import datetime
from typing import Optional, List
import pandas as pd

from app.schemas.fraud import FraudReport, FraudFinding
from app.services.pdf_forensics import PDFForensicsService
from app.services.opencv_pipeline import OpenCVPipeline
from app.services.benford_service import BenfordService
from app.services.fiscal_validator import FiscalValidatorService

logger = structlog.get_logger(__name__)

class FraudGuardOrchestrator:
    """
    Orquestador principal de la Capa Antifraude.
    Ejecuta las validaciones de las distintas capas (Layers) en paralelo y emite el FraudReport.
    """
    def __init__(self):
        self.pdf_forensics = PDFForensicsService()
        self.cv_pipeline = OpenCVPipeline()
        self.benford = BenfordService()
        self.fiscal_validator = FiscalValidatorService()

    async def analyze(
        self, 
        session_id: str, 
        pdf_path: Optional[str] = None, 
        file_bytes: Optional[bytes] = None,
        df: Optional[pd.DataFrame] = None,
        document_text: Optional[str] = ""
    ) -> FraudReport:
        logger.info("fraud_guard_start", session_id=session_id)
        findings: List[FraudFinding] = []

        loop = asyncio.get_event_loop()
        tasks = []

        # Layer 1: PDF Forensics (Metadatos y Firmas)
        if pdf_path:
            tasks.append(loop.run_in_executor(None, self.pdf_forensics.analyze_metadata, pdf_path))
            tasks.append(loop.run_in_executor(None, self.pdf_forensics.verify_signatures, pdf_path))
        
        # Layer 2: Visual Forensics (ELA)
        if file_bytes:
            tasks.append(self._run_visual_forensics(loop, file_bytes))
        
        # Layer 3: Numeric Forensics (Benford)
        if df is not None and not df.empty:
            tasks.append(loop.run_in_executor(None, self.benford.analyze_benford, df, None))
            
        # Layer 4: Fiscal Validation
        tasks.append(loop.run_in_executor(None, self.fiscal_validator.analyze_fiscal_data, df, document_text))

        # Recopilar todos los resultados
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for res in results:
            if isinstance(res, list):
                findings.extend(res)
            elif isinstance(res, Exception):
                logger.error("fraud_guard_task_failed", error=str(res), session_id=session_id)

        # Calcular Puntuación de Riesgo
        risk_score, risk_level = self._calculate_risk_score(findings)

        report = FraudReport(
            session_id=session_id,
            risk_score=risk_score,
            risk_level=risk_level,
            findings=findings,
            generated_at=datetime.utcnow()
        )

        logger.info("fraud_guard_complete", session_id=session_id, risk_score=risk_score, risk_level=risk_level)
        return report

    async def _run_visual_forensics(self, loop, file_bytes: bytes) -> List[FraudFinding]:
        findings = []
        images = await loop.run_in_executor(None, self.cv_pipeline.pdf_to_cv2_images, file_bytes, 150)
        for idx, img in enumerate(images):
            ela_result = await loop.run_in_executor(None, self.cv_pipeline.error_level_analysis, img, 90)
            if ela_result.get("suspicious"):
                findings.append(FraudFinding(
                    layer="visual_forensics",
                    indicator="ELA Artifacts",
                    severity="HIGH",
                    evidence=f"Se detectaron parches o alteraciones visuales por nivel de compresión inconsistente en la página {idx + 1}.",
                    page=idx + 1,
                    confidence=ela_result.get("ela_score", 0.8)
                ))
        return findings

    def _calculate_risk_score(self, findings: List[FraudFinding]) -> tuple[float, str]:
        if not findings: return 0.0, "LOW"
        
        severity_scores = {"LOW": 25, "MEDIUM": 50, "HIGH": 75, "CRITICAL": 100}
        weights = {"pdf_forensics": 0.30, "visual_forensics": 0.25, "numeric_semantic": 0.25, "fiscal_validation": 0.20}
        
        layer_max = {}
        for f in findings:
            layer_max[f.layer] = max(layer_max.get(f.layer, 0), severity_scores.get(f.severity, 0))
            
        # Ponderación dinámica basada solo en las capas que detectaron algo (o que se corrieron)
        active_weight_sum = sum(weights[l] for l in layer_max.keys())
        if active_weight_sum == 0:
            return 0.0, "LOW"
            
        risk_score = sum(layer_max[l] * (weights[l] / active_weight_sum) for l in layer_max.keys())
        
        level = "LOW"
        if risk_score >= 80: level = "CRITICAL"
        elif risk_score >= 60: level = "HIGH"
        elif risk_score >= 30: level = "MEDIUM"
        
        return round(float(risk_score), 2), level