import pytest
from predictor import Predictor
from presidio_client import PiiResult
from settings import Settings


class FakePresidio:
    def __init__(self, fail=False):
        self.fail = fail

    def process(self, text):
        if self.fail:
            raise ConnectionError("unavailable")
        return PiiResult(
            entities=[{"start": 6, "end": 30, "entity_type": "EMAIL_ADDRESS", "score": 0.98}],
            redacted_text="Email <EMAIL_ADDRESS>",
        )

    @staticmethod
    def label(entity_type):
        return "EMAIL"


class FakeModel:
    def __init__(self):
        self.candidate = None
        self.image_urls = None

    def classify_relevance(self, question, candidate, image_urls=None):
        self.candidate = candidate
        self.image_urls = image_urls
        return "relevant", 0.9


def test_retrieval_redacts_before_model(monkeypatch):
    monkeypatch.setenv("PRESIDIO_ENABLED", "true")
    monkeypatch.setenv("MODEL_SEND_PII", "false")
    monkeypatch.setenv("MODEL_SEND_IMAGES", "false")
    model = FakeModel()
    predictor = Predictor(Settings(), presidio=FakePresidio(), model=model)
    result = predictor.predict_task(
        {
            "data": {
                "task_type": "retrieval",
                "question": "Who?",
                "text": "Email erika.muster@example.test",
                "image": "https://example.test/private-scan.png",
            }
        }
    )
    assert model.candidate == "Email <EMAIL_ADDRESS>"
    assert model.image_urls == []
    assert result["result"][0]["value"]["choices"] == ["relevant"]


def test_multimodal_images_are_forwarded_by_default(monkeypatch):
    monkeypatch.setenv("PRESIDIO_ENABLED", "false")
    monkeypatch.delenv("MODEL_SEND_IMAGES", raising=False)
    model = FakeModel()
    predictor = Predictor(Settings(), presidio=FakePresidio(), model=model)

    predictor.predict_task(
        {
            "data": {
                "task_type": "retrieval",
                "question": "What is shown?",
                "text": "A scanned page",
                "image": "https://example.test/page.png",
                "images": ["https://example.test/detail.png"],
            }
        }
    )

    assert model.image_urls == ["https://example.test/page.png", "https://example.test/detail.png"]


def test_pii_entities_become_label_studio_spans(monkeypatch):
    monkeypatch.setenv("PRESIDIO_ENABLED", "true")
    predictor = Predictor(Settings(), presidio=FakePresidio(), model=FakeModel())
    result = predictor.predict_task({"data": {"task_type": "pii", "text": "Email erika.muster@example.test"}})
    span = result["result"][0]
    assert span["from_name"] == "pii"
    assert span["value"]["labels"] == ["EMAIL"]
    assert result["result"][-1]["value"]["choices"] == ["required"]


def test_presidio_failure_is_fail_closed(monkeypatch):
    monkeypatch.setenv("PRESIDIO_ENABLED", "true")
    monkeypatch.setenv("PII_FAIL_CLOSED", "true")
    model = FakeModel()
    predictor = Predictor(Settings(), presidio=FakePresidio(fail=True), model=model)
    with pytest.raises(ConnectionError):
        predictor.predict_task({"data": {"task_type": "retrieval", "question": "Who?", "text": "secret"}})
    assert model.candidate is None
