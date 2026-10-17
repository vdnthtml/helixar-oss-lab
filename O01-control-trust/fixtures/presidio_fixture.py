from presidio_analyzer import AnalyzerEngine, Pattern, PatternRecognizer, RecognizerRegistry
from presidio_anonymizer import AnonymizerEngine

registry = RecognizerRegistry(supported_languages=["en"])
registry.add_recognizer(PatternRecognizer(supported_entity="EMAIL_ADDRESS", patterns=[Pattern("email.invalid", r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.invalid", 0.9)]))
analyzer = AnalyzerEngine(registry=registry, nlp_engine=None, supported_languages=["en"])
text = "Contact operator@tenant.invalid with receipt.invalid only."
results = analyzer.analyze(text=text, language="en", entities=["EMAIL_ADDRESS"])
assert len(results) == 1 and abs(results[0].score - 0.9) < 1e-9, results
redacted = AnonymizerEngine().anonymize(text=text, analyzer_results=results).text
assert "operator@tenant.invalid" not in redacted and "<EMAIL_ADDRESS>" in redacted
print(f"PASS presidio_custom_recognizer matches={len(results)} redacted={redacted}")
