import pytest
import numpy as np
import cv2
from app.services.opencv_pipeline import OpenCVPipeline

def test_quality_gate_sharp_image():
    """Verifica que una imagen nítida de alto contraste pase el Quality Gate."""
    pipeline = OpenCVPipeline(laplacian_threshold=100.0)
    
    # Creamos una imagen nítida: fondo negro con un cuadrado blanco sólido (bordes duros)
    sharp_image = np.zeros((200, 200, 3), dtype=np.uint8)
    cv2.rectangle(sharp_image, (50, 50), (150, 150), (255, 255, 255), -1)
    
    result = pipeline.quality_gate_image(sharp_image)
    assert result["passed"] is True
    assert result["variance"] > 100.0

def test_quality_gate_blurry_image():
    """Verifica que una imagen borrosa/fuera de foco sea rechazada."""
    pipeline = OpenCVPipeline(laplacian_threshold=100.0)
    
    sharp_image = np.zeros((200, 200, 3), dtype=np.uint8)
    cv2.rectangle(sharp_image, (50, 50), (150, 150), (255, 255, 255), -1)
    # Aplicamos un desenfoque Gaussiano extremo
    blurry_image = cv2.GaussianBlur(sharp_image, (51, 51), 0)
    
    result = pipeline.quality_gate_image(blurry_image)
    assert result["passed"] is False
    assert result["variance"] < 100.0