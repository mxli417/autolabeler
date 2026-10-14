# Security checks

The regular pre-commit checks stay fast. Before a release, run the manual Trivy hook:

```bash
uv run pre-commit run trivy --hook-stage manual
```

The script uses the pinned `aquasec/trivy:0.75.0` container. It scans Dockerfiles and `compose.yaml`, pulls the current `python:3.12-slim-bookworm` base, builds the workbench and ML backend, then scans both images for fixable high and critical vulnerabilities. Its databases are cached in the `autolabeler_trivy_cache` Docker volume.

For a quick configuration-only check, run:

```powershell
pwsh -NoProfile -File scripts/security-scan.ps1 -ConfigOnly
```

Use `-SkipBuild` only when both `autolabeler-workbench:local` and `autolabeler-ml-backend:local` already exist. The image scan mounts the local Docker socket read-only so Trivy can inspect those images.

Both application images run as the unprivileged `app` user. On Linux, make sure the bind-mounted project and `workspace/` paths are writable by that user when using the workbench API; the CLI on the host is unaffected.

This is a dependency and configuration check, not a full security assessment. It does not detect unsafe application logic, leaked secrets already stored elsewhere, weak Label Studio permissions, prompt injection, or PII sent to a remote model endpoint. Review the report instead of adding broad ignores; if a finding must be accepted, record its identifier, rationale, owner, and expiry.
