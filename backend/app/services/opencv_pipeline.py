import cv2
import numpy as np
import pypdfium2 as pdfium
import structlog
from typing import Dict, Any, List

logger = structlog.get_logger(__name__)

class OpenCVPipeline:
    """
    Capa visual de OpenCV para Data-X.
    Sirve como Quality Gate pre-extracción y motor de enderezado (deskew)/mejora,
    eliminando la necesidad de depender de librerías externas de nicho.
    """
    def __init__(self, laplacian_threshold: float = 100.0):
        # Umbral por defecto: < 100 suele indicar una imagen bastante borrosa
        self.laplacian_threshold = laplacian_threshold

    def pdf_to_cv2_images(self, file_bytes: bytes, dpi: int = 150) -> List[np.ndarray]:
        """
        Extrae las páginas de un PDF en memoria y las convierte a una lista
        de imágenes (arrays de NumPy BGR) aptas para procesar con OpenCV.
        """
        images = []
        try:
            pdf = pdfium.PdfDocument(file_bytes)
            for i in range(len(pdf)):
                page = pdf[i]
                # Renderizar a PIL Image
                pil_image = page.render(scale=dpi/72).to_pil()
                # Convertir de RGB (PIL) a BGR (OpenCV)
                cv_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
                images.append(cv_image)
        except Exception as e:
            logger.error("pdf_to_cv2_images_failed", error=str(e))
        return images

    def quality_gate_image(self, image: np.ndarray) -> Dict[str, Any]:
        """
        Evalúa la calidad visual de una imagen usando la Varianza Laplaciana.
        Sirve para detectar imágenes borrosas o fuera de foco (Scans de mala calidad).
        """
        # Asegurar que la imagen esté en escala de grises para el filtro
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image

        # Calcular el foco / nitidez
        variance = cv2.Laplacian(gray, cv2.CV_64F).var()
        passed = variance >= self.laplacian_threshold
        
        logger.info("opencv_quality_gate", variance=round(variance, 2), passed=passed)
        
        return {
            "passed": bool(passed),
            "variance": float(variance),
            "reason": "LOW_SHARPNESS" if not passed else None
        }

    def deskew_image(self, image: np.ndarray) -> np.ndarray:
        """
        Endereza una imagen rotada utilizando cv2.minAreaRect.
        Reemplaza a herramientas externas como `jdeskew`.
        """
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
            
        # Invertir colores (fondo negro, texto/bordes blancos) para encontrar los contornos
        gray = cv2.bitwise_not(gray)
        
        # Obtener coordenadas de píxeles (texto)
        coords = np.column_stack(np.where(gray > 0))
        if len(coords) == 0:
            return image  # Imagen en blanco, no hay nada que enderezar
            
        # Calcular el rectángulo delimitador de área mínima
        angle = cv2.minAreaRect(coords)[-1]
        
        # Ajuste de ángulo basado en cómo OpenCV reporta minAreaRect
        if angle < -45:
            angle = -(90 + angle)
        else:
            angle = -angle
            
        # Si la rotación es microscópica, evitamos alterar la imagen original
        if abs(angle) < 0.5:
            return image
            
        (h, w) = image.shape[:2]
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        
        # Rotar la imagen, rellenando los bordes nuevos con el color de replicación
        rotated = cv2.warpAffine(image, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
        
        logger.info("opencv_deskew", angle=round(angle, 2))
        return rotated

    def enhance_image(self, image: np.ndarray) -> np.ndarray:
        """
        Aplica Denoising y CLAHE (Contrast Limited Adaptive Histogram Equalization)
        para maximizar el contraste del texto sobre el fondo.
        """
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
        denoised = cv2.fastNlMeansDenoising(gray, h=10)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(denoised)
        return cv2.cvtColor(enhanced, cv2.COLOR_GRAY2BGR) if len(image.shape) == 3 else enhanced

    def error_level_analysis(self, image: np.ndarray, quality: int = 90) -> Dict[str, Any]:
        """
        Layer 2 de FraudGuard: Análisis visual ELA.
        Detecta regiones de la imagen que fueron modificadas (copiar/pegar) 
        mediante la diferencia en artefactos de compresión JPEG.
        """
        if len(image.shape) != 3:
            # ELA funciona mejor en imágenes BGR/RGB
            image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
            
        # 1. Guardar en memoria con calidad JPEG conocida
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
        _, encoded_img = cv2.imencode('.jpg', image, encode_param)
        
        # 2. Volver a decodificar la imagen recomprimida
        compressed_img = cv2.imdecode(encoded_img, 1)
        
        # 3. Calcular la diferencia absoluta de píxeles
        diff = cv2.absdiff(image, compressed_img)
        
        # 4. Analizar la dispersión del error en escala de grises
        gray_diff = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
        max_diff = np.max(gray_diff)
        mean_diff = np.mean(gray_diff)
        std_diff = np.std(gray_diff)
        
        # Un std_diff (desviación estándar) alto significa que hay zonas con 
        # errores de compresión muy diferentes (fuerte indicio de manipulación)
        score = min(float(std_diff / 10.0), 1.0) # Normalización heurística
        
        logger.info("opencv_ela_analysis", max_error=int(max_diff), std_diff=round(std_diff, 2), score=round(score, 3))
        
        return {
            "suspicious": bool(score > 0.6), # Umbral de sospecha
            "ela_score": float(score),
            "mean_error": float(mean_diff),
            "max_error": float(max_diff)
        }