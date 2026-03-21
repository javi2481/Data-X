from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from app.core.config import settings

def setup_telemetry(app):
    """
    Configura OpenTelemetry para la aplicación FastAPI.
    """
    # Configurar el Resource con el nombre del servicio
    resource = Resource(attributes={
        SERVICE_NAME: settings.otel_service_name
    })

    # Crear el TracerProvider
    provider = TracerProvider(resource=resource)
    
    # Configurar el exportador a consola para desarrollo
    console_exporter = ConsoleSpanExporter()
    span_processor = BatchSpanProcessor(console_exporter)
    provider.add_span_processor(span_processor)

    # Establecer el TracerProvider global
    trace.set_tracer_provider(provider)

    # Instrumentar FastAPI
    FastAPIInstrumentor.instrument_app(app)
