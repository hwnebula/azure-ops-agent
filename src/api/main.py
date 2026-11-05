"""FastAPI entry point. Run with `uvicorn api.main:app --reload` (needs the [api] extra)."""

from fastapi import FastAPI

app = FastAPI(title="azure-ops-agent", version="0.1.0")


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


# TODO: POST /ask with Entra ID bearer auth, calling agent.orchestrator.Orchestrator.
