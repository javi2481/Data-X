import pytest


def test_pipeline_orchestrator_importable():
    """Verifica que el módulo existe y la clase es importable (lo mínimo para que ARQ no rompa)."""
    from app.services.pipeline_orchestrator import PipelineOrchestrator
    assert callable(PipelineOrchestrator)


def test_pipeline_orchestrator_has_run_method():
    from app.services.pipeline_orchestrator import PipelineOrchestrator
    orchestrator = PipelineOrchestrator()
    assert hasattr(orchestrator, 'run_full_pipeline')
    import asyncio
    assert asyncio.iscoroutinefunction(orchestrator.run_full_pipeline)
