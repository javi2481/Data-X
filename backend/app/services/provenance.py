from datetime import datetime
from typing import Any, List
from app.repositories.mongo import session_repo

class ProvenanceService:
    async def add_step(self, session_id: str, step_name: str, details: dict[str, Any] = None):
        """
        Registra un paso en la línea de tiempo de trazabilidad de la sesión.
        """
        step = {
            "step": step_name,
            "timestamp": datetime.utcnow(),
            "details": details or {}
        }
        
        # Recuperar sesión actual para añadir el paso
        session = await session_repo.get_session(session_id)
        if session:
            provenance = session.get("provenance", [])
            provenance.append(step)
            await session_repo.update_session(session_id, {"provenance": provenance})

    async def get_steps(self, session_id: str) -> List[dict[str, Any]]:
        """
        Obtiene todos los pasos de trazabilidad de una sesión.
        """
        session = await session_repo.get_session(session_id)
        if session:
            return session.get("provenance", [])
        return []

provenance_service = ProvenanceService()
