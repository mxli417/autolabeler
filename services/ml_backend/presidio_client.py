from __future__ import annotations

from dataclasses import dataclass

from http_json import post_json
from settings import Settings

ENTITY_TO_LABEL = {
    "PERSON": "PERSON",
    "EMAIL_ADDRESS": "EMAIL",
    "PHONE_NUMBER": "PHONE",
    "LOCATION": "ADDRESS",
    "IP_ADDRESS": "ID",
    "IBAN_CODE": "ID",
    "CREDIT_CARD": "ID",
    "US_SSN": "ID",
}


@dataclass(frozen=True)
class PiiResult:
    entities: list[dict]
    redacted_text: str


class PresidioClient:
    """Owns PII detection and redaction; raw entity text is never returned or logged."""

    def __init__(self, settings: Settings):
        self.settings = settings

    def process(self, text: str) -> PiiResult:
        entities = post_json(
            f"{self.settings.presidio_analyzer_url}/analyze",
            {
                "text": text,
                "language": self.settings.presidio_language,
                "score_threshold": self.settings.presidio_score_threshold,
            },
            self.settings.presidio_timeout_seconds,
        )
        anonymized = post_json(
            f"{self.settings.presidio_anonymizer_url}/anonymize",
            {
                "text": text,
                "analyzer_results": entities,
                "anonymizers": {"DEFAULT": {"type": "replace"}},
            },
            self.settings.presidio_timeout_seconds,
        )
        return PiiResult(entities=entities, redacted_text=anonymized["text"])

    @staticmethod
    def label(entity_type: str) -> str:
        return ENTITY_TO_LABEL.get(entity_type, "OTHER")
