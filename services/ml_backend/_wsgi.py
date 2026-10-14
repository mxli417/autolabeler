from __future__ import annotations

import os

from label_studio_ml.api import init_app
from model import DocumentEvalBackend

app = init_app(model_class=DocumentEvalBackend)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "9090")))
