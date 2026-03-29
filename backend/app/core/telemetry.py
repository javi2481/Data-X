import os
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.pymongo import PymongoInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
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
    
    # Si hay un endpoint OTLP configurado, exportar allí (Producción).
    # De lo contrario, usar consola (Desarrollo).
    otlp_endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT")
    if otlp_endpoint:
        exporter = OTLPSpanExporter(endpoint=otlp_endpoint)
    else:
        exporter = ConsoleSpanExporter()
        
    span_processor = BatchSpanProcessor(exporter)
    provider.add_span_processor(span_processor)

    # Establecer el TracerProvider global
    trace.set_tracer_provider(provider)

    # Instrumentar FastAPI
    FastAPIInstrumentor.instrument_app(app)
    
    # Instrumentar bases de datos y red para trazas completas
    PymongoInstrumentor().instrument()
    HTTPXClientInstrumentor().instrument()
