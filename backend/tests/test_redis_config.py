def test_redis_settings_come_from_config():
    """Verifica que job_queue usa la configuración centralizada de Settings."""
    from app.services.job_queue import JobQueueService
    from app.core.config import settings
    svc = JobQueueService()
    assert svc.redis_settings.host == settings.redis_host
    assert svc.redis_settings.port == settings.redis_port
