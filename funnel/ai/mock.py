import re

from funnel.ai.base import AIReply

PHONE_RE = re.compile(r"(?:\+?\d[\d\-\s()]{8,}\d)")
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")


class MockBrain:
    """Deterministic demo brain — works offline, no API key."""

    async def reply(self, history: list[dict[str, str]], user_message: str) -> AIReply:
        text = user_message.strip()
        lower = text.lower()
        joined = " ".join(m["content"] for m in history + [{"role": "user", "content": text}])

        name = _pick_name(joined)
        contact = _pick_contact(joined)
        interest = _pick_interest(joined, lower)

        if any(w in lower for w in ("заявк", "оставь", "свяжит", "хочу заказ", "нужен бот")):
            if not contact:
                return AIReply(
                    text=(
                        "Ок, оформлю черновик заявки. Напиши телефон или Telegram "
                        "для связи — и коротко, что нужно автоматизировать."
                    ),
                    name=name,
                    interest=interest or "автоматизация заявок",
                )
            summary = (
                f"Лид: {name or 'без имени'}; контакт: {contact}; "
                f"интерес: {interest or 'не уточнён'}."
            )
            return AIReply(
                text=(
                    "Черновик готов. Если всё верно — нажми «Отправить заявку» "
                    "или напиши «отправь заявку»."
                ),
                name=name,
                contact=contact,
                interest=interest or "автоматизация заявок",
                summary=summary,
                ready_to_submit=True,
            )

        if "цена" in lower or "сколько" in lower or "стоим" in lower:
            return AIReply(
                text=(
                    "В демо-витрине цены условные: пилот бота+CRM обычно "
                    "от 40–80 тыс. ₽ под задачу. Опиши нишу — соберу заявку менеджеру."
                ),
                name=name,
                contact=contact,
                interest=interest or "оценка пилота",
            )

        if any(w in lower for w in ("привет", "здравств", "hi", "hello")):
            return AIReply(
                text=(
                    "Привет. Я демо-ассистент воронки blessed-bless: отвечаю по услугам, "
                    "уточняю задачу и собираю заявку в mini-CRM. Что автоматизировать?"
                )
            )

        return AIReply(
            text=(
                "Понял. Могу подсказать по цепочке «лендинг → Telegram-бот с ИИ → CRM». "
                "Напиши задачу или скажи «оставь заявку» — соберу контакт."
            ),
            name=name,
            contact=contact,
            interest=interest or text[:120],
        )


def _pick_name(blob: str) -> str:
    match = re.search(r"(?:меня зовут|я)\s+([A-Za-zА-Яа-яЁё\-]{2,40})", blob, re.I)
    return match.group(1) if match else ""


def _pick_contact(blob: str) -> str:
    phone = PHONE_RE.search(blob)
    if phone:
        return re.sub(r"\s+", "", phone.group(0))
    email = EMAIL_RE.search(blob)
    if email:
        return email.group(0)
    tg = re.search(r"@([A-Za-z0-9_]{4,32})", blob)
    return f"@{tg.group(1)}" if tg else ""


def _pick_interest(blob: str, lower: str) -> str:
    if "crm" in lower or "срм" in lower:
        return "бот + CRM"
    if "ворон" in lower:
        return "воронка лидов"
    if "рассыл" in lower:
        return "рассылки"
    if "заяв" in lower:
        return "приём заявок"
    return ""
