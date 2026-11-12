import json
import re

import httpx

from funnel.ai.base import AIReply
from funnel.settings import Settings

SYSTEM_PROMPT = """Ты консультант демо-воронки для портфолио разработчика.
Помогаешь понять услугу: Telegram-бот с ИИ + mini-CRM + лендинг-источник лидов.
Собирай имя, контакт и интерес. Не выдумывай договорённости и цены как факт.
Если данных хватает для заявки, в конце ответа добавь JSON-блок ровно в формате:
```lead
{"name":"...","contact":"...","interest":"...","summary":"...","ready":true}
```
Иначе ready=false или блок не добавляй.
Отвечай коротко, по-русски, без канцелярита.
"""


class OpenAIBrain:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def reply(self, history: list[dict[str, str]], user_message: str) -> AIReply:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages.extend(history[-12:])
        messages.append({"role": "user", "content": user_message})

        payload = {
            "model": self._settings.openai_model,
            "messages": messages,
            "temperature": 0.4,
        }
        headers = {
            "Authorization": f"Bearer {self._settings.openai_api_key}",
            "Content-Type": "application/json",
        }
        url = f"{self._settings.openai_base_url.rstrip('/')}/chat/completions"

        async with httpx.AsyncClient(timeout=45.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()

        content = data["choices"][0]["message"]["content"]
        return _parse_lead_block(content)


def _parse_lead_block(content: str) -> AIReply:
    match = re.search(r"```lead\s*(\{.*?\})\s*```", content, re.S)
    clean = re.sub(r"```lead\s*\{.*?\}\s*```", "", content, flags=re.S).strip()
    if not match:
        return AIReply(text=clean or content.strip())

    try:
        raw = json.loads(match.group(1))
    except json.JSONDecodeError:
        return AIReply(text=clean or content.strip())

    return AIReply(
        text=clean or "Черновик заявки собран.",
        name=str(raw.get("name", ""))[:120],
        contact=str(raw.get("contact", ""))[:120],
        interest=str(raw.get("interest", ""))[:240],
        summary=str(raw.get("summary", ""))[:2000],
        ready_to_submit=bool(raw.get("ready")),
    )
