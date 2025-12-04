from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware
import logging

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("observability")

# Setup Tracer
trace.set_tracer_provider(TracerProvider())
tracer = trace.get_tracer(__name__)
trace.get_tracer_provider().add_span_processor(
    BatchSpanProcessor(ConsoleSpanExporter())
)

class ObservabilityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        with tracer.start_as_current_span(f"{request.method} {request.url.path}") as span:
            trace_id = format(span.get_span_context().trace_id, "032x")
            span.set_attribute("http.method", request.method)
            span.set_attribute("http.url", str(request.url))
            
            logger.info(f"Request: {request.method} {request.url.path} [TraceID: {trace_id}]")
            
            response = await call_next(request)
            
            span.set_attribute("http.status_code", response.status_code)
            logger.info(f"Response: {response.status_code} [TraceID: {trace_id}]")
            
            return response

def setup_observability(app: FastAPI):
    FastAPIInstrumentor.instrument_app(app)
    app.add_middleware(ObservabilityMiddleware)
