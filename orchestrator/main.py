"""Orchestrator entry point and FastAPI app."""

from __future__ import annotations
import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from common.config import get_settings
from common.logging import setup_logging, get_logger
from common.tracing import init_tracing
from orchestrator.agent_discovery import AgentDiscovery
from orchestrator.router import Router
from orchestrator.streaming import stream_response

logger = get_logger(__name__)

app = FastAPI(title="Multi-Agent Orchestrator", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

_discovery: AgentDiscovery | None = None
_router: Router | None = None


class QueryRequest(BaseModel):
    query: str
    stream: bool = False


@app.on_event("startup")
async def startup():
    global _discovery, _router
    _discovery = AgentDiscovery()
    _router = Router(_discovery)
    # Attempt agent discovery but don't fail if agents aren't up yet
    try:
        cards = await _discovery.discover_all()
        logger.info("agents_discovered", count=len(cards))
    except Exception as e:
        logger.warning("agent_discovery_partial", error=str(e))


@app.get("/health")
async def health():
    health_data = {"status": "ok", "service": "orchestrator"}
    if _discovery:
        try:
            agent_health = await _discovery.health_check()
            health_data["agents"] = agent_health
        except Exception:
            health_data["agents"] = {}
    return health_data


@app.get("/agents")
async def list_agents():
    if not _discovery:
        raise HTTPException(status_code=503, detail="Discovery not initialized")
    cards = await _discovery.discover_all()
    return {"agents": {name: card.model_dump() for name, card in cards.items()}}


@app.post("/query")
async def query(request: QueryRequest):
    if not _router:
        raise HTTPException(status_code=503, detail="Router not initialized")

    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    logger.info("orchestrator_query", query=request.query[:100], stream=request.stream)

    try:
        response = await _router.route(request.query)

        if request.stream:
            return StreamingResponse(
                stream_response(response),
                media_type="text/event-stream",
                headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
            )

        return response.model_dump()

    except Exception as e:
        logger.exception("orchestrator_error")
        raise HTTPException(status_code=500, detail={"message": str(e)})


@app.post("/query/stream")
async def query_stream(request: QueryRequest):
    """Convenience endpoint that always streams."""
    request.stream = True
    return await query(request)


def main():
    setup_logging()
    logger = get_logger("orchestrator")
    settings = get_settings()
    init_tracing("orchestrator")

    logger.info("orchestrator_starting", port=settings.orchestrator_port)

    uvicorn.run(
        "orchestrator.main:app",
        host="0.0.0.0",
        port=settings.orchestrator_port,
        log_config=None,
        reload=settings.app_env == "development",
    )


if __name__ == "__main__":
    main()
