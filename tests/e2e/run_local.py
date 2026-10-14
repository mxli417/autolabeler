from __future__ import annotations

import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).parent


def start(script: str, **environment: str) -> subprocess.Popen:
    env = os.environ.copy()
    env.update(environment)
    return subprocess.Popen(
        [sys.executable, str(HERE / script)],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
    )


def wait_for(url: str) -> None:
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=1):
                return
        except OSError:
            time.sleep(0.2)
    raise TimeoutError(f"Service did not become ready: {url}")


if __name__ == "__main__":
    processes = [
        start("fake_presidio.py", ROLE="analyzer", PORT="3101"),
        start("fake_presidio.py", ROLE="anonymizer", PORT="3102"),
        start("fake_responses.py", PORT="4000"),
    ]
    try:
        wait_for("http://127.0.0.1:3101/health")
        wait_for("http://127.0.0.1:3102/health")
        wait_for("http://127.0.0.1:4000/health")
        processes.append(
            start(
                "local_backend.py",
                MODEL_VERSION="e2e-multimodal-responses",
                MODEL_ENABLED="true",
                MODEL_PROVIDER="litellm",
                MODEL_BASE_URL="http://127.0.0.1:4000/v1",
                MODEL_API_KEY="e2e-only",
                MODEL_NAME="e2e-multimodal",
                MODEL_SEND_PII="false",
                MODEL_SEND_IMAGES="true",
                PRESIDIO_ENABLED="true",
                PRESIDIO_ANALYZER_URL="http://127.0.0.1:3101",
                PRESIDIO_ANONYMIZER_URL="http://127.0.0.1:3102",
                PII_FAIL_CLOSED="true",
            )
        )
        wait_for("http://127.0.0.1:9090/health")
        completed = subprocess.run(
            [sys.executable, str(HERE / "smoke.py")],
            check=True,
            capture_output=True,
            text=True,
        )
        print(completed.stdout.strip())
    finally:
        for process in reversed(processes):
            process.terminate()
        for process in reversed(processes):
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
