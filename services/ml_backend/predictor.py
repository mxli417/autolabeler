from __future__ import annotations

from presidio_client import PresidioClient
from responses_client import ResponsesClient
from settings import Settings


def task_image_urls(data: dict, limit: int) -> list[str]:
    """Collect Label Studio image/image(s) values without fetching them locally."""
    if limit <= 0:
        return []
    values = [data.get("image")]
    images = data.get("images", [])
    values.extend(images if isinstance(images, list) else [images])
    urls: list[str] = []
    for value in values:
        if isinstance(value, dict):
            value = value.get("image_url") or value.get("url")
        if isinstance(value, str) and value.strip() and value not in urls:
            urls.append(value.strip())
        if len(urls) >= limit:
            break
    return urls


class Predictor:
    """Turns task data into Label Studio results without storing document text."""

    def __init__(
        self,
        settings: Settings,
        presidio: PresidioClient | None = None,
        model: ResponsesClient | None = None,
    ):
        self.settings = settings
        self.presidio = presidio or PresidioClient(settings)
        self.model = model or ResponsesClient(settings)

    def predict_task(self, task: dict) -> dict:
        data = task.get("data", {})
        text = str(data.get("text", ""))
        question = str(data.get("question", ""))
        mode = data.get("task_type", "retrieval" if question else "pii")
        pii = None
        if self.settings.presidio_enabled:
            try:
                pii = self.presidio.process(text)
            except Exception:
                if self.settings.pii_fail_closed:
                    raise

        results = []
        scores = []
        if mode in {"pii", "auto"} and pii:
            for index, entity in enumerate(pii.entities):
                start, end = int(entity["start"]), int(entity["end"])
                results.append(
                    {
                        "id": f"pii-{index}-{start}-{end}",
                        "from_name": "pii",
                        "to_name": "source",
                        "type": "labels",
                        "value": {
                            "start": start,
                            "end": end,
                            "text": text[start:end],
                            "labels": [self.presidio.label(entity["entity_type"])],
                        },
                        "score": float(entity.get("score", 0.0)),
                    }
                )
                scores.append(float(entity.get("score", 0.0)))
            results.append(
                {
                    "from_name": "redaction",
                    "to_name": "source",
                    "type": "choices",
                    "value": {"choices": ["required" if pii.entities else "not_required"]},
                }
            )

        if mode in {"retrieval", "auto"}:
            model_text = text if self.settings.model_send_pii or not pii else pii.redacted_text
            image_urls = (
                task_image_urls(data, self.settings.model_max_images) if self.settings.model_send_images else []
            )
            label, confidence = self.model.classify_relevance(question, model_text, image_urls)
            results.append(
                {
                    "from_name": "relevance",
                    "to_name": "candidate",
                    "type": "choices",
                    "value": {"choices": [label]},
                    "score": confidence,
                }
            )
            scores.append(confidence)

        return {
            "result": results,
            "score": sum(scores) / len(scores) if scores else 0.0,
            "model_version": self.settings.model_version,
        }
