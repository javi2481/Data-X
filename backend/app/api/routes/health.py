from fastapi import APIRouter

router = APIRouter()

@router.get("", response_description="Verifica que el servicio esté arriba", tags=["health"])
async def health():
    """
    Retorna el estado de salud del backend.
    """
    return {"status": "ok"}
