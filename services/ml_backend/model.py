from __future__ import annotations

from label_studio_ml.model import LabelStudioMLBase
from predictor import Predictor
from settings import Settings


class DocumentEvalBackend(LabelStudioMLBase):
    """Label Studio adapter; Predictor orchestrates and ResponsesClient owns inference transport."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.settings = Settings()
        self.predictor = Predictor(self.settings)
        self.set("model_version", self.settings.model_version)

    def predict(self, tasks, context=None, **kwargs):
        return [self.predictor.predict_task(task) for task in tasks]

    def fit(self, event, data, **kwargs):
        # CE annotations are exported and evaluated offline; no implicit retraining.
        return {"status": "ignored", "reason": "offline evaluation backend"}
