from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from funnel.ai import get_brain
from funnel.db import get_session, init_db
from funnel.schemas import (
    ChatRequest,
    ChatResponse,
    FunnelStats,
    LeadCreate,
    LeadOut,
    LeadStatusUpdate,
)
from funnel.services import leads as lead_service
from funnel.settings import get_settings

STATIC_DIR = Path(__file__).resolve().parents[1] / "web" / "static"


def create_app() -> FastAPI:
    settings = get_settings()

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        init_db()
        yield

    app = FastAPI(
        title="AI Funnel Ecosystem Demo",
        version="0.1.0",
        description="Витрина: лендинг → чат/бот с ИИ → mini-CRM",
        lifespan=lifespan,
    )

    if STATIC_DIR.exists():
        app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    @app.get("/", response_class=HTMLResponse)
    def landing() -> FileResponse:
        index = STATIC_DIR / "index.html"
        if not index.exists():
            raise HTTPException(status_code=404, detail="Landing not found")
        return FileResponse(index)

    @app.get("/crm", response_class=HTMLResponse)
    def crm_page() -> FileResponse:
        page = STATIC_DIR / "crm.html"
        if not page.exists():
            raise HTTPException(status_code=404, detail="CRM UI not found")
        return FileResponse(page)

    @app.get("/health")
    def health() -> dict:
        return {
            "status": "ok",
            "env": settings.app_env,
            "llm": "openai" if settings.use_real_llm else "mock",
            "bot": settings.bot_enabled,
        }

    @app.post("/api/leads", response_model=LeadOut)
    def create_lead(payload: LeadCreate, session: Session = Depends(get_session)) -> LeadOut:
        if not payload.contact.strip():
            raise HTTPException(status_code=422, detail="contact is required")
        lead = lead_service.create_lead(session, payload)
        return LeadOut.model_validate(lead)

    @app.get("/api/leads", response_model=list[LeadOut])
    def list_leads(session: Session = Depends(get_session)) -> list[LeadOut]:
        return [LeadOut.model_validate(item) for item in lead_service.list_leads(session)]

    @app.get("/api/leads/{lead_id}", response_model=LeadOut)
    def get_lead(lead_id: int, session: Session = Depends(get_session)) -> LeadOut:
        lead = lead_service.get_lead(session, lead_id)
        if not lead:
            raise HTTPException(status_code=404, detail="lead not found")
        return LeadOut.model_validate(lead)

    @app.patch("/api/leads/{lead_id}", response_model=LeadOut)
    def patch_lead(
        lead_id: int,
        payload: LeadStatusUpdate,
        session: Session = Depends(get_session),
    ) -> LeadOut:
        lead = lead_service.update_status(session, lead_id, payload.status)
        if not lead:
            raise HTTPException(status_code=404, detail="lead not found")
        return LeadOut.model_validate(lead)

    @app.get("/api/stats", response_model=FunnelStats)
    def funnel_stats(session: Session = Depends(get_session)) -> FunnelStats:
        return lead_service.stats(session)

    @app.post("/api/chat", response_model=ChatResponse)
    async def chat(payload: ChatRequest, session: Session = Depends(get_session)) -> ChatResponse:
        history = lead_service.recent_history(session, payload.session_key)
        brain = get_brain(settings)
        answer = await brain.reply(history, payload.message)
        lead_service.add_turn(session, payload.session_key, "user", payload.message)
        lead_service.add_turn(session, payload.session_key, "assistant", answer.text)

        draft = None
        if answer.contact or answer.ready_to_submit:
            draft = LeadCreate(
                source=payload.source,
                name=answer.name,
                contact=answer.contact,
                interest=answer.interest,
                summary=answer.summary or answer.interest,
            )
        return ChatResponse(reply=answer.text, draft_lead=draft, ready_to_submit=answer.ready_to_submit)

    @app.post("/api/chat/submit", response_model=LeadOut)
    async def submit_from_chat(
        payload: ChatRequest,
        session: Session = Depends(get_session),
    ) -> LeadOut:
        """Force-submit: reuse last draft fields encoded in the message or create from chat."""
        history = lead_service.recent_history(session, payload.session_key)
        brain = get_brain(settings)
        answer = await brain.reply(history, payload.message)
        contact = answer.contact or payload.message.strip()
        if not contact:
            raise HTTPException(status_code=422, detail="не хватает контакта для заявки")
        lead = lead_service.create_lead(
            session,
            LeadCreate(
                source=payload.source,
                name=answer.name,
                contact=contact,
                interest=answer.interest or "заявка из чата",
                summary=answer.summary or payload.message,
            ),
            status="new",
        )
        return LeadOut.model_validate(lead)

    @app.middleware("http")
    async def demo_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Demo-Mode"] = "portfolio"
        return response

    return app


app = create_app()
