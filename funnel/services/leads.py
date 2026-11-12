from sqlalchemy import func, select
from sqlalchemy.orm import Session

from funnel.models import ConversationTurn, Lead
from funnel.schemas import FunnelStats, LeadCreate


def create_lead(session: Session, payload: LeadCreate, status: str = "new") -> Lead:
    lead = Lead(
        source=payload.source,
        name=payload.name.strip(),
        contact=payload.contact.strip(),
        interest=payload.interest.strip(),
        summary=payload.summary.strip(),
        telegram_user_id=payload.telegram_user_id.strip(),
        status=status,
    )
    session.add(lead)
    session.commit()
    session.refresh(lead)
    return lead


def list_leads(session: Session, limit: int = 100) -> list[Lead]:
    stmt = select(Lead).order_by(Lead.id.desc()).limit(limit)
    return list(session.scalars(stmt))


def get_lead(session: Session, lead_id: int) -> Lead | None:
    return session.get(Lead, lead_id)


def update_status(session: Session, lead_id: int, status: str) -> Lead | None:
    lead = session.get(Lead, lead_id)
    if not lead:
        return None
    lead.status = status
    session.commit()
    session.refresh(lead)
    return lead


def stats(session: Session) -> FunnelStats:
    total = session.scalar(select(func.count()).select_from(Lead)) or 0
    new_count = session.scalar(select(func.count()).where(Lead.status == "new")) or 0
    qualified = session.scalar(select(func.count()).where(Lead.status == "qualified")) or 0
    rows = session.execute(select(Lead.source, func.count()).group_by(Lead.source)).all()
    by_source = {source or "unknown": count for source, count in rows}
    return FunnelStats(
        leads_total=total,
        leads_new=new_count,
        leads_qualified=qualified,
        by_source=by_source,
    )


def add_turn(session: Session, session_key: str, role: str, content: str) -> None:
    session.add(ConversationTurn(session_key=session_key, role=role, content=content))
    session.commit()


def recent_history(session: Session, session_key: str, limit: int = 12) -> list[dict[str, str]]:
    stmt = (
        select(ConversationTurn)
        .where(ConversationTurn.session_key == session_key)
        .order_by(ConversationTurn.id.desc())
        .limit(limit)
    )
    turns = list(reversed(list(session.scalars(stmt))))
    return [{"role": t.role, "content": t.content} for t in turns]
