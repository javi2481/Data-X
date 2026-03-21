from opentelemetry import trace
import structlog

def add_otel_trace_info(_, __, event_dict):
    """
    Agrega trace_id y span_id a los logs de structlog si hay un span activo.
    """
    span = trace.get_current_span()
    if span and span.is_recording():
        ctx = span.get_span_context()
        if ctx.is_valid:
            event_dict["trace_id"] = hex(ctx.trace_id)
            event_dict["span_id"] = hex(ctx.span_id)
    return event_dict

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        add_otel_trace_info,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.ConsoleRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(0),
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
    cache_logger_on_first_use=True,
)


def get_logger(name: str = __name__):
    return structlog.get_logger(name)
