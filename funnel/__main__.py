import argparse
import uvicorn

from funnel.settings import get_settings


def main() -> None:
    parser = argparse.ArgumentParser(description="AI Funnel Ecosystem Demo")
    parser.add_argument("command", choices=["api", "bot"], help="api — FastAPI; bot — Telegram")
    args = parser.parse_args()
    settings = get_settings()

    if args.command == "api":
        uvicorn.run(
            "funnel.api.app:app",
            host=settings.api_host,
            port=settings.api_port,
            reload=False,
        )
        return

    from funnel.bot.main import main as bot_main

    bot_main()


if __name__ == "__main__":
    main()
