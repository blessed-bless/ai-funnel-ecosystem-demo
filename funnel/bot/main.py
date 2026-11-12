import asyncio
import logging

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.types import KeyboardButton, Message, ReplyKeyboardMarkup

from funnel.ai import get_brain
from funnel.db import SessionLocal, init_db
from funnel.schemas import LeadCreate
from funnel.services import leads as lead_service
from funnel.settings import get_settings

logger = logging.getLogger(__name__)


def _keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Услуги"), KeyboardButton(text="Оставить заявку")],
            [KeyboardButton(text="Как устроена воронка")],
        ],
        resize_keyboard=True,
    )


def _source_from_start(text: str | None) -> str:
    if not text:
        return "telegram"
    parts = text.split(maxsplit=1)
    if len(parts) == 2 and parts[0] == "/start":
        code = parts[1].strip()[:64]
        return code or "telegram"
    return "telegram"


async def run_bot() -> None:
    settings = get_settings()
    if not settings.bot_enabled:
        raise SystemExit("TELEGRAM_BOT_TOKEN пуст — бот в демо можно не запускать, хватит API.")

    init_db()
    bot = Bot(token=settings.telegram_bot_token)
    dp = Dispatcher()
    brain = get_brain(settings)

    @dp.message(CommandStart())
    async def start(message: Message) -> None:
        source = _source_from_start(message.text)
        session_key = f"tg:{message.from_user.id}"
        with SessionLocal() as session:
            lead_service.add_turn(
                session,
                session_key,
                "system",
                f"source={source}",
            )
        await message.answer(
            "Демо-воронка blessed-bless.\n"
            "Я собираю интерес и контакт, потом кладу заявку в mini-CRM.\n"
            "Напиши задачу или жми кнопки.",
            reply_markup=_keyboard(),
        )

    @dp.message(Command("crm"))
    async def crm_hint(message: Message) -> None:
        await message.answer(f"CRM UI: {settings.public_base_url.rstrip('/')}/crm")

    @dp.message(F.text == "Услуги")
    async def services(message: Message) -> None:
        await message.answer(
            "Пилот под ключ: лендинг-источник → Telegram-бот с ИИ → mini-CRM заявок.\n"
            "Mock-мозг работает без ключей; настоящий LLM подключается через .env."
        )

    @dp.message(F.text == "Как устроена воронка")
    async def funnel_info(message: Message) -> None:
        await message.answer(
            "1) Человек приходит с меткой источника (?start=landing / ig_bio)\n"
            "2) Бот уточняет задачу\n"
            "3) После контакта создаётся лид в SQLite CRM\n"
            "4) Менеджер смотрит /crm"
        )

    @dp.message(F.text == "Оставить заявку")
    async def ask_lead(message: Message) -> None:
        await message.answer(
            "Напиши одной строкой: имя, контакт (@user / телефон) и что нужно. "
            "Или просто «оставь заявку» — я спрошу недостающее."
        )

    @dp.message(F.text)
    async def chat(message: Message) -> None:
        session_key = f"tg:{message.from_user.id}"
        text = message.text or ""
        with SessionLocal() as session:
            history = [
                item
                for item in lead_service.recent_history(session, session_key)
                if item["role"] in {"user", "assistant"}
            ]
            answer = await brain.reply(history, text)
            lead_service.add_turn(session, session_key, "user", text)
            lead_service.add_turn(session, session_key, "assistant", answer.text)

            created = None
            submit = answer.ready_to_submit or "отправь заявку" in text.lower()
            if submit and answer.contact:
                created = lead_service.create_lead(
                    session,
                    LeadCreate(
                        source="telegram",
                        name=answer.name or (message.from_user.full_name or ""),
                        contact=answer.contact,
                        interest=answer.interest or "telegram lead",
                        summary=answer.summary or text,
                        telegram_user_id=str(message.from_user.id),
                    ),
                )

        if created:
            await message.answer(
                f"Заявка #{created.id} в CRM.\n"
                f"Контакт: {created.contact}\n"
                f"Смотреть: {settings.public_base_url.rstrip('/')}/crm"
            )
            if settings.telegram_admin_chat_id:
                try:
                    await bot.send_message(
                        settings.telegram_admin_chat_id,
                        f"Новый лид #{created.id}: {created.contact} — {created.interest}",
                    )
                except Exception:
                    logger.exception("admin notify failed lead_id=%s", created.id)
            return

        await message.answer(answer.text, reply_markup=_keyboard())

    logger.info("bot polling started")
    await dp.start_polling(bot)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    asyncio.run(run_bot())


if __name__ == "__main__":
    main()
