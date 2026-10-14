from types import SimpleNamespace

import pytest
from responses_client import ResponsesClient, output_text
from settings import Settings


class FakeResponses:
    def __init__(self):
        self.request = None

    def create(self, **request):
        self.request = request
        return SimpleNamespace(output_text='{"label":"relevant","confidence":0.8}')


class FakeOpenAI:
    def __init__(self):
        self.responses = FakeResponses()


def test_model_api_key_is_enough_for_openai_defaults(monkeypatch):
    monkeypatch.setenv("MODEL_API_KEY", "test-key")
    monkeypatch.setenv("MODEL_BASE_URL", "https://api.openai.com/v1")
    monkeypatch.delenv("MODEL_ENABLED", raising=False)
    monkeypatch.delenv("MODEL_NAME", raising=False)
    monkeypatch.delenv("MODEL_SEND_IMAGES", raising=False)

    settings = Settings()

    assert settings.model_enabled is True
    assert settings.model_name == "gpt-6-luna"
    assert settings.model_send_images is True


def test_calls_multimodal_responses_api_through_litellm(monkeypatch):
    monkeypatch.setenv("MODEL_ENABLED", "true")
    monkeypatch.setenv("MODEL_PROVIDER", "litellm")
    monkeypatch.setenv("MODEL_BASE_URL", "http://model.test/v1")
    monkeypatch.setenv("MODEL_NAME", "document-vision")
    client = FakeOpenAI()

    result = ResponsesClient(Settings(), client=client).classify_relevance(
        "Who?",
        "The candidate",
        ["https://example.test/page.png"],
    )

    assert result == ("relevant", 0.8)
    request = client.responses.request
    assert request is not None
    assert "messages" not in request
    assert request["input"][0]["content"][0]["type"] == "input_text"
    assert request["input"][0]["content"][1] == {
        "type": "input_image",
        "image_url": "https://example.test/page.png",
        "detail": "auto",
    }
    assert request["store"] is False


def test_openai_requires_api_key(monkeypatch):
    monkeypatch.setenv("MODEL_ENABLED", "true")
    monkeypatch.setenv("MODEL_PROVIDER", "openai")
    monkeypatch.setenv("MODEL_NAME", "configured-model")
    monkeypatch.delenv("MODEL_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    with pytest.raises(ValueError, match="API_KEY"):
        ResponsesClient(Settings(), client=FakeOpenAI()).classify_relevance("Who?", "Candidate")


def test_litellm_uses_its_own_key_and_default_url(monkeypatch):
    monkeypatch.setenv("MODEL_PROVIDER", "litellm")
    monkeypatch.setenv("OPENAI_API_KEY", "must-not-leave")
    monkeypatch.setenv("LITELLM_API_KEY", "proxy-key")
    monkeypatch.delenv("MODEL_API_KEY", raising=False)
    monkeypatch.delenv("MODEL_BASE_URL", raising=False)

    settings = Settings()
    assert settings.model_api_key == "proxy-key"
    assert settings.model_base_url == "http://host.docker.internal:4000/v1"


def test_output_text_skips_non_message_items():
    response = {
        "output": [
            {"type": "reasoning", "summary": []},
            {"type": "message", "content": [{"type": "output_text", "text": "first"}]},
            {"type": "message", "content": [{"type": "output_text", "text": " second"}]},
        ]
    }
    assert output_text(response) == "first second"
