from __future__ import annotations

import json
import time
import urllib.error
import urllib.request

BACKEND = "http://127.0.0.1:9090"
ONE_PIXEL_PNG = (
    "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
)


def request(path: str, payload: dict | None = None) -> object:
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(
        f"{BACKEND}{path}",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST" if data else "GET",
    )
    with urllib.request.urlopen(req, timeout=10) as response:
        return json.load(response)


def wait_for_backend() -> None:
    deadline = time.monotonic() + 60
    while time.monotonic() < deadline:
        try:
            request("/health")
            return
        except (OSError, urllib.error.HTTPError):
            time.sleep(1)
    raise TimeoutError("ML backend did not become healthy")


if __name__ == "__main__":
    wait_for_backend()
    result = request(
        "/predict",
        {
            "tasks": [
                {
                    "id": 1,
                    "data": {
                        "task_type": "retrieval",
                        "question": "Does the document identify the contracting party?",
                        "text": "Contact erika.muster@example.test. The contract names Acme GmbH.",
                        "image": ONE_PIXEL_PNG,
                    },
                }
            ],
            "project": "e2e",
            "label_config": "<View><Text name='candidate' value='$text'/><Choices name='relevance' toName='candidate'><Choice value='relevant'/></Choices></View>",
        },
    )
    predictions = result.get("results", result) if isinstance(result, dict) else result
    prediction = predictions[0]
    relevance = next(item for item in prediction["result"] if item["from_name"] == "relevance")
    assert relevance["value"]["choices"] == ["relevant"], result
    assert relevance["score"] == 0.91, result
    assert prediction["model_version"] == "e2e-multimodal-responses", result
    print(json.dumps({"status": "passed", "prediction": prediction}, indent=2))
