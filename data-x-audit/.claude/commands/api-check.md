# /api-check — Validar contratos backend ↔ frontend
Leer todos los schemas Pydantic en backend/app/schemas/
Leer todos los types en frontend/src/types/contracts.ts
Comparar campo por campo y reportar:
- Campos que existen en backend pero no en frontend
- Campos que existen en frontend pero no en backend
- Tipos que no coinciden
- Campos opcionales vs requeridos que no matchean
