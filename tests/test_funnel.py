import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Isolated in-memory DB before app import side effects settle.
os.environ["DATABASE_URL"] = "sqlite://"
os.environ["OPENAI_API_KEY"] = ""
os.environ["TELEGRAM_BOT_TOKEN"] = ""

from funnel.db import Base, get_session
from funnel.api.app import create_app
from funnel.settings import get_settings


@pytest.fixture()
def client(tmp_path: Path):
    get_settings.cache_clear()
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    def _override():
        session = TestingSession()
        try:
            yield session
        finally:
            session.close()

    app = create_app()
    app.dependency_overrides[get_session] = _override
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    get_settings.cache_clear()


def test_health(client: TestClient):
    res = client.get("/health")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "ok"
    assert body["llm"] == "mock"


def test_lead_crud_and_stats(client: TestClient):
    created = client.post(
        "/api/leads",
        json={
            "source": "landing",
            "name": "Анна",
            "contact": "@anna_demo",
            "interest": "бот + CRM",
            "summary": "Нужен пилот воронки",
        },
    )
    assert created.status_code == 200
    lead = created.json()
    assert lead["id"] >= 1
    assert lead["status"] == "new"

    listed = client.get("/api/leads")
    assert listed.status_code == 200
    assert len(listed.json()) == 1

    patched = client.patch(f"/api/leads/{lead['id']}", json={"status": "qualified"})
    assert patched.status_code == 200
    assert patched.json()["status"] == "qualified"

    stats = client.get("/api/stats").json()
    assert stats["leads_total"] == 1
    assert stats["leads_qualified"] == 1
    assert stats["by_source"]["landing"] == 1


def test_chat_mock_builds_draft(client: TestClient):
    first = client.post(
        "/api/chat",
        json={
            "session_key": "test-session",
            "message": "Привет",
            "source": "landing",
        },
    )
    assert first.status_code == 200
    assert "демо" in first.json()["reply"].lower() or "ворон" in first.json()["reply"].lower()

    second = client.post(
        "/api/chat",
        json={
            "session_key": "test-session",
            "message": "Оставь заявку, я @demo_boss, нужен бот под заявки",
            "source": "landing",
        },
    )
    assert second.status_code == 200
    body = second.json()
    assert body["ready_to_submit"] is True
    assert body["draft_lead"]["contact"] == "@demo_boss"

    lead = client.post("/api/leads", json=body["draft_lead"])
    assert lead.status_code == 200
    assert lead.json()["contact"] == "@demo_boss"


@pytest.mark.asyncio
async def test_mock_brain_offline():
    from funnel.ai.mock import MockBrain

    brain = MockBrain()
    reply = await brain.reply([], "оставь заявку, телефон +7 900 111-22-33")
    assert reply.ready_to_submit is True
    assert "79001112233" in reply.contact.replace("-", "").replace(" ", "") or "+79001112233" in reply.contact.replace(" ", "")
