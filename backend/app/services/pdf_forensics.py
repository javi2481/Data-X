import structlog
from typing import List
from app.schemas.fraud import FraudFinding

logger = structlog.get_logger(__name__)

try:
    import pikepdf
    PIKEPDF_AVAILABLE = True
except ImportError:
    PIKEPDF_AVAILABLE = False

try:
    from pyhanko.pdf_utils.reader import PdfFileReader
    from pyhanko.sign.validation import validate_pdf_signature
    PYHANKO_AVAILABLE = True
except ImportError:
    PYHANKO_AVAILABLE = False

class PDFForensicsService:
    """
    Layer 1 de FraudGuard: Análisis de metadatos ocultos y firmas digitales del PDF.
    Busca software de edición de imágenes y alteraciones criptográficas silenciosas.
    """
    def analyze_metadata(self, pdf_path: str) -> List[FraudFinding]:
        findings = []
        if not PIKEPDF_AVAILABLE:
            logger.warning("pikepdf_not_available")
            return findings

        try:
            with pikepdf.Pdf.open(pdf_path) as pdf:
                meta = pdf.docinfo
                creator = str(meta.get("/Creator", "")).lower()
                producer = str(meta.get("/Producer", "")).lower()
                
                # Software de manipulación de imágenes/PDFs que no debería generar facturas/balances oficiales
                suspicious_tools = ["photoshop", "illustrator", "gimp", "ilovepdf", "canva"]
                
                for tool in suspicious_tools:
                    if tool in creator or tool in producer:
                        findings.append(FraudFinding(
                            layer="pdf_forensics",
                            indicator="Suspicious Software",
                            severity="HIGH",
                            evidence=f"El documento fue editado o creado con software sospechoso: '{tool}'. (Metadatos: Creator='{meta.get('/Creator', '')}' / Producer='{meta.get('/Producer', '')}')",
                            confidence=0.9
                        ))
                        break
        except Exception as e:
            logger.error("pdf_metadata_analysis_failed", error=str(e))
        
        return findings

    def verify_signatures(self, pdf_path: str) -> List[FraudFinding]:
        findings = []
        if not PYHANKO_AVAILABLE:
            logger.warning("pyhanko_not_available")
            return findings

        try:
            with open(pdf_path, 'rb') as doc_file:
                reader = PdfFileReader(doc_file)
                signatures = reader.embedded_signatures
                
                for sig in signatures:
                    # Validación básica de integridad del hash
                    status = validate_pdf_signature(sig)
                    if not status.intact:
                        findings.append(FraudFinding(
                            layer="pdf_forensics",
                            indicator="Broken Signature",
                            severity="CRITICAL",
                            evidence=f"La firma digital '{sig.field_name}' es inválida o el documento fue alterado maliciosamente después de firmarse.",
                            confidence=0.99
                        ))
        except Exception as e:
            logger.error("pdf_signature_verification_failed", error=str(e))
            
        return findings