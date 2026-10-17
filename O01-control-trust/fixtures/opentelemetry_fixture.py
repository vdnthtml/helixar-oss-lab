from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

exporter = InMemorySpanExporter()
provider = TracerProvider(resource=Resource.create({"service.name": "o01.invalid"}))
provider.add_span_processor(SimpleSpanProcessor(exporter))
trace.set_tracer_provider(provider)
tracer = trace.get_tracer("helixar.o01", "1.0")
with tracer.start_as_current_span("proposal.evaluate") as span:
    span.set_attribute("helixar.tenant.id", "tenant-a.invalid")
    span.set_attribute("helixar.policy.version", "policy.invalid.v1")
    span.set_attribute("helixar.receipt.id", "receipt.invalid")
spans = exporter.get_finished_spans()
assert len(spans) == 1
attrs = spans[0].attributes
assert attrs["helixar.tenant.id"] == "tenant-a.invalid"
assert not any(k in attrs for k in ("gen_ai.prompt", "gen_ai.completion", "tool.arguments"))
print("PASS otel_in_memory_export spans=1 sensitive_content_attributes=0")
